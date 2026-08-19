#!/usr/bin/env python3
from pathlib import Path
import traceback
here=Path(__file__).parent
base=here/'r59l_cert_driver.py'
src=base.read_text()

def one(old,new,label):
    global src
    n=src.count(old)
    if n!=1: raise SystemExit(f'r59m cert anchor {label} count {n}')
    src=src.replace(old,new,1)
def alln(old,new,count,label):
    global src
    n=src.count(old)
    if n!=count: raise SystemExit(f'r59m cert anchor {label} count {n}, expected {count}')
    src=src.replace(old,new)

one("'patch_v108_r59l_periodic_fls_frindex_forensics.py'","'patch_v108_r59m_hub_multi_tt_activation.py'",'patch target')
alln('kernel-r59l.nx','kernel-r59m.nx',2,'kernel evidence target')
one('2c4734c29577a4710b27577ec2dfa33dcf6f117a25e21607dff5ee6b9632a6de','8b236b8b21a181e5db9fbeec3c5b64840df0d3158980bde3176647e6cf651bc8','exact r59m identity target')
one("'Frames-0.9.98-v108-r59l-Periodic-FLS-FRINDEX-Forensics-Rufus-UEFI.iso'","'Frames-0.9.98-v108-r59m-Hub-Multi-TT-Activation-Rufus-UEFI.iso'",'ISO target')
one("'R59L-SHA.txt'","'R59M-SHA.txt'",'SHA evidence target')
one("'R25K-R59L.patch'","'R25K-R59M.patch'",'patch evidence target')
one("'FRAMES_V108_R59L'","'FRAMES_V108_R59M'",'ISO label target')
one('R59L-AGGREGATE.json','R59M-AGGREGATE.json','aggregate target')
one("'frames-0.9.98-v108-r59l-periodic-fls-frindex-forensics'","'frames-0.9.98-v108-r59m-hub-multi-tt-activation'",'profile target')
one("'Frames 0.9.98 v108 r59l — Periodic FLS Normalization + FRINDEX Forensics'","'Frames 0.9.98 v108 r59m — Hub Multi-TT Activation'",'cert title target')
one('R59L PASS_VM_PENDING_PHYSICAL','R59M PASS_VM_PENDING_PHYSICAL','PASS target')
alln('R59L-FAILURE.txt','R59M-FAILURE.txt',2,'failure target')
one('r59l exact kernel identity mismatch','r59m exact kernel identity mismatch','identity label')
one("'physical_r59l':'PENDING'",
    "'physical_r59l':'PHYSICAL_PERIODIC_QH_FETCHED_NO_INTERRUPT_COMPLETION','physical_r59l_telemetry':'R5L_F0_I921_L0_Q1_N0_A1_P1','physical_r59m':'PENDING'",
    'physical r59l result + r59m pending')

ns={'__name__':'__main__','__file__':str(base)}
try:
    exec(compile(src,str(base),'exec'),ns,ns)
    k=Path('evidence/kernel-r59m.nx')
    if not k.exists(): raise SystemExit('r59m evidence kernel missing')
    s=k.read_text()
    r56=s[s.index('fn v156_ehci_second_hub_census'):s.index('fn v157_ehci_tt_control')]
    arm=s[s.index('fn v159_ehci_mouse_periodic_arm'):s.index('fn v135_hid_control_fallback_prepare')]
    for q in ('let hubproto=volatile_read8(data+6)','if hubproto==2','v155_ehci_control(xhci_state,1,68353,0)','volatile_write64(xhci_state+3880,hubproto)','volatile_write64(xhci_state+3888,ttrc)'):
        if q not in r56: raise SystemExit('r59m hub multi-TT source gate missing '+q)
    for q in ('cmd=clear_flag(cmd,4)','cmd=clear_flag(cmd,8)','let info2=1090591745','volatile_write32(op+20,flo)','cmd=set_flag(cmd,16)'):
        if q not in arm: raise SystemExit('r59m inherited periodic source gate missing '+q)
    for q in ('volatile_read64(xhci+3880)','volatile_read64(xhci+3888)','fls=(c/4)%4','volatile_read32(dm+12)==tdlo','(ot/128)%2','(volatile_read32(op+4)/16384)%2'):
        if q not in s: raise SystemExit('r59m visible/forensic telemetry gate missing '+q)
    low=(r56+arm).lower()
    if any(x in low for x in ('write(10)','nvme_submit_write','ahci_write','fat_write','block_write','input_push(')):
        raise SystemExit('r59m exceeds diagnostic/read-only scope')
except BaseException:
    out=Path('evidence'); out.mkdir(parents=True,exist_ok=True)
    (out/'R59M-FAILURE.txt').write_text(traceback.format_exc())
    raise
