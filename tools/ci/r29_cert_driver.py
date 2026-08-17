#!/usr/bin/env python3
from pathlib import Path
base=Path(__file__).with_name('r28c_cert_driver.py')
src=base.read_text()
repls={
"R26_SHA='8e1401d483bcff3a5e67caf3c6183fdafe370a3de742675ca0adc255c67d13b5'":"R26_SHA='21c34b8d03e581a60c55056e9bf363c298128ea3a3a5e94ad2cb1e15120b1b33'",
"patch_v108_r28c_hub_ep0_state_isolation.py":"patch_v108_r29_root_port_recovery.py",
"Frames-0.9.98-v108-r28c-EP0-Address-Evaluate-Hub-State-Isolation-Rufus-UEFI.iso":"Frames-0.9.98-v108-r29-Root-Port-Power-Reset-Recovery-Rufus-UEFI.iso",
"R28C-SHA.txt":"R29-SHA.txt",
"R25K-R28C.patch":"R25K-R29.patch",
"FRAMES_V108_R28C":"FRAMES_V108_R29",
"(ROOT/'evidence/R28C-AGGREGATE.json')":"(ROOT/'evidence/R29-AGGREGATE.json')",
"'profile':'frames-0.9.98-v108-r28c-ep0-address-evaluate-hub-state-isolation'":"'profile':'frames-0.9.98-v108-r29-root-port-power-reset-recovery'",
"'physical_r26':'FAIL_LOG_UNTOUCHED_USB_NATIVE_OPEN','physical_r27':'FAIL_USB_PHYSICAL_NO_HID','physical_r28b':'FAIL_VM_HUB_CONTEXT_STATE','physical_r28c':'PENDING'":"'physical_r26':'FAIL_LOG_UNTOUCHED_USB_NATIVE_OPEN','physical_r27':'FAIL_USB_PHYSICAL_NO_HID','physical_r28b':'FAIL_VM_HUB_CONTEXT_STATE','physical_r28c':'FAIL_USB_PHYSICAL_NO_HID','physical_r29':'PENDING'",
"Frames 0.9.98 v108 r28c — EP0 Addressed-State + Evaluate Context + Hub State Isolation":"Frames 0.9.98 v108 r29 — Root Port Power + Per-Port Reset Recovery",
"print('R28C PASS_VM_PENDING_PHYSICAL',iso_sha)":"print('R29 PASS_VM_PENDING_PHYSICAL',iso_sha)",
"'kernel-r28c.nx'":"'kernel-r29.nx'",
}
for old,new in repls.items():
    n=src.count(old)
    if n!=1: raise SystemExit(f'r29 driver anchor mismatch {old!r}: {n}')
    src=src.replace(old,new,1)

# r28c is itself a wrapper around r28_cert_driver.py.  Extend the literal
# model-gate payload inside that wrapper rather than searching for text that
# only exists after r28c executes.
needle="  req(q in hub,'r28c hub EP0 state isolation missing '+q)\n\"\"\""
insert="""  req(q in hub,'r28c hub EP0 state isolation missing '+q)
 req('fn xhci_power_root_ports_v129' in s,'r29 root-port power helper missing')
 pwr=fn_text(s,'xhci_power_root_ports_v129')
 for q in ('(hcc/8)%2','set_flag(w,512)','pit_wait(119320)','volatile_write64(xhci_state+2032,connected)'):
  req(q in pwr,'r29 root-port power contract missing '+q)
 rst=fn_text(s,'xhci_reset_connected_port_from')
 for q in ('failed=failed+1','first_reason=reason','p=p+1','return p+1'):
  req(q in rst,'r29 per-port reset recovery missing '+q)
 req(rst.count('return 0;')==2,'r29 reset path regained per-port abort')
 req('if pspeed<=2 && volatile_read64(hardware_state+736)==0' not in s,'r29 first-root telemetry remained LSFS-only')
 req('v108_text_xpwr_v129' in s and 'v108_text_xrty_v129' in s,'r29 physical recovery telemetry missing')
\"\"\""""
if src.count(needle)!=1: raise SystemExit(f'r29 inherited gate payload anchor mismatch {src.count(needle)}')
src=src.replace(needle,insert,1)
ns={'__name__':'__main__','__file__':str(base)}
exec(compile(src,str(base),'exec'),ns,ns)
