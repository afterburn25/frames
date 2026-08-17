#!/usr/bin/env python3
from pathlib import Path
import traceback
base=Path(__file__).with_name('r35_cert_driver.py')
src=base.read_text()
repls={
"R26_SHA='168f103ae3ba8f6dc403b1fa4c18aab01ab8160bd63387efffd1688ef8532ad0'":"R26_SHA='a9761e17e71d803df703a7cfe6b4461a6d02ea6c398d2299c1f0fd72f48f8b28'",
"patch_v108_r35_hid_control_poll_fallback.py":"patch_v108_r35b_g750jm_hm87_hid_interval.py",
"Frames-0.9.98-v108-r35-HID-Control-Poll-Fallback-Recovery-Rufus-UEFI.iso":"Frames-0.9.98-v108-r35b-G750JM-HM87-HID-Interval-Recovery-Rufus-UEFI.iso",
"R35-SHA.txt":"R35B-SHA.txt",
"R25K-R35.patch":"R25K-R35B.patch",
"FRAMES_V108_R35":"FRAMES_V108_R35B",
"(ROOT/'evidence/R35-AGGREGATE.json')":"(ROOT/'evidence/R35B-AGGREGATE.json')",
"'profile':'frames-0.9.98-v108-r35-hid-control-poll-fallback-recovery'":"'profile':'frames-0.9.98-v108-r35b-g750jm-hm87-hid-interval-recovery'",
"'physical_r32':'FAIL_USB_PHYSICAL_XHCI_ONE_ROOT_AFTER_SETTLE','physical_r33':'REJECTED_VM_SMOOTH_OVERLAY_REDRAW','physical_r33b':'REJECTED_VM_SMOOTH_FULL_PANEL_MOTION_REDRAW','physical_r33c':'NOT_TESTED','physical_r34':'FAIL_USB_PHYSICAL_HID_CONFIGURED_NO_LIVE_INTERRUPT_REPORT','physical_r34_telemetry':'R34_B1_P5_A1_O1_C5_E0_USB_H1_R0_P2','physical_r35':'PENDING'":"'physical_r32':'FAIL_USB_PHYSICAL_XHCI_ONE_ROOT_AFTER_SETTLE','physical_r33':'REJECTED_VM_SMOOTH_OVERLAY_REDRAW','physical_r33b':'REJECTED_VM_SMOOTH_FULL_PANEL_MOTION_REDRAW','physical_r33c':'NOT_TESTED','physical_r34':'FAIL_USB_PHYSICAL_HID_CONFIGURED_NO_LIVE_INTERRUPT_REPORT','physical_r34_telemetry':'R34_B1_P5_A1_O1_C5_E0_USB_H1_R0_P2','physical_r35':'NOT_TESTED','physical_r35b':'PENDING'",
"Frames 0.9.98 v108 r35 — HID EP0 Control-Poll Fallback Recovery":"Frames 0.9.98 v108 r35b — G750JM/HM87 HID Interval Recovery",
"print('R35 PASS_VM_PENDING_PHYSICAL',iso_sha)":"print('R35B PASS_VM_PENDING_PHYSICAL',iso_sha)",
"'kernel-r35.nx'":"'kernel-r35b.nx'",
"(out/'R35-FAILURE.txt')":"(out/'R35B-FAILURE.txt')",
}
for old,new in repls.items():
    n=src.count(old)
    if n!=1: raise SystemExit(f'r35b driver anchor mismatch {old!r}: {n}')
    src=src.replace(old,new,1)
needle=" req('cy<768' in s,'r35 lower telemetry cursor overlap coverage missing')"
insert=needle+"""
 req('var v:u64=binterval; var p:u64=0; while v>1 { v=v/2; p=p+1; }' in s,'r35b LS/FS floor interval conversion missing')
 req('while v<binterval { v=v*2; p=p+1; }' not in s,'r35b stale ceil interval conversion remains')
 req('volatile_write64(xhci_state+2664,speed)' in s and 'volatile_write64(xhci_state+2672,binterval)' in s and 'volatile_write64(xhci_state+2680,interval)' in s,'r35b physical interval telemetry missing')
 req('vendor!=32902 || device!=35889' in s,'r35b Lynx Point 8086:8C31 target guard missing')
 req('u2m==16383 && u3m==63 && u2r==u2m && u3r==u3m' in s and 'hm87_contract_v135b' in s,'r35b G750JM/HM87 route contract stamp missing')
 req('pci_cfg_read32(bus,dev,fun,212)' in s and 'pci_cfg_read32(bus,dev,fun,208)' in s and 'pci_cfg_read32(bus,dev,fun,220)' in s and 'pci_cfg_read32(bus,dev,fun,216)' in s,'r35b Lynx Point route registers changed unexpectedly')
 for bi,expected in [(1,3),(2,4),(3,4),(4,5),(5,5),(8,6),(10,6),(16,7),(31,7),(255,10)]:
  vv=bi; pp=0
  while vv>1: vv//=2; pp+=1
  pp+=3
  if pp>10: pp=10
  req(pp==expected,f'r35b interval model mismatch bInterval={bi}: {pp}!={expected}')
"""
if src.count(needle)!=1: raise SystemExit(f'r35b inherited r35 gate anchor mismatch {src.count(needle)}')
src=src.replace(needle,insert,1)
ns={'__name__':'__main__','__file__':str(base)}
try:
    exec(compile(src,str(base),'exec'),ns,ns)
except BaseException:
    out=Path('evidence')
    out.mkdir(parents=True,exist_ok=True)
    (out/'R35B-FAILURE.txt').write_text(traceback.format_exc())
    raise
