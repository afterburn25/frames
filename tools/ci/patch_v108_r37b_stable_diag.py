#!/usr/bin/env python3
from pathlib import Path
import hashlib, subprocess, sys
if len(sys.argv)!=2: raise SystemExit('usage: patch_v108_r37b_stable_diag.py <kernel/main.nx>')
p=Path(sys.argv[1])
base=Path(__file__).with_name('patch_v108_r37_g750jm_xhci_ring_ps2.py')
subprocess.run([sys.executable,str(base),str(p)],check=True,stdout=subprocess.DEVNULL)
s=p.read_text()
BASE='03f446845e111e35b8cff6b216c5fee2d214dc0a4d6e25898f8a03b891c0c511'
if hashlib.sha256(s.encode()).hexdigest()!=BASE: raise SystemExit('r37 base mismatch')

def rep(old,new,label):
 global s
 n=s.count(old)
 if n!=1: raise SystemExit(f'{label} count {n}')
 s=s.replace(old,new,1)

# r36 physical testing showed that whole-panel diagnostic redraws can interfere
# with touchpad responsiveness and make evidence photography difficult. r37b
# keeps the full overlay for low-rate semantic state changes, but updates the
# high-rate xHCI endpoint row in an isolated dirty rectangle.
anchor='fn v108_input_overlay_present(process:u64,state:u64,input_state:u64,xhci:u64) -> u64 {'
helper=r'''fn v108_input_overlay_r37_draw_v137(surface:u64,xhci:u64) -> u64 {
    if surface==0 { return 0; }
    let w=volatile_read64(surface+16); var px:u64=8; if w>430 { px=w-420; }
    let py:u64=8; let bg:u64=4279308561; let white:u64=4294244347; let green:u64=4286644030; let amber:u64=4294934528; let red:u64=4294907956;
    if display_fill_rect(surface,(px*65536)+(py+726),(410*65536)+28,bg)==0 { return 0; }
    v108_text_r37_v137(surface,px+10,py+730,white);
    if xhci!=0 {
        v108_draw_small_u64(surface,((px+112)*65536)+(py+730),volatile_read64(xhci+2696),green);
        v108_draw_small_u64(surface,((px+160)*65536)+(py+730),volatile_read64(xhci+2824),amber);
        v108_draw_small_u64(surface,((px+208)*65536)+(py+730),volatile_read64(xhci+2832),white);
        v108_draw_small_u64(surface,((px+256)*65536)+(py+730),volatile_read64(xhci+2728),white);
        v108_draw_small_u64(surface,((px+316)*65536)+(py+730),volatile_read64(xhci+2816),green);
        v108_draw_small_u64(surface,((px+376)*65536)+(py+730),volatile_read64(xhci+2784),red);
    }
    return 1;
}
fn v108_input_overlay_r37_present_v137(process:u64,state:u64,input_state:u64,xhci:u64) -> u64 {
    if process==0 || state==0 { return 0; }
    let surface=volatile_read64(process+616); let dirty=volatile_read64(process+624); let cursor=volatile_read64(process+640); let timing=volatile_read64(process+664); let present=volatile_read64(process+672);
    if surface==0 || dirty==0 || cursor==0 || timing==0 || present==0 { return 0; }
    let cx=volatile_read64(state+8); let cy=volatile_read64(state+16); let w=volatile_read64(surface+16); var px:u64=8; if w>430 { px=w-420; } let py:u64=8;
    var overlap:u64=0; if cx+8>px && cx<px+410 && cy+16>py+726 && cy<py+754 { overlap=1; }
    if overlap!=0 { v108_cursor_restore(cursor,surface); }
    if v108_input_overlay_r37_draw_v137(surface,xhci)==0 { return 0; }
    if overlap!=0 { if v108_cursor_capture(cursor,surface,cx,cy)==0 { return 0; } if v108_input_pointer_draw_v115(surface,state,input_state)==0 { return 0; } }
    let xy=(px*65536)+(py+726); let wh=(410*65536)+28;
    if dirty_add(dirty,xy,wh,16)==0 || present_enqueue(present,xy,wh,16)==0 { return 0; }
    if overlap!=0 { dirty_add(dirty,(cx*65536)+cy,(8*65536)+16,16); present_enqueue(present,(cx*65536)+cy,(8*65536)+16,16); }
    if present_flush(present,surface,timing)==0 { return 0; }
    return 1;
}
'''+anchor
rep(anchor,helper,'compact r37 endpoint row helpers')

