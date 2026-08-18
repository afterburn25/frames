#!/usr/bin/env python3
from pathlib import Path
import traceback
here=Path(__file__).parent
base=here/'r55_cert_driver.py'
src=base.read_text()

def one(old,new,label):
    global src
    n=src.count(old)
    if n!=1: raise SystemExit(f'r55b cert anchor {label} count {n}')
    src=src.replace(old,new,1)

def alln(old,new,count,label):
    global src
    n=src.count(old)
    if n!=count: raise SystemExit(f'r55b cert anchor {label} count {n}, expected {count}')
    src=src.replace(old,new)

one("'patch_v108_r55_ehci_intel_hub_discovery.py'","'patch_v108_r55b_ehci_intel_hub_discovery_4param.py'",'patch target')
one('kernel-r55.nx','kernel-r55b.nx','kernel evidence target')
one('7f3aebe8d7ac75cada7b32dcffd4074c84651e1dd22c179bc2e34e0375fbc4d7','038e9e9e930c8d9ae160925d474b13b2919681ed42e17f9584ebbe23f8f5faf2','exact kernel identity target')
one("'Frames-0.9.98-v108-r55-EHCI-Intel-Hub-Discovery-Rufus-UEFI.iso'","'Frames-0.9.98-v108-r55b-EHCI-Intel-Hub-Discovery-4Param-Rufus-UEFI.iso'",'ISO target')
one("'R55-SHA.txt'","'R55B-SHA.txt'",'SHA evidence target')
one("'R25K-R55.patch'","'R25K-R55B.patch'",'patch evidence target')
one("'FRAMES_V108_R55'","'FRAMES_V108_R55B'",'ISO label target')
one('R55-AGGREGATE.json','R55B-AGGREGATE.json','aggregate target')
one("'frames-0.9.98-v108-r55-ehci-intel-hub-discovery'","'frames-0.9.98-v108-r55b-ehci-intel-hub-discovery-4param'",'profile target')
one("'Frames 0.9.98 v108 r55 — EHCI Intel Hub Discovery'","'Frames 0.9.98 v108 r55b — EHCI Intel Hub Discovery 4-Parameter ABI'",'cert title target')
one('R55 PASS_VM_PENDING_PHYSICAL','R55B PASS_VM_PENDING_PHYSICAL','PASS target')
alln('R55-FAILURE.txt','R55B-FAILURE.txt',2,'failure target')
one('r55 exact kernel identity mismatch','r55b exact kernel identity mismatch','identity label')
one("'physical_r55':'PENDING'","'physical_r55':'NOT_RELEASED_COMPILE_REJECTED_NX4004','physical_r55b':'PENDING'",'r55 compile rejection and r55b pending')

# Adapt r55 structural gates to the corrected four-parameter helper. The EHCI
# ordinal and DMA page are carried in already-reserved xHCI state slots, keeping
# the Nexus x64 ABI at <=4 arguments without changing transaction semantics.
one("'v155_ehci_control(xhci_state,ord,0,dma,66816,0)' in r55fn","'v155_ehci_control(xhci_state,0,66816,0)' in r55fn",'SET_ADDRESS model')
one("'v155_ehci_control(xhci_state,ord,1,dma,2533274823952000,9)' in r55fn","'v155_ehci_control(xhci_state,1,2533274823952000,9)' in r55fn",'GET_CONFIG model')
one("'v155_ehci_control(xhci_state,ord,1,dma,setcfg,0)' in r55fn","'v155_ehci_control(xhci_state,1,setcfg,0)' in r55fn",'SET_CONFIGURATION model')
one("'v155_ehci_control(xhci_state,ord,1,dma,2533275478263456,9)' in r55fn","'v155_ehci_control(xhci_state,1,2533275478263456,9)' in r55fn",'GET_HUB_DESCRIPTOR model')
anchor="    req('volatile_read64(xhci_state+3792)!=1' in r55fn and 'volatile_read64(xhci_state+3816)!=9' in r55fn and 'volatile_read64(xhci_state+3832)!=32903' in r55fn and 'volatile_read64(xhci_state+3840)!=32776' in r55fn,'r55 exact physical Intel hub identity gate missing')"
extra=anchor+"""
    req('fn v155_ehci_control(xhci_state:u64,addr:u64,setupv:u64,length:u64) -> u64' in r55fn,'r55b four-parameter EHCI helper signature missing')
    req('fn v155_ehci_control(xhci_state:u64,ord:u64,addr:u64,dma:u64,setupv:u64,length:u64)' not in r55fn,'r55b retained unsupported six-parameter helper')
    req('let ord=volatile_read64(xhci_state+3800)' in r55fn and 'let dma=volatile_read64(xhci_state+4040)' in r55fn,'r55b EHCI helper state handoff missing')
    req('volatile_write64(xhci_state+4040,dma)' in r55fn,'r55b DMA state slot write missing')
"""
one(anchor,extra,'four-parameter ABI gates')

ns={'__name__':'__main__','__file__':str(base)}
try:
    exec(compile(src,str(base),'exec'),ns,ns)
except BaseException:
    out=Path('evidence'); out.mkdir(parents=True,exist_ok=True)
    (out/'R55B-FAILURE.txt').write_text(traceback.format_exc())
    raise
