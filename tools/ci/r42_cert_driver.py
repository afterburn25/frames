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

# r42 is the persistent interrupt-IN recovery revision derived from the exact
# protected r41b kernel.  The receiver may legitimately leave an interrupt TD
# pending while idle/NAKing; only the exact physical receiver bypasses the old
# timer-driven stop path while its endpoint remains Running.  Genuine stopped,
# halted, babble and other non-Running states retain the inherited recovery.
one("'patch_v108_r41b_maxxter_usb1_hid_babble_protocol.py'","'patch_v108_r42_hid_persistent_interrupt_in.py'",'patch target')
one('kernel-r41b.nx','kernel-r42.nx','kernel evidence target')
alln('17139d64aafd6d797bab85fc925da51cf13fc0849cfa4f2a3191fcc3e686c814','1b293c4c6a23d08786794c16910715cc68638c803fd0248a630daeac1e25c3bf',2,'exact kernel identity')
one("'Frames-0.9.98-v108-r41b-Maxxter-USB1-HID-Babble-Protocol-Recovery-Rufus-UEFI.iso'","'Frames-0.9.98-v108-r42-HID-Persistent-Interrupt-IN-Rufus-UEFI.iso'",'ISO target')
one("'R41B-SHA.txt'","'R42-SHA.txt'",'SHA evidence target')
one("'R25K-R41B.patch'","'R25K-R42.patch'",'patch evidence target')
one("'FRAMES_V108_R41B'","'FRAMES_V108_R42'",'ISO label target')
one('R41B-AGGREGATE.json','R42-AGGREGATE.json','aggregate target')
one("'frames-0.9.98-v108-r41b-maxxter-usb1-hid-babble-protocol-recovery'","'frames-0.9.98-v108-r42-hid-persistent-interrupt-in'",'profile target')
one("'Frames 0.9.98 v108 r41b — Maxxter USB1 HID Babble + Protocol Recovery'","'Frames 0.9.98 v108 r42 — HID Persistent Interrupt-IN Recovery'",'cert title target')
one('R41B PASS_VM_PENDING_PHYSICAL','R42 PASS_VM_PENDING_PHYSICAL','PASS target')
alln('R41B-FAILURE.txt','R42-FAILURE.txt',2,'failure target')
one("'physical_r41':'SUPERSEDED_BEFORE_PHYSICAL_BY_USB1_SPEED_SCOPE','physical_r41b':'PENDING'","'physical_r41':'SUPERSEDED_BEFORE_PHYSICAL_BY_USB1_SPEED_SCOPE','physical_r41b':'PHYSICAL_CONTROL_HEALTHY_REPORT142_INTERRUPTTD_STOPPED_E26_NO_BABBLE','physical_r41b_telemetry':'R41B_G1_P0_D142_L8_B0_E26','physical_r42':'PENDING'",'physical history target')

# Inject r42-specific fail-closed model checks into the inherited certification
# chain.  Unlike the superseded first r42 implementation, this revision must
# retain the genuine Stop Endpoint recovery code; the exact receiver simply
# returns early while endpoint state is Running.
anchor="    req('speed==2 && vid==9354 && pid==4267 && protocol==2' not in s,'r41b retained low-speed-only poll scope')"
extra=anchor+"""
    req(r37_sha=='1b293c4c6a23d08786794c16910715cc68638c803fd0248a630daeac1e25c3bf','r42 exact kernel identity mismatch '+r37_sha)
    req('(r42_speed==1 || r42_speed==2) && r42_vid==9354 && r42_pid==4267 && r42_proto==2' in s,'r42 exact-device persistent-idle scope missing')
    req('if r42_target && state==1' in s,'r42 Running endpoint persistent interrupt-IN hold missing')
    req('v136_xhci_command_endpoint(xhci_state,15,0)' in s,'r42 genuine Stop Endpoint recovery machinery missing')
    req('if code==3 && target' in s and 'if request<32 { next=32; }' in s,'r42 bounded babble recovery regressed')
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
