#!/usr/bin/env python3
from pathlib import Path
import traceback
here=Path(__file__).parent

# Extend the inherited r52 display-shape compatibility through the r59 runtime
# report row while retaining the original EHCI route-before/after proof.
r57p=here/'r57_cert_driver.py'
r57src=r57p.read_text()
old_compat="or ('volatile_read64(xhci+3920)' in s and 'volatile_read64(xhci+3928)' in s and 'volatile_read64(xhci+3936)' in s and 'volatile_read64(xhci+3944)' in s and 'volatile_read64(xhci+3952)' in s and 'volatile_read64(xhci+3960)' in s and 'volatile_read64(xhci+3968)' in s)) and 'volatile_write64(xhci_state+3752,before_bit)' in s"
new_compat="or ('volatile_read64(xhci+3920)' in s and 'volatile_read64(xhci+3928)' in s and 'volatile_read64(xhci+3936)' in s and 'volatile_read64(xhci+3944)' in s and 'volatile_read64(xhci+3952)' in s and 'volatile_read64(xhci+3960)' in s and 'volatile_read64(xhci+3968)' in s) or ('volatile_read64(xhci+4056)' in s and 'volatile_read64(xhci+4064)' in s and 'volatile_read64(xhci+4072)' in s and 'volatile_read64(xhci+4080)' in s)) and 'volatile_write64(xhci_state+3752,before_bit)' in s"
if r57src.count(old_compat)==1:
    r57p.write_text(r57src.replace(old_compat,new_compat,1))
elif r57src.count(new_compat)!=1:
    raise SystemExit('r59 r57/r52 row compatibility anchor missing')

# r56 also had a display-only E/N/C overlay assertion. r59 retains the
# underlying second-controller census code but replaces that visible row.
r56p=here/'r56_cert_driver.py'
r56src=r56p.read_text()
old_r56="    req('volatile_read64(xhci+3928)' in s and 'volatile_read64(xhci+3936)' in s and 'volatile_read64(xhci+3944)' in s,'r56 E/N/C physical overlay fields missing')"
new_r56="    req((('volatile_read64(xhci+3928)' in s and 'volatile_read64(xhci+3936)' in s and 'volatile_read64(xhci+3944)' in s) or ('volatile_read64(xhci+4056)' in s and 'volatile_read64(xhci+4064)' in s and 'volatile_read64(xhci+4072)' in s and 'volatile_read64(xhci+4080)' in s)),'r56 E/N/C physical overlay fields missing')"
if r56src.count(old_r56)==1:
    r56p.write_text(r56src.replace(old_r56,new_r56,1))
elif r56src.count(new_r56)!=1:
    raise SystemExit('r59 r56 overlay compatibility anchor missing')

base=here/'r58_cert_driver.py'
src=base.read_text()

def one(old,new,label):
    global src
    n=src.count(old)
    if n!=1: raise SystemExit(f'r59 cert anchor {label} count {n}')
    src=src.replace(old,new,1)
def alln(old,new,count,label):
    global src
    n=src.count(old)
    if n!=count: raise SystemExit(f'r59 cert anchor {label} count {n}, expected {count}')
    src=src.replace(old,new)

