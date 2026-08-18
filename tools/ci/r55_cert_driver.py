#!/usr/bin/env python3
from pathlib import Path
import traceback
here=Path(__file__).parent
base=here/'r54_cert_driver.py'
src=base.read_text()

def one(old,new,label):
    global src
    n=src.count(old)
    if n!=1: raise SystemExit(f'r55 cert anchor {label} count {n}')
    src=src.replace(old,new,1)

def alln(old,new,count,label):
    global src
    n=src.count(old)
    if n!=count: raise SystemExit(f'r55 cert anchor {label} count {n}, expected {count}')
    src=src.replace(old,new)

one("'patch_v108_r54_ehci_root_descriptor_probe.py'","'patch_v108_r55_ehci_intel_hub_discovery.py'",'patch target')
one('kernel-r54.nx','kernel-r55.nx','kernel evidence target')
one('ebcf7baf18422cc72804eec9e18a317ed5daf1baee65330528be66c07d599c19','7f3aebe8d7ac75cada7b32dcffd4074c84651e1dd22c179bc2e34e0375fbc4d7','exact kernel identity target')
one("'Frames-0.9.98-v108-r54-EHCI-Root-Descriptor-Probe-Rufus-UEFI.iso'","'Frames-0.9.98-v108-r55-EHCI-Intel-Hub-Discovery-Rufus-UEFI.iso'",'ISO target')
one("'R54-SHA.txt'","'R55-SHA.txt'",'SHA evidence target')
one("'R25K-R54.patch'","'R25K-R55.patch'",'patch evidence target')
one("'FRAMES_V108_R54'","'FRAMES_V108_R55'",'ISO label target')
one('R54-AGGREGATE.json','R55-AGGREGATE.json','aggregate target')
one("'frames-0.9.98-v108-r54-ehci-root-descriptor-probe'","'frames-0.9.98-v108-r55-ehci-intel-hub-discovery'",'profile target')
one("'Frames 0.9.98 v108 r54 — EHCI Root Device Descriptor Probe'","'Frames 0.9.98 v108 r55 — EHCI Intel Hub Discovery'",'cert title target')
one('R54 PASS_VM_PENDING_PHYSICAL','R55 PASS_VM_PENDING_PHYSICAL','PASS target')
alln('R54-FAILURE.txt','R55-FAILURE.txt',2,'failure target')
one('r54 exact kernel identity mismatch','r55 exact kernel identity mismatch','identity label')
one("'physical_r54':'PENDING'","'physical_r54':'PHYSICAL_EHCI_ROOT_INTEL_HUB_DESCRIPTOR_PASS','physical_r54_telemetry':'R54_S1_E1_R1_C9_M64_V32903_D32776','physical_r55':'PENDING'",'physical r54 evidence and r55 pending')

# Keep the inherited r54 bounded-descriptor gates scoped only to v154; r55
# adds controlled address/configuration and hub-class requests afterward.
one("r54fn=s[s.index('fn v154_ehci_root_descriptor_probe'):s.index('fn xhci_configure_boot_hid')]","r54fn=s[s.index('fn v154_ehci_root_descriptor_probe'):s.index('fn v155_ehci_control')]",'r54 model slice boundary')

# r55 replaces the visible r54 row. Extend the inherited r52 compatibility
# adaptation to recognize the r55 overlay while retaining route-state writes.
needle="or ('volatile_read64(xhci+3792)' in s and 'volatile_read64(xhci+3800)' in s and 'volatile_read64(xhci+3808)' in s and 'volatile_read64(xhci+3816)' in s and 'volatile_read64(xhci+3824)' in s and 'volatile_read64(xhci+3832)' in s and 'volatile_read64(xhci+3840)' in s))"
replacement="or ('volatile_read64(xhci+3792)' in s and 'volatile_read64(xhci+3800)' in s and 'volatile_read64(xhci+3808)' in s and 'volatile_read64(xhci+3816)' in s and 'volatile_read64(xhci+3824)' in s and 'volatile_read64(xhci+3832)' in s and 'volatile_read64(xhci+3840)' in s) or ('volatile_read64(xhci+3920)' in s and 'volatile_read64(xhci+3936)' in s and 'volatile_read64(xhci+3944)' in s and 'volatile_read64(xhci+3952)' in s and 'volatile_read64(xhci+3960)' in s and 'volatile_read64(xhci+3968)' in s and 'volatile_read64(xhci+3976)' in s))"
if src.count(needle)!=1: raise SystemExit(f'r55 r52/r54 row compatibility anchor count {src.count(needle)}')
src=src.replace(needle,replacement,1)

anchor="    req(all(x not in r54fn.lower() for x in ['set_configuration','set_address','periodiclistbase','nvme_submit_write','ahci_write','write(10)']),'r54 exceeds bounded root-descriptor scope')"
extra=anchor+"""
    r55fn=s[s.index('fn v155_ehci_control'):s.index('fn xhci_configure_boot_hid')]
    req('volatile_read64(xhci_state+3792)!=1' in r55fn and 'volatile_read64(xhci_state+3816)!=9' in r55fn and 'volatile_read64(xhci_state+3832)!=32903' in r55fn and 'volatile_read64(xhci_state+3840)!=32776' in r55fn,'r55 exact physical Intel hub identity gate missing')
    req('v155_ehci_control(xhci_state,ord,0,dma,66816,0)' in r55fn,'r55 bounded hub SET_ADDRESS missing')
    req('v155_ehci_control(xhci_state,ord,1,dma,2533274823952000,9)' in r55fn,'r55 configuration-header request missing')
    req('let setcfg=2304+(cfg*65536)' in r55fn and 'v155_ehci_control(xhci_state,ord,1,dma,setcfg,0)' in r55fn,'r55 exact hub SET_CONFIGURATION missing')
    req('v155_ehci_control(xhci_state,ord,1,dma,2533275478263456,9)' in r55fn,'r55 hub descriptor request missing')
    req('let nports=volatile_read8(data+2)' in r55fn and 'nports>15' in r55fn,'r55 bounded hub-port count validation missing')
    req('525091+(p*4294967296)' in r55fn,'r55 bounded PORT_POWER request missing')
    req('1125899906842787+(p*4294967296)' in r55fn,'r55 per-port GET_STATUS request missing')
    req('cmd=clear_flag(cmd,16)' in r55fn and 'set_flag(cmd,16)' not in r55fn,'r55 periodic schedule is not held disabled')
    req('cmd=set_flag(cmd,32)' in r55fn and 'cmd=clear_flag(cmd,32)' in r55fn,'r55 asynchronous control schedule missing/bounds missing')
    req('volatile_write32(op+8,0)' in r55fn,'r55 EHCI interrupts are not disabled')
    req('v155_ehci_intel_hub_discovery(xhci,phys_state)' in s and 'volatile_read64(xhci+3792)==1' in s,'r55 hub discovery is not gated by successful r54 physical identity')
    req(all(x not in r55fn.lower() for x in ['set_flag(cmd,16)','periodiclistbase','interrupt endpoint','nvme_submit_write','ahci_write','write(10)']),'r55 exceeds bounded hub-discovery scope')
"""
one(anchor,extra,'r55 hub discovery model gates')

ns={'__name__':'__main__','__file__':str(base)}
try:
    exec(compile(src,str(base),'exec'),ns,ns)
except BaseException:
    out=Path('evidence'); out.mkdir(parents=True,exist_ok=True)
    (out/'R55-FAILURE.txt').write_text(traceback.format_exc())
    raise
