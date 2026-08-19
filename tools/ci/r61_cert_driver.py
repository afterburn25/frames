#!/usr/bin/env python3
from pathlib import Path
import hashlib, traceback

here=Path(__file__).parent
base=here/'r60_cert_driver.py'
src=base.read_text()

def one(old,new,label):
    global src
    n=src.count(old)
    if n!=1:
        raise SystemExit(f'r61 cert anchor {label} count {n}')
    src=src.replace(old,new,1)

def alln(old,new,count,label):
    global src
    n=src.count(old)
    if n!=count:
        raise SystemExit(f'r61 cert anchor {label} count {n}, expected {count}')
    src=src.replace(old,new)

one("'patch_v108_r60_reference_ehci_boot_mouse.py'","'patch_v108_r61_altsetting_reset_tt_boot_mouse.py'",'patch target')
alln('kernel-r60.nx','kernel-r61.nx',2,'kernel evidence target')
one('dc1d8d0590965f6d499eba0fe2d010287d6052d2c7ceab73dff41120fadcc04d','5903008c46c2d6e4be84a5eab7fa44a322ba7a594ff8cb810fcbe277e716d9ee','exact r61 identity target')
one("'Frames-0.9.98-v108-r60-Reference-EHCI-Boot-Mouse-Rufus-UEFI.iso'","'Frames-0.9.98-v108-r61-AltSetting-RESET-TT-Boot-Mouse-Rufus-UEFI.iso'",'ISO target')
one("'R60-SHA.txt'","'R61-SHA.txt'",'SHA evidence target')
one("'R25K-R60.patch'","'R25K-R61.patch'",'patch evidence target')
one("'FRAMES_V108_R60'","'FRAMES_V108_R61'",'ISO label target')
one('R60-AGGREGATE.json','R61-AGGREGATE.json','aggregate target')
one("'frames-0.9.98-v108-r60-reference-ehci-boot-mouse'","'frames-0.9.98-v108-r61-altsetting-reset-tt-boot-mouse'",'profile target')
one("'Frames 0.9.98 v108 r60 — Reference-Driven EHCI Boot Mouse Integration'","'Frames 0.9.98 v108 r61 — Alternate Setting + RESET_TT Boot Mouse Integration'",'cert title target')
one('R60 PASS_VM_PENDING_PHYSICAL','R61 PASS_VM_PENDING_PHYSICAL','PASS target')
alln("'R60-FAILURE.txt'","'R61-FAILURE.txt'",2,'failure target')
one('r60 exact kernel identity mismatch','r61 exact kernel identity mismatch','identity label')
one("'physical_r59h':'PENDING','physical_r60':'PENDING'","'physical_r59h':'PENDING','physical_r60':'NOT_PHYSICALLY_TESTED_SUPERSEDED_BY_R61','physical_r59t2':'PHYSICAL_ASYNC_SPLIT_ACTIVE_NO_PROGRESS','physical_r59t2_telemetry':'R5T_G270351_N0_B0_0_B1_0_B2_0_B3_0','physical_r61':'PENDING'",'physical evidence handoff')

ns={'__name__':'__main__','__file__':str(base)}
try:
    exec(compile(src,str(base),'exec'),ns,ns)
    k=Path('evidence/kernel-r61.nx')
    if not k.exists():
        raise SystemExit('r61 evidence kernel missing')
    s=k.read_text()
    if hashlib.sha256(s.encode()).hexdigest()!='5903008c46c2d6e4be84a5eab7fa44a322ba7a594ff8cb810fcbe277e716d9ee':
        raise SystemExit('r61 evidence kernel SHA mismatch')
    arm=s[s.index('fn v159_ehci_mouse_periodic_arm'):s.index('fn v159_ehci_mouse_periodic_tick')]
    tick=s[s.index('fn v159_ehci_mouse_periodic_tick'):s.index('fn v135_hid_control_fallback_prepare')]
    for q in (
        'let full_setup=usb_setup_length_v113(usb_setup_value_v113(128,6,512,0),total)',
        'let al0=volatile_read8(data0+off0+3)',
        'if if0==mif && ic0==3 && sub0==1 && pr0==2',
        'if ea0==mep && at0%4==3 { epfound=1; }',
        'let setif=1+(11*256)+(malt*65536)+(mif*4294967296)',
        'v157_ehci_tt_control(xhci_state,2,setif,0)',
        'v155_ehci_control(xhci_state,1,5066549597570688,18)',
        'if hubproto==2 { ttidx=port; }',
        'let resettt=35+(9*256)+(ttidx*4294967296)',
        'v155_ehci_control(xhci_state,1,resettt,0)',
        'volatile_write64(xhci_state+3984,malt)',
        'volatile_write64(xhci_state+3992,ifrc)',
        'volatile_write64(xhci_state+4000,ttrc)',
        'let info2=1090591745',
        'let token=560512',
    ):
        if q not in arm:
            raise SystemExit('r61 preflight/periodic witness missing '+q)
    for q in (
        'input_push(input_state,4,0,buttons)',
        'input_push(input_state,5,0,dx)',
        'input_push(input_state,6,0,dy)',
        'volatile_write32(qtd+8,560512)',
    ):
        if q not in tick:
            raise SystemExit('r61 retained r60 completion/delivery witness missing '+q)
    for q in (
        'gate=1+(ta*2)+(qa*4)+(sx*8)+(er*16)+(rem*1024)+(orem*32768)',
        'volatile_read64(xhci+3984)',
        'volatile_read64(xhci+3992)',
        'volatile_read64(xhci+4000)',
        'volatile_read64(xhci+4064)',
    ):
        if q not in s:
            raise SystemExit('r61 physical telemetry witness missing '+q)
    low=(arm+tick).lower()
    if any(x in low for x in ('write(10)','nvme_submit_write','ahci_write','fat_write','block_write')):
        raise SystemExit('r61 exceeds read-only input-integration scope')
except BaseException:
    out=Path('evidence'); out.mkdir(parents=True,exist_ok=True)
    (out/'R61-FAILURE.txt').write_text(traceback.format_exc())
    raise
