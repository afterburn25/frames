#!/usr/bin/env python3
from pathlib import Path
here=Path(__file__).parent
base=here/'patch_v108_r55_ehci_intel_hub_discovery.py'
src=base.read_text()

def one(old,new,label):
    global src
    n=src.count(old)
    if n!=1: raise SystemExit(f'r55b {label} count {n}')
    src=src.replace(old,new,1)

def alln(old,new,count,label):
    global src
    n=src.count(old)
    if n!=count: raise SystemExit(f'r55b {label} count {n}, expected {count}')
    src=src.replace(old,new)

one(
"fn v155_ehci_control(xhci_state:u64,ord:u64,addr:u64,dma:u64,setupv:u64,length:u64) -> u64 {\n    if xhci_state==0 || ord==0 || dma==0 { return 2; }",
"fn v155_ehci_control(xhci_state:u64,addr:u64,setupv:u64,length:u64) -> u64 {\n    if xhci_state==0 { return 2; }\n    let ord=volatile_read64(xhci_state+3800); let dma=volatile_read64(xhci_state+4040); if ord==0 || dma==0 { return 2; }",
'four-parameter EHCI control helper')
one(
"let dma=alloc_dma_page(phys_state,3); if dma==0 { unsafe { volatile_write64(xhci_state+3920,3); } return 3; }\n    var rc=v155_ehci_control(xhci_state,ord,0,dma,66816,0);",
"let dma=alloc_dma_page(phys_state,3); if dma==0 { unsafe { volatile_write64(xhci_state+3920,3); } return 3; } unsafe { volatile_write64(xhci_state+4040,dma); }\n    var rc=v155_ehci_control(xhci_state,0,66816,0);",
'DMA state handoff + SET_ADDRESS call')
one('v155_ehci_control(xhci_state,ord,1,dma,2533274823952000,9)','v155_ehci_control(xhci_state,1,2533274823952000,9)','GET_CONFIG call')
one('v155_ehci_control(xhci_state,ord,1,dma,setcfg,0)','v155_ehci_control(xhci_state,1,setcfg,0)','SET_CONFIGURATION call')
one('v155_ehci_control(xhci_state,ord,1,dma,2533275478263456,9)','v155_ehci_control(xhci_state,1,2533275478263456,9)','GET_HUB_DESCRIPTOR call')
one('v155_ehci_control(xhci_state,ord,1,dma,req,0)','v155_ehci_control(xhci_state,1,req,0)','PORT_POWER call')
one('v155_ehci_control(xhci_state,ord,1,dma,req,4)','v155_ehci_control(xhci_state,1,req,4)','PORT_STATUS call')
one("EXPECTED='7f3aebe8d7ac75cada7b32dcffd4074c84651e1dd22c179bc2e34e0375fbc4d7'","EXPECTED='038e9e9e930c8d9ae160925d474b13b2919681ed42e17f9584ebbe23f8f5faf2'",'exact r55b identity')
ns={'__name__':'__main__','__file__':str(base)}
exec(compile(src,str(base),'exec'),ns,ns)
