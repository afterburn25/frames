#!/usr/bin/env python3
from pathlib import Path
import traceback
here=Path(__file__).parent
base=here/'r59j_cert_driver.py'
src=base.read_text()

def one(old,new,label):
    global src
    n=src.count(old)
    if n!=1: raise SystemExit(f'r59l cert anchor {label} count {n}')
    src=src.replace(old,new,1)
def alln(old,new,count,label):
    global src
    n=src.count(old)
    if n!=count: raise SystemExit(f'r59l cert anchor {label} count {n}, expected {count}')
    src=src.replace(old,new)

one("'patch_v108_r59j_correct_split_schedule_overlay.py'","'patch_v108_r59l_periodic_fls_frindex_forensics.py'",'patch target')
one('kernel-r59j.nx','kernel-r59l.nx','kernel evidence target')
one('69168127d829d3b182ab874fef9bbdd1c734ecffca9e5457f94f8d53b012fc54','c14b8e7bf4d51ceb20188ea7a8a911242df9337b0377944e147e5faac03a891d','exact r59l identity target')
one("'Frames-0.9.98-v108-r59j-Correct-Split-Schedule-Overlay-Rufus-UEFI.iso'","'Frames-0.9.98-v108-r59l-Periodic-FLS-FRINDEX-Forensics-Rufus-UEFI.iso'",'ISO target')
one("'R59J-SHA.txt'","'R59L-SHA.txt'",'SHA evidence target')
one("'R25K-R59J.patch'","'R25K-R59L.patch'",'patch evidence target')
one("'FRAMES_V108_R59J'","'FRAMES_V108_R59L'",'ISO label target')
one('R59J-AGGREGATE.json','R59L-AGGREGATE.json','aggregate target')
one("'frames-0.9.98-v108-r59j-correct-split-schedule-overlay'","'frames-0.9.98-v108-r59l-periodic-fls-frindex-forensics'",'profile target')
one("'Frames 0.9.98 v108 r59j — Correct EHCI Split Schedule + Live Overlay'","'Frames 0.9.98 v108 r59l — Periodic FLS Normalization + FRINDEX Forensics'",'cert title target')
one('R59J PASS_VM_PENDING_PHYSICAL','R59L PASS_VM_PENDING_PHYSICAL','PASS target')
alln('R59J-FAILURE.txt','R59L-FAILURE.txt',2,'failure target')
one('r59j exact kernel identity mismatch','r59l exact kernel identity mismatch','identity label')
one("'physical_r59j':'PENDING'",
    "'physical_r59j':'PHYSICAL_QH_ACTIVE_NO_SPLIT_NO_PROGRESS','physical_r59j_telemetry':'R5J_S1_N0_A1_X0_E0_R8_D0','physical_r59k':'PHYSICAL_ASYNC_QH_ACTIVE_NO_INTERRUPT_COMPLETION','physical_r59k_telemetry':'R5K_S1_N0_A1_E0_B0_X0_Y0','physical_r59l':'PENDING'",
    'physical r59j+r59k results + r59l pending')

ns={'__name__':'__main__','__file__':str(base)}
try:
    exec(compile(src,str(base),'exec'),ns,ns)
    k=Path('evidence/kernel-r59l.nx')
    if not k.exists(): raise SystemExit('r59l evidence kernel missing')
    s=k.read_text()
    arm=s[s.index('fn v159_ehci_mouse_periodic_arm'):s.index('fn v135_hid_control_fallback_prepare')]
    for q in ('cmd=clear_flag(cmd,4)','cmd=clear_flag(cmd,8)','let info2=1090591745','volatile_write32(op+20,flo)','cmd=set_flag(cmd,16)'):
        if q not in arm: raise SystemExit('r59l periodic/FLS source gate missing '+q)
    for q in ('fls=(c/4)%4','fi=(fr/8)%1024','volatile_read32(frame+(fi*4))==qlo+2','volatile_read32(dm+12)==tdlo','(ot/128)%2','(volatile_read32(op+4)/16384)%2'):
        if q not in s: raise SystemExit('r59l FRINDEX telemetry gate missing '+q)
    low=arm.lower()
    if any(x in low for x in ('write(10)','nvme_submit_write','ahci_write','fat_write','block_write','input_push(')):
        raise SystemExit('r59l exceeds forensic/read-only scope')
except BaseException:
    out=Path('evidence'); out.mkdir(parents=True,exist_ok=True)
    (out/'R59L-FAILURE.txt').write_text(traceback.format_exc())
    raise
