#!/usr/bin/env python3
from pathlib import Path
import traceback
here=Path(__file__).parent
base=here/'r42_cert_driver.py'
src=base.read_text()

def one(old,new,label):
    global src
    n=src.count(old)
    if n!=1: raise SystemExit(f'r44 cert anchor {label} count {n}')
    src=src.replace(old,new,1)

def alln(old,new,count,label):
    global src
    n=src.count(old)
    if n!=count: raise SystemExit(f'r44 cert anchor {label} count {n}, expected {count}')
    src=src.replace(old,new)

one("'patch_v108_r42_hid_persistent_interrupt_in.py'","'patch_v108_r44_hid_ring_forensic.py'",'patch target')
one('kernel-r42.nx','kernel-r44.nx','kernel evidence target')
alln('1b293c4c6a23d08786794c16910715cc68638c803fd0248a630daeac1e25c3bf','5fca6164e902f9720bef0d789ca46d2af480b065f32e1a6f61990476066962c1',2,'exact kernel identity')
one("'Frames-0.9.98-v108-r42-HID-Persistent-Interrupt-IN-Rufus-UEFI.iso'","'Frames-0.9.98-v108-r44-HID-Transfer-Ring-Forensic-Rufus-UEFI.iso'",'ISO target')
one("'R42-SHA.txt'","'R44-SHA.txt'",'SHA evidence target')
one("'R25K-R42.patch'","'R25K-R44.patch'",'patch evidence target')
one("'FRAMES_V108_R42'","'FRAMES_V108_R44'",'ISO label target')
one('R42-AGGREGATE.json','R44-AGGREGATE.json','aggregate target')
one("'frames-0.9.98-v108-r42-hid-persistent-interrupt-in'","'frames-0.9.98-v108-r44-hid-transfer-ring-forensic'",'profile target')
one("'Frames 0.9.98 v108 r42 — HID Persistent Interrupt-IN Recovery'","'Frames 0.9.98 v108 r44 — HID Transfer-Ring Forensic'",'cert title target')
one('R42 PASS_VM_PENDING_PHYSICAL','R44 PASS_VM_PENDING_PHYSICAL','PASS target')
alln('R42-FAILURE.txt','R44-FAILURE.txt',2,'failure target')
one("'physical_r41':'SUPERSEDED_BEFORE_PHYSICAL_BY_USB1_SPEED_SCOPE','physical_r41b':'PHYSICAL_CONTROL_HEALTHY_REPORT142_INTERRUPTTD_STOPPED_E26_NO_BABBLE','physical_r41b_telemetry':'R41B_G1_P0_D142_L8_B0_E26','physical_r42':'PENDING'","'physical_r41':'SUPERSEDED_BEFORE_PHYSICAL_BY_USB1_SPEED_SCOPE','physical_r41b':'PHYSICAL_CONTROL_HEALTHY_REPORT142_INTERRUPTTD_STOPPED_E26_NO_BABBLE','physical_r41b_telemetry':'R41B_G1_P0_D142_L8_B0_E26','physical_r42':'PHYSICAL_INTERRUPT_RUNNING_NO_USB_REPORT','physical_r42_telemetry':'R42_G1_P0_D142_L8_B0_E0_USB_R0','physical_r43':'PHYSICAL_REGRESSION_USB_FAIL_TOUCHPAD_FAIL_EP0_STATUS11','physical_r43_telemetry':'R43_C1_K1_M1_N76_A0_E11','physical_r44':'PENDING'",'physical history target')

