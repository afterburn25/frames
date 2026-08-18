#!/usr/bin/env python3
from pathlib import Path
import traceback
here=Path(__file__).parent
base=here/'r40_cert_driver.py'
src=base.read_text()

def one(old,new,label):
    global src
    n=src.count(old)
    if n!=1: raise SystemExit(f'r41 cert anchor {label} count {n}')
    src=src.replace(old,new,1)

def alln(old,new,count,label):
    global src
    n=src.count(old)
    if n!=count: raise SystemExit(f'r41 cert anchor {label} count {n}, expected {count}')
    src=src.replace(old,new)

one("'patch_v108_r40_usb_hid_identity_wifi_pci_detail_ro.py'","'patch_v108_r41_maxxter_ls_hid_babble_protocol.py'",'patch target')
one('kernel-r40.nx','kernel-r41.nx','kernel evidence target')
alln('ae9598872e6806907e8bb623050f4314dbdda140ecd6b9c620f36e1c669b4c6c','2e201d05458889915040ad726cbd756c41a5429199bee0738f32dd9fe8a9aed4',2,'exact kernel identity')
one("'Frames-0.9.98-v108-r40-USB-HID-Identity-WiFi-PCI-Detail-Rufus-UEFI.iso'","'Frames-0.9.98-v108-r41-Maxxter-LS-HID-Babble-Protocol-Recovery-Rufus-UEFI.iso'",'ISO target')
one("'R40-SHA.txt'","'R41-SHA.txt'",'SHA evidence target')
one("'R25K-R40.patch'","'R25K-R41.patch'",'patch evidence target')
one("'FRAMES_V108_R40'","'FRAMES_V108_R41'",'ISO label target')
one('R40-AGGREGATE.json','R41-AGGREGATE.json','aggregate target')
one("'frames-0.9.98-v108-r40-usb-hid-identity-wifi-pci-detail-read-only'","'frames-0.9.98-v108-r41-maxxter-low-speed-hid-babble-protocol-recovery'",'profile target')
one("'Frames 0.9.98 v108 r40 — USB HID Identity + WiFi PCI Detail (Read-Only)'","'Frames 0.9.98 v108 r41 — Maxxter Low-Speed HID Babble + Protocol Recovery'",'cert title target')
one('R40 PASS_VM_PENDING_PHYSICAL','R41 PASS_VM_PENDING_PHYSICAL','PASS target')
alln('R40-FAILURE.txt','R41-FAILURE.txt',2,'failure target')
one("'physical_r40':'PENDING'","'physical_r40':'PHYSICAL_MAXXTER_248A_10AB_LOW_SPEED_BABBLE_E3_WIFI_BCM4352_IDENTIFIED','physical_r40_telemetry':'R40_S1_I1_H2_V9354_P4267_E3_W40_V5348_D17329_SV6715_SD8483_R3','physical_r41':'PENDING'",'physical r40 evidence target')

# r41 replaces only the r40 USB identity row; keep the inherited r40 read-only
# WiFi model gate but point its display-name checks at the new r41 row.
alln('fn v140_text_r40_v140','fn v141_text_r41_v141',2,'r40 display compatibility')
anchor="    req('ps2_poll_fallback_burst_v112(input_state,48);' in s and 'return ps2_elan4_motion_v112(input_state,a,b);' in s,'r40 regressed recovered touchpad path')"
extra=anchor+"""
    req(r37_sha=='2e201d05458889915040ad726cbd756c41a5429199bee0738f32dd9fe8a9aed4','r41 exact kernel identity mismatch '+r37_sha)
    req('usb_setup_value_v113(161,3,0,interface_num)' in s and 'volatile_write64(xhci_state+3160,gp_val)' in s,'r41 GET_PROTOCOL verification missing')
    req('usb_setup_value_v113(129,6,8704,interface_num)' in s and 'volatile_write64(xhci_state+3232,report_len)' in s,'r41 HID report descriptor probe missing')
    req('speed==2 && vid==9354 && pid==4267 && protocol==2' in s and 'if code==3 && target' in s,'r41 Maxxter low-speed babble scope missing')
    req('if request<16 { next=16; }' in s and 'if request<32 { next=32; }' in s and 'adaptive<=32' in s,'r41 babble recovery is not bounded to 32 bytes')
    req('fn v141_text_r41_v141' in s and 'R41 G P D L B E' not in s,'r41 generated label must use glyph helper rather than raw string')
    req('ps2_poll_fallback_burst_v112(input_state,48);' in s and 'return ps2_elan4_motion_v112(input_state,a,b);' in s,'r41 altered recovered touchpad path')
"""
if src.count(anchor)!=1: raise SystemExit(f'r41 model-gate injection anchor count {src.count(anchor)}')
src=src.replace(anchor,extra,1)

ns={'__name__':'__main__','__file__':str(base)}
try:
    exec(compile(src,str(base),'exec'),ns,ns)
except BaseException:
    out=Path('evidence'); out.mkdir(parents=True,exist_ok=True)
    (out/'R41-FAILURE.txt').write_text(traceback.format_exc())
    raise
