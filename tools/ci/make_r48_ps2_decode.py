#!/usr/bin/env python3
from pathlib import Path
import sys

p=Path(sys.argv[1]); s=p.read_text()

def rep(old,new,label):
    n=s.count(old)
    if n!=1: raise SystemExit(f'{label}: expected 1 site, found {n}')
    return s.replace(old,new)

# Diagnostic title R47 -> R48.
s=rep(s,
'''pointer_diag_draw_tag4(surface,(78*65536)+18,82+(52*256)+(55*65536)+(32*16777216),green);    // R47''',
'''pointer_diag_draw_tag4(surface,(78*65536)+18,82+(52*256)+(56*65536)+(32*16777216),green);    // R48''','title')

# Capture each completed 3-byte frame before the existing header check.
s=rep(s,
'''        let header=volatile_read64(input_state+2808); let dx=volatile_read64(input_state+2816);
        unsafe {
            volatile_write64(input_state+3016,data);''',
'''        let header=volatile_read64(input_state+2808); let dx=volatile_read64(input_state+2816);
        let r48_frame_diag=volatile_read64(input_state+3976);
        if r48_frame_diag!=0 { unsafe { volatile_write64(r48_frame_diag+320,header%256); volatile_write64(r48_frame_diag+328,dx%256); volatile_write64(r48_frame_diag+336,data%256); volatile_write64(r48_frame_diag+344,volatile_read64(r48_frame_diag+344)+1); } }
        unsafe {
            volatile_write64(input_state+3016,data);''','frame capture')

# Record header-valid decision while retaining existing behavior.
s=rep(s,
'''        if (header/8)%2==0 {
            unsafe { volatile_write64(input_state+3064,volatile_read64(input_state+3064)+1); }
            return 1;
        }
        return ps2_mouse_decode_packet(input_state,header,dx,data);''',
'''        if (header/8)%2==0 {
            if r48_frame_diag!=0 { unsafe { volatile_write64(r48_frame_diag+352,0); volatile_write64(r48_frame_diag+360,volatile_read64(r48_frame_diag+360)+1); } }
            unsafe { volatile_write64(input_state+3064,volatile_read64(input_state+3064)+1); }
            return 1;
        }
        if r48_frame_diag!=0 { unsafe { volatile_write64(r48_frame_diag+352,1); volatile_write64(r48_frame_diag+368,volatile_read64(r48_frame_diag+368)+1); } }
        return ps2_mouse_decode_packet(input_state,header,dx,data);''','header valid')

# Count packet-decoder entries and preserve latest raw packet bytes.
s=rep(s,
'''fn ps2_mouse_decode_packet(input_state:u64,header:u64,dx:u64,dy:u64) -> u64 {
    if input_state==0 || volatile_read64(input_state+32)!=1 { return 0; }
    if (header/8)%2==0 { unsafe { volatile_write64(input_state+2960,volatile_read64(input_state+2960)+1); } return 0; }''',
'''fn ps2_mouse_decode_packet(input_state:u64,header:u64,dx:u64,dy:u64) -> u64 {
    if input_state==0 || volatile_read64(input_state+32)!=1 { return 0; }
    let r48_packet_diag=volatile_read64(input_state+3976);
    if r48_packet_diag!=0 { unsafe { volatile_write64(r48_packet_diag+376,volatile_read64(r48_packet_diag+376)+1); volatile_write64(r48_packet_diag+320,header%256); volatile_write64(r48_packet_diag+328,dx%256); volatile_write64(r48_packet_diag+336,dy%256); } }
    if (header/8)%2==0 { unsafe { volatile_write64(input_state+2960,volatile_read64(input_state+2960)+1); } return 0; }''','packet entry')

