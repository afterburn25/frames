#!/usr/bin/env python3
from pathlib import Path
import traceback
here=Path(__file__).parent
base=here/'r65_cert_driver.py'
src=base.read_text()
old_patch="'patch_v108_r65_persistent_tt_periodic_qh.py'"
new_patch="'patch_v108_r65_display_compat.py'"
if src.count(old_patch)!=1: raise SystemExit('r65 final patch-target anchor mismatch '+str(src.count(old_patch)))
src=src.replace(old_patch,new_patch,1)
old_sha='c34e637562aeea6a0156fb7142502d006ced9ea961bac3eccc336e7db4d64785'
new_sha='9a4864e1eb630f531caf60e5c6c8a43cf3ece3169a25bcaab2042818ea8ccee6'
if src.count(old_sha)<2: raise SystemExit('r65 final SHA anchors missing '+str(src.count(old_sha)))
src=src.replace(old_sha,new_sha)

# r59h pinned its visible qTD error witness to a historical packed `rr` field.
# r65 exposes the same live error state directly from the hardware-owned QH
# overlay (`e=(ot/4)%32`). Adapt only this runner-local presentation gate.
r59hp=here/'r59h_cert_driver.py'; r59h=r59hp.read_text()
old="    req('(rr/4)%32' in s,'r59h qTD error telemetry missing')"
new="    req((('(rr/4)%32' in s) or ('e=(ot/4)%32' in s)),'r59h/r65 EHCI error telemetry missing')"
if r59h.count(old)==1:
    r59hp.write_text(r59h.replace(old,new,1))
elif r59h.count(new)!=1:
    raise SystemExit('r65 r59h error telemetry compatibility anchor missing')

ns={'__name__':'__main__','__file__':str(base)}
try:
    exec(compile(src,str(base),'exec'),ns,ns)
except BaseException:
    out=Path('evidence'); out.mkdir(parents=True,exist_ok=True); (out/'R65-FAILURE.txt').write_text(traceback.format_exc()); raise
