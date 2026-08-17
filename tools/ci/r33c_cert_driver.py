#!/usr/bin/env python3
from pathlib import Path
base=Path(__file__).with_name('r33b_cert_driver.py')
src=base.read_text()
repls={
"R26_SHA='78081f168b3612b0f36d81b7dacca130a0f1ef0808385db81ae7a8178c130bb4'":"R26_SHA='53a6e654154d2d622650c16aefac12bc9cbee9c4a3cfc772948dd60feeb62c3e'",
"patch_v108_r33b_overlay_render_recovery.py":"patch_v108_r33c_motion_telemetry_isolation.py",
"Frames-0.9.98-v108-r33b-EHCI-Ownership-Reroute-Render-Recovery-Rufus-UEFI.iso":"Frames-0.9.98-v108-r33c-EHCI-Ownership-Reroute-Motion-Telemetry-Recovery-Rufus-UEFI.iso",
"R33B-SHA.txt":"R33C-SHA.txt",
"R25K-R33B.patch":"R25K-R33C.patch",
"FRAMES_V108_R33B":"FRAMES_V108_R33C",
"(ROOT/'evidence/R33B-AGGREGATE.json')":"(ROOT/'evidence/R33C-AGGREGATE.json')",
"'profile':'frames-0.9.98-v108-r33b-ehci-ownership-reroute-render-recovery'":"'profile':'frames-0.9.98-v108-r33c-ehci-ownership-reroute-motion-telemetry-recovery'",
"'physical_r32':'FAIL_USB_PHYSICAL_XHCI_ONE_ROOT_AFTER_SETTLE','physical_r33':'REJECTED_VM_SMOOTH_OVERLAY_REDRAW','physical_r33b':'PENDING'":"'physical_r32':'FAIL_USB_PHYSICAL_XHCI_ONE_ROOT_AFTER_SETTLE','physical_r33':'REJECTED_VM_SMOOTH_OVERLAY_REDRAW','physical_r33b':'REJECTED_VM_SMOOTH_FULL_PANEL_MOTION_REDRAW','physical_r33c':'PENDING'",
"Frames 0.9.98 v108 r33b — EHCI Ownership + xHCI Reroute + Render Recovery":"Frames 0.9.98 v108 r33c — EHCI Ownership + xHCI Reroute + Motion Telemetry Recovery",
"print('R33B PASS_VM_PENDING_PHYSICAL',iso_sha)":"print('R33C PASS_VM_PENDING_PHYSICAL',iso_sha)",
"'kernel-r33b.nx'":"'kernel-r33c.nx'",
}
for old,new in repls.items():
 n=src.count(old)
 if n!=1: raise SystemExit(f'r33c driver anchor mismatch {old!r}: {n}')
 src=src.replace(old,new,1)
needle=" req('(410*65536)+760' not in s,'r33b overlay height regression remains')"
insert=needle+"""
 req('fn v108_input_overlay_motion_draw_v133c' in s and 'fn v108_input_overlay_motion_present_v133c' in s,'r33c compact motion telemetry helpers missing')
 rt=fn_text(s,'desktop_input_runtime')
 req('motion_telemetry_redraw:u64=0' in rt and 'motion_telemetry_redraw=1' in rt,'r33c motion telemetry state missing')
 req('now_idle-moved>180000000' in rt and 'motion_telemetry_redraw=1' in rt,'r33c raw-idle path not isolated')
 req('v108_input_overlay_motion_present_v133c(process,input_state)' in rt,'r33c compact motion present not used')
 live=fn_text(s,'v108_input_overlay_motion_draw_v133c')
 req('(410*65536)+94' in live and 'v108_text_p2raw' in live and 'v108_text_xhc' not in live,'r33c motion redraw is not compact')
 req('volatile_write64(xhci_state+2368,post_v133)' in s,'r33c lost EHCI/xHCI ownership evidence')"""
if src.count(needle)!=1: raise SystemExit(f'r33c inherited gate anchor mismatch {src.count(needle)}')
src=src.replace(needle,insert,1)
ns={'__name__':'__main__','__file__':str(base)}
exec(compile(src,str(base),'exec'),ns,ns)
