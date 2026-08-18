#!/usr/bin/env python3
from pathlib import Path
import traceback
here=Path(__file__).parent
base=here/'r52_cert_driver.py'
src=base.read_text()

def one(old,new,label):
    global src
    n=src.count(old)
    if n!=1: raise SystemExit(f'r53 cert anchor {label} count {n}')
    src=src.replace(old,new,1)

def alln(old,new,count,label):
    global src
    n=src.count(old)
    if n!=count: raise SystemExit(f'r53 cert anchor {label} count {n}, expected {count}')
    src=src.replace(old,new)

one("'patch_v108_r52_intel_ehci_companion_wake.py'","'patch_v108_r53_ehci_port_reset_companion_classifier.py'",'patch target')
one('kernel-r52.nx','kernel-r53.nx','kernel evidence target')
one('7f854b564c7ddee71382ebe616ec1dd70dad3ce679684b1babd1550ac40ffcf3','TBD_R53_SHA','exact kernel identity target')
one("'Frames-0.9.98-v108-r52-Intel-EHCI-Companion-Wake-Proof-Rufus-UEFI.iso'","'Frames-0.9.98-v108-r53-EHCI-Port-Reset-Companion-Classifier-Rufus-UEFI.iso'",'ISO target')
one("'R52-SHA.txt'","'R53-SHA.txt'",'SHA evidence target')
one("'R25K-R52.patch'","'R25K-R53.patch'",'patch evidence target')
one("'FRAMES_V108_R52'","'FRAMES_V108_R53'",'ISO label target')
one('R52-AGGREGATE.json','R53-AGGREGATE.json','aggregate target')
one("'frames-0.9.98-v108-r52-intel-ehci-companion-wake-proof'","'frames-0.9.98-v108-r53-ehci-port-reset-companion-classifier'",'profile target')
one("'Frames 0.9.98 v108 r52 — Intel EHCI Companion Wake Proof'","'Frames 0.9.98 v108 r53 — EHCI Port Reset + Companion Classifier'",'cert title target')
one('R52 PASS_VM_PENDING_PHYSICAL','R53 PASS_VM_PENDING_PHYSICAL','PASS target')
alln('R52-FAILURE.txt','R53-FAILURE.txt',2,'failure target')
one('r52 exact kernel identity mismatch','r53 exact kernel identity mismatch','identity label')
one("'physical_r52':'PENDING'","'physical_r52':'PHYSICAL_EHCI1_PORT1_VISIBLE_BOTH_EHCI_RUNNING_CONFIGFLAG','physical_r52_telemetry':'R52_W1_E1_P1_C1_R2_F2_V6147','physical_r53':'PENDING'",'physical r52 evidence and r53 pending')

one("s[s.index('fn v152_intel_ehci_companion_wake_probe'):s.index('fn xhci_configure_boot_hid')]","s[s.index('fn v153_intel_ehci_port_reset_companion_classifier'):s.index('fn xhci_configure_boot_hid')]",'model function slice')
one("'volatile_read64(xhci+3696)!=1 && volatile_read64(xhci+3696)!=4 && volatile_read64(xhci+3696)!=5' in s","'volatile_read64(xhci+3760)!=0' in s",'stale xHCI suppression gate')
one("'v152_intel_ehci_companion_wake_probe(xhci)' in s","'v153_intel_ehci_port_reset_companion_classifier(xhci)' in s",'probe invocation gate')
# The r52 model still requires wake/route safety. Add r53-specific reset and
# companion classification requirements immediately after that inherited block.
anchor="    req(all(x not in lower for x in ['periodiclistbase','asynclistaddr','ehci_submit','ehci_transfer']),'r52 unexpectedly adds EHCI transfer/schedule programming')"
extra=anchor+"""
    req('wr=set_flag(wr,256)' in r52fn and 'wr=clear_flag(wr,256)' in r52fn,'r53 bounded EHCI port reset proof missing')
    req('ow=set_flag(ow,8192)' in r52fn and 'let ncc=(hcs/4096)%16' in r52fn,'r53 standard EHCI companion ownership classification missing')
    req('v153_pci_count_usb_prog(0)' in r52fn and 'v153_pci_count_usb_prog(16)' in r52fn,'r53 UHCI/OHCI companion inventory missing')
    req('volatile_write64(xhci_state+3768,done)' in r52fn and 'volatile_write64(xhci_state+3776,ncc)' in r52fn and 'volatile_write64(xhci_state+3784,line)' in r52fn,'r53 post-reset evidence storage missing')
    req(all(x not in r52fn.lower() for x in ['periodiclistbase','asynclistaddr','qtd','qh_link','ehci_submit','ehci_transfer']),'r53 unexpectedly adds host transfer scheduling')
"""
one(anchor,extra,'r53 model gates')

# Update the historical r36 compatibility variant embedded in the inherited
# r52 driver so it accepts the exact route-bit keyed suppression used by r53.
one("if xhci!=0 && volatile_read64(xhci+808)!=0 && volatile_read64(xhci+3696)!=1 && volatile_read64(xhci+3696)!=4 && volatile_read64(xhci+3696)!=5 { xhci_hid_poll_continuous(xhci,input_state); }","if xhci!=0 && volatile_read64(xhci+808)!=0 && volatile_read64(xhci+3760)!=0 { xhci_hid_poll_continuous(xhci,input_state); }",'r36 compatibility polling variant')

ns={'__name__':'__main__','__file__':str(base)}
try:
    exec(compile(src,str(base),'exec'),ns,ns)
except BaseException:
    out=Path('evidence'); out.mkdir(parents=True,exist_ok=True)
    (out/'R53-FAILURE.txt').write_text(traceback.format_exc())
    raise
