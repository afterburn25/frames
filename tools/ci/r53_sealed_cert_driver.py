#!/usr/bin/env python3
from pathlib import Path
here=Path(__file__).parent

# r53 preserves the r52 per-port-power operation but first clears EHCI
# read/write-clear change bits into a sanitized local `pw`.  Adapt only the
# inherited r52 text-shape assertion in the CI workspace; the semantic power,
# schedule-disable, Run/HCHalted, route, runtime and safety gates remain intact.
r52p=here/'r52_cert_driver.py'
r52src=r52p.read_text()
r52old="    req('set_flag(ps,4096)' in r52fn,'r52 per-port power-on proof missing')"
r52new="    req(('set_flag(ps,4096)' in r52fn) or ('set_flag(pw,4096)' in r52fn),'r52/r53 per-port power-on proof missing')"
if r52src.count(r52old)!=1: raise SystemExit(f'r53 r52 power compatibility anchor count {r52src.count(r52old)}')
r52p.write_text(r52src.replace(r52old,r52new,1))

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
