#!/usr/bin/env python3
# r28 physical USB recovery: standards-normal LS/FS EP0 Addressed-state flow.
from pathlib import Path
base=Path(__file__).with_name('r27_cert_driver.py')
src=base.read_text()
repls={
"R26_SHA='6504e3d3210821592acffb0e86c96aa6aa5aaa5e42e23699e44a830f185b2450'":"R26_SHA='1d165f9aac5eeb40519d17920a019e586495a3b37c7a394fe17b221f9d702108'",
"ISO_NAME='Frames-0.9.98-v108-r27-USB-Event-Mailbox-Controller-Recovery-Rufus-UEFI.iso'":"ISO_NAME='Frames-0.9.98-v108-r28-EP0-Address-Evaluate-Recovery-Rufus-UEFI.iso'",
"patch_v108_r27_usb_event_mailbox.py":"patch_v108_r28_ep0_address_evaluate.py",
"R27-SHA.txt":"R28-SHA.txt",
"R25K-R27.patch":"R25K-R28.patch",
"FRAMES_V108_R27":"FRAMES_V108_R28",
"Frames 0.9.98 v108 r27 USB Event Mailbox + Controller Recovery physical candidate":"Frames 0.9.98 v108 r28 EP0 Address + Evaluate Context physical recovery candidate",
"(ROOT/'evidence/R27-AGGREGATE.json')":"(ROOT/'evidence/R28-AGGREGATE.json')",
"'profile':'frames-0.9.98-v108-r27-usb-event-mailbox-controller-recovery'":"'profile':'frames-0.9.98-v108-r28-ep0-address-evaluate-recovery'",
"'physical_r26':'FAIL_LOG_UNTOUCHED_USB_NATIVE_OPEN','physical_r27':'PENDING'":"'physical_r26':'FAIL_LOG_UNTOUCHED_USB_NATIVE_OPEN','physical_r27':'FAIL_USB_PHYSICAL_NO_HID','physical_r28':'PENDING'",
"Frames 0.9.98 v108 r27 — USB Event Mailbox + Controller Recovery":"Frames 0.9.98 v108 r28 — EP0 Addressed-State + Evaluate Context Recovery",
"print('R27 PASS_VM_PENDING_PHYSICAL',iso_sha)":"print('R28 PASS_VM_PENDING_PHYSICAL',iso_sha)",
"'kernel-r27.nx'":"'kernel-r28.nx'",
}
for old,new in repls.items():
    n=src.count(old)
    if n!=1:
        raise SystemExit(f'r28 driver anchor mismatch {old!r}: {n}')
    src=src.replace(old,new,1)

gate_old="req('v108_text_xevt_v127' in s,'r27 event mailbox telemetry missing')"
gate_new=gate_old+"""
 req('fn xhci_command_submit_evaluate_v128' in s,'r28 Evaluate Context command missing')
 addr=fn_text(s,'xhci_address_default_device')
 req('if speed<=2 { bsr=0; address_first=1; }' in addr,'r28 LS/FS address-first path missing')
 fin=fn_text(s,'xhci_finalize_address_and_descriptor')
 for q in ('if address_first!=0','volatile_write32(input+4,2)','xhci_command_submit_evaluate_v128','if mps!=oldmps'):
  req(q in fin,'r28 EP0 evaluate flow missing '+q)
 req('v108_text_ep0a_v128' in s and 'v108_text_ep0f_v128' in s,'r28 physical EP0 telemetry missing')
 req('volatile_write64(xhci_state+1912,volatile_read64(hardware_state+744))' in s,'r28 frozen EP0 evidence missing')
"""
if src.count(gate_old)!=1:
    raise SystemExit('r28 model extension anchor mismatch')
src=src.replace(gate_old,gate_new,1)

ns={'__name__':'__main__','__file__':str(base)}
exec(compile(src,str(base),'exec'),ns,ns)
