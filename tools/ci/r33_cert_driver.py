#!/usr/bin/env python3
from pathlib import Path
base=Path(__file__).with_name('r32_cert_driver.py')
src=base.read_text()
repls={
"R26_SHA='dab5d471bf8cc80a38573fa52aa502f1bc488d9d3ecb655ce734350e123d732f'":"R26_SHA='d81cf6d3a6ff53c57d18748e1fcf7da49f03f9b580f26e59b21a01a08a1495cf'",
"patch_v108_r32_usb_settle_input_recovery.py":"patch_v108_r33_ehci_ownership_recovery.py",
"Frames-0.9.98-v108-r32-USB-Settle-Input-Recovery-Rufus-UEFI.iso":"Frames-0.9.98-v108-r33-EHCI-Ownership-Reroute-Recovery-Rufus-UEFI.iso",
"R32-SHA.txt":"R33-SHA.txt",
"R25K-R32.patch":"R25K-R33.patch",
"FRAMES_V108_R32":"FRAMES_V108_R33",
"(ROOT/'evidence/R32-AGGREGATE.json')":"(ROOT/'evidence/R33-AGGREGATE.json')",
"'profile':'frames-0.9.98-v108-r32-usb-settle-input-recovery'":"'profile':'frames-0.9.98-v108-r33-ehci-ownership-reroute-recovery'",
"'physical_r30b':'FAIL_USB_PHYSICAL_NO_HID_PHANTOM_RIGHT_MENU','physical_r31':'REJECTED_COMPILE_TELEMETRY_SCOPE','physical_r31b':'FAIL_USB_PHYSICAL_NO_HID_PHANTOM_RIGHT_MENU_TEXT_FOCUS','physical_r32':'PENDING'":"'physical_r30b':'FAIL_USB_PHYSICAL_NO_HID_PHANTOM_RIGHT_MENU','physical_r31':'REJECTED_COMPILE_TELEMETRY_SCOPE','physical_r31b':'FAIL_USB_PHYSICAL_NO_HID_PHANTOM_RIGHT_MENU_TEXT_FOCUS','physical_r32':'FAIL_USB_PHYSICAL_XHCI_ONE_ROOT_AFTER_SETTLE','physical_r33':'PENDING'",
"Frames 0.9.98 v108 r32 — USB Settle + Input Regression Recovery":"Frames 0.9.98 v108 r33 — EHCI Ownership + xHCI Reroute Recovery",
"print('R32 PASS_VM_PENDING_PHYSICAL',iso_sha)":"print('R33 PASS_VM_PENDING_PHYSICAL',iso_sha)",
"'kernel-r32.nx'":"'kernel-r33.nx'",
}
for old,new in repls.items():
    n=src.count(old)
    if n!=1: raise SystemExit(f'r33 driver anchor mismatch {old!r}: {n}')
    src=src.replace(old,new,1)
needle=" req('v108_text_r32_v132' in s and 'volatile_read64(xhci+2288)' in s and 'volatile_read64(xhci+2304)' in s,'r32 physical settle telemetry missing')"
insert=needle+"""
 req('v108_ehci_release_one_v133' in s and 'v108_ehci_release_companions_v133' in s,'r33 EHCI ownership release helpers missing')
 rel=fn_text(s,'v108_ehci_release_one_v133')
 req('pci_cfg_write32(bdf,eecp+4,0)' in rel and 'volatile_write32(op+8,0)' in rel,'r33 EHCI legacy/interrupt quiesce missing')
 req('clear_flag(cmd,1)' in rel and '/4096)%2' in rel,'r33 EHCI halt gate missing')
 scan=fn_text(s,'v108_xhci_scan_pointer_v116')
 req(scan.index('v108_ehci_release_companions_v133') < scan.index('xhci_controller_init'),'r33 EHCI release does not precede xHCI init')
 req('route_post_v133=v108_intel_xhci_route_ports_v120' in scan,'r33 post-init Intel reroute missing')
 req('volatile_write64(xhci_state+2368,post_v133)' in scan,'r33 post-reroute census telemetry missing')
 req('v108_text_r33_v133' in s and 'volatile_read64(xhci+2312)' in s and 'volatile_read64(xhci+2368)' in s,'r33 physical EHCI/xHCI telemetry row missing')"""
if src.count(needle)!=1: raise SystemExit(f'r33 inherited model gate anchor mismatch {src.count(needle)}')
src=src.replace(needle,insert,1)
ns={'__name__':'__main__','__file__':str(base)}
exec(compile(src,str(base),'exec'),ns,ns)