one("'patch_v108_r58_ehci_composite_hid_census.py'","'patch_v108_r59_ehci_mouse_periodic_report_probe.py'",'patch target')
one('kernel-r58.nx','kernel-r59.nx','kernel evidence target')
one('e8edf7b8d38982b27b997258230ee5f0a51ebd46586bb6cfca679a00aae16f49','38544595b9ce8c1d7775319247b9d544adadf16b2526d6ca9dbfb41fa0f7a9b7','exact r59 identity target')
one("'Frames-0.9.98-v108-r58-EHCI-Composite-HID-Census-Rufus-UEFI.iso'","'Frames-0.9.98-v108-r59-EHCI-Mouse-Periodic-Report-Probe-Rufus-UEFI.iso'",'ISO target')
one("'R58-SHA.txt'","'R59-SHA.txt'",'SHA evidence target')
one("'R25K-R58.patch'","'R25K-R59.patch'",'patch evidence target')
one("'FRAMES_V108_R58'","'FRAMES_V108_R59'",'ISO label target')
one('R58-AGGREGATE.json','R59-AGGREGATE.json','aggregate target')
one("'frames-0.9.98-v108-r58-ehci-composite-hid-census'","'frames-0.9.98-v108-r59-ehci-mouse-periodic-report-probe'",'profile target')
one("'Frames 0.9.98 v108 r58 — EHCI Composite HID Interface Census'","'Frames 0.9.98 v108 r59 — EHCI Mouse Periodic Report Probe'",'cert title target')
one('R58 PASS_VM_PENDING_PHYSICAL','R59 PASS_VM_PENDING_PHYSICAL','PASS target')
alln('R58-FAILURE.txt','R59-FAILURE.txt',2,'failure target')
one('r58 exact kernel identity mismatch','r59 exact kernel identity mismatch','identity label')
one("'physical_r56':'PHYSICAL_EHCI2_HUB8_CHILD_PORT2_FULL_SPEED','physical_r56_telemetry':'R56_S1_E2_N8_C1_B2_F2_T0','physical_r57':'PHYSICAL_TT_CHILD_ENUM_BOOT_HID_PROTOCOL1','physical_r57_telemetry':'R57_S1_P2_M8_V9354_D4267_R1_E130','physical_r58':'PENDING'",
    "'physical_r56':'PHYSICAL_EHCI2_HUB8_CHILD_PORT2_FULL_SPEED','physical_r56_telemetry':'R56_S1_E2_N8_C1_B2_F2_T0','physical_r57':'PHYSICAL_TT_CHILD_ENUM_BOOT_HID_PROTOCOL1','physical_r57_telemetry':'R57_S1_P2_M8_V9354_D4267_R1_E130','physical_r58':'PHYSICAL_COMPOSITE_HID_MOUSE_ENDPOINT_DISCOVERED','physical_r58_telemetry':'R58_S1_P2_K129_M130_I0_L8_C2','physical_r59':'PENDING'",
    'physical r58 result + r59 pending')
anchor="    req('R58' not in s,'r58 textual label unexpectedly embedded as raw string')"
extra=anchor+"""
    r59fn=s[s.index('fn v159_ehci_mouse_periodic_arm'):s.index('fn v135_hid_control_fallback_prepare')]
    req('v157_ehci_tt_control(xhci_state,2,setcfg,0)' in r59fn,'r59 SET_CONFIGURATION through TT missing')
    req('v157_ehci_tt_control(xhci_state,2,setproto,0)' in r59fn,'r59 HID SET_PROTOCOL boot request missing')
    req('alloc_dma_page(phys_state,4)' in r59fn,'r59 dedicated periodic frame page missing')
    req('volatile_write32(op+20,flo)' in r59fn,'r59 PERIODICLISTBASE programming missing')
    req('while i<1024' in r59fn and 'i%mint==0' in r59fn,'r59 interval-shaped 1024 frame list missing')
    req('info2=1090591745' in r59fn,'r59 EHCI split S-mask/C-mask hub1 port2 capabilities missing')
    req('token=527744' in r59fn and 'volatile_write32(qtd+8,527744)' in r59fn,'r59 8-byte interrupt-IN qTD arm/rearm missing')
    req('cmd=set_flag(cmd,16)' in r59fn and 'cmd=clear_flag(cmd,16)' in r59fn,'r59 bounded periodic schedule enable/disable missing')
    req('(tok/128)%2' in r59fn and 'let errs=(tok/4)%32' in r59fn,'r59 qTD completion/error polling missing')
    req('volatile_write64(xhci_state+4064' in r59fn and 'volatile_write64(xhci_state+4072' in r59fn and 'volatile_write64(xhci_state+4080' in r59fn and 'volatile_write64(xhci_state+4088' in r59fn,'r59 raw report telemetry state missing')
    req('r59_redraw=v159_ehci_mouse_periodic_tick(xhci)' in s and 'var telemetry_redraw:u64=r59_redraw' in s,'r59 live desktop polling/redraw hook missing')
    req('volatile_read64(xhci+4056)' in s and 'volatile_read64(xhci+4064)' in s and 'volatile_read64(xhci+4072)' in s and 'volatile_read64(xhci+4080)' in s,'r59 visible runtime telemetry row missing')
    low59=r59fn.lower(); req(all(x not in low59 for x in ['write(10)','nvme_submit_write','ahci_write','fat_write','block_write','input_push(']),'r59 exceeds raw diagnostic/safety scope')
    req('R59' not in s,'r59 textual label unexpectedly embedded as raw string')
"""
one(anchor,extra,'r59 periodic report model gates')

ns={'__name__':'__main__','__file__':str(base)}
try:
    exec(compile(src,str(base),'exec'),ns,ns)
except BaseException:
    out=Path('evidence'); out.mkdir(parents=True,exist_ok=True)
    (out/'R59-FAILURE.txt').write_text(traceback.format_exc())
    raise
