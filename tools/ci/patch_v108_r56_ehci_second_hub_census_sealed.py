#!/usr/bin/env python3
from pathlib import Path
here=Path(__file__).parent
base=here/'patch_v108_r56_ehci_second_hub_census.py'
src=base.read_text()
old="EXPECTED='0000000000000000000000000000000000000000000000000000000000000000'"
new="EXPECTED='156c10d74ab7513c1eb72630cdcf425eeaa79d85d4fde463c5f0d9b695199654'"
if src.count(old)!=1: raise SystemExit(f'r56 sealed hash anchor count {src.count(old)}')
src=src.replace(old,new,1)
ns={'__name__':'__main__','__file__':str(base)}
exec(compile(src,str(base),'exec'),ns,ns)
