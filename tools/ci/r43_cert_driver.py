#!/usr/bin/env python3
from pathlib import Path
import traceback
here=Path(__file__).parent
base=here/'r42_cert_driver.py'
src=base.read_text()

def one(old,new,label):
    global src
    n=src.count(old)
    if n!=1: raise SystemExit(f'r43 cert anchor {label} count {n}')
    src=src.replace(old,new,1)

def alln(old,new,count,label):
    global src
    n=src.count(old)
    if n!=count: raise SystemExit(f'r43 cert anchor {label} count {n}, expected {count}')
    src=src.replace(old,new)

one("'patch_v108_r42_hid_persistent_interrupt_in.py'","'patch_v108_r43_hid_control_fallback_live.py'",'patch target')
one('kernel-r42.nx','kernel-r43.nx','kernel evidence target')
alln('1b293c4c6a23d08786794c16910715cc68638c803fd0248a630daeac1e25c3bf','926590a17115ca1e2c9bfa99224f8e8a0d190041bdd700fde411aafe594c2725',2,'exact kernel identity')
one("'Frames-0.9.98-v108-r42-HID-Persistent-Interrupt-IN-Rufus-UEFI.iso'","'Frames-0.9.98-v108-r43-HID-Control-Fallback-Live-Rufus-UEFI.iso'",'ISO target')
one("'R42-SHA.txt'","'R43-SHA.txt'",'SHA evidence target')
one("'R25K-R42.patch'","'R25K-R43.patch'",'patch evidence target')
one("'FRAMES_V108_R42'","'FRAMES_V108_R43'",'ISO label target')
one('R42-AGGREGATE.json','R43-AGGREGATE.json','aggregate target')
one("'frames-0.9.98-v108-r42-hid-persistent-interrupt-in'","'frames-0.9.98-v108-r43-hid-control-fallback-live'",'profile target')
one("'Frames 0.9.98 v108 r42 — HID Persistent Interrupt-IN Recovery'","'Frames 0.9.98 v108 r43 — HID Control Fallback Live'",'cert title target')
one('R42 PASS_VM_PENDING_PHYSICAL','R43 PASS_VM_PENDING_PHYSICAL','PASS target')
alln('R42-FAILURE.txt','R43-FAILURE.txt',2,'failure target')
one('r42 exact kernel identity mismatch','r43 exact kernel identity mismatch','identity label')
one("'physical_r41':'SUPERSEDED_BEFORE_PHYSICAL_BY_USB1_SPEED_SCOPE','physical_r41b':'PHYSICAL_CONTROL_HEALTHY_REPORT142_INTERRUPTTD_STOPPED_E26_NO_BABBLE','physical_r41b_telemetry':'R41B_G1_P0_D142_L8_B0_E26','physical_r42':'PENDING'","'physical_r41':'SUPERSEDED_BEFORE_PHYSICAL_BY_USB1_SPEED_SCOPE','physical_r41b':'PHYSICAL_CONTROL_HEALTHY_REPORT142_INTERRUPTTD_STOPPED_E26_NO_BABBLE','physical_r41b_telemetry':'R41B_G1_P0_D142_L8_B0_E26','physical_r42':'PHYSICAL_INTERRUPT_RUNNING_NO_USB_REPORT','physical_r42_telemetry':'R42_G1_P0_D142_L8_B0_E0_USB_R0','physical_r43':'PENDING'",'physical history target')

anchor="    req('ps2_poll_fallback_burst_v112(input_state,48);' in s and 'return ps2_elan4_motion_v112(input_state,a,b);' in s,'r42 altered recovered touchpad path')"
extra=anchor+"""
    req(r37_sha=='926590a17115ca1e2c9bfa99224f8e8a0d190041bdd700fde411aafe594c2725','r43 exact kernel identity mismatch '+r37_sha)
    req('(r43_speed==1 || r43_speed==2) && r43_vid==9354 && r43_pid==4267 && r43_proto==2' in s,'r43 exact receiver control fallback scope missing')
    req('v135_hid_control_fallback_prepare(xhci,phys_state)' in s,'r43 control fallback prepare missing')
    req('if volatile_read64(xhci+2560)==1 { v135_hid_control_fallback_poll(xhci,input_state); }' in s,'r43 live class-control fallback poll missing')
    req('if volatile_read64(xhci_state+816)!=0 { return 1; }' in s,'r43 fallback does not yield to interrupt-IN success')
    req('R43 C K M N A E' not in s,'r43 label unexpectedly stored as plaintext rather than encoded draw calls')
    req('volatile_read64(xhci+2560)' in s and 'volatile_read64(xhci+2592)' in s and 'volatile_read64(xhci+2608)' in s and 'volatile_read64(xhci+2616)' in s,'r43 physical fallback telemetry row missing')
"""
if src.count(anchor)!=1: raise SystemExit(f'r43 model-gate injection anchor count {src.count(anchor)}')
src=src.replace(anchor,extra,1)

