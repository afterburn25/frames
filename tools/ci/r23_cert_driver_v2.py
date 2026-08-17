#!/usr/bin/env python3
from pathlib import Path
base=Path(__file__).with_name('r23_cert_driver.py')
s=base.read_text()
old="'python3','tools/ci/qemu_ps2_cursor_smoothness_r18.py'"
new="'python3','tools/ci/qemu_ps2_cursor_smoothness_r23.py'"
if s.count(old)!=1:
    raise SystemExit('r23 driver smoothness anchor mismatch')
s=s.replace(old,new,1)
ns={'__name__':'__main__','__file__':str(base)}
exec(compile(s,str(base),'exec'),ns,ns)
