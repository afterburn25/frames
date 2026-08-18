#!/usr/bin/env python3
from pathlib import Path
import traceback
here=Path(__file__).parent
base=here/'r55b_cert_driver.py'
src=base.read_text()

def one(old,new,label):
    global src
    n=src.count(old)
    if n!=1: raise SystemExit(f'r55c cert anchor {label} count {n}')
    src=src.replace(old,new,1)

def alln(old,new,count,label):
    global src
    n=src.count(old)
    if n!=count: raise SystemExit(f'r55c cert anchor {label} count {n}, expected {count}')
    src=src.replace(old,new)

one("'patch_v108_r55b_ehci_intel_hub_discovery_4param.py'","'patch_v108_r55c_ehci_hub_address_preflight.py'",'patch target')
one('kernel-r55b.nx','kernel-r55c.nx','kernel evidence target')
one('038e9e9e930c8d9ae160925d474b13b2919681ed42e17f9584ebbe23f8f5faf2','8341c00a24f8dad89dec417dcaa93c1ff648344652cd6fda4ef47afd459f4595','exact kernel identity target')
one("'Frames-0.9.98-v108-r55b-EHCI-Intel-Hub-Discovery-4Param-Rufus-UEFI.iso'","'Frames-0.9.98-v108-r55c-EHCI-Hub-Address-Preflight-Rufus-UEFI.iso'",'ISO target')
one("'R55B-SHA.txt'","'R55C-SHA.txt'",'SHA evidence target')
one("'R25K-R55B.patch'","'R25K-R55C.patch'",'patch evidence target')
one("'FRAMES_V108_R55B'","'FRAMES_V108_R55C'",'ISO label target')
one('R55B-AGGREGATE.json','R55C-AGGREGATE.json','aggregate target')
one("'frames-0.9.98-v108-r55b-ehci-intel-hub-discovery-4param'","'frames-0.9.98-v108-r55c-ehci-hub-address-preflight'",'profile target')
one("'Frames 0.9.98 v108 r55b — EHCI Intel Hub Discovery 4-Parameter ABI'","'Frames 0.9.98 v108 r55c — EHCI Hub Address Preflight + DMA Reuse'",'cert title target')
one('R55B PASS_VM_PENDING_PHYSICAL','R55C PASS_VM_PENDING_PHYSICAL','PASS target')
alln('R55B-FAILURE.txt','R55C-FAILURE.txt',2,'failure target')
one('r55b exact kernel identity mismatch','r55c exact kernel identity mismatch','identity label')
one("'physical_r55':'NOT_RELEASED_COMPILE_REJECTED_NX4004','physical_r55b':'PENDING'","'physical_r55':'NOT_RELEASED_COMPILE_REJECTED_NX4004','physical_r55b':'PHYSICAL_HUB_DISCOVERY_STOPPED_STATE3','physical_r55b_telemetry':'R55_S3_N0_C0_E0_B0_F0_T0','physical_r55c':'PENDING'",'physical r55b result + r55c pending')

anchor="    req('volatile_write64(xhci_state+4040,dma)' in r55fn,'r55b DMA state slot write missing')"
extra=anchor+"""
    req('let dma=volatile_read64(xhci_state+3848)' in r55fn,'r55c does not reuse the physically proven r54 DMA page')
    req('alloc_dma_page(phys_state,3)' not in r55fn,'r55c unexpectedly consumes a second EHCI DMA page')
    req('v155_ehci_control(xhci_state,0,2251799830464128,8)' in r55fn,'r55c address-0 descriptor preflight missing')
    req('volatile_read8(pdata)<8' in r55fn and 'volatile_read8(pdata+1)!=1' in r55fn and 'volatile_read8(pdata+7)!=64' in r55fn,'r55c preflight descriptor validation missing')
    req('volatile_write64(xhci_state+3920,20+rc)' in r55fn and 'volatile_write64(xhci_state+3920,30+rc)' in r55fn,'r55c encoded helper/address failure states missing')
    req('R5C' not in s,'r55c textual label unexpectedly embedded as raw string')
"""
one(anchor,extra,'r55c DMA/preflight model gates')

ns={'__name__':'__main__','__file__':str(base)}
try:
    exec(compile(src,str(base),'exec'),ns,ns)
except BaseException:
    out=Path('evidence'); out.mkdir(parents=True,exist_ok=True)
    (out/'R55C-FAILURE.txt').write_text(traceback.format_exc())
    raise
