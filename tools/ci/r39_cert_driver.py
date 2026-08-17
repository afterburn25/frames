#!/usr/bin/env python3
from pathlib import Path
import traceback
here=Path(__file__).parent
base=here/'r37b_cert_driver.py'
src=base.read_text()

def one(old,new,label):
    global src
    n=src.count(old)
    if n!=1: raise SystemExit(f'r39 cert anchor {label} count {n}')
    src=src.replace(old,new,1)

def alln(old,new,count,label):
    global src
    n=src.count(old)
    if n!=count: raise SystemExit(f'r39 cert anchor {label} count {n}, expected {count}')
    src=src.replace(old,new)

one("'patch_v108_r37b_stable_diag.py'","'patch_v108_r39_g750jm_hid_idle_disabled_wifi_ro.py'",'patch target')
one('kernel-r37b.nx','kernel-r39.nx','kernel evidence target')
one('2cb422d2c7d00cdbb1da3eee4ee696c9ae0723b3f28669bf80efe256d14de650','ba873c5bcfb810faa6210f440832ad359c5e91c012541fc2431c2bd1acb3a8d1','exact kernel identity')
one("'Frames-0.9.98-v108-r37b-G750JM-xHCI-Ring-Elantech-Stable-Diagnostics-Rufus-UEFI.iso'","'Frames-0.9.98-v108-r39-G750JM-HID-Idle-Disabled-Recovery-WiFi-Discovery-Rufus-UEFI.iso'",'ISO target')
one("'R37B-SHA.txt'","'R39-SHA.txt'",'SHA evidence target')
one("'R25K-R37B.patch'","'R25K-R39.patch'",'patch evidence target')
one("'FRAMES_V108_R37B'","'FRAMES_V108_R39'",'ISO label target')
one('R37B-AGGREGATE.json','R39-AGGREGATE.json','aggregate target')
one("'frames-0.9.98-v108-r37b-g750jm-xhci-ring-elantech-stable-diagnostics'","'frames-0.9.98-v108-r39-g750jm-hid-idle-disabled-recovery-wifi-discovery'",'profile target')
one("'Frames 0.9.98 v108 r37b — G750JM xHCI Ring + Elantech Stable Diagnostics'","'Frames 0.9.98 v108 r39 — G750JM HID Idle + Disabled Recovery + WiFi Discovery'",'cert title target')
one('R37B PASS_VM_PENDING_PHYSICAL','R39 PASS_VM_PENDING_PHYSICAL','PASS target')
alln('R37B-FAILURE.txt','R39-FAILURE.txt',2,'failure target')
one("'physical_r37':'NOT_TESTED','physical_r37b':'PENDING'","'physical_r37':'NOT_TESTED','physical_r37b':'FAIL_USB_PHYSICAL_TOUCHPAD_RECOVERED_HID_STOP_EVENT_Q0','physical_r37b_telemetry':'R37_S1_Q0_C1_K3_F2_E26','physical_r38':'FAIL_USB_PHYSICAL_ENDPOINT_DISABLED_NO_TRANSFER_EVENT','physical_r38_telemetry':'R38_S0_Q0_A0_T0_V255_E0','physical_r39':'PENDING'",'physical history target')

needle="    req('(410*65536)+28' in s and '(py+726)' in s,'r37b compact row geometry missing')"
insert=needle+"""
    req(r37_sha=='ba873c5bcfb810faa6210f440832ad359c5e91c012541fc2431c2bd1acb3a8d1','r39 exact kernel identity mismatch '+r37_sha)
    req('let idle_setup=2593+(2048*65536)+(interface_num*4294967296)' in s and 'volatile_write64(xhci_state+2960,idle_ok)' in s,'r39 bounded HID SET_IDLE missing')
    req('fn v139_xhci_hid_reconfigure_disabled' in s and 'if state==0 { v139_xhci_hid_reconfigure_disabled(xhci_state); return 1; }' in s,'r39 disabled endpoint recovery missing')
    req('volatile_read64(xhci_state+2968)>=2' in s and 'xhci_command_submit_configure(xhci_state,input,slot)' in s,'r39 bounded endpoint reconfigure missing')
    req('fn v139_wifi_pci_discover_ro' in s and 'while bus<32' in s and 'base==2 && sub==128' in s,'r39 WiFi PCI discovery missing')
    w0=s.index('fn v139_wifi_pci_discover_ro'); w1=s.index('fn v139_text_r39_v139',w0); wifi=s[w0:w1]
    req('pci_cfg_read32' in wifi and 'pci_cfg_write32' not in wifi,'r39 WiFi discovery is not read-only')
    req('fn v139_text_wifi_v139' in s and 'volatile_read64(xhci+3008)' in s and 'volatile_read64(xhci+3016)' in s and 'volatile_read64(xhci+3024)' in s,'r39 WiFi telemetry row missing')
    req('(410*65536)+780' in s and '(py+748)' in s,'r39 expanded read-only WiFi overlay geometry missing')
    req('ps2_poll_fallback_burst_v112(input_state,48);' in s and 'return ps2_elan4_motion_v112(input_state,a,b);' in s,'r39 regressed recovered touchpad path')
    req('fn v138_xhci_hid_drain_old_events' not in s,'r39 accidentally retained r38 HID regression path')
"""
one(needle,insert,'r39 model gates')

# r39 adds one read-only WiFi telemetry row, growing the full panel from 760 to
# 780 pixels. Adapt only this CI checkout's inherited r35 compatibility checks;
# historical certifiers in the repository remain unchanged.
r35p=here/'r35_cert_driver.py'
r35s=r35p.read_text()
old="new_gate=\" req('(410*65536)+760' in s,'r35 extended overlay height missing')\""
new="new_gate=\" req((('(410*65536)+760' in s) or ('(410*65536)+780' in s)),'r35/r39 extended overlay height missing')\""
if r35s.count(old)!=1: raise SystemExit('r39 private r35 height compatibility anchor mismatch')
r35s=r35s.replace(old,new,1)
r35s=r35s.replace("req('(410*65536)+760' in ov and 'py+712' in ov,'r35 overlay does not retain r34 telemetry')","req((('(410*65536)+760' in ov) or ('(410*65536)+780' in ov)) and 'py+712' in ov,'r35/r39 overlay does not retain r34 telemetry')",1)
r35s=r35s.replace("req('(410*65536)+760' in ov and 'py+730' in ov,'r35 overlay does not contain fallback telemetry row')","req((('(410*65536)+760' in ov) or ('(410*65536)+780' in ov)) and 'py+730' in ov,'r35/r39 overlay does not contain fallback telemetry row')",1)
r35p.write_text(r35s)

ns={'__name__':'__main__','__file__':str(base)}
try:
    exec(compile(src,str(base),'exec'),ns,ns)
except BaseException:
    out=Path('evidence'); out.mkdir(parents=True,exist_ok=True)
    (out/'R39-FAILURE.txt').write_text(traceback.format_exc())
    raise