anchor="    req('ps2_poll_fallback_burst_v112(input_state,48);' in s and 'return ps2_elan4_motion_v112(input_state,a,b);' in s,'r42 altered recovered touchpad path')"
extra=anchor+"""
    req(r37_sha=='5fca6164e902f9720bef0d789ca46d2af480b065f32e1a6f61990476066962c1','r44 exact kernel identity mismatch '+r37_sha)
    req('v135_hid_control_fallback_prepare(xhci,phys_state)' not in s,'r44 reintroduced r43 EP0 fallback prepare')
    req('v135_hid_control_fallback_poll(xhci,input_state)' not in s,'r44 reintroduced r43 EP0 fallback poll')
    req('fn v144_hid_forensic_snapshot' in s and 'volatile_write64(xhci_state+3280,packed)' in s,'r44 passive DMA snapshot missing')
    req('volatile_write64(xhci_state+3256,trb)' in s and 'volatile_write64(xhci_state+3272,tail)' in s,'r44 submitted transfer TRB telemetry missing')
    req('let event_param=volatile_read64(trb)' in s and 'volatile_write64(xhci_state+3320,volatile_read64(xhci_state+3320)+1)' in s,'r44 raw Transfer Event telemetry missing')
    req('(event_param-(event_param%16))==(submitted-(submitted%16))' in s and 'volatile_write64(xhci_state+3328,volatile_read64(xhci_state+3328)+1)' in s,'r44 Transfer Event/TRB correlation missing')
    req('volatile_write64(xhci_state+3336,volatile_read64(xhci_state+3336)+1)' in s,'r44 mailbox transfer-event counter missing')
    req('if r42_target && state==1' in s and 'v136_xhci_command_endpoint(xhci_state,15,0)' in s,'r44 regressed r42 endpoint policy')
    f0=s.index('fn v144_hid_forensic_snapshot'); f1=s.index('fn v136_xhci_endpoint_snapshot',f0); f=s[f0:f1]
    req('volatile_read8' in f and 'volatile_write64' in f and 'volatile_write32' not in f and 'xhci_control' not in f and 'v136_xhci_command_endpoint' not in f and 'pit_wait' not in f,'r44 forensic helper is not passive')
    req('v144_hid_forensic_snapshot(xhci)' in s,'r44 passive forensic live integration missing')
    req('volatile_read64(xhci+808)' in s and 'volatile_read64(xhci+3272)' in s and 'volatile_read64(xhci+2824)' in s and 'volatile_read64(xhci+3320)' in s and 'volatile_read64(xhci+3328)' in s and 'volatile_read64(xhci+3336)' in s and 'volatile_read64(xhci+3280)' in s,'r44 physical forensic row missing')
"""
if src.count(anchor)!=1: raise SystemExit(f'r44 model-gate injection anchor count {src.count(anchor)}')
src=src.replace(anchor,extra,1)

# r44 repurposes the old W40 display row for USB transfer-ring forensics but
# leaves the r40 read-only WiFi PCI snapshot and stored board identity intact.
# Adapt only the historical display assertion in this CI checkout.
r40p=here/'r40_cert_driver.py'
r40src=r40p.read_text()
old_wifi="    req('fn v140_text_wifi_v140' in s and 'volatile_read64(xhci+3072)' in s and 'volatile_read64(xhci+3080)' in s and 'volatile_read64(xhci+3064)' in s,'r40 WiFi board-identity telemetry missing')"
new_wifi="    req('fn v140_wifi_pci_detail_ro' in s and 'volatile_write64(xhci+3064,revclass%256)' in s and 'volatile_write64(xhci+3072,subsys%65536)' in s and 'volatile_write64(xhci+3080,(subsys/65536)%65536)' in s,'r44 lost r40 read-only WiFi board-identity state')"
if r40src.count(old_wifi)!=1: raise SystemExit(f'r44 r40 WiFi compatibility anchor count {r40src.count(old_wifi)}')
r40p.write_text(r40src.replace(old_wifi,new_wifi,1))

ns={'__name__':'__main__','__file__':str(base)}
try:
    exec(compile(src,str(base),'exec'),ns,ns)
except BaseException:
    out=Path('evidence'); out.mkdir(parents=True,exist_ok=True)
    (out/'R44-FAILURE.txt').write_text(traceback.format_exc())
    raise
