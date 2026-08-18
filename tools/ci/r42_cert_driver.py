#!/usr/bin/env python3
from pathlib import Path
import traceback
here=Path(__file__).parent
base=here/'r41b_cert_driver.py'
src=base.read_text()

def one(old,new,label):
    global src
    n=src.count(old)
    if n!=1: raise SystemExit(f'r42 cert anchor {label} count {n}')
    src=src.replace(old,new,1)

def alln(old,new,count,label):
    global src
    n=src.count(old)
    if n!=count: raise SystemExit(f'r42 cert anchor {label} count {n}, expected {count}')
    src=src.replace(old,new)

one("'patch_v108_r41b_maxxter_usb1_hid_babble_protocol.py'","'patch_v108_r42_hid_nak_tolerant_running.py'",'patch target')
one('kernel-r41b.nx','kernel-r42.nx','kernel evidence target')
alln('17139d64aafd6d797bab85fc925da51cf13fc0849cfa4f2a3191fcc3e686c814','c55c327fb1e85921c4ecf4cf79d2a764ffb8e0375a5507baeb02c8ce50f0213d',2,'exact kernel identity')
one("'Frames-0.9.98-v108-r41b-Maxxter-USB1-HID-Babble-Protocol-Recovery-Rufus-UEFI.iso'","'Frames-0.9.98-v108-r42-HID-NAK-Tolerant-Running-Endpoint-Rufus-UEFI.iso'",'ISO target')
one("'R41B-SHA.txt'","'R42-SHA.txt'",'SHA evidence target')
one("'R25K-R41B.patch'","'R25K-R42.patch'",'patch evidence target')
one("'FRAMES_V108_R41B'","'FRAMES_V108_R42'",'ISO label target')
one('R41B-AGGREGATE.json','R42-AGGREGATE.json','aggregate target')
one("'frames-0.9.98-v108-r41b-maxxter-usb1-hid-babble-protocol-recovery'","'frames-0.9.98-v108-r42-hid-nak-tolerant-running-endpoint'",'profile target')
one("'Frames 0.9.98 v108 r41b — Maxxter USB1 HID Babble + Protocol Recovery'","'Frames 0.9.98 v108 r42 — HID NAK-Tolerant Running Endpoint'",'cert title target')
one('R41B PASS_VM_PENDING_PHYSICAL','R42 PASS_VM_PENDING_PHYSICAL','PASS target')
alln('R41B-FAILURE.txt','R42-FAILURE.txt',2,'failure target')
one("'physical_r41':'SUPERSEDED_BEFORE_PHYSICAL_BY_USB1_SPEED_SCOPE','physical_r41b':'PENDING'","'physical_r41':'SUPERSEDED_BEFORE_PHYSICAL_BY_USB1_SPEED_SCOPE','physical_r41b':'PHYSICAL_CONTROL_HEALTHY_REPORT142_INTERRUPTTD_STOPPED_E26_NO_BABBLE','physical_r41b_telemetry':'R41B_G1_P0_D142_L8_B0_E26','physical_r42':'PENDING'",'physical history target')

# r37's historical physical repair intentionally added a timer-driven Stop Endpoint
# no-progress policy. r42 physical evidence proves that policy can stop a healthy
# wireless HID interrupt TD while it is simply idle/NAKing. Adapt only this CI
# checkout's historical compatibility assertions; the repository history remains.
r37p=here/'r37_cert_driver.py'
r37src=r37p.read_text()
old_stop="    req('v136_xhci_command_endpoint(xhci_state,15,0)' in s,'r37 bounded Stop Endpoint recovery missing')"
new_stop="    req('v136_xhci_command_endpoint(xhci_state,15,0)' not in s,'r42 timer-driven Stop Endpoint remains in HID runtime')"
if r37src.count(old_stop)!=1: raise SystemExit(f'r42 r37 stop compatibility anchor count {r37src.count(old_stop)}')
r37src=r37src.replace(old_stop,new_stop,1)
old_progress="    req('if kicks<3' in s and 'volatile_read64(xhci_state+2816)<2' in s,'r37 bounded no-progress recovery policy missing')"
new_progress="    req('if state==1 {' in s and 'volatile_write64(xhci_state+2728,0)' in s and 'volatile_read64(xhci_state+808)==0' in s,'r42 NAK-tolerant Running endpoint policy missing')"
if r37src.count(old_progress)!=1: raise SystemExit(f'r42 r37 no-progress compatibility anchor count {r37src.count(old_progress)}')
r37p.write_text(r37src.replace(old_progress,new_progress,1))

anchor="    req('speed==2 && vid==9354 && pid==4267 && protocol==2' not in s,'r41b retained low-speed-only poll scope')"
extra=anchor+"""
    req(r37_sha=='c55c327fb1e85921c4ecf4cf79d2a764ffb8e0375a5507baeb02c8ce50f0213d','r42 exact kernel identity mismatch '+r37_sha)
    req('v136_xhci_command_endpoint(xhci_state,15,0)' not in s,'r42 timer-driven Stop Endpoint call still present')
    req('volatile_write64(xhci_state+2728,0)' in s and 'volatile_read64(xhci_state+808)==0' in s and 'volatile_write64(xhci_state+3256' in s,'r42 running HID NAK/pending tolerance missing')
    req('code==26 || code==27 || code==28' in s and 'volatile_write64(xhci_state+3248' in s,'r42 Stopped completion quarantine missing')
    req('let stopped_state=v136_xhci_endpoint_snapshot(xhci_state)' in s,'r42 Stopped endpoint state capture missing')
    req('let es=v136_xhci_endpoint_snapshot(xhci_state)' in s and 'if es==2 || es==3' in s,'r42 Babble state-driven recovery missing')
    req('fn v141_text_r41_v141' in s and 'volatile_read64(xhci+2696)' in s and 'volatile_read64(xhci+808)' in s and 'volatile_read64(xhci+816)' in s,'r42 S/I/L/B/R/E physical telemetry missing')
    req('ps2_poll_fallback_burst_v112(input_state,48);' in s and 'return ps2_elan4_motion_v112(input_state,a,b);' in s,'r42 altered recovered touchpad path')
"""
if src.count(anchor)!=1: raise SystemExit(f'r42 model-gate injection anchor count {src.count(anchor)}')
src=src.replace(anchor,extra,1)

ns={'__name__':'__main__','__file__':str(base)}
try:
    exec(compile(src,str(base),'exec'),ns,ns)
except BaseException:
    out=Path('evidence'); out.mkdir(parents=True,exist_ok=True)
    (out/'R42-FAILURE.txt').write_text(traceback.format_exc())
    raise
