#!/usr/bin/env python3
from pathlib import Path
import traceback
here=Path(__file__).parent
base=here/'r59d_cert_driver.py'
src=base.read_text()

def one(old,new,label):
    global src
    n=src.count(old)
    if n!=1: raise SystemExit(f'r59e cert anchor {label} count {n}')
    src=src.replace(old,new,1)
def alln(old,new,count,label):
    global src
    n=src.count(old)
    if n!=count: raise SystemExit(f'r59e cert anchor {label} count {n}, expected {count}')
    src=src.replace(old,new)

one("'patch_v108_r59d_dma_ledger_capacity.py'","'patch_v108_r59e_ehci_periodic_execution_forensics.py'",'patch target')
one('kernel-r59d.nx','kernel-r59e.nx','kernel evidence target')
one('0b66bdc0bc1733985f835b86d5ed7862638dea7af682aec703e224b6b3d34f3d','a582d1f5f8464da49f06b67c9ced5fbf755bbde3106b9cae97991f1ff6f406fa','exact r59e identity target')
one("'Frames-0.9.98-v108-r59d-DMA-Ledger-Capacity-Rufus-UEFI.iso'","'Frames-0.9.98-v108-r59e-EHCI-Periodic-Execution-Forensics-Rufus-UEFI.iso'",'ISO target')
one("'R59D-SHA.txt'","'R59E-SHA.txt'",'SHA evidence target')
one("'R25K-R59D.patch'","'R25K-R59E.patch'",'patch evidence target')
one("'FRAMES_V108_R59D'","'FRAMES_V108_R59E'",'ISO label target')
one('R59D-AGGREGATE.json','R59E-AGGREGATE.json','aggregate target')
one("'frames-0.9.98-v108-r59d-dma-ledger-capacity'","'frames-0.9.98-v108-r59e-ehci-periodic-execution-forensics'",'profile target')
one("'Frames 0.9.98 v108 r59d — DMA Ledger Capacity Repair'","'Frames 0.9.98 v108 r59e — EHCI Periodic Execution Forensics'",'cert title target')
one('R59D PASS_VM_PENDING_PHYSICAL','R59E PASS_VM_PENDING_PHYSICAL','PASS target')
alln('R59D-FAILURE.txt','R59E-FAILURE.txt',2,'failure target')
one('r59d exact kernel identity mismatch','r59e exact kernel identity mismatch','identity label')
one("'physical_r59c':'PHYSICAL_DMA_LEDGER_CAPACITY_EXHAUSTED','physical_r59c_telemetry':'R5C_S27_N0_C0_B0_X0_Y0_W0','physical_r59d':'PENDING'",
    "'physical_r59c':'PHYSICAL_DMA_LEDGER_CAPACITY_EXHAUSTED','physical_r59c_telemetry':'R5C_S27_N0_C0_B0_X0_Y0_W0','physical_r59d':'PHYSICAL_PERIODIC_SCHEDULE_ARMED_QTD_NO_COMPLETION','physical_r59d_telemetry':'R5D_S1_N0_C0_B0_X0_Y0_W0','physical_r59e':'PENDING'",
    'physical r59d result + r59e pending')
anchor="    req('R5D' not in s,'r59d textual label unexpectedly embedded as raw string')"
extra=anchor+"""
    r59efn=s[s.index('fn v159_ehci_mouse_periodic_arm'):s.index('fn v135_hid_control_fallback_prepare')]
    req('volatile_read32(qh+12)' in r59efn and 'cur==(qtd%4294967296)' in r59efn,'r59e QH current-qTD fetch proof missing')
    req('volatile_read32(op+12)%16384' in r59efn,'r59e FRINDEX observation missing')
    req('volatile_read32(op+4)/16384' in r59efn,'r59e periodic schedule status observation missing')
    req('volatile_write64(xhci_state+4072,qmatch)' in r59efn,'r59e QH/qTD match telemetry missing')
    req('volatile_write64(xhci_state+4080,tok)' in r59efn,'r59e qTD token telemetry missing')
    req('volatile_write64(xhci_state+4088,fri+(pss*16384))' in r59efn,'r59e FRINDEX/PSS packed telemetry missing')
    req('volatile_write64(xhci_state+4064,volatile_read64(xhci_state+4064)+1)' in r59efn,'r59e completion counter lost')
    req('fm%16384' in s and '(rr/128)%2' in s and '(rr/4)%32' in s and '(fm/16384)%2' in s,'r59e visible forensic row missing')
    low59e=r59efn.lower(); req(all(x not in low59e for x in ['write(10)','nvme_submit_write','ahci_write','fat_write','block_write','input_push(']),'r59e exceeds forensic/read-only scope')
    req('R5E' not in s,'r59e textual label unexpectedly embedded as raw string')
"""
one(anchor,extra,'r59e forensic model gates')

ns={'__name__':'__main__','__file__':str(base)}
try:
    exec(compile(src,str(base),'exec'),ns,ns)
except BaseException:
    out=Path('evidence'); out.mkdir(parents=True,exist_ok=True)
    (out/'R59E-FAILURE.txt').write_text(traceback.format_exc())
    raise
