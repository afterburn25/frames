#!/usr/bin/env python3
from pathlib import Path

base=Path(__file__).with_name('r25_cert_driver.py')
s=base.read_text()
repls={
    "R25_SHA='068ed900f8942ecec797e2f5fa5e79f95fce51ef817b2e3336af05d643528674'":"R25_SHA='9224366a0d53bab0815d8c04f17017fc20858dc2a196f41cf159bf85ac24f395'",
    "patch_v108_r25_flightrec_usbwrite.py":"patch_v108_r25c_bracefix.py",
}
for old,new in repls.items():
    if s.count(old)!=1:
        raise SystemExit(f'r25 v3 anchor mismatch for {old!r}: {s.count(old)}')
    s=s.replace(old,new,1)
ns={'__name__':'__main__','__file__':str(base)}
exec(compile(s,str(base),'exec'),ns,ns)
