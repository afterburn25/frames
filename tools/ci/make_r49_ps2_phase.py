#!/usr/bin/env python3
from pathlib import Path
import sys
p=Path(sys.argv[1]); s=p.read_text()

def rep(old,new,label):
    global s
    n=s.count(old)
    if n!=1:
        raise SystemExit(f'{label}: expected 1 site, found {n}')
    s=s.replace(old,new)

rep('pointer_diag_draw_tag4(surface,(78*65536)+18,82+(52*256)+(55*65536)+(32*16777216),green);    // R47',
    'pointer_diag_draw_tag4(surface,(78*65536)+18,82+(52*256)+(57*65536)+(32*16777216),green);    // R49','title')

rep('''fn ps2_phase_finish_lock(input_state:u64,phase:u64) -> u64 {\n    if input_state==0 || phase>2 { return 0; }\n    unsafe {''',
'''fn ps2_phase_finish_lock(input_state:u64,phase:u64) -> u64 {\n    if input_state==0 || phase>2 { return 0; }\n    let r49_diag=volatile_read64(input_state+3976);\n    if r49_diag!=0 { unsafe { volatile_write64(r49_diag+472,volatile_read64(r49_diag+472)+1); volatile_write64(r49_diag+480,phase); } }\n    unsafe {''','finish lock')

rep('''fn ps2_phase_acquire_byte(input_state:u64,data:u64) -> u64 {\n    if input_state==0 { return 0; }\n    var count=volatile_read64(input_state+3040); if count>12 { count=0; }''',
'''fn ps2_phase_acquire_byte(input_state:u64,data:u64) -> u64 {\n    if input_state==0 { return 0; }\n    let r49_diag=volatile_read64(input_state+3976);\n    if r49_diag!=0 { unsafe { volatile_write64(r49_diag+416,data%256); volatile_write64(r49_diag+424,volatile_read64(r49_diag+424)+1); } }\n    var count=volatile_read64(input_state+3040); if count>12 { count=0; }\n    if r49_diag!=0 { unsafe { volatile_write64(r49_diag+432,count); volatile_write64(r49_diag+440,volatile_read64(input_state+3032)); } }''','acquire entry')

rep('''    var winners:u64=0; var phase:u64=0;\n    if s0==4 { winners=winners+1; phase=0; }\n    if s1==4 { winners=winners+1; phase=1; }\n    if s2==4 { winners=winners+1; phase=2; }\n    if winners==1 { return ps2_phase_finish_lock(input_state,phase); }\n\n    ps2_phase_buffer_shift(input_state);''',
'''    var winners:u64=0; var phase:u64=0;\n    if s0==4 { winners=winners+1; phase=0; }\n    if s1==4 { winners=winners+1; phase=1; }\n    if s2==4 { winners=winners+1; phase=2; }\n    if r49_diag!=0 { unsafe { volatile_write64(r49_diag+448,s0); volatile_write64(r49_diag+456,s1); volatile_write64(r49_diag+464,s2); volatile_write64(r49_diag+488,winners); } }\n    if winners==1 { return ps2_phase_finish_lock(input_state,phase); }\n\n    if r49_diag!=0 { unsafe { volatile_write64(r49_diag+496,volatile_read64(r49_diag+496)+1); } }\n    ps2_phase_buffer_shift(input_state);''','scores and shift')

rows=[
('''    pointer_diag_row(surface,(642*65536)+158,79+(86*256)+(70*65536)+(76*16777216),volatile_read64(input_state+3024));        // OVFL''','''    pointer_diag_row(surface,(642*65536)+158,1096045392,volatile_read64(input_state+3032));                                      // PSTA'''),
('''    pointer_diag_row(surface,(642*65536)+170,72+(48*256)+(48*65536)+(48*16777216),h0);                                       // H000''','''    pointer_diag_row(surface,(642*65536)+170,1414415184,volatile_read64(input_state+3040));                                      // PCNT'''),
('''    pointer_diag_row(surface,(642*65536)+182,72+(48*256)+(48*65536)+(49*16777216),h1);                                       // H001''','''    pointer_diag_row(surface,(642*65536)+182,1129525331,volatile_read64(diag+448));                                              // S0SC'''),
('''    pointer_diag_row(surface,(642*65536)+194,72+(48*256)+(48*65536)+(50*16777216),h2);                                       // H002''','''    pointer_diag_row(surface,(642*65536)+194,1129525587,volatile_read64(diag+456));                                              // S1SC'''),
('''    pointer_diag_row(surface,(642*65536)+206,72+(48*256)+(48*65536)+(51*16777216),h3);                                       // H003''','''    pointer_diag_row(surface,(642*65536)+206,1129525843,volatile_read64(diag+464));                                              // S2SC'''),
('''    pointer_diag_row(surface,(642*65536)+218,75+(66*256)+(89*65536)+(84*16777216),volatile_read64(input_state+3768));       // KBYT''','''    pointer_diag_row(surface,(642*65536)+218,1397639511,volatile_read64(diag+488));                                              // WINS'''),
]
for old,new in rows:
    rep(old,new,'panel row')

rep('''    let d39=volatile_read64(input_state+3976); if d39!=0 {\n        pointer_diag_row(surface,(642*65536)+230,66+(65*256)+(82*65536)+(82*16777216),volatile_read64(d39+96));           // BARR\n        pointer_diag_row(surface,(642*65536)+242,66+(65*256)+(82*65536)+(70*16777216),volatile_read64(d39+104));          // BARF\n    }''',
'''    pointer_diag_row(surface,(642*65536)+230,1413892179,volatile_read64(diag+496));                                           // SHFT\n    pointer_diag_row(surface,(642*65536)+242,1262702412,volatile_read64(diag+472));                                           // LOCK''','bottom rows')

p.write_text(s)
