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
    'pointer_diag_draw_tag4(surface,(78*65536)+18,82+(53*256)+(50*65536)+(32*16777216),green);    // R52',
    'title')

rep('''    let packed=buttons+(x_mag*256)+(x_neg*131072)+(y_mag*262144)+(y_neg*134217728);\n    if x_mag>96 || y_mag>96 { let snap=(x_mag%512)+((x_neg%2)*512)+((y_mag%512)*1024)+((y_neg%2)*524288); ps2_diag_snapshot_jump(input_state,header+(dx*256)+(dy*65536),snap); }\n    generic_pointer_emit_relative(input_state,1,packed);''',
'''    var safe_x=x_mag; var safe_y=y_mag;\n    let r52_diag=volatile_read64(input_state+3976);\n    if safe_x>32 {\n        safe_x=32;\n        if r52_diag!=0 { unsafe { volatile_write64(r52_diag+504,volatile_read64(r52_diag+504)+1); } }\n    }\n    if safe_y>32 {\n        safe_y=32;\n        if r52_diag!=0 { unsafe { volatile_write64(r52_diag+512,volatile_read64(r52_diag+512)+1); } }\n    }\n    if x_mag>96 || y_mag>96 {\n        let snap=(x_mag%512)+((x_neg%2)*512)+((y_mag%512)*1024)+((y_neg%2)*524288);\n        ps2_diag_snapshot_jump(input_state,header+(dx*256)+(dy*65536),snap);\n        if r52_diag!=0 { unsafe { volatile_write64(r52_diag+520,volatile_read64(r52_diag+520)+1); } }\n    }\n    let packed=buttons+(safe_x*256)+(x_neg*131072)+(safe_y*262144)+(y_neg*134217728);\n    generic_pointer_emit_relative(input_state,1,packed);''',
    'bounded delta emission')

rep('pointer_diag_row(surface,(642*65536)+182,1129525331,volatile_read64(diag+448));                                              // S0SC',
    'pointer_diag_row(surface,(642*65536)+182,1129206850,volatile_read64(diag+504));                                              // BNDX',
    'BNDX row')
rep('pointer_diag_row(surface,(642*65536)+194,1129525587,volatile_read64(diag+456));                                              // S1SC',
    'pointer_diag_row(surface,(642*65536)+194,1129207106,volatile_read64(diag+512));                                              // BNDY',
    'BNDY row')
rep('pointer_diag_row(surface,(642*65536)+206,1129525843,volatile_read64(diag+464));                                              // S2SC',
    'pointer_diag_row(surface,(642*65536)+206,1145522500,volatile_read64(diag+520));                                              // BIGD',
    'BIGD row')

p.write_text(s)
