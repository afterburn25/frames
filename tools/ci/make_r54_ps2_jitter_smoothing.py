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
    'pointer_diag_draw_tag4(surface,(78*65536)+18,82+(53*256)+(52*65536)+(32*16777216),green);    // R54',
    'title')

old='''    if x_mag>96 || y_mag>96 {\n        let snap=(x_mag%512)+((x_neg%2)*512)+((y_mag%512)*1024)+((y_neg%2)*524288);\n        ps2_diag_snapshot_jump(input_state,header+(dx*256)+(dy*65536),snap);\n        if r52_diag!=0 { unsafe { volatile_write64(r52_diag+520,volatile_read64(r52_diag+520)+1); } }\n    }\n    let packed=buttons+(safe_x*256)+(x_neg*131072)+(safe_y*262144)+(y_neg*134217728);\n    generic_pointer_emit_relative(input_state,1,packed);'''
new='''    if x_mag>96 || y_mag>96 {\n        let snap=(x_mag%512)+((x_neg%2)*512)+((y_mag%512)*1024)+((y_neg%2)*524288);\n        ps2_diag_snapshot_jump(input_state,header+(dx*256)+(dy*65536),snap);\n        if r52_diag!=0 { unsafe { volatile_write64(r52_diag+520,volatile_read64(r52_diag+520)+1); } }\n    }\n    // r54 one-packet micro-reversal smoothing. Preserve r52's bounded packet\n    // stream, but suppress one isolated <=4-unit reversal per axis. The current\n    // sample still becomes the new history, so sustained intentional reversal\n    // passes on the very next packet rather than sticking or forcing resync.\n    var emit_x=safe_x; var emit_y=safe_y;\n    if r52_diag!=0 {\n        let prev_x_neg=volatile_read64(r52_diag+544)%2;\n        let prev_y_neg=volatile_read64(r52_diag+552)%2;\n        let prev_x_mag=volatile_read64(r52_diag+560);\n        let prev_y_mag=volatile_read64(r52_diag+568);\n        if safe_x>0 && safe_x<=4 && prev_x_mag>0 && (x_neg%2)!=prev_x_neg {\n            emit_x=0;\n            unsafe { volatile_write64(r52_diag+576,volatile_read64(r52_diag+576)+1); }\n        }\n        if safe_y>0 && safe_y<=4 && prev_y_mag>0 && (y_neg%2)!=prev_y_neg {\n            emit_y=0;\n            unsafe { volatile_write64(r52_diag+576,volatile_read64(r52_diag+576)+1); }\n        }\n        unsafe {\n            volatile_write64(r52_diag+544,x_neg%2);\n            volatile_write64(r52_diag+552,y_neg%2);\n            volatile_write64(r52_diag+560,safe_x);\n            volatile_write64(r52_diag+568,safe_y);\n        }\n    }\n    let packed=buttons+(emit_x*256)+(x_neg*131072)+(emit_y*262144)+(y_neg*134217728);\n    generic_pointer_emit_relative(input_state,1,packed);'''
rep(old,new,'micro reversal smoothing')

rep('pointer_diag_row(surface,(642*65536)+218,1397639511,volatile_read64(diag+488));                                              // WINS',
    'pointer_diag_row(surface,(642*65536)+218,1381255498,volatile_read64(diag+576));                                              // JITR',
    'JITR row')

p.write_text(s)
