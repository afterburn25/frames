#!/usr/bin/env python3
from pathlib import Path
here=Path(__file__).parent
base=here/'patch_v108_r53_ehci_port_reset_companion_classifier.py'
src=base.read_text()
old="EXPECTED='TBD_R53_SHA'"
new="EXPECTED='815287063aae3e8d2ab56dbd4514de4cafdcd4ee763ff355f65b0867468d05d6'"
if src.count(old)!=1: raise SystemExit(f'r53 sealed patch identity anchor count {src.count(old)}')
src=src.replace(old,new,1)
ns={'__name__':'__main__','__file__':str(base)}
exec(compile(src,str(base),'exec'),ns,ns)
