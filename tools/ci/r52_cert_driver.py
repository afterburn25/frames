#!/usr/bin/env python3
from pathlib import Path
import traceback
here=Path(__file__).parent
base=here/'r50_cert_driver.py'
src=base.read_text()

def one(old,new,label):
    global src
    n=src.count(old)
    if n!=1: raise SystemExit(f'r52 cert anchor {label} count {n}')
    src=src.replace(old,new,1)

def alln(old,new,count,label):
    global src
    n=src.count(old)
    if n!=count: raise SystemExit(f'r52 cert anchor {label} count {n}, expected {count}')
    src=src.replace(old,new)

one("'patch_v108_r50_device_endpoint_status_proof.py'","'patch_v108_r52_intel_ehci_companion_wake.py'",'patch target')
one('kernel-r50.nx','kernel-r52.nx','kernel evidence target')
one('30d8239eb1c91a5b70246744d856e1a7aae77360baeaa024033fb135070fd6f1','7f854b564c7ddee71382ebe616ec1dd70dad3ce679684b1babd1550ac40ffcf3','exact kernel identity target')
one("'Frames-0.9.98-v108-r50-USB-Device-Endpoint-Status-Proof-Rufus-UEFI.iso'","'Frames-0.9.98-v108-r52-Intel-EHCI-Companion-Wake-Proof-Rufus-UEFI.iso'",'ISO target')
one("'R50-SHA.txt'","'R52-SHA.txt'",'SHA evidence target')
one("'R25K-R50.patch'","'R25K-R52.patch'",'patch evidence target')
one("'FRAMES_V108_R50'","'FRAMES_V108_R52'",'ISO label target')
one('R50-AGGREGATE.json','R52-AGGREGATE.json','aggregate target')
one("'frames-0.9.98-v108-r50-usb-device-endpoint-status-proof'","'frames-0.9.98-v108-r52-intel-ehci-companion-wake-proof'",'profile target')
one("'Frames 0.9.98 v108 r50 — USB Device Endpoint Status Proof'","'Frames 0.9.98 v108 r52 — Intel EHCI Companion Wake Proof'",'cert title target')
one('R50 PASS_VM_PENDING_PHYSICAL','R52 PASS_VM_PENDING_PHYSICAL','PASS target')
alln('R50-FAILURE.txt','R52-FAILURE.txt',2,'failure target')
one('r50 exact kernel identity mismatch','r52 exact kernel identity mismatch','identity label')

one("'physical_r50':'PENDING'","'physical_r50':'PHYSICAL_DEVICE_CONFIG1_ALT0_MOUSE_EP130_NOT_HALTED_FULLSPEED_NO_INTERRUPT_REPORT','physical_r50_telemetry':'R50_C1_I0_E130_H0_X0_S1_P1','physical_r51':'PHYSICAL_ROUTE_MOVED_NO_EHCI_CCS','physical_r51_telemetry':'R51_S4_B1_A0_E0_P0_C0_V0','physical_r52':'PENDING'",'physical r50/r51 evidence and r52 pending')

old_row="""    req('volatile_read64(xhci+3624)' in s and 'volatile_read64(xhci+3632)' in s and 'volatile_read64(xhci+3640)' in s and 'volatile_read64(xhci+3648)' in s and 'volatile_read64(xhci+3656)' in s and 'volatile_read64(xhci+3672)' in s and 'volatile_read64(xhci+3680)' in s,'r50 physical device-status row missing')"""
new_row="""    req('volatile_read64(xhci+3696)' in s and 'volatile_read64(xhci+3704)' in s and 'volatile_read64(xhci+3712)' in s and 'volatile_read64(xhci+3720)' in s and 'volatile_read64(xhci+3728)' in s and 'volatile_read64(xhci+3736)' in s and 'volatile_read64(xhci+3744)' in s and 'volatile_write64(xhci_state+3752,before_bit)' in s and 'volatile_write64(xhci_state+3760,after_bit)' in s,'r52 physical EHCI companion wake row/route proof missing')"""
one(old_row,new_row,'r52 physical row gate')

