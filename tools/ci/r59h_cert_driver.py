#!/usr/bin/env python3
# r59h certification trigger after workflow registration
from pathlib import Path
import traceback
here=Path(__file__).parent
base=here/'r59g_cert_driver.py'
src=base.read_text()

def one(old,new,label):
    global src
    n=src.count(old)
    if n!=1: raise SystemExit(f'r59h cert anchor {label} count {n}')
    src=src.replace(old,new,1)
def alln(old,new,count,label):
    global src
    n=src.count(old)
    if n!=count: raise SystemExit(f'r59h cert anchor {label} count {n}, expected {count}')
    src=src.replace(old,new)

one("'patch_v108_r59g_ehci_split_state_control_report.py'","'patch_v108_r59h_linux_split_schedule_repair.py'",'patch target')
one('kernel-r59g.nx','kernel-r59h.nx','kernel evidence target')
one('4381aec1a83db1eeb7baa55e803aacecff30e7b6154238bff892a51fbf0e1dd7','ee129f22dca19ba7d1d7a1cc41a7b90bfcba0dc472ad7493c38ca2a1537c094e','exact r59h identity target')
one("'Frames-0.9.98-v108-r59g-EHCI-Split-State-Control-Report-Rufus-UEFI.iso'","'Frames-0.9.98-v108-r59h-Linux-Split-Schedule-Repair-Rufus-UEFI.iso'",'ISO target')
one("'R59G-SHA.txt'","'R59H-SHA.txt'",'SHA evidence target')
one("'R25K-R59G.patch'","'R25K-R59H.patch'",'patch evidence target')
one("'FRAMES_V108_R59G'","'FRAMES_V108_R59H'",'ISO label target')
one('R59G-AGGREGATE.json','R59H-AGGREGATE.json','aggregate target')
one("'frames-0.9.98-v108-r59g-ehci-split-state-control-report'","'frames-0.9.98-v108-r59h-linux-split-schedule-repair'",'profile target')
one("'Frames 0.9.98 v108 r59g — EHCI Split-State Control-Report Forensics'","'Frames 0.9.98 v108 r59h — Linux-Derived EHCI Split Schedule Repair'",'cert title target')
one('R59G PASS_VM_PENDING_PHYSICAL','R59H PASS_VM_PENDING_PHYSICAL','PASS target')
alln('R59G-FAILURE.txt','R59H-FAILURE.txt',2,'failure target')
one('r59g exact kernel identity mismatch','r59h exact kernel identity mismatch','identity label')
one("'physical_r59g':'PENDING'",
    "'physical_r59g':'PHYSICAL_INTERVAL4_SPLITSTATE0_GETREPORT_XACTERR_CMASK1C','physical_r59g_telemetry':'R5G_S1_N0_I4_X0_G6_M1_C28','physical_r59h':'PENDING'",
    'physical r59g result + r59h pending')

one("    req('161+(1*256)+(256*65536)+(mif*4294967296)+(8*281474976710656)' in r59gfn,'r59g HID GET_REPORT control probe missing')",
    "    req('161+(1*256)+(256*65536)+(mif*4294967296)+(8*281474976710656)' not in r59gfn,'r59h failed GET_REPORT control probe remains')",
    'GET_REPORT model gate')
one("    req('volatile_write64(xhci_state+3984,grc)' in r59gfn and 'volatile_write64(xhci_state+3992,grow)' in r59gfn,'r59g GET_REPORT telemetry missing')",
    "    req('volatile_write64(xhci_state+3984,0)' in r59gfn and 'volatile_write64(xhci_state+3992,0)' in r59gfn,'r59h GET_REPORT telemetry clear missing')",
    'GET_REPORT telemetry gate')
one("    req('let info2=1090591745' in r59gfn,'r59g inherited EHCI TT geometry unexpectedly changed')",
    "    req('let info2=1090586113' in r59gfn and 'let info2=1090591745' not in r59gfn,'r59h Linux-derived C-mask 0x06 repair missing')",
    'split schedule geometry gate')
anchor="    req('(rr/2)%2' in s,'r59g SplitXState visible telemetry missing')"
one(anchor,anchor+"\n    req('(rr/4)%32' in s,'r59h qTD error telemetry missing')",'r59h qTD error telemetry gate')

# r59 itself historically certified the original 0x1c Complete-Split mask.
# r59h intentionally replaces that one field with Linux-derived 0x06; widen
# only this private inherited assertion while keeping hub/port/S-mask proof.
r59p=here/'r59_cert_driver.py'
r59src=r59p.read_text()
r59old="    req('info2=1090591745' in r59fn,'r59 EHCI split S-mask/C-mask hub1 port2 capabilities missing')"
r59new="    req(('info2=1090591745' in r59fn) or ('info2=1090586113' in r59fn),'r59/r59h EHCI split hub1 port2 capabilities missing')"
if r59src.count(r59old)==1:
    r59p.write_text(r59src.replace(r59old,r59new,1))
elif r59src.count(r59new)!=1:
    raise SystemExit('r59h inherited r59 split-geometry gate anchor missing')

ns={'__name__':'__main__','__file__':str(base)}
try:
    exec(compile(src,str(base),'exec'),ns,ns)
except BaseException:
    out=Path('evidence'); out.mkdir(parents=True,exist_ok=True)
    (out/'R59H-FAILURE.txt').write_text(traceback.format_exc())
    raise
