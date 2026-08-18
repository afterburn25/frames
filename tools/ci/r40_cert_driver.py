#!/usr/bin/env python3
from pathlib import Path
import traceback
here=Path(__file__).parent
base=here/'r39b_cert_driver.py'
src=base.read_text()

def one(old,new,label):
    global src
    n=src.count(old)
    if n!=1: raise SystemExit(f'r40 cert anchor {label} count {n}')
    src=src.replace(old,new,1)

def alln(old,new,count,label):
    global src
    n=src.count(old)
    if n!=count: raise SystemExit(f'r40 cert anchor {label} count {n}, expected {count}')
    src=src.replace(old,new)

one("'patch_v108_r39b_g750jm_hid_idle_1s_wifi_ro.py'","'patch_v108_r40_usb_hid_identity_wifi_pci_detail_ro.py'",'patch target')
one('kernel-r39b.nx','kernel-r40.nx','kernel evidence target')
alln('7ca4e51896453e0bcaa131d7f4497e64e95556cb96941c599fa4151eb71bbea5','ae9598872e6806907e8bb623050f4314dbdda140ecd6b9c620f36e1c669b4c6c',1,'exact kernel identity')
one("'Frames-0.9.98-v108-r39b-G750JM-HID-Idle-1s-WiFi-Discovery-Rufus-UEFI.iso'","'Frames-0.9.98-v108-r40-USB-HID-Identity-WiFi-PCI-Detail-Rufus-UEFI.iso'",'ISO target')
one("'R39B-SHA.txt'","'R40-SHA.txt'",'SHA evidence target')
one("'R25K-R39B.patch'","'R25K-R40.patch'",'patch evidence target')
one("'FRAMES_V108_R39B'","'FRAMES_V108_R40'",'ISO label target')
one('R39B-AGGREGATE.json','R40-AGGREGATE.json','aggregate target')
one("'frames-0.9.98-v108-r39b-g750jm-hid-idle-1s-wifi-discovery'","'frames-0.9.98-v108-r40-usb-hid-identity-wifi-pci-detail-read-only'",'profile target')
one("'Frames 0.9.98 v108 r39b — G750JM HID Idle 1s + Disabled Recovery + WiFi Discovery'","'Frames 0.9.98 v108 r40 — USB HID Identity + WiFi PCI Detail (Read-Only)'",'cert title target')
one('R39B PASS_VM_PENDING_PHYSICAL','R40 PASS_VM_PENDING_PHYSICAL','PASS target')
alln('R39B-FAILURE.txt','R40-FAILURE.txt',2,'failure target')
one("'physical_r39':'REJECTED_CI_LOG_STARVATION_32MS_SET_IDLE','physical_r39b':'PENDING'","'physical_r39':'REJECTED_CI_LOG_STARVATION_32MS_SET_IDLE','physical_r39b':'PHYSICAL_RUNNING_SET_IDLE_NO_TRANSFER_WIFI_ID_FOUND','physical_r39b_telemetry':'R39_S1_Q0_I1_R0_C0_E0_WIFI_14E4_43B1_B3D0F0','physical_r40':'PENDING'",'physical history target')

needle="one(\"let idle_setup=2593+(2048*65536)+(interface_num*4294967296)\",\"let idle_setup=2593+(64000*65536)+(interface_num*4294967296)\",'one-second SET_IDLE model gate')"
insert=needle+"""

# r40 is deliberately diagnostic-only relative to the green r39b runtime. It
# exposes already-read USB descriptor identity and performs only PCI config reads
# for the discovered wireless device. Protect those boundaries explicitly.
r40_needle="    req('fn v139_text_wifi_v139' in s and 'volatile_read64(xhci+3008)' in s and 'volatile_read64(xhci+3016)' in s and 'volatile_read64(xhci+3024)' in s,'r39 WiFi telemetry row missing')"
r40_extra=r40_needle+\"\"\"
    req(r37_sha=='ae9598872e6806907e8bb623050f4314dbdda140ecd6b9c620f36e1c669b4c6c','r40 exact kernel identity mismatch '+r37_sha)
    req('fn v140_wifi_pci_detail_ro' in s and 'pci_cfg_read32(bus,dev,fun,44)' in s and 'pci_cfg_read32(bus,dev,fun,8)' in s,'r40 WiFi subsystem/revision probe missing')
    w0=s.index('fn v140_wifi_pci_detail_ro'); w1=s.index('fn v140_text_r40_v140',w0); w=s[w0:w1]
    req('pci_cfg_read32' in w and 'pci_cfg_write32' not in w and 'volatile_write32' not in w,'r40 WiFi detail probe is not config-read-only')
    req('pci_cfg_read32(bus,dev,fun,16)' in w and 'pci_cfg_read32(bus,dev,fun,20)' in w and 'pci_cfg_read32(bus,dev,fun,4)' in w and 'pci_cfg_read32(bus,dev,fun,60)' in w,'r40 read-only resource snapshot incomplete')
    req('v140_wifi_pci_detail_ro(xhci)' in s and 'volatile_write64(xhci+3120,1)' in s,'r40 WiFi detail snapshot integration missing')
    req('fn v140_text_r40_v140' in s and 'volatile_read64(xhci+272)' in s and 'volatile_read64(xhci+280)' in s and 'volatile_read64(xhci+336)' in s,'r40 selected USB HID identity telemetry missing')
    req('fn v140_text_wifi_v140' in s and 'volatile_read64(xhci+3072)' in s and 'volatile_read64(xhci+3080)' in s and 'volatile_read64(xhci+3064)' in s,'r40 WiFi board-identity telemetry missing')
    req('let idle_setup=2593+(64000*65536)+(interface_num*4294967296)' in s,'r40 regressed r39b one-second HID idle cadence')
    req('ps2_poll_fallback_burst_v112(input_state,48);' in s and 'return ps2_elan4_motion_v112(input_state,a,b);' in s,'r40 regressed recovered touchpad path')
\"\"\"
if src.count(r40_needle)!=1: raise SystemExit(f'r40 inherited r39 model-gate anchor count {src.count(r40_needle)}')
src=src.replace(r40_needle,r40_extra,1)
"""
one(needle,insert,'r40 model gate injection')

ns={'__name__':'__main__','__file__':str(base)}
try:
    exec(compile(src,str(base),'exec'),ns,ns)
except BaseException:
    out=Path('evidence'); out.mkdir(parents=True,exist_ok=True)
    (out/'R40-FAILURE.txt').write_text(traceback.format_exc())
    raise
