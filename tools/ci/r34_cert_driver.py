#!/usr/bin/env python3
from pathlib import Path
import traceback
base=Path(__file__).with_name('r33c_cert_driver.py')
src=base.read_text()
repls={
"R26_SHA='53a6e654154d2d622650c16aefac12bc9cbee9c4a3cfc772948dd60feeb62c3e'":"R26_SHA='faed1632f131333e4e2c81c393b1e0df6a7940fde2c8506605e9b8964e7c5621'",
"patch_v108_r33c_motion_telemetry_isolation.py":"patch_v108_r34_late_reroute_reinit.py",
"Frames-0.9.98-v108-r33c-EHCI-Ownership-Reroute-Motion-Telemetry-Recovery-Rufus-UEFI.iso":"Frames-0.9.98-v108-r34-Late-Reroute-xHCI-Reinit-Recovery-Rufus-UEFI.iso",
"R33C-SHA.txt":"R34-SHA.txt",
"R25K-R33C.patch":"R25K-R34.patch",
"FRAMES_V108_R33C":"FRAMES_V108_R34",
"(ROOT/'evidence/R33C-AGGREGATE.json')":"(ROOT/'evidence/R34-AGGREGATE.json')",
"'profile':'frames-0.9.98-v108-r33c-ehci-ownership-reroute-motion-telemetry-recovery'":"'profile':'frames-0.9.98-v108-r34-late-reroute-xhci-reinit-recovery'",
"'physical_r32':'FAIL_USB_PHYSICAL_XHCI_ONE_ROOT_AFTER_SETTLE','physical_r33':'REJECTED_VM_SMOOTH_OVERLAY_REDRAW','physical_r33b':'REJECTED_VM_SMOOTH_FULL_PANEL_MOTION_REDRAW','physical_r33c':'PENDING'":"'physical_r32':'FAIL_USB_PHYSICAL_XHCI_ONE_ROOT_AFTER_SETTLE','physical_r33':'REJECTED_VM_SMOOTH_OVERLAY_REDRAW','physical_r33b':'REJECTED_VM_SMOOTH_FULL_PANEL_MOTION_REDRAW','physical_r33c':'FAIL_USB_PHYSICAL_LATE_REROUTE_NO_HID','physical_r34':'PENDING'",
"Frames 0.9.98 v108 r33c — EHCI Ownership + xHCI Reroute + Motion Telemetry Recovery":"Frames 0.9.98 v108 r34 — Late-Reroute xHCI Reinitialization Recovery",
"print('R33C PASS_VM_PENDING_PHYSICAL',iso_sha)":"print('R34 PASS_VM_PENDING_PHYSICAL',iso_sha)",
"'kernel-r33c.nx'":"'kernel-r34.nx'",
}
for old,new in repls.items():
 n=src.count(old)
 if n!=1: raise SystemExit(f'r34 driver anchor mismatch {old!r}: {n}')
 src=src.replace(old,new,1)
needle=" req('volatile_write64(xhci_state+2368,post_v133)' in s,'r33c lost EHCI/xHCI ownership evidence')"
insert=needle+"""
 req('var init_ok_v120=xhci_controller_init' in s,'r34 mutable initial xHCI init result missing')
 scan=fn_text(s,'v108_xhci_scan_pointer_v116')
 req('before_v134=volatile_read64(xhci_state+2032)' in scan and 'if post_v133>before_v134' in scan,'r34 late-route growth gate missing')
 req(scan.count('xhci_controller_init(hardware_state,phys_state,xhci_state,pml4)')>=2,'r34 xHCI reinitialization call missing')
 req('route_reinit_pre_v134' in scan and 'route_reinit_post_v134' in scan,'r34 reinit routing sandwich missing')
 req('xhci_power_root_ports_v129(xhci_state)' in scan and 'reinit_after_v134=xhci_root_port_settle_v132(xhci_state)' in scan,'r34 reinit power/settle missing')
 req('volatile_write64(xhci_state+2496,before_v134)' in scan and 'volatile_write64(xhci_state+2536,reinit_err_v134)' in scan,'r34 physical reinit telemetry missing')
 req('v108_text_r34_v134' in s and 'volatile_read64(xhci+2496)' in s and 'volatile_read64(xhci+2536)' in s,'r34 overlay telemetry row missing')
 req('(410*65536)+778' in s,'r34 overlay height extension missing')"""
if src.count(needle)!=1: raise SystemExit(f'r34 inherited gate anchor mismatch {src.count(needle)}')
src=src.replace(needle,insert,1)
ns={'__name__':'__main__','__file__':str(base)}
try:
 exec(compile(src,str(base),'exec'),ns,ns)
except BaseException:
 out=Path('evidence')
 out.mkdir(parents=True,exist_ok=True)
 (out/'R34-FAILURE.txt').write_text(traceback.format_exc())
 raise
