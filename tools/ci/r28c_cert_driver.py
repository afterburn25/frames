#!/usr/bin/env python3
from pathlib import Path
base=Path(__file__).with_name('r28_cert_driver.py')
src=base.read_text()
repls={
"R26_SHA='1d165f9aac5eeb40519d17920a019e586495a3b37c7a394fe17b221f9d702108'":"R26_SHA='8e1401d483bcff3a5e67caf3c6183fdafe370a3de742675ca0adc255c67d13b5'",
"patch_v108_r28_ep0_address_evaluate.py":"patch_v108_r28c_hub_ep0_state_isolation.py",
"Frames-0.9.98-v108-r28-EP0-Address-Evaluate-Recovery-Rufus-UEFI.iso":"Frames-0.9.98-v108-r28c-EP0-Address-Evaluate-Hub-State-Isolation-Rufus-UEFI.iso",
"R28-SHA.txt":"R28C-SHA.txt",
"R25K-R28.patch":"R25K-R28C.patch",
"FRAMES_V108_R28":"FRAMES_V108_R28C",
"(ROOT/'evidence/R28-AGGREGATE.json')":"(ROOT/'evidence/R28C-AGGREGATE.json')",
"'profile':'frames-0.9.98-v108-r28-ep0-address-evaluate-recovery'":"'profile':'frames-0.9.98-v108-r28c-ep0-address-evaluate-hub-state-isolation'",
"'physical_r26':'FAIL_LOG_UNTOUCHED_USB_NATIVE_OPEN','physical_r27':'FAIL_USB_PHYSICAL_NO_HID','physical_r28':'PENDING'":"'physical_r26':'FAIL_LOG_UNTOUCHED_USB_NATIVE_OPEN','physical_r27':'FAIL_USB_PHYSICAL_NO_HID','physical_r28b':'FAIL_VM_HUB_CONTEXT_STATE','physical_r28c':'PENDING'",
"Frames 0.9.98 v108 r28 — EP0 Addressed-State + Evaluate Context Recovery":"Frames 0.9.98 v108 r28c — EP0 Addressed-State + Evaluate Context + Hub State Isolation",
"print('R28 PASS_VM_PENDING_PHYSICAL',iso_sha)":"print('R28C PASS_VM_PENDING_PHYSICAL',iso_sha)",
"'kernel-r28.nx'":"'kernel-r28c.nx'",
}
for old,new in repls.items():
    n=src.count(old)
    if n!=1: raise SystemExit(f'r28c driver anchor mismatch {old!r}: {n}')
    src=src.replace(old,new,1)
# Extend the model gate so a future refactor cannot silently remove the hub isolation.
gate="req('v108_text_ep0a_v128' in s and 'v108_text_ep0f_v128' in s,'r28 physical EP0 telemetry missing')"
extra=gate+"""
 hub=fn_text(s,'xhci_address_hub_child_v113')
 for q in ('volatile_write64(xhci_state+1848,0)','volatile_write64(xhci_state+1880,0)','volatile_write64(xhci_state+1888,0)'):
  req(q in hub,'r28c hub EP0 state isolation missing '+q)
"""
if src.count(gate)!=1: raise SystemExit('r28c model extension anchor mismatch')
src=src.replace(gate,extra,1)
ns={'__name__':'__main__','__file__':str(base)}
exec(compile(src,str(base),'exec'),ns,ns)
