#!/usr/bin/env python3
from pathlib import Path
import traceback
here=Path(__file__).parent
base=here/'r59f_cert_driver.py'
src=base.read_text()

def one(old,new,label):
    global src
    n=src.count(old)
    if n!=1: raise SystemExit(f'r59g cert anchor {label} count {n}')
    src=src.replace(old,new,1)
def alln(old,new,count,label):
    global src
    n=src.count(old)
    if n!=count: raise SystemExit(f'r59g cert anchor {label} count {n}, expected {count}')
    src=src.replace(old,new)

one("'patch_v108_r59f_hid_report_protocol_periodic.py'","'patch_v108_r59g_ehci_split_state_control_report.py'",'patch target')
one('kernel-r59f.nx','kernel-r59g.nx','kernel evidence target')
one('51103efecc88695f2f75cb786d273d7379c5628424e9f1f391853bdb5e81198e','4381aec1a83db1eeb7baa55e803aacecff30e7b6154238bff892a51fbf0e1dd7','exact r59g identity target')
one("'Frames-0.9.98-v108-r59f-HID-Report-Protocol-Periodic-Rufus-UEFI.iso'","'Frames-0.9.98-v108-r59g-EHCI-Split-State-Control-Report-Rufus-UEFI.iso'",'ISO target')
one("'R59F-SHA.txt'","'R59G-SHA.txt'",'SHA evidence target')
one("'R25K-R59F.patch'","'R25K-R59G.patch'",'patch evidence target')
one("'FRAMES_V108_R59F'","'FRAMES_V108_R59G'",'ISO label target')
one('R59F-AGGREGATE.json','R59G-AGGREGATE.json','aggregate target')
one("'frames-0.9.98-v108-r59f-hid-report-protocol-periodic'","'frames-0.9.98-v108-r59g-ehci-split-state-control-report'",'profile target')
one("'Frames 0.9.98 v108 r59f — HID Report Protocol Periodic Repair'","'Frames 0.9.98 v108 r59g — EHCI Split-State Control-Report Forensics'",'cert title target')
one('R59F PASS_VM_PENDING_PHYSICAL','R59G PASS_VM_PENDING_PHYSICAL','PASS target')
alln('R59F-FAILURE.txt','R59G-FAILURE.txt',2,'failure target')
one('r59f exact kernel identity mismatch','r59g exact kernel identity mismatch','identity label')
one("'physical_r59f':'PENDING'",
    "'physical_r59f':'PHYSICAL_REPORT_PROTOCOL_QH_FETCHED_ACTIVE_NO_ERROR','physical_r59f_telemetry':'R5F_S1_N0_F1657_Q1_A1_E0_P1','physical_r59g':'PENDING'",
    'physical r59f result + r59g pending')
anchor="    req('R5F' not in s,'r59f textual label unexpectedly embedded as raw string')"
extra=anchor+"""
    r59gfn=s[s.index('fn v159_ehci_mouse_periodic_arm'):s.index('fn v135_hid_control_fallback_prepare')]
    req('161+(1*256)+(256*65536)+(mif*4294967296)+(8*281474976710656)' in r59gfn,'r59g HID GET_REPORT control probe missing')
    req('volatile_write64(xhci_state+3984,grc)' in r59gfn and 'volatile_write64(xhci_state+3992,grow)' in r59gfn,'r59g GET_REPORT telemetry missing')
    req('(rr/2)%2' in s,'r59g SplitXState visible telemetry missing')
    req('volatile_read64(xhci+3976)' in s,'r59g physical bInterval visible telemetry missing')
    req('sm=qi%256' in s and 'cm=(qi/256)%256' in s,'r59g QH S-mask/C-mask visible telemetry missing')
    req('let info2=1090591745' in r59gfn,'r59g inherited EHCI TT geometry unexpectedly changed')
    req('let token=527744' in r59gfn,'r59g inherited EHCI IN qTD token unexpectedly changed')
    low59g=r59gfn.lower(); req(all(x not in low59g for x in ['write(10)','nvme_submit_write','ahci_write','fat_write','block_write','input_push(']),'r59g exceeds diagnostic/read-only scope')
    req('R5G' not in s,'r59g textual label unexpectedly embedded as raw string')
"""
one(anchor,extra,'r59g split-state/control-report model gates')

ns={'__name__':'__main__','__file__':str(base)}
try:
    exec(compile(src,str(base),'exec'),ns,ns)
except BaseException:
    out=Path('evidence'); out.mkdir(parents=True,exist_ok=True)
    (out/'R59G-FAILURE.txt').write_text(traceback.format_exc())
    raise
