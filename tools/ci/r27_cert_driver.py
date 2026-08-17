#!/usr/bin/env python3
# r27 USB-only recovery: shared xHCI transfer-event mailbox + physical controller evidence.
from pathlib import Path
base=Path(__file__).with_name('r26_cert_driver.py')
src=base.read_text()
repls={
"R26_SHA='5dc6c6b04f7103a3981287d048264c94b75bfb12fd50538ca0a285979aa001fc'":"R26_SHA='6504e3d3210821592acffb0e86c96aa6aa5aaa5e42e23699e44a830f185b2450'",
"ISO_NAME='Frames-0.9.98-v108-r26-ISO-Native-FlightRecorder-Input-USB-Repair-Rufus-UEFI.iso'":"ISO_NAME='Frames-0.9.98-v108-r27-USB-Event-Mailbox-Controller-Recovery-Rufus-UEFI.iso'",
"patch_v108_r26_iso_native_log.py":"patch_v108_r27_usb_event_mailbox.py",
"'FRAMES_ISO_LOG_R26_ARMED'":"'serial_marker_iso_log_r26'",
"'FRAMES_LOG_PERSIST_R26_DISABLED'":"'serial_marker_log_persist_disabled_r26'",
"'FRAMES_INPUT_AFTER_LOG_FAIL_R26_OK'":"'serial_marker_input_after_log_fail_r26'",
"R26-SHA.txt":"R27-SHA.txt",
"R25K-R26.patch":"R25K-R27.patch",
"FRAMES_V108_R26":"FRAMES_V108_R27",
"Frames 0.9.98 v108 r26 ISO-native Flight Recorder physical candidate":"Frames 0.9.98 v108 r27 USB Event Mailbox + Controller Recovery physical candidate",
"(ROOT/'evidence/R26-AGGREGATE.json')":"(ROOT/'evidence/R27-AGGREGATE.json')",
"'profile':'frames-0.9.98-v108-r26-iso-native-flight-recorder-write-groundwork'":"'profile':'frames-0.9.98-v108-r27-usb-event-mailbox-controller-recovery'",
"'physical_r26':'PENDING'":"'physical_r26':'FAIL_LOG_UNTOUCHED_USB_NATIVE_OPEN','physical_r27':'PENDING'",
"Frames 0.9.98 v108 r26 — ISO-Native Flight Recorder + Input/USB Repair":"Frames 0.9.98 v108 r27 — USB Event Mailbox + Controller Recovery",
"print('R26 PASS_VM_PENDING_PHYSICAL',iso_sha)":"print('R27 PASS_VM_PENDING_PHYSICAL',iso_sha)",
}
for old,new in repls.items():
    if src.count(old)!=1:
        raise SystemExit(f'r27 driver anchor mismatch {old!r}: {src.count(old)}')
    src=src.replace(old,new,1)
# r26 references the generated kernel twice (copy + model gate). Both are
# intentionally renamed together for r27.
if src.count('kernel-r26.nx')!=2:
    raise SystemExit(f"r27 kernel evidence anchor mismatch: {src.count('kernel-r26.nx')}")
src=src.replace('kernel-r26.nx','kernel-r27.nx')
anchor='def build_iso(F,iso):\n'
extra=r'''_r26_model_gate=model_gate
def model_gate(r25k,r27):
 _r26_model_gate(r25k,r27)
 s=pathlib.Path(r27).read_text()
 for q in ('fn xhci_event_mailbox_put_v127','fn xhci_event_mailbox_take_v127','fn xhci_event_mailbox_count_v127','volatile_write64(xhci_state+1840,event_mailbox)'):
  req(q in s,'r27 shared event mailbox missing '+q)
 for n in ('xhci_wait_command_completion','xhci_wait_transfer_event','xhci_wait_hid_event','xhci_wait_bulk_event','xhci_hid_poll_continuous'):
  f=fn_text(s,n)
  req('xhci_event_mailbox_put_v127' in f or n=='xhci_hid_poll_continuous','r27 event route put missing '+n)
  if n!='xhci_wait_command_completion': req('xhci_event_mailbox_take_v127' in f,'r27 event route take missing '+n)
 req('v108_text_eown_v127' in s and 'v108_text_eprt_v127' in s,'r27 EHCI ownership/port telemetry missing')
 req('v108_text_xevt_v127' in s,'r27 event mailbox telemetry missing')
'''
if src.count(anchor)!=1: raise SystemExit('r27 model extension anchor')
src=src.replace(anchor,extra+anchor,1)
ns={'__name__':'__main__','__file__':str(base)}
exec(compile(src,str(base),'exec'),ns,ns)
