#!/usr/bin/env python3
from pathlib import Path
import traceback
here=Path(__file__).parent
base=here/'r59h_cert_driver.py'
src=base.read_text()

def one(old,new,label):
    global src
    n=src.count(old)
    if n!=1: raise SystemExit(f'r59j cert anchor {label} count {n}')
    src=src.replace(old,new,1)
def alln(old,new,count,label):
    global src
    n=src.count(old)
    if n!=count: raise SystemExit(f'r59j cert anchor {label} count {n}, expected {count}')
    src=src.replace(old,new)

one("'patch_v108_r59h_linux_split_schedule_repair.py'","'patch_v108_r59j_correct_split_schedule_overlay.py'",'patch target')
one('kernel-r59h.nx','kernel-r59j.nx','kernel evidence target')
one('ee129f22dca19ba7d1d7a1cc41a7b90bfcba0dc472ad7493c38ca2a1537c094e','69168127d829d3b182ab874fef9bbdd1c734ecffca9e5457f94f8d53b012fc54','exact r59j identity target')
one("'Frames-0.9.98-v108-r59h-Linux-Split-Schedule-Repair-Rufus-UEFI.iso'","'Frames-0.9.98-v108-r59j-Correct-Split-Schedule-Overlay-Rufus-UEFI.iso'",'ISO target')
one("'R59H-SHA.txt'","'R59J-SHA.txt'",'SHA evidence target')
one("'R25K-R59H.patch'","'R25K-R59J.patch'",'patch evidence target')
one("'FRAMES_V108_R59H'","'FRAMES_V108_R59J'",'ISO label target')
one('R59H-AGGREGATE.json','R59J-AGGREGATE.json','aggregate target')
one("'frames-0.9.98-v108-r59h-linux-split-schedule-repair'","'frames-0.9.98-v108-r59j-correct-split-schedule-overlay'",'profile target')
one("'Frames 0.9.98 v108 r59h — Linux-Derived EHCI Split Schedule Repair'","'Frames 0.9.98 v108 r59j — Correct EHCI Split Schedule + Live Overlay'",'cert title target')
one('R59H PASS_VM_PENDING_PHYSICAL','R59J PASS_VM_PENDING_PHYSICAL','PASS target')
alln('R59H-FAILURE.txt','R59J-FAILURE.txt',2,'failure target')
one('r59h exact kernel identity mismatch','r59j exact kernel identity mismatch','identity label')
one("'physical_r59h':'PENDING'",
    "'physical_r59h':'PHYSICAL_CMASK06_PERIODIC_ACTIVE_NO_COMPLETION','physical_r59h_telemetry':'R5H_S1_N0_I4_X0_E0_M1_C6','physical_r59i':'PHYSICAL_QH_ACTIVE_NO_SPLIT_NO_PROGRESS','physical_r59i_telemetry':'R5I_S1_N0_A1_X0_E0_R8_D0','physical_r59j':'PENDING'",
    'physical r59h+r59i results + r59j pending')

# r59j corrects the r59h schedule experiment: current Linux EHCI interrupt
# scheduling places CSPLITs 2-4 microframes after the SSPLIT.  Require the
# restored 0x1c C-mask and reject the r59h 0x06 experiment.
one("    req('let info2=1090586113' in r59gfn and 'let info2=1090591745' not in r59gfn,'r59h Linux-derived C-mask 0x06 repair missing')",
    "    req('let info2=1090591745' in r59gfn and 'let info2=1090586113' not in r59gfn,'r59j corrected C-mask 0x1c missing')",
    'correct inherited split schedule gate')

# Keep the r59i live-QH-overlay proof in the r59j certification model.
oldgate="one(anchor,anchor+\"\\n    req('(rr/4)%32' in s,'r59h qTD error telemetry missing')\",'r59h qTD error telemetry gate')"
newgate="one(anchor,anchor+\"\\n    req('(rr/4)%32' in s,'r59h qTD error telemetry missing')\\n    req('volatile_read32(dm+24)' in s and '(ot/128)%2' in s and '(ot/2)%2' in s and '(ot/4)%32' in s and '(ot/65536)%32768' in s and '(ot/2147483648)%2' in s,'r59j live QH overlay telemetry missing')\",'r59j overlay telemetry gate')"
one(oldgate,newgate,'overlay model gate injection')

ns={'__name__':'__main__','__file__':str(base)}
try:
    exec(compile(src,str(base),'exec'),ns,ns)
except BaseException:
    out=Path('evidence'); out.mkdir(parents=True,exist_ok=True)
    (out/'R59J-FAILURE.txt').write_text(traceback.format_exc())
    raise
