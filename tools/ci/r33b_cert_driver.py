#!/usr/bin/env python3
from pathlib import Path
base=Path(__file__).with_name('r33_cert_driver.py')
src=base.read_text()
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
