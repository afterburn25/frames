#!/usr/bin/env python3
from pathlib import Path
here=Path(__file__).parent
base=here/'r53_cert_driver.py'
src=base.read_text()
old_patch="'patch_v108_r53_ehci_port_reset_companion_classifier.py'"
new_patch="'patch_v108_r53_ehci_port_reset_companion_classifier_sealed.py'"
if src.count(old_patch)!=1: raise SystemExit(f'r53 sealed cert patch anchor count {src.count(old_patch)}')
src=src.replace(old_patch,new_patch,1)
old_sha="'TBD_R53_SHA'"
new_sha="'815287063aae3e8d2ab56dbd4514de4cafdcd4ee763ff355f65b0867468d05d6'"
if src.count(old_sha)!=1: raise SystemExit(f'r53 sealed cert identity anchor count {src.count(old_sha)}')
src=src.replace(old_sha,new_sha,1)
ns={'__name__':'__main__','__file__':str(base)}
exec(compile(src,str(base),'exec'),ns,ns)
