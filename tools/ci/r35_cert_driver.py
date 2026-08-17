#!/usr/bin/env python3
from pathlib import Path
import traceback
base=Path(__file__).with_name('r34_cert_driver.py')
src=base.read_text()
repls={
"R26_SHA='faed1632f131333e4e2c81c393b1e0df6a7940fde2c8506605e9b8964e7c5621'":"R26_SHA='168f103ae3ba8f6dc403b1fa4c18aab01ab8160bd63387efffd1688ef8532ad0'",
"patch_v108_r34_late_reroute_reinit.py":"patch_v108_r35_hid_control_poll_fallback.py",
"Frames-0.9.98-v108-r34-Late-Reroute-xHCI-Reinit-Recovery-Rufus-UEFI.iso":"Frames-0.9.98-v108-r35-HID-Control-Poll-Fallback-Recovery-Rufus-UEFI.iso",
"R34-SHA.txt":"R35-SHA.txt",
"R25K-R34.patch":"R25K-R35.patch",
"FRAMES_V108_R34":"FRAMES_V108_R35",
"(ROOT/'evidence/R34-AGGREGATE.json')":"(ROOT/'evidence/R35-AGGREGATE.json')",
"'profile':'frames-0.9.98-v108-r34-late-reroute-xhci-reinit-recovery'":"'profile':'frames-0.9.98-v108-r35-hid-control-poll-fallback-recovery'",
"'physical_r32':'FAIL_USB_PHYSICAL_XHCI_ONE_ROOT_AFTER_SETTLE','physical_r33':'REJECTED_VM_SMOOTH_OVERLAY_REDRAW','physical_r33b':'REJECTED_VM_SMOOTH_FULL_PANEL_MOTION_REDRAW','physical_r33c':'NOT_TESTED','physical_r34':'PENDING'":"'physical_r32':'FAIL_USB_PHYSICAL_XHCI_ONE_ROOT_AFTER_SETTLE','physical_r33':'REJECTED_VM_SMOOTH_OVERLAY_REDRAW','physical_r33b':'REJECTED_VM_SMOOTH_FULL_PANEL_MOTION_REDRAW','physical_r33c':'NOT_TESTED','physical_r34':'FAIL_USB_PHYSICAL_HID_CONFIGURED_NO_LIVE_INTERRUPT_REPORT','physical_r34_telemetry':'R34_B1_P5_A1_O1_C5_E0_USB_H1_R0_P2','physical_r35':'PENDING'",
"Frames 0.9.98 v108 r34 — Late-Reroute xHCI Reinitialization Recovery":"Frames 0.9.98 v108 r35 — HID EP0 Control-Poll Fallback Recovery",
"print('R34 PASS_VM_PENDING_PHYSICAL',iso_sha)":"print('R35 PASS_VM_PENDING_PHYSICAL',iso_sha)",
"'kernel-r34.nx'":"'kernel-r35.nx'",
"(out/'R34-FAILURE.txt')":"(out/'R35-FAILURE.txt')",
}
for old,new in repls.items():
 n=src.count(old)
 if n!=1: raise SystemExit(f'r35 driver anchor mismatch {old!r}: {n}')
 src=src.replace(old,new,1)
old=" req('(410*65536)+742' in ov and 'py+712' in ov,'r34 compact overlay does not contain the new telemetry row')"
new=""" req('(410*65536)+760' in ov and 'py+712' in ov,'r35 overlay does not retain r34 telemetry')
 req('fn v135_xhci_wait_ep0_bounded' in s,'r35 bounded EP0 event wait missing')
 req('fn v135_xhci_control_get_into' in s and 'v135_xhci_wait_ep0_bounded(xhci_state,slot)' in s,'r35 reusable bounded EP0 control IN path missing')
 req('fn v135_hid_control_fallback_prepare' in s,'r35 HID control fallback prepare missing')
 req('usb_setup_value_v113(33,11,0,ki)' in s and 'usb_setup_value_v113(33,11,0,mi)' in s,'r35 alternate boot protocol preparation missing')
 req('fn v135_hid_control_fallback_poll' in s and 'usb_setup_value_v113(161,1,256,iface)' in s,'r35 HID GET_REPORT fallback missing')
 req('volatile_read64(xhci_state+816)!=0' in s,'r35 interrupt-first fallback gate missing')
 req('v135_hid_control_fallback_prepare(xhci,phys_state)' in s and 'v135_hid_control_fallback_poll(xhci,input_state)' in s,'r35 desktop runtime fallback integration missing')
 req('volatile_write64(xhci_state+2560,1)' in s and 'volatile_write64(xhci_state+2592,volatile_read64(xhci_state+2592)+1)' in s,'r35 fallback telemetry state missing')
 req('v108_text_r35_v135' in s and 'volatile_read64(xhci+2560)' in s and 'volatile_read64(xhci+2616)' in s,'r35 physical telemetry row missing')
 ov=fn_text(s,'v108_input_overlay_draw')
 req('(410*65536)+760' in ov and 'py+730' in ov,'r35 overlay does not contain fallback telemetry row')
 req('cy<768' in s,'r35 lower telemetry cursor overlap coverage missing')"""
if src.count(old)!=1: raise SystemExit(f'r35 inherited r34 gate anchor mismatch {src.count(old)}')
src=src.replace(old,new,1)
ns={'__name__':'__main__','__file__':str(base)}
try:
 exec(compile(src,str(base),'exec'),ns,ns)
except BaseException:
 out=Path('evidence')
 out.mkdir(parents=True,exist_ok=True)
 (out/'R35-FAILURE.txt').write_text(traceback.format_exc())
 raise
