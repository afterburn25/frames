#!/usr/bin/env python3
from pathlib import Path
import traceback
here=Path(__file__).parent

# Preserve r56b's compatibility repair for the inherited r52/r54 physical-row
# assertions. r57 keeps the same route-before/after proof and the same state
# offsets while changing the final row semantics to child-HID descriptor data.
r52p=here/'r52_cert_driver.py'
r52src=r52p.read_text()
old_assert="    req('volatile_read64(xhci+3696)' in s and 'volatile_read64(xhci+3704)' in s and 'volatile_read64(xhci+3712)' in s and 'volatile_read64(xhci+3720)' in s and 'volatile_read64(xhci+3728)' in s and 'volatile_read64(xhci+3736)' in s and 'volatile_read64(xhci+3744)' in s and 'volatile_write64(xhci_state+3752,before_bit)' in s and 'volatile_write64(xhci_state+3760,after_bit)' in s,'r52 physical EHCI companion wake row/route proof missing')"
new_assert="    req(((('volatile_read64(xhci+3696)' in s and 'volatile_read64(xhci+3704)' in s and 'volatile_read64(xhci+3712)' in s and 'volatile_read64(xhci+3720)' in s and 'volatile_read64(xhci+3728)' in s and 'volatile_read64(xhci+3736)' in s and 'volatile_read64(xhci+3744)' in s) or ('volatile_read64(xhci+3792)' in s and 'volatile_read64(xhci+3800)' in s and 'volatile_read64(xhci+3808)' in s and 'volatile_read64(xhci+3816)' in s and 'volatile_read64(xhci+3824)' in s and 'volatile_read64(xhci+3832)' in s and 'volatile_read64(xhci+3840)' in s) or ('volatile_read64(xhci+3920)' in s and 'volatile_read64(xhci+3928)' in s and 'volatile_read64(xhci+3936)' in s and 'volatile_read64(xhci+3944)' in s and 'volatile_read64(xhci+3960)' in s and 'volatile_read64(xhci+3968)' in s and 'volatile_read64(xhci+3976)' in s)) and 'volatile_write64(xhci_state+3752,before_bit)' in s and 'volatile_write64(xhci_state+3760,after_bit)' in s),'r52/r54/r56 physical EHCI row/route proof missing')"
if r52src.count(old_assert)==1:
    r52p.write_text(r52src.replace(old_assert,new_assert,1))
elif r52src.count(new_assert)!=1:
    raise SystemExit('r57 r52 row compatibility anchor missing')

r54p=here/'r54_cert_driver.py'
r54src=r54p.read_text()
old_block="""if r52src.count(r52row_old)==1:
    r52p.write_text(r52src.replace(r52row_old,r52row_new,1))
elif r52src.count(r52row_new)!=1:
    raise SystemExit('r54 r52 physical-row compatibility anchor missing')"""
new_block="""if r52src.count(r52row_old)==1:
    r52p.write_text(r52src.replace(r52row_old,r52row_new,1))
elif r52src.count(r52row_new)==1:
    pass
elif 'volatile_read64(xhci+3928)' in r52src and 'volatile_write64(xhci_state+3752,before_bit)' in r52src and 'volatile_write64(xhci_state+3760,after_bit)' in r52src:
    pass
else:
    raise SystemExit('r54/r56/r57 r52 physical-row compatibility anchor missing')"""
if r54src.count(old_block)==1:
    r54p.write_text(r54src.replace(old_block,new_block,1))
elif r54src.count(new_block)!=1:
    raise SystemExit('r57 r54 idempotent compatibility anchor missing')

base=here/'r56_cert_driver.py'
src=base.read_text()
def one(old,new,label):
    global src
    n=src.count(old)
    if n!=1: raise SystemExit(f'r57 cert anchor {label} count {n}')
    src=src.replace(old,new,1)
def alln(old,new,count,label):
    global src
    n=src.count(old)
    if n!=count: raise SystemExit(f'r57 cert anchor {label} count {n}, expected {count}')
    src=src.replace(old,new)

