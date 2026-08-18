#!/usr/bin/env python3
from pathlib import Path
import traceback
here=Path(__file__).parent
base=here/'r57_cert_driver.py'
src=base.read_text()

def one(old,new,label):
    global src
    n=src.count(old)
    if n!=1: raise SystemExit(f'r58 cert anchor {label} count {n}')
    src=src.replace(old,new,1)
def alln(old,new,count,label):
    global src
    n=src.count(old)
    if n!=count: raise SystemExit(f'r58 cert anchor {label} count {n}, expected {count}')
    src=src.replace(old,new)

one("'patch_v108_r57_ehci_tt_child_hid_probe.py'","'patch_v108_r58_ehci_composite_hid_census.py'",'patch target')
one('kernel-r57.nx','kernel-r58.nx','kernel evidence target')
one('bb436345a163096d52a04605c7bfb09cf756f90c06be6830b9ed130bb52e2c36','0000000000000000000000000000000000000000000000000000000000000000','provisional r58 identity target')
one("'Frames-0.9.98-v108-r57-EHCI-TT-Child-HID-Probe-Rufus-UEFI.iso'","'Frames-0.9.98-v108-r58-EHCI-Composite-HID-Census-Rufus-UEFI.iso'",'ISO target')
one("'R57-SHA.txt'","'R58-SHA.txt'",'SHA evidence target')
one("'R25K-R57.patch'","'R25K-R58.patch'",'patch evidence target')
one("'FRAMES_V108_R57'","'FRAMES_V108_R58'",'ISO label target')
one('R57-AGGREGATE.json','R58-AGGREGATE.json','aggregate target')
one("'frames-0.9.98-v108-r57-ehci-tt-child-hid-probe'","'frames-0.9.98-v108-r58-ehci-composite-hid-census'",'profile target')
one("'Frames 0.9.98 v108 r57 — EHCI TT Child HID Descriptor Probe'","'Frames 0.9.98 v108 r58 — EHCI Composite HID Interface Census'",'cert title target')
one('R57 PASS_VM_PENDING_PHYSICAL','R58 PASS_VM_PENDING_PHYSICAL','PASS target')
alln('R57-FAILURE.txt','R58-FAILURE.txt',2,'failure target')
one('r57 exact kernel identity mismatch','r58 exact kernel identity mismatch','identity label')
one("'physical_r56':'PHYSICAL_EHCI2_HUB8_CHILD_PORT2_FULL_SPEED','physical_r56_telemetry':'R56_S1_E2_N8_C1_B2_F2_T0','physical_r57':'PENDING'","'physical_r56':'PHYSICAL_EHCI2_HUB8_CHILD_PORT2_FULL_SPEED','physical_r56_telemetry':'R56_S1_E2_N8_C1_B2_F2_T0','physical_r57':'PHYSICAL_TT_CHILD_ENUM_BOOT_HID_PROTOCOL1','physical_r57_telemetry':'R57_S1_P2_M8_V9354_D4267_R1_E130','physical_r58':'PENDING'",'physical r57 result + r58 pending')
anchor="    low57=r57fn.lower(); req(all(x not in low57 for x in ['write(10)','nvme_submit_write','ahci_write','fat_write','block_write']),'r57 exceeds read-only child descriptor scope')"
extra=anchor+"""
    req('hid_count=hid_count+1' in r57fn,'r58 HID interface census counter missing')
    req('active_proto==1 && k_ep==0' in r57fn and 'active_proto==2 && m_ep==0' in r57fn,'r58 keyboard/mouse split endpoint capture missing')
    req('volatile_write64(xhci_state+3936,k_ep)' in r57fn and 'volatile_write64(xhci_state+3944,m_ep)' in r57fn,'r58 keyboard/mouse endpoint telemetry missing')
    req('volatile_write64(xhci_state+3952,m_iface)' in r57fn and 'volatile_write64(xhci_state+3960,m_mps)' in r57fn and 'volatile_write64(xhci_state+3968,hid_count)' in r57fn,'r58 mouse interface/MPS/count telemetry missing')
    req('if m_ep==0' in r57fn and 'volatile_write64(xhci_state+3920,23)' in r57fn,'r58 explicit no-mouse state missing')
    req('R58' not in s,'r58 textual label unexpectedly embedded as raw string')
"""
one(anchor,extra,'r58 composite HID model gates')

ns={'__name__':'__main__','__file__':str(base)}
try:
    exec(compile(src,str(base),'exec'),ns,ns)
except BaseException:
    out=Path('evidence'); out.mkdir(parents=True,exist_ok=True)
    (out/'R58-FAILURE.txt').write_text(traceback.format_exc())
    raise
