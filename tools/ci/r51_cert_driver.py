#!/usr/bin/env python3
from pathlib import Path
import traceback
here=Path(__file__).parent
base=here/'r50_cert_driver.py'
src=base.read_text()

def one(old,new,label):
    global src
    n=src.count(old)
    if n!=1: raise SystemExit(f'r51 cert anchor {label} count {n}')
    src=src.replace(old,new,1)

def alln(old,new,count,label):
    global src
    n=src.count(old)
    if n!=count: raise SystemExit(f'r51 cert anchor {label} count {n}, expected {count}')
    src=src.replace(old,new)

one("'patch_v108_r50_device_endpoint_status_proof.py'","'patch_v108_r51_intel_ehci_route_probe.py'",'patch target')
one('kernel-r50.nx','kernel-r51.nx','kernel evidence target')
one('30d8239eb1c91a5b70246744d856e1a7aae77360baeaa024033fb135070fd6f1','25f02ab7852059b40c9387f0a139b8407a0e99dbc25038a917594a5f9526975a','exact kernel identity target')
one("'Frames-0.9.98-v108-r50-USB-Device-Endpoint-Status-Proof-Rufus-UEFI.iso'","'Frames-0.9.98-v108-r51-Intel-EHCI-Route-Probe-Rufus-UEFI.iso'",'ISO target')
one("'R50-SHA.txt'","'R51-SHA.txt'",'SHA evidence target')
one("'R25K-R50.patch'","'R25K-R51.patch'",'patch evidence target')
one("'FRAMES_V108_R50'","'FRAMES_V108_R51'",'ISO label target')
one('R50-AGGREGATE.json','R51-AGGREGATE.json','aggregate target')
one("'frames-0.9.98-v108-r50-usb-device-endpoint-status-proof'","'frames-0.9.98-v108-r51-intel-ehci-route-probe'",'profile target')
one("'Frames 0.9.98 v108 r50 — USB Device Endpoint Status Proof'","'Frames 0.9.98 v108 r51 — Intel EHCI Route Probe'",'cert title target')
one('R50 PASS_VM_PENDING_PHYSICAL','R51 PASS_VM_PENDING_PHYSICAL','PASS target')
alln('R50-FAILURE.txt','R51-FAILURE.txt',2,'failure target')
one('r50 exact kernel identity mismatch','r51 exact kernel identity mismatch','identity label')

one("'physical_r50':'PENDING'","'physical_r50':'PHYSICAL_DEVICE_CONFIG1_ALT0_MOUSE_EP130_NOT_HALTED_FULLSPEED_NO_INTERRUPT_REPORT','physical_r50_telemetry':'R50_C1_I0_E130_H0_X0_S1_P1','physical_r51':'PENDING'",'physical r50 evidence and r51 pending')

old_row="""    req('volatile_read64(xhci+3624)' in s and 'volatile_read64(xhci+3632)' in s and 'volatile_read64(xhci+3640)' in s and 'volatile_read64(xhci+3648)' in s and 'volatile_read64(xhci+3656)' in s and 'volatile_read64(xhci+3672)' in s and 'volatile_read64(xhci+3680)' in s,'r50 physical device-status row missing')"""
new_row="""    req('volatile_read64(xhci+3696)' in s and 'volatile_read64(xhci+3704)' in s and 'volatile_read64(xhci+3712)' in s and 'volatile_read64(xhci+3720)' in s and 'volatile_read64(xhci+3728)' in s and 'volatile_read64(xhci+3736)' in s and 'volatile_read64(xhci+3744)' in s,'r51 physical Intel EHCI route row missing')"""
one(old_row,new_row,'r51 physical row gate')

anchor="    req('v135_hid_control_fallback_poll' not in cfg50,'r50 reintroduced continuous GET_REPORT fallback')"
extra=anchor+"""
    r51fn=s[s.index('fn v151_intel_ehci_route_probe'):s.index('fn xhci_configure_boot_hid')]
    req('vendor!=32902 || device!=35889 || vid!=9354 || pid!=4267 || sw_port!=2 || speed!=1 || ep!=130' in r51fn,'r51 exact Intel/receiver/port/endpoint guard missing')
    req('let u2m=pci_cfg_read32(bus,dev,fun,212)' in r51fn and 'let before=pci_cfg_read32(bus,dev,fun,208)' in r51fn,'r51 Intel USB2 route mask/read proof missing')
    req('pci_cfg_write32(bdf,208,before-mask)' in r51fn and r51fn.count('pci_cfg_write32')==1,'r51 route mutation is not single-bit bounded')
    req('v108_pci_nth_ehci_v121(ord)' in r51fn and 'volatile_read32(op+68+((p-1)*4))' in r51fn,'r51 EHCI companion/PORTSC proof missing')
    req('volatile_write64(xhci_state+3696,1)' in r51fn and 'volatile_write64(xhci_state+3744,found_ps)' in r51fn,'r51 route telemetry storage missing')
    req('volatile_read64(xhci+3696)!=1' in s,'r51 stale xHCI HID path is not gated after successful reroute')
    req('v151_intel_ehci_route_probe(xhci)' in s,'r51 route probe is not invoked')
"""
one(anchor,extra,'r51 guarded EHCI alternate-path model gates')

ns={'__name__':'__main__','__file__':str(base)}
try:
    exec(compile(src,str(base),'exec'),ns,ns)
except BaseException:
    out=Path('evidence'); out.mkdir(parents=True,exist_ok=True)
    (out/'R51-FAILURE.txt').write_text(traceback.format_exc())
    raise
