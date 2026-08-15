#!/usr/bin/env python3
from pathlib import Path
import subprocess, sys

p=Path(sys.argv[1])
subprocess.check_call([sys.executable, str(Path(__file__).with_name('make_r52_ps2_bounded_delta.py')), str(p)])
s=p.read_text()

def rep(old,new,label):
    global s
    n=s.count(old)
    if n!=1:
        raise SystemExit(f'{label}: expected 1 site, found {n}')
    s=s.replace(old,new)

rep('pointer_diag_draw_tag4(surface,(78*65536)+18,82+(53*256)+(50*65536)+(32*16777216),green);    // R52',
    'pointer_diag_draw_tag4(surface,(78*65536)+18,82+(53*256)+(51*65536)+(32*16777216),green);    // R53',
    'title')

rep('''fn ps2_mouse_decode_byte(input_state:u64,data:u64) -> u64 {\n    if input_state==0 || volatile_read64(input_state+32)!=1 { return 0; }\n    var packet_size=volatile_read64(input_state+3096); if packet_size!=4 { packet_size=3; }''',
'''fn ps2_mouse_decode_byte(input_state:u64,data:u64) -> u64 {\n    if input_state==0 || volatile_read64(input_state+32)!=1 { return 0; }\n    let r53_diag=volatile_read64(input_state+3976);\n    if r53_diag!=0 {\n        let a=volatile_read64(r53_diag+544)%4294967296;\n        let b=volatile_read64(r53_diag+552)%4294967296;\n        let c=volatile_read64(r53_diag+560)%4294967296;\n        let na=((a%16777216)*256)+((b/16777216)%256);\n        let nb=((b%16777216)*256)+((c/16777216)%256);\n        let nc=((c%16777216)*256)+(data%256);\n        unsafe {\n            volatile_write64(r53_diag+544,na);\n            volatile_write64(r53_diag+552,nb);\n            volatile_write64(r53_diag+560,nc);\n            volatile_write64(r53_diag+576,volatile_read64(r53_diag+576)+1);\n        }\n    }\n    var packet_size=volatile_read64(input_state+3096); if packet_size!=4 { packet_size=3; }\n    if r53_diag!=0 { unsafe { volatile_write64(r53_diag+584,packet_size); } }''',
    'raw AUX rolling capture')

rep('''fn ps2_mouse_decode_packet(input_state:u64,header:u64,dx:u64,dy:u64) -> u64 {\n    if input_state==0 || volatile_read64(input_state+32)!=1 { return 0; }''',
'''fn ps2_mouse_decode_packet(input_state:u64,header:u64,dx:u64,dy:u64) -> u64 {\n    if input_state==0 || volatile_read64(input_state+32)!=1 { return 0; }\n    let r53_pkt_diag=volatile_read64(input_state+3976);\n    if r53_pkt_diag!=0 { unsafe { volatile_write64(r53_pkt_diag+568,(header%256)+((dx%256)*256)+((dy%256)*65536)); } }''',
    'interpreted packet capture')

rep('pointer_diag_row(surface,(642*65536)+182,1129206850,volatile_read64(diag+504));                                              // BNDX',
    'pointer_diag_row(surface,(642*65536)+182,811024722,volatile_read64(diag+544));                                              // RAW0',
    'RAW0 row')
rep('pointer_diag_row(surface,(642*65536)+194,1129207106,volatile_read64(diag+512));                                              // BNDY',
    'pointer_diag_row(surface,(642*65536)+194,827801938,volatile_read64(diag+552));                                              // RAW1',
    'RAW1 row')
rep('pointer_diag_row(surface,(642*65536)+206,1145522500,volatile_read64(diag+520));                                              // BIGD',
    'pointer_diag_row(surface,(642*65536)+206,844579154,volatile_read64(diag+560));                                              // RAW2',
    'RAW2 row')
rep('pointer_diag_row(surface,(642*65536)+218,1397639511,volatile_read64(diag+488));                                              // WINS',
    'pointer_diag_row(surface,(642*65536)+218,861162320,volatile_read64(diag+568));                                              // PKT3',
    'PKT3 row')
rep('pointer_diag_row(surface,(642*65536)+230,1413892179,volatile_read64(diag+496));                                           // SHFT',
    'pointer_diag_row(surface,(642*65536)+230,1414415186,volatile_read64(diag+576));                                           // RCNT',
    'RCNT row')
rep('pointer_diag_row(surface,(642*65536)+242,1262702412,volatile_read64(diag+472));                                           // LOCK',
    'pointer_diag_row(surface,(642*65536)+242,1514754896,volatile_read64(diag+584));                                           // PSIZ',
    'PSIZ row')

p.write_text(s)
