#!/usr/bin/env python3
from pathlib import Path
base=Path(__file__).with_name('r31_cert_driver.py')
src=base.read_text()
repls={
"R26_SHA='cf7a3f890811d6ff245ec822bf5fd38d01f405c990c7dce6161efb117699797c'":"R26_SHA='57944cdb9f5060b5b170a42280fe37dce32125040f5e1da6295df615e1f81e6e'",
"patch_v108_r31_usb_state_isolation.py":"patch_v108_r31b_overlay_state.py",
"Frames-0.9.98-v108-r31-USB-State-Isolation-Controller-Order-Recovery-Rufus-UEFI.iso":"Frames-0.9.98-v108-r31b-USB-State-Isolation-Controller-Order-Recovery-Rufus-UEFI.iso",
"R31-SHA.txt":"R31B-SHA.txt",
"R25K-R31.patch":"R25K-R31B.patch",
"FRAMES_V108_R31":"FRAMES_V108_R31B",
"(ROOT/'evidence/R31-AGGREGATE.json')":"(ROOT/'evidence/R31B-AGGREGATE.json')",
"'profile':'frames-0.9.98-v108-r31-usb-state-isolation-controller-order-recovery'":"'profile':'frames-0.9.98-v108-r31b-usb-state-isolation-controller-order-recovery'",
"'physical_r30b':'FAIL_USB_PHYSICAL_NO_HID_PHANTOM_RIGHT_MENU','physical_r31':'PENDING'":"'physical_r30b':'FAIL_USB_PHYSICAL_NO_HID_PHANTOM_RIGHT_MENU','physical_r31':'REJECTED_COMPILE_TELEMETRY_SCOPE','physical_r31b':'PENDING'",
"Frames 0.9.98 v108 r31 — USB State Isolation + Controller Start Order Recovery":"Frames 0.9.98 v108 r31b — USB State Isolation + Controller Start Order Recovery",
"print('R31 PASS_VM_PENDING_PHYSICAL',iso_sha)":"print('R31B PASS_VM_PENDING_PHYSICAL',iso_sha)",
"'kernel-r31.nx'":"'kernel-r31b.nx'",
}
for old,new in repls.items():
 n=src.count(old)
 if n!=1: raise SystemExit(f'r31b driver anchor mismatch {old!r}: {n}')
 src=src.replace(old,new,1)
needle=" req('v108_text_xpri_v131' in s and 'v108_text_xlog_v131' in s,'r31 primary/fallback USB telemetry missing')"
insert=needle+"""
 ov=fn_text(s,'v108_input_overlay_draw')
 req('hardware_state+' not in ov,'r31b overlay still references hardware_state outside scope')
 for q in ('volatile_read64(xhci+2192)','volatile_read64(xhci+2280)'):
  req(q in ov,'r31b overlay state bridge missing '+q)
 scan=fn_text(s,'v108_xhci_scan_pointer_v116')
 req('volatile_write64(xhci_state+2192' in scan and 'volatile_write64(xhci_state+2280' in scan,'r31b USB evidence not copied into display state')"""
if src.count(needle)!=1: raise SystemExit(f'r31b inherited model gate anchor mismatch {src.count(needle)}')
src=src.replace(needle,insert,1)
ns={'__name__':'__main__','__file__':str(base)}
exec(compile(src,str(base),'exec'),ns,ns)
