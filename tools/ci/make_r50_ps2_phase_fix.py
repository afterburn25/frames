#!/usr/bin/env python3
from pathlib import Path
import subprocess, sys

p=Path(sys.argv[1])
# Reuse the proven r49 telemetry first, then apply the one-site behavioral repair.
subprocess.check_call([sys.executable, str(Path(__file__).with_name('make_r49_ps2_phase.py')), str(p)])
s=p.read_text()

def rep(old,new,label):
    global s
    n=s.count(old)
    if n!=1:
        raise SystemExit(f'{label}: expected 1 site, found {n}')
    s=s.replace(old,new)

rep('pointer_diag_draw_tag4(surface,(78*65536)+18,82+(52*256)+(57*65536)+(32*16777216),green);    // R49',
    'pointer_diag_draw_tag4(surface,(78*65536)+18,82+(53*256)+(48*65536)+(32*16777216),green);    // R50',
    'title')

rep('''    unsafe {
        volatile_write64(input_state+3032,1);  // exact sync after FA
        volatile_write64(input_state+3072,0);  // canonical phase
        volatile_write64(input_state+2800,0);
        volatile_write64(input_state+3176,0);
    }
    return 1;''',
'''    // r50 physical touchpad repair: FA proves command completion, not packet
    // byte phase. Real i8042 touchpads can leave the first live byte stream at
    // a different 3-byte offset than emulators. Do not force SYNC here. Reset
    // phase acquisition and let the existing 12-byte/4-header scorer establish
    // the unique physical stream phase before any pointer event is emitted.
    unsafe {
        volatile_write64(input_state+3032,0);
        volatile_write64(input_state+3040,0);
        volatile_write64(input_state+3072,0);
        volatile_write64(input_state+2800,0);
        volatile_write64(input_state+3176,0);
    }
    return 1;''',
    'post-FA forced-sync repair')

p.write_text(s)
