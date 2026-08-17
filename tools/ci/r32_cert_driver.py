#!/usr/bin/env python3
from pathlib import Path
base=Path(__file__).with_name('r31_cert_driver.py')
src=base.read_text()
repls={
"R26_SHA='cf7a3f890811d6ff245ec822bf5fd38d01f405c990c7dce6161efb117699797c'":"R26_SHA='dab5d471bf8cc80a38573fa52aa502f1bc488d9d3ecb655ce734350e123d732f'",
"patch_v108_r31_usb_state_isolation.py":"patch_v108_r32_usb_settle_input_recovery.py",
"Frames-0.9.98-v108-r31-USB-State-Isolation-Controller-Order-Recovery-Rufus-UEFI.iso":"Frames-0.9.98-v108-r32-USB-Settle-Input-Recovery-Rufus-UEFI.iso",
"R31-SHA.txt":"R32-SHA.txt",
"R25K-R31.patch":"R25K-R32.patch",
"FRAMES_V108_R31":"FRAMES_V108_R32",
"(ROOT/'evidence/R31-AGGREGATE.json')":"(ROOT/'evidence/R32-AGGREGATE.json')",
"'profile':'frames-0.9.98-v108-r31-usb-state-isolation-controller-order-recovery'":"'profile':'frames-0.9.98-v108-r32-usb-settle-input-recovery'",
"'physical_r30b':'FAIL_USB_PHYSICAL_NO_HID_PHANTOM_RIGHT_MENU','physical_r31':'PENDING'":"'physical_r30b':'FAIL_USB_PHYSICAL_NO_HID_PHANTOM_RIGHT_MENU','physical_r31':'REJECTED_COMPILE_TELEMETRY_SCOPE','physical_r31b':'FAIL_USB_PHYSICAL_NO_HID_PHANTOM_RIGHT_MENU_TEXT_FOCUS','physical_r32':'PENDING'",
"Frames 0.9.98 v108 r31 — USB State Isolation + Controller Start Order Recovery":"Frames 0.9.98 v108 r32 — USB Settle + Input Regression Recovery",
"print('R31 PASS_VM_PENDING_PHYSICAL',iso_sha)":"print('R32 PASS_VM_PENDING_PHYSICAL',iso_sha)",
"'kernel-r31.nx'":"'kernel-r32.nx'",
}
for old,new in repls.items():
    n=src.count(old)
    if n!=1: raise SystemExit(f'r32 driver anchor mismatch {old!r}: {n}')
    src=src.replace(old,new,1)

needle=" req('v108_text_xpri_v131' in s and 'v108_text_xlog_v131' in s,'r31 primary/fallback USB telemetry missing')"
insert=needle+"""
 req('volatile_write64(xhci_state+2192' in s and 'volatile_read64(xhci+2192)' in s,'r31b telemetry bridge missing')
 req('xhci_root_port_settle_v132' in s,'r32 bounded root-port settle missing')
 ci=fn_text(s,'xhci_controller_init')
 req('let connected=xhci_root_port_settle_v132(xhci_state)' in ci,'r32 controller does not use settled root-port census')
 settle=fn_text(s,'xhci_root_port_settle_v132')
 req('while rounds<10 && stable<5' in settle and 'pit_wait(119320)' in settle,'r32 root-port settle is not bounded/stable')
 btn=fn_text(s,'ps2_elan4_buttons_v111')
 req('if typ==1 || typ==2 {' in btn and 'if typ==3' in btn,'r32 Elantech packet-class gate missing')
 motion=btn.split('if typ==3',1)[1]
 req('raw_right=(raw/2)%2' not in motion,'r32 motion packet can still synthesize right-button state')
 click=fn_text(s,'v108_input_test_click_v112')
 req('(old_buttons/2)%2' not in click and 'if (buttons/2)%2!=0' in click,'r32 stale right state can still block text focus')
 req('v108_text_r32_v132' in s and 'volatile_read64(xhci+2288)' in s and 'volatile_read64(xhci+2304)' in s,'r32 physical settle telemetry missing')"""
if src.count(needle)!=1: raise SystemExit(f'r32 inherited model gate anchor mismatch {src.count(needle)}')
src=src.replace(needle,insert,1)
ns={'__name__':'__main__','__file__':str(base)}
exec(compile(src,str(base),'exec'),ns,ns)