anchor="    req('v135_hid_control_fallback_poll' not in cfg50,'r50 reintroduced continuous GET_REPORT fallback')"
extra=anchor+"""
    r52fn=s[s.index('fn v152_intel_ehci_companion_wake_probe'):s.index('fn xhci_configure_boot_hid')]
    req('vendor!=32902 || device!=35889 || vid!=9354 || pid!=4267 || sw_port!=2 || speed!=1 || ep!=130' in r52fn,'r52 exact Intel/receiver/port/endpoint guard missing')
    req('let u2m=pci_cfg_read32(bus,dev,fun,212)' in r52fn and 'let before=pci_cfg_read32(bus,dev,fun,208)' in r52fn,'r52 Intel USB2 route mask/read proof missing')
    req('pci_cfg_write32(bdf,208,before-mask)' in r52fn and r52fn.count('pci_cfg_write32(bdf,208,before-mask)')==1,'r52 route mutation is not single-bit bounded')
    req('v108_pci_nth_ehci_v121(ord)' in r52fn and r52fn.count('v108_pci_nth_ehci_v121(ord)')>=2,'r52 EHCI companion wake/rescan proof missing')
    req('volatile_write32(op+8,0)' in r52fn,'r52 EHCI interrupts are not explicitly disabled')
    req('cmd=clear_flag(cmd,16); cmd=clear_flag(cmd,32); cmd=clear_flag(cmd,64)' in r52fn,'r52 periodic/async/IAAD schedule-disable proof missing')
    req('volatile_write32(op+64,1)' in r52fn,'r52 EHCI CONFIGFLAG ownership proof missing')
    req('set_flag(ps,4096)' in r52fn,'r52 per-port power-on proof missing')
    req('cmd=set_flag(cmd,1)' in r52fn and 'volatile_read32(op+4)/4096' in r52fn,'r52 EHCI Run/HCHalted proof missing')
    req('volatile_read64(xhci+3696)!=1 && volatile_read64(xhci+3696)!=4 && volatile_read64(xhci+3696)!=5' in s,'r52 stale xHCI path is not suppressed after successful route mutation')
    req('v152_intel_ehci_companion_wake_probe(xhci)' in s,'r52 companion wake probe is not invoked')
    lower=r52fn.lower()
    req(all(x not in lower for x in ['periodiclistbase','asynclistaddr','ehci_submit','ehci_transfer']),'r52 unexpectedly adds EHCI transfer/schedule programming')
"""
one(anchor,extra,'r52 guarded EHCI wake model gates')

# r36 structurally required its historical unguarded xHCI polling statement.
# r52 deliberately suppresses stale xHCI polling only after the exact receiver
# has been physically rerouted. Accept that bounded equivalent while retaining
# every other inherited r36 gate.
r36p=here/'r36_cert_driver.py'
r36src=r36p.read_text()
r36old="    req('if xhci!=0 && volatile_read64(xhci+808)!=0 { xhci_hid_poll_continuous(xhci,input_state); }' in s,'r36 USB poll is not fail-open in desktop loop')"
r36new="    req(('if xhci!=0 && volatile_read64(xhci+808)!=0 { xhci_hid_poll_continuous(xhci,input_state); }' in s) or ('if xhci!=0 && volatile_read64(xhci+808)!=0 && volatile_read64(xhci+3696)!=1 && volatile_read64(xhci+3696)!=4 && volatile_read64(xhci+3696)!=5 { xhci_hid_poll_continuous(xhci,input_state); }' in s),'r36/r52 USB polling contract missing')"
if r36src.count(r36old)!=1: raise SystemExit(f'r52 r36 poll compatibility anchor count {r36src.count(r36old)}')
r36p.write_text(r36src.replace(r36old,r36new,1))

ns={'__name__':'__main__','__file__':str(base)}
try:
    exec(compile(src,str(base),'exec'),ns,ns)
except BaseException:
    out=Path('evidence'); out.mkdir(parents=True,exist_ok=True)
    (out/'R52-FAILURE.txt').write_text(traceback.format_exc())
    raise
