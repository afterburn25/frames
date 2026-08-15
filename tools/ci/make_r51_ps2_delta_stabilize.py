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
    'pointer_diag_draw_tag4(surface,(78*65536)+18,82+(53*256)+(49*65536)+(32*16777216),green);    // R51',
    'title')

# Fail closed on physically implausible/corrupt standard PS/2 packets. Keep all
# valid r50 packet behavior unchanged. On a rejected packet, drop phase lock so
# the existing 12-byte acquisition scorer can re-establish the real cadence.
rep('''    let packed=buttons+(x_mag*256)+(x_neg*131072)+(y_mag*262144)+(y_neg*134217728);\n    if x_mag>96 || y_mag>96 { let snap=(x_mag%512)+((x_neg%2)*512)+((y_mag%512)*1024)+((y_neg%2)*524288); ps2_diag_snapshot_jump(input_state,header+(dx*256)+(dy*65536),snap); }\n    generic_pointer_emit_relative(input_state,1,packed);''',
'''    let r51_diag=volatile_read64(input_state+3976);\n    let x_raw_sign=(dx/128)%2; let y_raw_sign=(dy/128)%2;\n    let x_over=(header/64)%2; let y_over=(header/128)%2;\n    let sign_bad:u64=if x_raw_sign!=(x_neg%2) || y_raw_sign!=(y_neg%2) { 1 } else { 0 };\n    let big_delta:u64=if x_mag>96 || y_mag>96 { 1 } else { 0 };\n    let overflow_bad:u64=if x_over!=0 || y_over!=0 { 1 } else { 0 };\n    if overflow_bad!=0 || sign_bad!=0 || big_delta!=0 {\n        if r51_diag!=0 { unsafe {\n            volatile_write64(r51_diag+504,volatile_read64(r51_diag+504)+1);\n            if overflow_bad!=0 { volatile_write64(r51_diag+512,volatile_read64(r51_diag+512)+1); }\n            if sign_bad!=0 { volatile_write64(r51_diag+520,volatile_read64(r51_diag+520)+1); }\n            if big_delta!=0 { volatile_write64(r51_diag+528,volatile_read64(r51_diag+528)+1); }\n            volatile_write64(r51_diag+536,volatile_read64(r51_diag+536)+1);\n        } }\n        unsafe {\n            volatile_write64(input_state+3032,0);\n            volatile_write64(input_state+3040,0);\n            volatile_write64(input_state+2800,0);\n            volatile_write64(input_state+3176,0);\n        }\n        return 1;\n    }\n    let packed=buttons+(x_mag*256)+(x_neg*131072)+(y_mag*262144)+(y_neg*134217728);\n    generic_pointer_emit_relative(input_state,1,packed);''',
    'packet sanity gate')

# Reuse phase-score rows for r51 stabilization counters while retaining phase,
# acquisition count, shifts and locks on screen.
rep('pointer_diag_row(surface,(642*65536)+182,1129525331,volatile_read64(diag+448));                                              // S0SC',
    'pointer_diag_row(surface,(642*65536)+182,1347436866,volatile_read64(diag+504));                                              // BADP',
    'BADP row')
rep('pointer_diag_row(surface,(642*65536)+194,1129525587,volatile_read64(diag+456));                                              // S1SC',
    'pointer_diag_row(surface,(642*65536)+194,1179797071,volatile_read64(diag+512));                                              // OVRF',
    'OVRF row')
rep('pointer_diag_row(surface,(642*65536)+206,1129525843,volatile_read64(diag+464));                                              // S2SC',
    'pointer_diag_row(surface,(642*65536)+206,1296516947,volatile_read64(diag+520));                                              // SGNM',
    'SGNM row')
rep('pointer_diag_row(surface,(642*65536)+218,1397639511,volatile_read64(diag+488));                                              // WINS',
    'pointer_diag_row(surface,(642*65536)+218,1145522500,volatile_read64(diag+528));                                              // BIGD',
    'BIGD row')

p.write_text(s)
