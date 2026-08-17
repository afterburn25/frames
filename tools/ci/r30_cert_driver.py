#!/usr/bin/env python3
from pathlib import Path
base=Path(__file__).with_name('r29_cert_driver.py')
src=base.read_text()
repls={
"R26_SHA='21c34b8d03e581a60c55056e9bf363c298128ea3a3a5e94ad2cb1e15120b1b33'":"R26_SHA='430399228868e7cef069c5a45bb7c687954cc6e87dc9e461ba8669516e82ea4d'",
"patch_v108_r29_root_port_recovery.py":"patch_v108_r30_hid_first_right_click.py",
"Frames-0.9.98-v108-r29-Root-Port-Power-Reset-Recovery-Rufus-UEFI.iso":"Frames-0.9.98-v108-r30-HID-First-Right-Click-Recovery-Rufus-UEFI.iso",
"R29-SHA.txt":"R30-SHA.txt",
"R25K-R29.patch":"R25K-R30.patch",
"FRAMES_V108_R29":"FRAMES_V108_R30",
"(ROOT/'evidence/R29-AGGREGATE.json')":"(ROOT/'evidence/R30-AGGREGATE.json')",
"'profile':'frames-0.9.98-v108-r29-root-port-power-reset-recovery'":"'profile':'frames-0.9.98-v108-r30-hid-first-right-click-recovery'",
"'physical_r26':'FAIL_LOG_UNTOUCHED_USB_NATIVE_OPEN','physical_r27':'FAIL_USB_PHYSICAL_NO_HID','physical_r28b':'FAIL_VM_HUB_CONTEXT_STATE','physical_r28c':'FAIL_USB_PHYSICAL_NO_HID','physical_r29':'PENDING'":"'physical_r26':'FAIL_LOG_UNTOUCHED_USB_NATIVE_OPEN','physical_r27':'FAIL_USB_PHYSICAL_NO_HID','physical_r28b':'FAIL_VM_HUB_CONTEXT_STATE','physical_r28c':'FAIL_USB_PHYSICAL_NO_HID','physical_r29':'FAIL_USB_PHYSICAL_NO_HID_RIGHT_MENU_MISSING_BOOT_CLICK_DELAY','physical_r30':'PENDING'",
"Frames 0.9.98 v108 r29 — Root Port Power + Per-Port Reset Recovery":"Frames 0.9.98 v108 r30 — HID-First USB Scan + Physical Right-Click Recovery",
"print('R29 PASS_VM_PENDING_PHYSICAL',iso_sha)":"print('R30 PASS_VM_PENDING_PHYSICAL',iso_sha)",
"'kernel-r29.nx'":"'kernel-r30.nx'",
}
for old,new in repls.items():
    n=src.count(old)
    if n!=1: raise SystemExit(f'r30 driver anchor mismatch {old!r}: {n}')
    src=src.replace(old,new,1)

# r29 injects its model checks inside a triple-quoted payload in
# r29_cert_driver.py. Extend that payload using one stable plain-text check
# rather than coupling r30 to the wrapper's closing quote representation.
needle=" req('v108_text_xpwr_v129' in s and 'v108_text_xrty_v129' in s,'r29 physical recovery telemetry missing')"
insert=needle+"""
 scan=fn_text(s,'v108_xhci_scan_pointer_v116')
 req('v108_msc_snapshot_v125(xhci_state,hardware_state,phys_state,fr)' not in scan,'r30 HID scan still configures MSC before HID')
 for q in ('hid_probe_v130','volatile_write64(xhci_state+2072','volatile_write64(xhci_state+2160'):
  req(q in scan,'r30 second-device telemetry missing '+q)
 rb=fn_text(s,'ps2_elan4_buttons_v111')
 req('var need:u64=1;' in rb,'r30 ELAN right click still requires repeated packets')
 gi=fn_text(s,'gui_input_buttons')
 req('if right!=0 && old_right==0' in gi and 'volatile_write64(state+128,1)' in gi,'r30 right-down context open missing')
 req('v108_text_x2a_v130' in s and 'v108_text_x2f_v130' in s and 'v108_text_rbtn_v130' in s,'r30 physical telemetry labels missing')"""
if src.count(needle)!=1: raise SystemExit(f'r30 inherited gate payload anchor mismatch {src.count(needle)}')
src=src.replace(needle,insert,1)
ns={'__name__':'__main__','__file__':str(base)}
exec(compile(src,str(base),'exec'),ns,ns)
