#!/usr/bin/env python3
from pathlib import Path
here=Path(__file__).parent
# r33b keeps the r32 settled-port evidence in state, but reuses the visible row
# for EHCI/xHCI ownership telemetry so the software-rendered overlay stays within
# the already-certified redraw budget. Preserve historical r32/r33 unchanged and
# adapt only private copies used by this certification chain.
r32=here/'r32_cert_driver.py'; compat=here/'r32_r33b_compat.py'
compat_src=r32.read_text()
old_r32=" req('v108_text_r32_v132' in s and 'volatile_read64(xhci+2288)' in s and 'volatile_read64(xhci+2304)' in s,'r32 physical settle telemetry missing')"
new_r32=" req('v108_text_r32_v132' in s and 'volatile_write64(xhci_state+2288' in s and 'volatile_write64(xhci_state+2304' in s,'r32/r33b settled-port telemetry state missing')"
if compat_src.count(old_r32)!=1: raise SystemExit('r33b r32 compatibility gate anchor mismatch')
compat.write_text(compat_src.replace(old_r32,new_r32,1))
base=here/'r33_cert_driver.py'
src=base.read_text()
base_anchor="base=Path(__file__).with_name('r32_cert_driver.py')"
if src.count(base_anchor)!=1: raise SystemExit('r33b r33 base anchor mismatch')
src=src.replace(base_anchor,"base=Path(__file__).with_name('r32_r33b_compat.py')",1)
# r33 uses the r32 assertion itself as the insertion anchor for r33 checks.
# Point that private generator anchor at the structural r32/r33b assertion too.
old_needle='needle="'+old_r32+'"'
new_needle='needle="'+new_r32+'"'
if src.count(old_needle)!=1: raise SystemExit('r33b r33 inherited needle anchor mismatch')
src=src.replace(old_needle,new_needle,1)
repls={
"R26_SHA='d81cf6d3a6ff53c57d18748e1fcf7da49f03f9b580f26e59b21a01a08a1495cf'":"R26_SHA='78081f168b3612b0f36d81b7dacca130a0f1ef0808385db81ae7a8178c130bb4'",
"patch_v108_r33_ehci_ownership_recovery.py":"patch_v108_r33b_overlay_render_recovery.py",
"Frames-0.9.98-v108-r33-EHCI-Ownership-Reroute-Recovery-Rufus-UEFI.iso":"Frames-0.9.98-v108-r33b-EHCI-Ownership-Reroute-Render-Recovery-Rufus-UEFI.iso",
"R33-SHA.txt":"R33B-SHA.txt",
"R25K-R33.patch":"R25K-R33B.patch",
"FRAMES_V108_R33":"FRAMES_V108_R33B",
"(ROOT/'evidence/R33-AGGREGATE.json')":"(ROOT/'evidence/R33B-AGGREGATE.json')",
"'profile':'frames-0.9.98-v108-r33-ehci-ownership-reroute-recovery'":"'profile':'frames-0.9.98-v108-r33b-ehci-ownership-reroute-render-recovery'",
"'physical_r32':'FAIL_USB_PHYSICAL_XHCI_ONE_ROOT_AFTER_SETTLE','physical_r33':'PENDING'":"'physical_r32':'FAIL_USB_PHYSICAL_XHCI_ONE_ROOT_AFTER_SETTLE','physical_r33':'REJECTED_VM_SMOOTH_OVERLAY_REDRAW','physical_r33b':'PENDING'",
"Frames 0.9.98 v108 r33 — EHCI Ownership + xHCI Reroute Recovery":"Frames 0.9.98 v108 r33b — EHCI Ownership + xHCI Reroute + Render Recovery",
"print('R33 PASS_VM_PENDING_PHYSICAL',iso_sha)":"print('R33B PASS_VM_PENDING_PHYSICAL',iso_sha)",
"'kernel-r33.nx'":"'kernel-r33b.nx'",
}
for old,new in repls.items():
 n=src.count(old)
 if n!=1: raise SystemExit(f'r33b driver anchor mismatch {old!r}: {n}')
 src=src.replace(old,new,1)
needle=" req('v108_text_r33_v133' in s and 'volatile_read64(xhci+2312)' in s and 'volatile_read64(xhci+2368)' in s,'r33 physical EHCI/xHCI telemetry row missing')"
insert=needle+"""
 ov=fn_text(s,'v108_input_overlay_draw')
 req('v108_text_r33_v133(surface' not in ov,'r33b slow extra telemetry row still rendered')
 req('volatile_read64(xhci+2312)' in ov and 'volatile_read64(xhci+2368)' in ov,'r33b merged final telemetry missing')
 req('(410*65536)+760' not in s,'r33b overlay height regression remains')"""
if src.count(needle)!=1: raise SystemExit(f'r33b inherited gate anchor mismatch {src.count(needle)}')
src=src.replace(needle,insert,1)
ns={'__name__':'__main__','__file__':str(base)}
exec(compile(src,str(base),'exec'),ns,ns)
