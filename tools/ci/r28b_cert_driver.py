#!/usr/bin/env python3
from pathlib import Path
base=Path(__file__).with_name('r28_cert_driver.py')
src=base.read_text()
repls={
"R26_SHA='1d165f9aac5eeb40519d17920a019e586495a3b37c7a394fe17b221f9d702108'":"R26_SHA='f35bf73ef6c28f3a0e58416071a4b231bcf3b9ca632fdff23078a3ef1e479af7'",
"patch_v108_r28_ep0_address_evaluate.py":"patch_v108_r28b_ep0_identity.py",
"Frames-0.9.98-v108-r28-EP0-Address-Evaluate-Recovery-Rufus-UEFI.iso":"Frames-0.9.98-v108-r28b-EP0-Address-Evaluate-Recovery-Rufus-UEFI.iso",
"R28-SHA.txt":"R28B-SHA.txt",
"R25K-R28.patch":"R25K-R28B.patch",
"FRAMES_V108_R28":"FRAMES_V108_R28B",
"(ROOT/'evidence/R28-AGGREGATE.json')":"(ROOT/'evidence/R28B-AGGREGATE.json')",
"'profile':'frames-0.9.98-v108-r28-ep0-address-evaluate-recovery'":"'profile':'frames-0.9.98-v108-r28b-ep0-address-evaluate-recovery'",
"'physical_r26':'FAIL_LOG_UNTOUCHED_USB_NATIVE_OPEN','physical_r27':'FAIL_USB_PHYSICAL_NO_HID','physical_r28':'PENDING'":"'physical_r26':'FAIL_LOG_UNTOUCHED_USB_NATIVE_OPEN','physical_r27':'FAIL_USB_PHYSICAL_NO_HID','physical_r28b':'PENDING'",
"Frames 0.9.98 v108 r28 — EP0 Addressed-State + Evaluate Context Recovery":"Frames 0.9.98 v108 r28b — EP0 Addressed-State + Evaluate Context Recovery",
"print('R28 PASS_VM_PENDING_PHYSICAL',iso_sha)":"print('R28B PASS_VM_PENDING_PHYSICAL',iso_sha)",
"'kernel-r28.nx'":"'kernel-r28b.nx'",
}
for old,new in repls.items():
    n=src.count(old)
    if n!=1: raise SystemExit(f'r28b driver anchor mismatch {old!r}: {n}')
    src=src.replace(old,new,1)
ns={'__name__':'__main__','__file__':str(base)}
exec(compile(src,str(base),'exec'),ns,ns)
