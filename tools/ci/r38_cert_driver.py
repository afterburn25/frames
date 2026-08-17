#!/usr/bin/env python3
from pathlib import Path
import traceback
here=Path(__file__).parent
base=here/'r37b_cert_driver.py'
src=base.read_text()

def one(old,new,label):
 global src
 n=src.count(old)
 if n!=1: raise SystemExit(f'r38 cert anchor {label} count {n}')
 src=src.replace(old,new,1)

def alln(old,new,count,label):
 global src
 n=src.count(old)
 if n!=count: raise SystemExit(f'r38 cert anchor {label} count {n}, expected {count}')
 src=src.replace(old,new)

one("'patch_v108_r37b_stable_diag.py'","'patch_v108_r38_hid_event_identity_altsetting.py'",'patch target')
one('kernel-r37b.nx','kernel-r38.nx','kernel evidence target')
one('2cb422d2c7d00cdbb1da3eee4ee696c9ae0723b3f28669bf80efe256d14de650','c6962f3cb939e6b83308f85f07cb8b319ee322747cd419b99b1c2e82e5c8375d','exact kernel identity')
one("'Frames-0.9.98-v108-r37b-G750JM-xHCI-Ring-Elantech-Stable-Diagnostics-Rufus-UEFI.iso'","'Frames-0.9.98-v108-r38-G750JM-HID-Event-Identity-AltSetting-Recovery-Rufus-UEFI.iso'",'ISO target')
one("'R37B-SHA.txt'","'R38-SHA.txt'",'SHA evidence target')
one("'R25K-R37B.patch'","'R25K-R38.patch'",'patch evidence target')
one("'FRAMES_V108_R37B'","'FRAMES_V108_R38'",'ISO label target')
one("R37B-AGGREGATE.json","R38-AGGREGATE.json",'aggregate target')
one("'frames-0.9.98-v108-r37b-g750jm-xhci-ring-elantech-stable-diagnostics'","'frames-0.9.98-v108-r38-g750jm-hid-event-identity-altsetting-recovery'",'profile target')
one("'Frames 0.9.98 v108 r37b — G750JM xHCI Ring + Elantech Stable Diagnostics'","'Frames 0.9.98 v108 r38 — G750JM HID Event Identity + Alt Setting Recovery'",'cert title target')
one("R37B PASS_VM_PENDING_PHYSICAL","R38 PASS_VM_PENDING_PHYSICAL",'PASS target')
alln('R37B-FAILURE.txt','R38-FAILURE.txt',2,'failure target')
one("'physical_r37':'NOT_TESTED','physical_r37b':'PENDING'","'physical_r37':'NOT_TESTED','physical_r37b':'FAIL_USB_PHYSICAL_TOUCHPAD_RECOVERED_HID_STOP_EVENT_Q0','physical_r37b_telemetry':'R37_S1_Q0_C1_K3_F2_E26','physical_r38':'PENDING'",'physical history target')

needle="    req('(410*65536)+28' in s and '(py+726)' in s,'r37b compact row geometry missing')"
insert=needle+"""
    req(r37_sha=='c6962f3cb939e6b83308f85f07cb8b319ee322747cd419b99b1c2e82e5c8375d','r38 exact kernel identity mismatch '+r37_sha)
    req('interface_alt=volatile_read8(full+off+3)' in s and 'volatile_write64(xhci_state+2848,alt)' in s,'r38 HID alternate-setting capture/selection missing')
    req('interface_setup=2817+(interface_alt*65536)+(interface_num*4294967296)' in s,'r38 SET_INTERFACE activation missing')
    req('fn v138_xhci_hid_drain_old_events' in s and 'v138_xhci_hid_drain_old_events(xhci_state)' in s,'r38 stopped-generation drain missing')
    req('volatile_write64(xhci_state+2928,trb)' in s and 'let active_trb=volatile_read64(xhci_state+2928)' in s,'r38 active HID TRB identity missing')
    req('source=volatile_read64(trb)' in s and 'source!=active_trb' in s,'r38 transfer-event TRB identity gate missing')
    req('code>=26 && code<=28' in s and 'volatile_write64(xhci_state+2872' in s,'r38 stale stopped-event quarantine missing')
    req('volatile_read64(xhci+2848)' in s and 'volatile_read64(xhci+2888)' in s and 'volatile_read64(xhci+2896)' in s,'r38 physical generation telemetry missing')
    req('ps2_poll_fallback_burst_v112(input_state,48);' in s and 'return ps2_elan4_motion_v112(input_state,a,b);' in s,'r38 regressed recovered touchpad path')
"""
one(needle,insert,'r38 model gates')

ns={'__name__':'__main__','__file__':str(base)}
try:
 exec(compile(src,str(base),'exec'),ns,ns)
except BaseException:
 out=Path('evidence'); out.mkdir(parents=True,exist_ok=True)
 (out/'R38-FAILURE.txt').write_text(traceback.format_exc())
 raise
