#!/usr/bin/env python3
from pathlib import Path

base=Path(__file__).with_name('r25_cert_driver.py')
s=base.read_text()
old="patch_v108_r25_flightrec_usbwrite.py"
new="patch_v108_r25b_bracefix.py"
if s.count(old)!=1:
    raise SystemExit(f'r25 v2 patch anchor mismatch: {s.count(old)}')
s=s.replace(old,new,1)
ns={'__name__':'__main__','__file__':str(base)}
exec(compile(s,str(base),'exec'),ns,ns)