# r36 intentionally removed the older always-on/blocking EP0 HID fallback.
# r43 deliberately reintroduces the already-bounded class-control machinery,
# but only for the exact physical receiver and only as a fail-open alternate
# path after r42 proved interrupt-IN can remain Running without a live report.
# Adapt historical compatibility assertions in this CI checkout without
# changing the repository's r36 source or weakening the r43 scope checks.
r36p=here/'r36_cert_driver.py'
r36src=r36p.read_text()
old_prepare="    req('v135_hid_control_fallback_prepare(xhci,phys_state)' not in s,'r36 startup still invokes blocking EP0 fallback')"
new_prepare="    req('v135_hid_control_fallback_prepare(xhci,phys_state)' not in s or ('(r43_speed==1 || r43_speed==2) && r43_vid==9354 && r43_pid==4267 && r43_proto==2' in s),'r43 reintroduced unscoped EP0 fallback')"
if r36src.count(old_prepare)!=1: raise SystemExit(f'r43 r36 prepare compatibility anchor count {r36src.count(old_prepare)}')
r36src=r36src.replace(old_prepare,new_prepare,1)
old_poll="    req('v135_hid_control_fallback_poll(xhci,input_state)' not in s,'r36 live loop still invokes blocking EP0 fallback')"
new_poll="    req('v135_hid_control_fallback_poll(xhci,input_state)' not in s or 'if volatile_read64(xhci+2560)==1 { v135_hid_control_fallback_poll(xhci,input_state); }' in s,'r43 reintroduced unguarded EP0 fallback poll')"
if r36src.count(old_poll)!=1: raise SystemExit(f'r43 r36 poll compatibility anchor count {r36src.count(old_poll)}')
r36src=r36src.replace(old_poll,new_poll,1)
old_gate="new_gate=\" req('v135_hid_control_fallback_prepare(xhci,phys_state)' not in s and 'v135_hid_control_fallback_poll(xhci,input_state)' not in s,'r36 blocking EP0 fallback remains integrated')\""
new_gate="new_gate=\" req('(r43_speed==1 || r43_speed==2) && r43_vid==9354 && r43_pid==4267 && r43_proto==2' in s and 'v135_hid_control_fallback_prepare(xhci,phys_state)' in s and 'if volatile_read64(xhci+2560)==1 { v135_hid_control_fallback_poll(xhci,input_state); }' in s,'r43 exact-device control fallback integration missing')\""
if r36src.count(old_gate)!=1: raise SystemExit(f'r43 r36/r35 integration compatibility anchor count {r36src.count(old_gate)}')
r36p.write_text(r36src.replace(old_gate,new_gate,1))

# r43 repurposes the old W40 board-identity display row for the new fallback
# telemetry, but it does not remove the read-only WiFi PCI snapshot or its
# stored board identity. Preserve r40's substantive read-only invariant while
# allowing the diagnostic display row itself to evolve.
r40p=here/'r40_cert_driver.py'
r40src=r40p.read_text()
old_wifi="    req('fn v140_text_wifi_v140' in s and 'volatile_read64(xhci+3072)' in s and 'volatile_read64(xhci+3080)' in s and 'volatile_read64(xhci+3064)' in s,'r40 WiFi board-identity telemetry missing')"
new_wifi="    req('fn v140_wifi_pci_detail_ro' in s and 'volatile_write64(xhci+3064,revclass%256)' in s and 'volatile_write64(xhci+3072,subsys%65536)' in s and 'volatile_write64(xhci+3080,(subsys/65536)%65536)' in s,'r43 lost r40 read-only WiFi board-identity state')"
if r40src.count(old_wifi)!=1: raise SystemExit(f'r43 r40 WiFi compatibility anchor count {r40src.count(old_wifi)}')
r40p.write_text(r40src.replace(old_wifi,new_wifi,1))

ns={'__name__':'__main__','__file__':str(base)}
try:
    exec(compile(src,str(base),'exec'),ns,ns)
except BaseException:
    out=Path('evidence'); out.mkdir(parents=True,exist_ok=True)
    (out/'R43-FAILURE.txt').write_text(traceback.format_exc())
    raise
