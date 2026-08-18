#!/usr/bin/env python3
from pathlib import Path
import traceback
here=Path(__file__).parent

# r54 preserves r53's sanitized EHCI per-port power operation. Keep the
# inherited compatibility adaptation before executing the r53-derived chain.
r52p=here/'r52_cert_driver.py'
r52src=r52p.read_text()
r52old="    req('set_flag(ps,4096)' in r52fn,'r52 per-port power-on proof missing')"
r52new="    req(('set_flag(ps,4096)' in r52fn) or ('set_flag(pw,4096)' in r52fn),'r52/r53/r54 per-port power-on proof missing')"
if r52src.count(r52old)==1:
    r52p.write_text(r52src.replace(r52old,r52new,1))
elif r52src.count(r52new)!=1:
    raise SystemExit('r54 r52 power compatibility anchor missing')

# r54 replaces the visible r52/r53 bottom telemetry row, but the underlying
# r52 route-state fields remain present in the classifier. Adapt only the
# historical on-screen row-shape assertion to accept the new r54 overlay while
# retaining both route-write evidence fields.
r52src=r52p.read_text()
r52row_old="    req('volatile_read64(xhci+3696)' in s and 'volatile_read64(xhci+3704)' in s and 'volatile_read64(xhci+3712)' in s and 'volatile_read64(xhci+3720)' in s and 'volatile_read64(xhci+3728)' in s and 'volatile_read64(xhci+3736)' in s and 'volatile_read64(xhci+3744)' in s and 'volatile_write64(xhci_state+3752,before_bit)' in s and 'volatile_write64(xhci_state+3760,after_bit)' in s,'r52 physical EHCI companion wake row/route proof missing')"
r52row_new="    req(((('volatile_read64(xhci+3696)' in s and 'volatile_read64(xhci+3704)' in s and 'volatile_read64(xhci+3712)' in s and 'volatile_read64(xhci+3720)' in s and 'volatile_read64(xhci+3728)' in s and 'volatile_read64(xhci+3736)' in s and 'volatile_read64(xhci+3744)' in s) or ('volatile_read64(xhci+3792)' in s and 'volatile_read64(xhci+3800)' in s and 'volatile_read64(xhci+3808)' in s and 'volatile_read64(xhci+3816)' in s and 'volatile_read64(xhci+3824)' in s and 'volatile_read64(xhci+3832)' in s and 'volatile_read64(xhci+3840)' in s)) and 'volatile_write64(xhci_state+3752,before_bit)' in s and 'volatile_write64(xhci_state+3760,after_bit)' in s),'r52/r54 physical EHCI row/route proof missing')"
if r52src.count(r52row_old)==1:
    r52p.write_text(r52src.replace(r52row_old,r52row_new,1))
elif r52src.count(r52row_new)!=1:
    raise SystemExit('r54 r52 physical-row compatibility anchor missing')

base=here/'r53_cert_driver.py'
src=base.read_text()

def one(old,new,label):
    global src
    n=src.count(old)
    if n!=1: raise SystemExit(f'r54 cert anchor {label} count {n}')
    src=src.replace(old,new,1)

def alln(old,new,count,label):
    global src
    n=src.count(old)
    if n!=count: raise SystemExit(f'r54 cert anchor {label} count {n}, expected {count}')
    src=src.replace(old,new)

one("'patch_v108_r53_ehci_port_reset_companion_classifier.py'","'patch_v108_r54_ehci_root_descriptor_probe.py'",'patch target')
one('kernel-r53.nx','kernel-r54.nx','kernel evidence target')
one('TBD_R53_SHA','ebcf7baf18422cc72804eec9e18a317ed5daf1baee65330528be66c07d599c19','exact kernel identity target')
one("'Frames-0.9.98-v108-r53-EHCI-Port-Reset-Companion-Classifier-Rufus-UEFI.iso'","'Frames-0.9.98-v108-r54-EHCI-Root-Descriptor-Probe-Rufus-UEFI.iso'",'ISO target')
one("'R53-SHA.txt'","'R54-SHA.txt'",'SHA evidence target')
one("'R25K-R53.patch'","'R25K-R54.patch'",'patch evidence target')
one("'FRAMES_V108_R53'","'FRAMES_V108_R54'",'ISO label target')
one('R53-AGGREGATE.json','R54-AGGREGATE.json','aggregate target')
one("'frames-0.9.98-v108-r53-ehci-port-reset-companion-classifier'","'frames-0.9.98-v108-r54-ehci-root-descriptor-probe'",'profile target')
one("'Frames 0.9.98 v108 r53 — EHCI Port Reset + Companion Classifier'","'Frames 0.9.98 v108 r54 — EHCI Root Device Descriptor Probe'",'cert title target')
one('R53 PASS_VM_PENDING_PHYSICAL','R54 PASS_VM_PENDING_PHYSICAL','PASS target')
alln('R53-FAILURE.txt','R54-FAILURE.txt',2,'failure target')
one('r53 exact kernel identity mismatch','r54 exact kernel identity mismatch','identity label')

