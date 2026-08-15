#!/usr/bin/env python3
from pathlib import Path
import subprocess, sys

p=Path(sys.argv[1])
subprocess.check_call([sys.executable, str(Path(__file__).with_name('make_r50_ps2_phase_fix.py')), str(p)])
s=p.read_text()

def rep(old,new,label):
    global s
    n=s.count(old)
    if n!=1:
        raise SystemExit(f'{label}: expected 1 site, found {n}')
    s=s.replace(old,new)

rep('pointer_diag_draw_tag4(surface,(78*65536)+18,82+(53*256)+(48*65536)+(32*16777216),green);    // R50',
    'pointer_diag_draw_tag4(surface,(78*65536)+18,82+(53*256)+(51*65536)+(66*16777216),green);    // R53B',
    'title')

# Rolling 12-byte physical AUX capture. Diagnostic-only; packet behavior unchanged.
rep('''fn ps2_mouse_decode_byte(input_state:u64,data:u64) -> u64 {\n    if input_state==0 || volatile_read64(input_state+32)!=1 { return 0; }\n    var packet_size=volatile_read64(input_state+3096); if packet_size!=4 { packet_size=3; }''',
'''fn ps2_mouse_decode_byte(input_state:u64,data:u64) -> u64 {\n    if input_state==0 || volatile_read64(input_state+32)!=1 { return 0; }\n    let r53b_diag=volatile_read64(input_state+3976);\n    if r53b_diag!=0 {\n        let a=volatile_read64(r53b_diag+544)%4294967296;\n        let b=volatile_read64(r53b_diag+552)%4294967296;\n        let c=volatile_read64(r53b_diag+560)%4294967296;\n        let na=((a%16777216)*256)+((b/16777216)%256);\n        let nb=((b%16777216)*256)+((c/16777216)%256);\n        let nc=((c%16777216)*256)+(data%256);\n        unsafe {\n            volatile_write64(r53b_diag+544,na);\n            volatile_write64(r53b_diag+552,nb);\n            volatile_write64(r53b_diag+560,nc);\n            volatile_write64(r53b_diag+576,volatile_read64(r53b_diag+576)+1);\n        }\n    }\n    var packet_size=volatile_read64(input_state+3096); if packet_size!=4 { packet_size=3; }\n    if r53b_diag!=0 { unsafe { volatile_write64(r53b_diag+584,packet_size); } }''',
    'raw AUX rolling capture')

rep('''fn ps2_mouse_decode_packet(input_state:u64,header:u64,dx:u64,dy:u64) -> u64 {\n    if input_state==0 || volatile_read64(input_state+32)!=1 { return 0; }''',
'''fn ps2_mouse_decode_packet(input_state:u64,header:u64,dx:u64,dy:u64) -> u64 {\n    if input_state==0 || volatile_read64(input_state+32)!=1 { return 0; }\n    let r53b_pkt_diag=volatile_read64(input_state+3976);\n    if r53b_pkt_diag!=0 { unsafe { volatile_write64(r53b_pkt_diag+568,(header%256)+((dx%256)*256)+((dy%256)*65536)); } }''',
    'interpreted packet capture')

# Read physical xHCI HID state directly in the diagnostic panel. This distinguishes
# enumeration/configuration, protocol selection, interrupt-IN arming, and report completion.
rep('''    let diag=volatile_read64(input_state+3976);\n    var h0:u64=0; var h1:u64=0; var h2:u64=0; var h3:u64=0;''',
'''    let diag=volatile_read64(input_state+3976);\n    let r53b_xhci=volatile_read64(input_state+3008);\n    var ucfg:u64=0; var uprt:u64=0; var uarm:u64=0; var urpt:u64=0; var ulen:u64=0; var u0b:u64=0; var u1b:u64=0;\n    if r53b_xhci!=0 { ucfg=volatile_read64(r53b_xhci+416); uprt=volatile_read64(r53b_xhci+336); uarm=volatile_read64(r53b_xhci+808); urpt=volatile_read64(r53b_xhci+816); ulen=volatile_read64(r53b_xhci+440); u0b=volatile_read64(r53b_xhci+456); u1b=volatile_read64(r53b_xhci+464); }\n    var h0:u64=0; var h1:u64=0; var h2:u64=0; var h3:u64=0;''',
    'USB panel state locals')

