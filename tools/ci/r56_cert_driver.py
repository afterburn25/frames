#!/usr/bin/env python3
from pathlib import Path
import traceback
here=Path(__file__).parent
base=here/'r55c_cert_driver.py'
src=base.read_text()

def one(old,new,label):
    global src
    n=src.count(old)
    if n!=1: raise SystemExit(f'r56 cert anchor {label} count {n}')
    src=src.replace(old,new,1)

def alln(old,new,count,label):
    global src
    n=src.count(old)
    if n!=count: raise SystemExit(f'r56 cert anchor {label} count {n}, expected {count}')
    src=src.replace(old,new)

one("'patch_v108_r55c_ehci_hub_address_preflight.py'","'patch_v108_r56_ehci_second_hub_census.py'",'patch target')
one('kernel-r55c.nx','kernel-r56.nx','kernel evidence target')
one('8341c00a24f8dad89dec417dcaa93c1ff648344652cd6fda4ef47afd459f4595','0000000000000000000000000000000000000000000000000000000000000000','provisional exact kernel identity target')
one("'Frames-0.9.98-v108-r55c-EHCI-Hub-Address-Preflight-Rufus-UEFI.iso'","'Frames-0.9.98-v108-r56-EHCI-Second-Hub-Census-Rufus-UEFI.iso'",'ISO target')
one("'R55C-SHA.txt'","'R56-SHA.txt'",'SHA evidence target')
one("'R25K-R55C.patch'","'R25K-R56.patch'",'patch evidence target')
one("'FRAMES_V108_R55C'","'FRAMES_V108_R56'",'ISO label target')
one('R55C-AGGREGATE.json','R56-AGGREGATE.json','aggregate target')
one("'frames-0.9.98-v108-r55c-ehci-hub-address-preflight'","'frames-0.9.98-v108-r56-ehci-second-hub-census'",'profile target')
one("'Frames 0.9.98 v108 r55c — EHCI Hub Address Preflight + DMA Reuse'","'Frames 0.9.98 v108 r56 — EHCI Second Rate-Matching Hub Census'",'cert title target')
one('R55C PASS_VM_PENDING_PHYSICAL','R56 PASS_VM_PENDING_PHYSICAL','PASS target')
alln('R55C-FAILURE.txt','R56-FAILURE.txt',2,'failure target')
one('r55c exact kernel identity mismatch','r56 exact kernel identity mismatch','identity label')
one("'physical_r55':'NOT_RELEASED_COMPILE_REJECTED_NX4004','physical_r55b':'PHYSICAL_HUB_DISCOVERY_STOPPED_STATE3','physical_r55b_telemetry':'R55_S3_N0_C0_E0_B0_F0_T0','physical_r55c':'PENDING'","'physical_r55':'NOT_RELEASED_COMPILE_REJECTED_NX4004','physical_r55b':'PHYSICAL_HUB_DISCOVERY_STOPPED_STATE3','physical_r55b_telemetry':'R55_S3_N0_C0_E0_B0_F0_T0','physical_r55c':'PHYSICAL_EHCI1_INTEL_HUB6_ZERO_CONNECTED','physical_r55c_telemetry':'R5C_S7_N6_C0_E0_B0_F0_T3','physical_r56':'PENDING'",'physical r55c result + r56 pending')

anchor="    req('volatile_write64(xhci_state+3920,20+rc)' in r55fn and 'volatile_write64(xhci_state+3920,30+rc)' in r55fn,'r55c encoded helper/address failure states missing')"
extra=anchor+"""
    req('fn v156_ehci_second_hub_census(xhci_state:u64) -> u64' in s,'r56 second EHCI hub census function missing')
    r56fn=s[s.index('fn v156_ehci_second_hub_census'):s.index('fn xhci_configure_boot_hid')]
    req('first_state!=7' in r56fn and 'volatile_read64(xhci_state+3936)==0' in r56fn,'r56 is not gated by valid empty first-hub census')
    req('v108_pci_nth_ehci_v121(1)' in r56fn and 'let ord:u64=2' in r56fn,'r56 does not target EHCI ordinal 2')
    req('volatile_read64(xhci_state+3848)' in r56fn and 'volatile_write64(xhci_state+4040,dma)' in r56fn,'r56 does not reuse proven EHCI DMA page')
    req('wr=set_flag(wr,256)' in r56fn and 'wr=clear_flag(wr,256)' in r56fn,'r56 EHCI2 root-port reset proof missing')
    req('done%2==0 || (done/4)%2==0 || (done/8192)%2!=0' in r56fn,'r56 EHCI2 root connection/enable/owner validation missing')
    req('v155_ehci_control(xhci_state,0,5066549597570688,18)' in r56fn,'r56 EHCI2 root device descriptor transfer missing')
    req('cls!=9 || mps!=64 || vid!=32903' in r56fn,'r56 Intel high-speed root-hub identity gate missing')
    req('v155_ehci_control(xhci_state,0,66816,0)' in r56fn,'r56 EHCI2 hub SET_ADDRESS missing')
    req('2533274823952000' in r56fn and '2533275478263456' in r56fn,'r56 hub config/descriptor discovery missing')
    req('525091+(pnum*4294967296)' in r56fn,'r56 bounded downstream PORT_POWER missing')
    req('1125899906842787+(pnum*4294967296)' in r56fn,'r56 downstream GET_STATUS census missing')
    req('while round<5 && connected==0' in r56fn,'r56 downstream connection rescan is not bounded')
    req('v156_ehci_second_hub_census(xhci)' in s,'r56 second-hub census not invoked')
    req('volatile_read64(xhci+3928)' in s and 'volatile_read64(xhci+3936)' in s and 'volatile_read64(xhci+3944)' in s,'r56 E/N/C physical overlay fields missing')
    req('set_flag(cmd,16)' not in r56fn,'r56 unexpectedly enables EHCI periodic scheduling')
    low=r56fn.lower(); req(all(x not in low for x in ['ehci_interrupt','interrupt endpoint','write(10)','nvme_submit_write','ahci_write']),'r56 exceeds bounded census/safety scope')
"""
one(anchor,extra,'r56 second-hub model gates')

ns={'__name__':'__main__','__file__':str(base)}
try:
    exec(compile(src,str(base),'exec'),ns,ns)
except BaseException:
    out=Path('evidence'); out.mkdir(parents=True,exist_ok=True)
    (out/'R56-FAILURE.txt').write_text(traceback.format_exc())
    raise
