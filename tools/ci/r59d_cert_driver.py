#!/usr/bin/env python3
# r59d certification trigger after workflow registration
from pathlib import Path
import traceback
here=Path(__file__).parent
base=here/'r59c_cert_driver.py'
src=base.read_text()

def one(old,new,label):
    global src
    n=src.count(old)
    if n!=1: raise SystemExit(f'r59d cert anchor {label} count {n}')
    src=src.replace(old,new,1)
def alln(old,new,count,label):
    global src
    n=src.count(old)
    if n!=count: raise SystemExit(f'r59d cert anchor {label} count {n}, expected {count}')
    src=src.replace(old,new)

one("'patch_v108_r59c_ehci_periodic_reserved_fallback.py'","'patch_v108_r59d_dma_ledger_capacity.py'",'patch target')
one('kernel-r59c.nx','kernel-r59d.nx','kernel evidence target')
one('e1218ffe017749b252b6e939534f9d191bccbc68433f6a478f8f19c1506cb66c','0b66bdc0bc1733985f835b86d5ed7862638dea7af682aec703e224b6b3d34f3d','exact r59d identity target')
one("'Frames-0.9.98-v108-r59c-EHCI-Reserved-Page-Fallback-Rufus-UEFI.iso'","'Frames-0.9.98-v108-r59d-DMA-Ledger-Capacity-Rufus-UEFI.iso'",'ISO target')
one("'R59C-SHA.txt'","'R59D-SHA.txt'",'SHA evidence target')
one("'R25K-R59C.patch'","'R25K-R59D.patch'",'patch evidence target')
one("'FRAMES_V108_R59C'","'FRAMES_V108_R59D'",'ISO label target')
one('R59C-AGGREGATE.json','R59D-AGGREGATE.json','aggregate target')
one("'frames-0.9.98-v108-r59c-ehci-reserved-page-fallback'","'frames-0.9.98-v108-r59d-dma-ledger-capacity'",'profile target')
one("'Frames 0.9.98 v108 r59c — EHCI Reserved Page Fallback Repair'","'Frames 0.9.98 v108 r59d — DMA Ledger Capacity Repair'",'cert title target')
one('R59C PASS_VM_PENDING_PHYSICAL','R59D PASS_VM_PENDING_PHYSICAL','PASS target')
alln('R59C-FAILURE.txt','R59D-FAILURE.txt',2,'failure target')
one('r59c exact kernel identity mismatch','r59d exact kernel identity mismatch','identity label')
one("'physical_r59b':'PHYSICAL_PERIODIC_RESERVED_PAGE3_UNAVAILABLE','physical_r59b_telemetry':'R5B_S14_N0_C0_B0_X0_Y0_W0','physical_r59c':'PENDING'",
    "'physical_r59b':'PHYSICAL_PERIODIC_RESERVED_PAGE3_UNAVAILABLE','physical_r59b_telemetry':'R5B_S14_N0_C0_B0_X0_Y0_W0','physical_r59c':'PHYSICAL_DMA_LEDGER_CAPACITY_EXHAUSTED','physical_r59c_telemetry':'R5C_S27_N0_C0_B0_X0_Y0_W0','physical_r59d':'PENDING'",
    'physical r59c result + r59d pending')
anchor="    req('R5C' not in s,'r59c textual label unexpectedly embedded as raw string')"
extra=anchor+"""
    req('volatile_write64(state+16,80)' in s,'r59d DMA ledger advertised capacity is not 80')
    req('let limit=volatile_read64(state+16)' in s and 'limit>80' in s and 'count>=limit' in s,'r59d DMA record bounded-capacity enforcement missing')
    req('count>limit' in s,'r59d DMA audit bounded-capacity enforcement missing')
    req('state+64+(count*48)' in s,'r59d DMA record layout changed unexpectedly')
    req('while d<80' in s and 'volatile_read64(ledger+8)!=80' in s,'r59d allocator stress does not exercise 80-entry ledger')
    req(64+(80*48)<=4096,'r59d ledger geometry exceeds one page')
    r59dfn=s[s.index('fn v159_ehci_mouse_periodic_arm'):s.index('fn v135_hid_control_fallback_prepare')]
    req('dma_record(ledger,frame,4)' in r59dfn,'r59d EHCI frame ownership registration lost')
    req('volatile_write32(op+20,flo)' in r59dfn and 'cmd=set_flag(cmd,16)' in r59dfn,'r59d periodic schedule path lost')
    low59d=r59dfn.lower(); req(all(x not in low59d for x in ['write(10)','nvme_submit_write','ahci_write','fat_write','block_write','input_push(']),'r59d exceeds raw diagnostic/safety scope')
    req('R5D' not in s,'r59d textual label unexpectedly embedded as raw string')
"""
one(anchor,extra,'r59d ledger capacity model gates')

ns={'__name__':'__main__','__file__':str(base)}
try:
    exec(compile(src,str(base),'exec'),ns,ns)
except BaseException:
    out=Path('evidence'); out.mkdir(parents=True,exist_ok=True)
    (out/'R59D-FAILURE.txt').write_text(traceback.format_exc())
    raise
