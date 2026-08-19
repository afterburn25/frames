#!/usr/bin/env python3
from pathlib import Path
import hashlib, traceback

here=Path(__file__).parent
base=here/'r61_cert_driver.py'
src=base.read_text()

def repl(old,new,label,min_count=1):
    global src
    n=src.count(old)
    if n<min_count:
        raise SystemExit(f'r62 cert anchor {label} count {n}, expected >= {min_count}')
    src=src.replace(old,new)

repl("'patch_v108_r61_altsetting_reset_tt_boot_mouse.py'","'patch_v108_r62_hid_control_poll_mouse.py'",'patch target')
repl('kernel-r61.nx','kernel-r62.nx','kernel evidence target',2)
repl('5903008c46c2d6e4be84a5eab7fa44a322ba7a594ff8cb810fcbe277e716d9ee','1123e519510917e832d660d21faf8955c7f21ab174283d04930fb378f96569c6','exact r62 identity target',2)
repl("'Frames-0.9.98-v108-r61-AltSetting-RESET-TT-Boot-Mouse-Rufus-UEFI.iso'","'Frames-0.9.98-v108-r62-HID-Control-Poll-Mouse-Recovery-Rufus-UEFI.iso'",'ISO target')
repl("'R61-SHA.txt'","'R62-SHA.txt'",'SHA evidence target')
repl("'R25K-R61.patch'","'R25K-R62.patch'",'patch evidence target')
repl("'FRAMES_V108_R61'","'FRAMES_V108_R62'",'ISO label target')
repl('R61-AGGREGATE.json','R62-AGGREGATE.json','aggregate target')
repl("'frames-0.9.98-v108-r61-altsetting-reset-tt-boot-mouse'","'frames-0.9.98-v108-r62-hid-control-poll-mouse-recovery'",'profile target')
repl("'Frames 0.9.98 v108 r61 — Alternate Setting + RESET_TT Boot Mouse Integration'","'Frames 0.9.98 v108 r62 — HID GET_REPORT Control-Poll Mouse Recovery'",'cert title target')
repl('R61 PASS_VM_PENDING_PHYSICAL','R62 PASS_VM_PENDING_PHYSICAL','PASS target')
repl("'R61-FAILURE.txt'","'R62-FAILURE.txt'",'failure target',2)
repl('r61 exact kernel identity mismatch','r62 exact kernel identity mismatch','identity label')
old_phys="'physical_r59h':'PENDING','physical_r60':'NOT_PHYSICALLY_TESTED_SUPERSEDED_BY_R61','physical_r59t2':'PHYSICAL_ASYNC_SPLIT_ACTIVE_NO_PROGRESS','physical_r59t2_telemetry':'R5T_G270351_N0_B0_0_B1_0_B2_0_B3_0','physical_r61':'PENDING'"
new_phys="'physical_r59h':'PENDING','physical_r60':'NOT_PHYSICALLY_TESTED_SUPERSEDED_BY_R61','physical_r59t2':'PHYSICAL_ASYNC_SPLIT_ACTIVE_NO_PROGRESS','physical_r59t2_telemetry':'R5T_G270351_N0_B0_0_B1_0_B2_0_B3_0','physical_r61':'PHYSICAL_ALT0_RESET_TT_OK_PERIODIC_ACTIVE_NO_PROGRESS','physical_r61_telemetry':'R61_A0_I0_T1_G270343_N0_B0_X0','physical_r62':'PENDING'"
repl(old_phys,new_phys,'physical evidence handoff')

ns={'__name__':'__main__','__file__':str(base)}
try:
    exec(compile(src,str(base),'exec'),ns,ns)
    k=Path('evidence/kernel-r62.nx')
    if not k.exists(): raise SystemExit('r62 evidence kernel missing')
    s=k.read_text()
    if hashlib.sha256(s.encode()).hexdigest()!='1123e519510917e832d660d21faf8955c7f21ab174283d04930fb378f96569c6':
        raise SystemExit('r62 evidence kernel SHA mismatch')
    ast=s.index('fn v159_ehci_mouse_periodic_arm')
    tst=s.index('fn v159_ehci_mouse_periodic_tick')
    rst=s.index('fn v162_r61_periodic_reference_arm')
    arm=s[ast:tst]
    tick=s[tst:rst]
    for q in (
        'let full_setup=usb_setup_length_v113(usb_setup_value_v113(128,6,512,0),total)',
        'let setproto=33+(11*256)+(mif*4294967296)',
        'let resettt=35+(9*256)+(ttidx*4294967296)',
        'cmd=clear_flag(cmd,32); cmd=clear_flag(cmd,16)',
        'volatile_write64(xhci_state+4048,0)',
    ):
        if q not in arm: raise SystemExit('r62 quiescent preflight witness missing '+q)
    for q in (
        'let getreport=161+(1*256)+(256*65536)+(mif*4294967296)+(8*281474976710656)',
        'volatile_write64(xhci_state+3936,8)',
        'v157_ehci_tt_control(xhci_state,2,getreport,8)',
        'volatile_write64(xhci_state+3936,kep)',
        'if raw!=prev',
        'input_push(input_state,4,0,buttons)',
        'input_push(input_state,5,0,dx)',
        'input_push(input_state,6,0,dy)',
        'volatile_write64(xhci_state+4064,volatile_read64(xhci_state+4064)+1)',
        'volatile_write64(xhci_state+4072,volatile_read64(xhci_state+4072)+1)',
    ):
        if q not in tick: raise SystemExit('r62 live control-poll witness missing '+q)
    for forbidden in ('volatile_write32(op+20,flo)','cmd=set_flag(cmd,16)','volatile_write32(qtd+8,560512)'):
        if forbidden in arm or forbidden in tick: raise SystemExit('r62 live path still arms periodic transfer '+forbidden)
    if s.count('v162_r61_periodic_reference_arm(')!=1 or s.count('v162_r61_periodic_reference_tick(')!=1 or s.count('v162_r61_gate_reference(')!=1:
        raise SystemExit('r62 reference helper reachability contract failed')
    if s.count('r59_redraw=v159_ehci_mouse_periodic_tick(xhci,input_state);')!=1:
        raise SystemExit('r62 live desktop tick call missing or duplicated')
    active=(arm+tick).lower()
    if any(x in active for x in ('write(10)','nvme_submit_write','ahci_write','fat_write','block_write')):
        raise SystemExit('r62 exceeds read-only control-poll input scope')
except BaseException:
    out=Path('evidence'); out.mkdir(parents=True,exist_ok=True)
    (out/'R62-FAILURE.txt').write_text(traceback.format_exc())
    raise
