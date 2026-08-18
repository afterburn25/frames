#!/usr/bin/env python3
from pathlib import Path
here=Path(__file__).parent
base=here/'r55_cert_driver.py'
src=base.read_text()
old_patch="'patch_v108_r55_ehci_intel_hub_discovery.py'"
new_patch="'patch_v108_r55_ehci_intel_hub_discovery_sealed.py'"
if src.count(old_patch)!=1: raise SystemExit(f'r55 sealed cert patch anchor count {src.count(old_patch)}')
src=src.replace(old_patch,new_patch,1)
old_sha="'7f3aebe8d7ac75cada7b32dcffd4074c84651e1dd22c179bc2e34e0375fbc4d7'"
new_sha="'7d3784c990c52e61dcae428dbeb683888259faa77d84526ef336b778b02e5cdc'"
if src.count(old_sha)!=1: raise SystemExit(f'r55 sealed cert identity anchor count {src.count(old_sha)}')
src=src.replace(old_sha,new_sha,1)
ns={'__name__':'__main__','__file__':str(base)}
exec(compile(src,str(base),'exec'),ns,ns)
