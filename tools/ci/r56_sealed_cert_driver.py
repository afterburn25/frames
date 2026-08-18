#!/usr/bin/env python3
from pathlib import Path
here=Path(__file__).parent
base=here/'r56_cert_driver.py'
src=base.read_text()

def one(old,new,label):
    global src
    n=src.count(old)
    if n!=1: raise SystemExit(f'r56 sealed cert anchor {label} count {n}')
    src=src.replace(old,new,1)

one("'patch_v108_r56_ehci_second_hub_census.py'","'patch_v108_r56_ehci_second_hub_census_sealed.py'",'sealed patch target')
one('0000000000000000000000000000000000000000000000000000000000000000','156c10d74ab7513c1eb72630cdcf425eeaa79d85d4fde463c5f0d9b695199654','sealed exact kernel identity')
ns={'__name__':'__main__','__file__':str(base)}
exec(compile(src,str(base),'exec'),ns,ns)