one("'physical_r52':'PHYSICAL_EHCI1_PORT1_VISIBLE_BOTH_EHCI_RUNNING_CONFIGFLAG','physical_r52_telemetry':'R52_W1_E1_P1_C1_R2_F2_V6147','physical_r53':'PENDING'",
    "'physical_r52':'PHYSICAL_EHCI1_PORT1_VISIBLE_BOTH_EHCI_RUNNING_CONFIGFLAG','physical_r52_telemetry':'R52_W1_E1_P1_C1_R2_F2_V6147','physical_r53':'PHYSICAL_EHCI1_PORT1_RETAINED_ENABLED_NO_COMPANIONS','physical_r53_telemetry':'R53_S1_E1_P1_D1_O0_U0_H0','physical_r54':'PENDING'",
    'physical r53 evidence and r54 pending')

# r53's inherited no-schedule model must end before the new r54 function.
one("s[s.index('fn v153_intel_ehci_port_reset_companion_classifier'):s.index('fn xhci_configure_boot_hid')]",
    "s[s.index('fn v153_intel_ehci_port_reset_companion_classifier'):s.index('fn v154_ehci_root_descriptor_probe')]",
    'r53 model slice boundary')

# Add r54-specific single-shot asynchronous control-transfer gates after the
# r53 no-host-scheduling assertion. These gates certify the new function only.
anchor="    req(all(x not in r52fn.lower() for x in ['periodiclistbase','asynclistaddr','qtd','qh_link','ehci_submit','ehci_transfer']),'r53 unexpectedly adds host transfer scheduling')"
extra=anchor+"""
    r54fn=s[s.index('fn v154_ehci_root_descriptor_probe'):s.index('fn xhci_configure_boot_hid')]
    req('pci_enable_mmio_busmaster(ebdf)' in r54fn,'r54 EHCI PCI busmaster enable missing')
    req('volatile_write64(setup,5066549597570688)' in r54fn,'r54 GET_DESCRIPTOR(Device) setup packet missing')
    req('volatile_write32(qh+0,qlo+2)' in r54fn and 'volatile_write32(qh+4,1077993472)' in r54fn and 'volatile_write32(qh+8,1073741824)' in r54fn,'r54 asynchronous QH construction missing')
    req('volatile_write32(qs+8,528000)' in r54fn and 'volatile_write32(qd+8,2148666752)' in r54fn and 'volatile_write32(qt+8,2147519616)' in r54fn,'r54 SETUP/DATA/STATUS qTD chain missing')
    req('volatile_write32(op+24,qlo)' in r54fn,'r54 ASYNCLISTADDR programming missing')
    req(r54fn.count('cmd=set_flag(cmd,32)')==1 and r54fn.count('cmd=clear_flag(cmd,32)')>=2,'r54 asynchronous schedule is not single-shot bounded')
    req('cmd=clear_flag(cmd,16)' in r54fn and 'set_flag(cmd,16)' not in r54fn,'r54 periodic schedule is not held disabled')
    req('volatile_write32(op+8,0)' in r54fn,'r54 EHCI interrupts are not explicitly disabled')
    req('let cls=volatile_read8(data+4)' in r54fn and 'let vid=volatile_read8(data+8)+(volatile_read8(data+9)*256)' in r54fn and 'let pid=volatile_read8(data+10)+(volatile_read8(data+11)*256)' in r54fn,'r54 device descriptor parse missing')
    req('v154_ehci_root_descriptor_probe(xhci,phys_state)' in s and 'volatile_read64(xhci+3696)==1' in s,'r54 descriptor probe is not gated by physical r53 EHCI-retained state')
    req(all(x not in r54fn.lower() for x in ['set_configuration','set_address','periodiclistbase','nvme_submit_write','ahci_write','write(10)']),'r54 exceeds bounded root-descriptor scope')
"""
one(anchor,extra,'r54 descriptor model gates')

ns={'__name__':'__main__','__file__':str(base)}
try:
    exec(compile(src,str(base),'exec'),ns,ns)
except BaseException:
    out=Path('evidence'); out.mkdir(parents=True,exist_ok=True)
    (out/'R54-FAILURE.txt').write_text(traceback.format_exc())
    raise