old='''        var telemetry_redraw:u64=0; if xhci!=0 { let rs=volatile_read64(xhci+2696); let rq=volatile_read64(xhci+2824); let rc=volatile_read64(xhci+2832); let rf=volatile_read64(xhci+2816); let re=volatile_read64(xhci+2784); var changed:u64=0; if rs!=last_r37_s || rq!=last_r37_q || rc!=last_r37_c || rf!=last_r37_f || re!=last_r37_e { changed=1; } let dnow=read_tsc(); if changed!=0 && (dnow<last_r37_draw || dnow-last_r37_draw>=1000000000) { telemetry_redraw=1; last_r37_draw=dnow; } last_r37_s=rs; last_r37_q=rq; last_r37_c=rc; last_r37_f=rf; last_r37_e=re; } var motion_telemetry_redraw:u64=0;'''
new='''        var telemetry_redraw:u64=0; var r37_telemetry_redraw:u64=0; if xhci!=0 { let rs=volatile_read64(xhci+2696); let rq=volatile_read64(xhci+2824); let rc=volatile_read64(xhci+2832); let rf=volatile_read64(xhci+2816); let re=volatile_read64(xhci+2784); var changed:u64=0; if rs!=last_r37_s || rq!=last_r37_q || rc!=last_r37_c || rf!=last_r37_f || re!=last_r37_e { changed=1; } let dnow=read_tsc(); if changed!=0 && (dnow<last_r37_draw || dnow-last_r37_draw>=2000000000) { r37_telemetry_redraw=1; last_r37_draw=dnow; } last_r37_s=rs; last_r37_q=rq; last_r37_c=rc; last_r37_f=rf; last_r37_e=re; } var motion_telemetry_redraw:u64=0;'''
rep(old,new,'isolated endpoint telemetry scheduling')

# Report-count churn is useful in the RAM recorder but must not repaint all 760
# pixels of the diagnostics panel on every successful USB report.
rep('''        let usb_now=volatile_read64(input_state+3128); if usb_now!=last_usb_r { last_usb_r=usb_now; telemetry_redraw=1; }''','''        let usb_now=volatile_read64(input_state+3128); if usb_now!=last_usb_r { last_usb_r=usb_now; }''','high-rate USB report redraw suppression')

old='''        if telemetry_redraw!=0 { if v108_input_overlay_present(process,state,input_state,xhci)==0 { return 0; } } else { if motion_telemetry_redraw!=0 { if v108_input_overlay_motion_present_v133c(process,input_state)==0 { return 0; } } }'''
new='''        if telemetry_redraw!=0 { if v108_input_overlay_present(process,state,input_state,xhci)==0 { return 0; } } else { if r37_telemetry_redraw!=0 { if v108_input_overlay_r37_present_v137(process,state,input_state,xhci)==0 { return 0; } } else { if motion_telemetry_redraw!=0 { if v108_input_overlay_motion_present_v133c(process,input_state)==0 { return 0; } } } }'''
rep(old,new,'compact endpoint present integration')

p.write_text(s)
out=hashlib.sha256(s.encode()).hexdigest()
EXPECTED='2cb422d2c7d00cdbb1da3eee4ee696c9ae0723b3f28669bf80efe256d14de650'
if out!=EXPECTED: raise SystemExit(f'r37b output sha mismatch {out}')
print(out)
