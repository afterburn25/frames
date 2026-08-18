#!/usr/bin/env python3
from pathlib import Path
import traceback
here=Path(__file__).parent
base=here/'r59h_cert_driver.py'
src=base.read_text()

def one(old,new,label):
    global src
    n=src.count(old)
    if n!=1: raise SystemExit(f'r59i cert anchor {label} count {n}')
    src=src.replace(old,new,1)
def alln(old,new,count,label):
    global src
    n=src.count(old)
    if n!=count: raise SystemExit(f'r59i cert anchor {label} count {n}, expected {count}')
    src=src.replace(old,new)

one("'patch_v108_r59h_linux_split_schedule_repair.py'","'patch_v108_r59i_qh_overlay_forensics.py'",'patch target')
one('kernel-r59h.nx','kernel-r59i.nx','kernel evidence target')
one('ee129f22dca19ba7d1d7a1cc41a7b90bfcba0dc472ad7493c38ca2a1537c094e','cf8f80043153dbd377d2e6b0057e77beaa35b47a6201a863963bf56cefbc8e00','exact r59i identity target')
one("'Frames-0.9.98-v108-r59h-Linux-Split-Schedule-Repair-Rufus-UEFI.iso'","'Frames-0.9.98-v108-r59i-QH-Overlay-Forensics-Rufus-UEFI.iso'",'ISO target')
one("'R59H-SHA.txt'","'R59I-SHA.txt'",'SHA evidence target')
one("'R25K-R59H.patch'","'R25K-R59I.patch'",'patch evidence target')
one("'FRAMES_V108_R59H'","'FRAMES_V108_R59I'",'ISO label target')
one('R59H-AGGREGATE.json','R59I-AGGREGATE.json','aggregate target')
one("'frames-0.9.98-v108-r59h-linux-split-schedule-repair'","'frames-0.9.98-v108-r59i-qh-overlay-forensics'",'profile target')
one("'Frames 0.9.98 v108 r59h — Linux-Derived EHCI Split Schedule Repair'","'Frames 0.9.98 v108 r59i — Live QH Overlay Forensics'",'cert title target')
one('R59H PASS_VM_PENDING_PHYSICAL','R59I PASS_VM_PENDING_PHYSICAL','PASS target')
alln('R59H-FAILURE.txt','R59I-FAILURE.txt',2,'failure target')
one('r59h exact kernel identity mismatch','r59i exact kernel identity mismatch','identity label')
one("'physical_r59h':'PENDING'",
    "'physical_r59h':'PHYSICAL_CMASK06_PERIODIC_ACTIVE_NO_COMPLETION','physical_r59h_telemetry':'R5H_S1_N0_I4_X0_E0_M1_C6','physical_r59i':'PENDING'",
    'physical r59h result + r59i pending')

oldgate="one(anchor,anchor+\"\\n    req('(rr/4)%32' in s,'r59h qTD error telemetry missing')\",'r59h qTD error telemetry gate')"
newgate="one(anchor,anchor+\"\\n    req('(rr/4)%32' in s,'r59h qTD error telemetry missing')\\n    req('volatile_read32(dm+24)' in s and '(ot/128)%2' in s and '(ot/2)%2' in s and '(ot/4)%32' in s and '(ot/65536)%32768' in s and '(ot/2147483648)%2' in s,'r59i live QH overlay telemetry missing')\",'r59i overlay telemetry gate')"
one(oldgate,newgate,'overlay model gate injection')

ns={'__name__':'__main__','__file__':str(base)}
try:
    exec(compile(src,str(base),'exec'),ns,ns)
except BaseException:
    out=Path('evidence'); out.mkdir(parents=True,exist_ok=True)
    (out/'R59I-FAILURE.txt').write_text(traceback.format_exc())
    raise
