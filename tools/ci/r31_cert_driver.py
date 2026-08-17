#!/usr/bin/env python3
from pathlib import Path
base=Path(__file__).with_name('r30b_cert_driver.py')
src=base.read_text()
repls={
"R26_SHA='d947d603112369340749e6be8397bfed08bf1de49651a0a0602571afcb754c3b'":"R26_SHA='cf7a3f890811d6ff245ec822bf5fd38d01f405c990c7dce6161efb117699797c'",
"patch_v108_r30b_hid_first_device_state.py":"patch_v108_r31_usb_state_isolation.py",
"Frames-0.9.98-v108-r30b-HID-First-Device-State-Right-Click-Recovery-Rufus-UEFI.iso":"Frames-0.9.98-v108-r31-USB-State-Isolation-Controller-Order-Recovery-Rufus-UEFI.iso",
"R30B-SHA.txt":"R31-SHA.txt",
"R25K-R30B.patch":"R25K-R31.patch",
"FRAMES_V108_R30B":"FRAMES_V108_R31",
"(ROOT/'evidence/R30B-AGGREGATE.json')":"(ROOT/'evidence/R31-AGGREGATE.json')",
"'profile':'frames-0.9.98-v108-r30b-hid-first-device-state-right-click-recovery'":"'profile':'frames-0.9.98-v108-r31-usb-state-isolation-controller-order-recovery'",
"'physical_r29':'FAIL_USB_PHYSICAL_NO_HID_RIGHT_MENU_MISSING_BOOT_CLICK_DELAY','physical_r30':'REJECTED_LOG_GATE','physical_r30b':'PENDING'":"'physical_r29':'FAIL_USB_PHYSICAL_NO_HID_RIGHT_MENU_MISSING_BOOT_CLICK_DELAY','physical_r30':'REJECTED_LOG_GATE','physical_r30b':'FAIL_USB_PHYSICAL_NO_HID_PHANTOM_RIGHT_MENU','physical_r31':'PENDING'",
"Frames 0.9.98 v108 r30b — HID-First Per-Device State + Right-Click Recovery":"Frames 0.9.98 v108 r31 — USB State Isolation + Controller Start Order Recovery",
"print('R30B PASS_VM_PENDING_PHYSICAL',iso_sha)":"print('R31 PASS_VM_PENDING_PHYSICAL',iso_sha)",
"'kernel-r30b.nx'":"'kernel-r31.nx'",
}
for old,new in repls.items():
    n=src.count(old)
    if n!=1: raise SystemExit(f'r31 driver anchor mismatch {old!r}: {n}')
    src=src.replace(old,new,1)

needle=" req('v108_text_x2a_v130' in s and 'v108_text_x2f_v130' in s and 'v108_text_rbtn_v130' in s,'r30b physical telemetry labels missing')"
insert=needle+"""
 req('let usb_scan_state = bump_alloc' in s and 'volatile_write64(hardware_state+920,usb_scan_state)' in s,'r31 dedicated fallback controller state missing')
 retain=fn_text(s,'v108_log_msc_retain_v125')
 req('zero_page(scan)' in retain and 'zero_page(xhci_state)' not in retain,'r31 fallback MSC still zeros primary xHCI state')
 req('xhci_controller_init(hardware_state,phys_state,scan,pml4)' in retain,'r31 fallback MSC does not use isolated controller state')
 req('volatile_write64(msc+2176,1)' in retain,'r31 isolated MSC owner marker missing')
 sync=fn_text(s,'flight_sync_events_v125')
 req('volatile_read64(msc+2176)!=0' in sync,'r31 isolated MSC event-index guard missing')
 ci=fn_text(s,'xhci_controller_init')
 req(ci.index('volatile_write32(intr+8,1)') < ci.index('cmd=set_flag(cmd,1)'),'r31 event ring/interrupter still programmed after controller Run')
 req('volatile_write64(xhci_state+2184,1)' in ci,'r31 controller-order proof marker missing')
 req('v108_text_xpri_v131' in s and 'v108_text_xlog_v131' in s,'r31 primary/fallback USB telemetry missing')"""
if src.count(needle)!=1: raise SystemExit(f'r31 inherited model gate anchor mismatch {src.count(needle)}')
src=src.replace(needle,insert,1)
ns={'__name__':'__main__','__file__':str(base)}
exec(compile(src,str(base),'exec'),ns,ns)