# Middle-column lower rows become physical USB HID state.
repls=[
('pointer_diag_row(surface,(330*65536)+134,80+(50*256)+(69*65536)+(82*16777216),volatile_read64(input_state+3120));       // P2ER',
 'pointer_diag_row(surface,(330*65536)+134,1195787093,ucfg);                                                                  // UCFG'),
('pointer_diag_row(surface,(330*65536)+146,82+(73*256)+(78*65536)+(71*16777216),volatile_read64(input_state+3216));       // RING',
 'pointer_diag_row(surface,(330*65536)+146,1414680661,uprt);                                                                  // UPRT'),
('pointer_diag_row(surface,(330*65536)+158,67+(66*256)+(75*65536)+(86*16777216),volatile_read64(gui_state+192));          // CBKV',
 'pointer_diag_row(surface,(330*65536)+158,1297236053,uarm);                                                                  // UARM'),
('pointer_diag_row(surface,(330*65536)+170,67+(66*256)+(75*65536)+(88*16777216),volatile_read64(gui_state+200));          // CBKX',
 'pointer_diag_row(surface,(330*65536)+170,1414546005,urpt);                                                                  // URPT'),
('pointer_diag_row(surface,(330*65536)+182,67+(66*256)+(75*65536)+(89*16777216),volatile_read64(gui_state+208));          // CBKY',
 'pointer_diag_row(surface,(330*65536)+182,1313164373,ulen);                                                                  // ULEN'),
('pointer_diag_row(surface,(330*65536)+194,70+(85*256)+(76*65536)+(76*16777216),volatile_read64(gui_state+136));          // FULL',
 'pointer_diag_row(surface,(330*65536)+194,540156501,u0b);                                                                    // U0B '),
('pointer_diag_row(surface,(330*65536)+206,67+(85*256)+(82*65536)+(80*16777216),volatile_read64(gui_state+144));          // CURP',
 'pointer_diag_row(surface,(330*65536)+206,540222037,u1b);                                                                    // U1B '),
]
for old,new in repls:
    rep(old,new,'USB panel row')

# Right lower rows become raw AUX rolling stream + interpreted 3-byte packet.
repls2=[
('pointer_diag_row(surface,(642*65536)+182,1129525331,volatile_read64(diag+448));                                              // S0SC',
 'pointer_diag_row(surface,(642*65536)+182,811024722,volatile_read64(diag+544));                                              // RAW0'),
('pointer_diag_row(surface,(642*65536)+194,1129525587,volatile_read64(diag+456));                                              // S1SC',
 'pointer_diag_row(surface,(642*65536)+194,827801938,volatile_read64(diag+552));                                              // RAW1'),
('pointer_diag_row(surface,(642*65536)+206,1129525843,volatile_read64(diag+464));                                              // S2SC',
 'pointer_diag_row(surface,(642*65536)+206,844579154,volatile_read64(diag+560));                                              // RAW2'),
('pointer_diag_row(surface,(642*65536)+218,1397639511,volatile_read64(diag+488));                                              // WINS',
 'pointer_diag_row(surface,(642*65536)+218,861162320,volatile_read64(diag+568));                                              // PKT3'),
('pointer_diag_row(surface,(642*65536)+230,1413892179,volatile_read64(diag+496));                                           // SHFT',
 'pointer_diag_row(surface,(642*65536)+230,1414415186,volatile_read64(diag+576));                                           // RCNT'),
('pointer_diag_row(surface,(642*65536)+242,1262702412,volatile_read64(diag+472));                                           // LOCK',
 'pointer_diag_row(surface,(642*65536)+242,1514754896,volatile_read64(diag+584));                                           // PSIZ'),
]
for old,new in repls2:
    rep(old,new,'PS2 capture row')

p.write_text(s)
