#!/usr/bin/env python3
from pathlib import Path
import traceback
here=Path(__file__).parent
base=here/'r65_cert_driver.py'
src=base.read_text()
# Hash-capture rerun after retaining the inherited r59h qTD-error expression.
old_patch="'patch_v108_r65_persistent_tt_periodic_qh.py'"
new_patch="'patch_v108_r65_display_compat.py'"
if src.count(old_patch)!=1: raise SystemExit('r65 final patch-target anchor mismatch '+str(src.count(old_patch)))
src=src.replace(old_patch,new_patch,1)
old_sha='c34e637562aeea6a0156fb7142502d006ced9ea961bac3eccc336e7db4d64785'
new_sha='9a4864e1eb630f531caf60e5c6c8a43cf3ece3169a25bcaab2042818ea8ccee6'
if src.count(old_sha)<2: raise SystemExit('r65 final SHA anchors missing '+str(src.count(old_sha)))
src=src.replace(old_sha,new_sha)
ns={'__name__':'__main__','__file__':str(base)}
try:
    exec(compile(src,str(base),'exec'),ns,ns)
except BaseException:
    out=Path('evidence'); out.mkdir(parents=True,exist_ok=True); (out/'R65-FAILURE.txt').write_text(traceback.format_exc()); raise
