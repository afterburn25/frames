#!/usr/bin/env python3
# r26b authoritative identity + marker-model correction
from pathlib import Path
base=Path(__file__).with_name('r26_cert_driver.py')
src=base.read_text()
old='5dc6c6b04f7103a3981287d048264c94b75bfb12fd50538ca0a285979aa001fc'
new='7c8967f78588b37663db22c78f727bfa8685056045e88b7c126ffcd56a0cc66f'
if src.count(old)!=1: raise SystemExit(f'r26 driver identity anchor mismatch {src.count(old)}')
src=src.replace(old,new,1)
old_patch='patch_v108_r26_iso_native_log.py'
new_patch='patch_v108_r26b_identity.py'
if src.count(old_patch)!=1: raise SystemExit(f'r26 driver patch anchor mismatch {src.count(old_patch)}')
src=src.replace(old_patch,new_patch,1)
markers={
 "'FRAMES_ISO_LOG_R26_ARMED'":"'serial_marker_iso_log_r26'",
 "'FRAMES_LOG_PERSIST_R26_DISABLED'":"'serial_marker_log_persist_disabled_r26'",
 "'FRAMES_INPUT_AFTER_LOG_FAIL_R26_OK'":"'serial_marker_input_after_log_fail_r26'",
}
for oldm,newm in markers.items():
    if src.count(oldm)!=1: raise SystemExit(f'r26 model marker anchor mismatch {oldm}: {src.count(oldm)}')
    src=src.replace(oldm,newm,1)
ns={'__name__':'__main__','__file__':str(base)}
exec(compile(src,str(base),'exec'),ns,ns)