# Record decoded signed magnitudes and the exact emit-call boundary.
s=rep(s,
'''    let packed=buttons+(x_mag*256)+(x_neg*131072)+(y_mag*262144)+(y_neg*134217728);
    if x_mag>96 || y_mag>96 { let snap=(x_mag%512)+((x_neg%2)*512)+((y_mag%512)*1024)+((y_neg%2)*524288); ps2_diag_snapshot_jump(input_state,header+(dx*256)+(dy*65536),snap); }
    generic_pointer_emit_relative(input_state,1,packed);''',
'''    let packed=buttons+(x_mag*256)+(x_neg*131072)+(y_mag*262144)+(y_neg*134217728);
    if r48_packet_diag!=0 { unsafe { volatile_write64(r48_packet_diag+384,(x_mag%512)+((x_neg%2)*512)); volatile_write64(r48_packet_diag+392,(y_mag%512)+((y_neg%2)*512)); } }
    if x_mag>96 || y_mag>96 { let snap=(x_mag%512)+((x_neg%2)*512)+((y_mag%512)*1024)+((y_neg%2)*524288); ps2_diag_snapshot_jump(input_state,header+(dx*256)+(dy*65536),snap); }
    if r48_packet_diag!=0 { unsafe { volatile_write64(r48_packet_diag+400,volatile_read64(r48_packet_diag+400)+1); } }
    generic_pointer_emit_relative(input_state,1,packed);''','emit boundary')

# Reuse the eight lowest right-column rows for r48 telemetry.
rows=[
('''    pointer_diag_row(surface,(642*65536)+158,79+(86*256)+(70*65536)+(76*16777216),volatile_read64(input_state+3024));        // OVFL''','''    pointer_diag_row(surface,(642*65536)+158,82+(72*256)+(68*65536)+(82*16777216),volatile_read64(diag+320));               // RHDR'''),
('''    pointer_diag_row(surface,(642*65536)+170,72+(48*256)+(48*65536)+(48*16777216),h0);                                       // H000''','''    pointer_diag_row(surface,(642*65536)+170,82+(88*256)+(66*65536)+(89*16777216),volatile_read64(diag+328));               // RXBY'''),
('''    pointer_diag_row(surface,(642*65536)+182,72+(48*256)+(48*65536)+(49*16777216),h1);                                       // H001''','''    pointer_diag_row(surface,(642*65536)+182,82+(89*256)+(66*65536)+(89*16777216),volatile_read64(diag+336));               // RYBY'''),
('''    pointer_diag_row(surface,(642*65536)+194,72+(48*256)+(48*65536)+(50*16777216),h2);                                       // H002''','''    pointer_diag_row(surface,(642*65536)+194,72+(86*256)+(65*65536)+(76*16777216),volatile_read64(diag+352));               // HVAL'''),
('''    pointer_diag_row(surface,(642*65536)+206,72+(48*256)+(48*65536)+(51*16777216),h3);                                       // H003''','''    pointer_diag_row(surface,(642*65536)+206,80+(68*256)+(73*65536)+(78*16777216),volatile_read64(diag+376));               // PDIN'''),
('''    pointer_diag_row(surface,(642*65536)+218,75+(66*256)+(89*65536)+(84*16777216),volatile_read64(input_state+3768));       // KBYT''','''    pointer_diag_row(surface,(642*65536)+218,68+(88*256)+(77*65536)+(71*16777216),volatile_read64(diag+384));               // DXMG'''),
]
for old,new in rows: s=rep(s,old,new,'panel row')

# Replace guarded BARR/BARF rows with always-visible DYMG/EMIT rows.
s=rep(s,
'''    let d39=volatile_read64(input_state+3976); if d39!=0 {
        pointer_diag_row(surface,(642*65536)+230,66+(65*256)+(82*65536)+(82*16777216),volatile_read64(d39+96));           // BARR
        pointer_diag_row(surface,(642*65536)+242,66+(65*256)+(82*65536)+(70*16777216),volatile_read64(d39+104));          // BARF
    }''',
'''    pointer_diag_row(surface,(642*65536)+230,68+(89*256)+(77*65536)+(71*16777216),volatile_read64(diag+392));               // DYMG
    pointer_diag_row(surface,(642*65536)+242,69+(77*256)+(73*65536)+(84*16777216),volatile_read64(diag+400));               // EMIT''','bottom panel')

p.write_text(s)