one("'patch_v108_r56_ehci_second_hub_census.py'","'patch_v108_r57_ehci_tt_child_hid_probe.py'",'patch target')
one('kernel-r56.nx','kernel-r57.nx','kernel evidence target')
one('0000000000000000000000000000000000000000000000000000000000000000','bb436345a163096d52a04605c7bfb09cf756f90c06be6830b9ed130bb52e2c36','exact r57 kernel identity target')
one("'Frames-0.9.98-v108-r56-EHCI-Second-Hub-Census-Rufus-UEFI.iso'","'Frames-0.9.98-v108-r57-EHCI-TT-Child-HID-Probe-Rufus-UEFI.iso'",'ISO target')
one("'R56-SHA.txt'","'R57-SHA.txt'",'SHA evidence target')
one("'R25K-R56.patch'","'R25K-R57.patch'",'patch evidence target')
one("'FRAMES_V108_R56'","'FRAMES_V108_R57'",'ISO label target')
one('R56-AGGREGATE.json','R57-AGGREGATE.json','aggregate target')
one("'frames-0.9.98-v108-r56-ehci-second-hub-census'","'frames-0.9.98-v108-r57-ehci-tt-child-hid-probe'",'profile target')
one("'Frames 0.9.98 v108 r56 — EHCI Second Rate-Matching Hub Census'","'Frames 0.9.98 v108 r57 — EHCI TT Child HID Descriptor Probe'",'cert title target')
one('R56 PASS_VM_PENDING_PHYSICAL','R57 PASS_VM_PENDING_PHYSICAL','PASS target')
alln('R56-FAILURE.txt','R57-FAILURE.txt',2,'failure target')
one('r56 exact kernel identity mismatch','r57 exact kernel identity mismatch','identity label')
one("'physical_r55':'NOT_RELEASED_COMPILE_REJECTED_NX4004','physical_r55b':'PHYSICAL_HUB_DISCOVERY_STOPPED_STATE3','physical_r55b_telemetry':'R55_S3_N0_C0_E0_B0_F0_T0','physical_r55c':'PHYSICAL_EHCI1_INTEL_HUB6_ZERO_CONNECTED','physical_r55c_telemetry':'R5C_S7_N6_C0_E0_B0_F0_T3','physical_r56':'PENDING'","'physical_r55':'NOT_RELEASED_COMPILE_REJECTED_NX4004','physical_r55b':'PHYSICAL_HUB_DISCOVERY_STOPPED_STATE3','physical_r55b_telemetry':'R55_S3_N0_C0_E0_B0_F0_T0','physical_r55c':'PHYSICAL_EHCI1_INTEL_HUB6_ZERO_CONNECTED','physical_r55c_telemetry':'R5C_S7_N6_C0_E0_B0_F0_T3','physical_r56':'PHYSICAL_EHCI2_HUB8_CHILD_PORT2_FULL_SPEED','physical_r56_telemetry':'R56_S1_E2_N8_C1_B2_F2_T0','physical_r57':'PENDING'",'physical r56 result + r57 pending')
old_gate="    low=r56fn.lower(); req(all(x not in low for x in ['ehci_interrupt','interrupt endpoint','write(10)','nvme_submit_write','ahci_write']),'r56 exceeds bounded census/safety scope')"
new_gate=old_gate+"""
    req('fn v157_ehci_tt_control(xhci_state:u64,addr:u64,setupv:u64,length:u64) -> u64' in s,'r57 TT control helper missing')
    r57fn=s[s.index('fn v157_ehci_tt_control'):s.index('fn xhci_configure_boot_hid')]
    req('1208008704+(mps*65536)+(speed*4096)+addr' in r57fn,'r57 FS/LS control QH characteristics missing')
    req('1073807360+(port*8388608)' in r57fn,'r57 hub-address/port split characteristics missing')
    req('262947+(port*4294967296)' in r57fn and '1125899906842787+(port*4294967296)' in r57fn,'r57 downstream reset/status sequence missing')
    req('v157_ehci_tt_control(xhci_state,0,2251799830464128,8)' in r57fn,'r57 address-zero 8-byte descriptor probe missing')
    req('v157_ehci_tt_control(xhci_state,0,132352,0)' in r57fn,'r57 SET_ADDRESS 2 missing')
    req('v157_ehci_tt_control(xhci_state,2,5066549597570688,18)' in r57fn,'r57 full child device descriptor missing')
    req('usb_setup_value_v113(128,6,512,0)' in r57fn and 'total>256' in r57fn,'r57 bounded configuration descriptor probe missing')
    req('ic==3 && sub==1 && (pr==1 || pr==2)' in r57fn and 'ea>=128 && attr%4==3' in r57fn,'r57 boot-HID interrupt endpoint parser missing')
    req('set_flag(cmd,16)' not in r57fn,'r57 unexpectedly enables EHCI periodic schedule')
    low57=r57fn.lower(); req(all(x not in low57 for x in ['write(10)','nvme_submit_write','ahci_write','fat_write','block_write']),'r57 exceeds read-only child descriptor scope')
"""
one(old_gate,new_gate,'r57 TT/HID model gates')

ns={'__name__':'__main__','__file__':str(base)}
try:
    exec(compile(src,str(base),'exec'),ns,ns)
except BaseException:
    out=Path('evidence'); out.mkdir(parents=True,exist_ok=True)
    (out/'R57-FAILURE.txt').write_text(traceback.format_exc())
    raise
