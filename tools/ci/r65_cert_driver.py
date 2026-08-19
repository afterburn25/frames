#!/usr/bin/env python3
from pathlib import Path
import hashlib, traceback
here=Path(__file__).parent
base=here/'r61_cert_driver.py'
src=base.read_text()

def repl(old,new,label,min_count=1):
    global src
    n=src.count(old)
    if n<min_count: raise SystemExit(f'r65 cert anchor {label} count {n}, expected >= {min_count}')
    src=src.replace(old,new)

repl("'patch_v108_r61_altsetting_reset_tt_boot_mouse.py'","'patch_v108_r65_persistent_tt_periodic_qh.py'",'patch target')
repl('kernel-r61.nx','kernel-r65.nx','kernel evidence target',2)
repl('5903008c46c2d6e4be84a5eab7fa44a322ba7a594ff8cb810fcbe277e716d9ee','c34e637562aeea6a0156fb7142502d006ced9ea961bac3eccc336e7db4d64785','exact r65 identity target',2)
repl("'Frames-0.9.98-v108-r61-AltSetting-RESET-TT-Boot-Mouse-Rufus-UEFI.iso'","'Frames-0.9.98-v108-r65-Persistent-TT-Periodic-QH-Rufus-UEFI.iso'",'ISO target')
repl("'R61-SHA.txt'","'R65-SHA.txt'",'SHA evidence target')
repl("'R25K-R61.patch'","'R25K-R65.patch'",'patch evidence target')
repl("'FRAMES_V108_R61'","'FRAMES_V108_R65'",'ISO label target')
repl('R61-AGGREGATE.json','R65-AGGREGATE.json','aggregate target')
repl("'frames-0.9.98-v108-r61-altsetting-reset-tt-boot-mouse'","'frames-0.9.98-v108-r65-persistent-tt-periodic-qh'",'profile target')
repl("'Frames 0.9.98 v108 r61 — Alternate Setting + RESET_TT Boot Mouse Integration'","'Frames 0.9.98 v108 r65 — Persistent Intel TT Periodic QH Lifecycle'",'cert title target')
repl('R61 PASS_VM_PENDING_PHYSICAL','R65 PASS_VM_PENDING_PHYSICAL','PASS target')
repl("'R61-FAILURE.txt'","'R65-FAILURE.txt'",'failure target',2)
repl('r61 exact kernel identity mismatch','r65 exact kernel identity mismatch','identity label')
repl("'physical_r61':'PENDING'","'physical_r61':'PHYSICAL_ALT0_RESET_TT_OK_PERIODIC_ACTIVE_NO_PROGRESS','physical_r61_telemetry':'R61_A0_I0_T1_G270343_N0_B0_X0','physical_r62':'PHYSICAL_GETREPORT8_RC6_NO_DATA','physical_r62_telemetry':'R62_C6_N0_D0_B0_X0_Y0','physical_r63':'PHYSICAL_GETREPORT3_RC6_NO_DATA','physical_r63_telemetry':'R63_C6_N0_D0_B0_X0_Y0','physical_r64':'PHYSICAL_GETREPORT_ZLP_DATA_STAGE','physical_r64_telemetry':'R64_C6_A0_H0_E0_R3_S0_Q0_D0','physical_r65':'PENDING'",'physical evidence continuation')

# Adapt r61's own final model assertions to the r65 lifecycle. r65 retains the
# r61 preflight, boot protocol and RESET_TT, but the live scheduler is the
# exact legacy-Linux S=0x01/C=0x06 geometry for this 8-byte FS IN endpoint,
# while the new-scheduler 0x1c geometry remains a named reference constant.
old="'let info2=1090591745','let token=560512'"
new="'let info2=1090586113','let newsched_info2:u64=1090591745','let token=560512'"
repl(old,new,'r61 final geometry witnesses')
old="for q in ('input_push(input_state,4,0,buttons)','input_push(input_state,5,0,dx)','input_push(input_state,6,0,dy)','volatile_write32(qtd+8,560512)'):"
new="for q in ('input_push(input_state,4,0,buttons)','input_push(input_state,5,0,dx)','input_push(input_state,6,0,dy)','volatile_write64(xhci_state+4080,idx+1)'):"
repl(old,new,'r61 final completion witnesses')
old="'r61 retained r60 completion/delivery witness missing '+q"
new="'r65 persistent completion/delivery witness missing '+q"
repl(old,new,'r61 completion error label')
old="'volatile_write64(xhci_state+3984,malt)','volatile_write64(xhci_state+3992,ifrc)','volatile_write64(xhci_state+4000,ttrc)'"
new="'volatile_write64(xhci_state+3984,profile)','volatile_write64(xhci_state+3992,6)','volatile_write64(xhci_state+4000,ttrc)'"
repl(old,new,'r61 telemetry witnesses')

# r60 rewrites the inherited r59h geometry assertion and has its own final
# r60 checks. Widen those runner-local checks for r65's deliberately retained
# dual-reference geometry and initial-only qTD activation.
r60p=here/'r60_cert_driver.py'; r60=r60p.read_text()
old="newgeom=\"    req('let info2=1090591745' in r59gfn and 'let info2=1090586113' not in r59gfn,'r60 default TT new-scheduler C-mask 0x1c missing')\""
new="newgeom=\"    req('let info2=1090586113' in r59gfn and 'let newsched_info2:u64=1090591745' in r59gfn,'r60/r65 retained Linux legacy/new split geometries missing')\""
if r60.count(old)==1: r60=r60.replace(old,new,1)
elif r60.count(new)!=1: raise SystemExit('r65 r60 geometry adapter anchor missing')
old="('let info2=1090591745' in r60fn and 'let info2=1090586113' not in r60fn,'r60 TT new-scheduler geometry missing'),"
new="('let info2=1090586113' in r60fn and 'let newsched_info2:u64=1090591745' in r60fn,'r60/r65 Linux split geometry references missing'),"
if r60.count(old)==1: r60=r60.replace(old,new,1)
elif r60.count(new)!=1: raise SystemExit('r65 r60 final geometry anchor missing')
r60p.write_text(r60)

ns={'__name__':'__main__','__file__':str(base)}
try:
    exec(compile(src,str(base),'exec'),ns,ns)
    k=Path('evidence/kernel-r65.nx')
    if not k.exists(): raise SystemExit('r65 evidence kernel missing')
    s=k.read_text()
    if hashlib.sha256(s.encode()).hexdigest()!='c34e637562aeea6a0156fb7142502d006ced9ea961bac3eccc336e7db4d64785': raise SystemExit('r65 evidence kernel SHA mismatch')
    arm=s[s.index('fn v159_ehci_mouse_periodic_arm'):s.index('fn v159_ehci_mouse_periodic_tick')]
    tick=s[s.index('fn v159_ehci_mouse_periodic_tick'):s.index('fn v162_r61_periodic_reference_arm')]
    for q in (
        'hubvid==32903','hubpid==32776','hubproto==1','hubchars==9','port==2','thinkbits==8',
        'let gap_uf:u64=1','let legacy_cmask=3*power2_u64(gap_uf)','let info2=1090586113',
        'let legacy_info2:u64=1090586113','let newsched_info2:u64=1090591745',
        'let qcount:u64=24','volatile_write32(qtd+8,560512)','volatile_write32(dummy+8,64)',
        'cmd=set_flag(cmd,16)','volatile_write64(xhci_state+3984,profile)','volatile_write64(xhci_state+3992,6)'):
        if q not in arm: raise SystemExit('r65 persistent periodic arm witness missing '+q)
    for q in (
        'let idx=volatile_read64(xhci_state+4080)','let tok=volatile_read32(td+8)','let otok=volatile_read32(qh+24)',
        'input_push(input_state,4,0,buttons)','input_push(input_state,5,0,dx)','input_push(input_state,6,0,dy)',
        'volatile_write64(xhci_state+4080,idx+1)'):
        if q not in tick: raise SystemExit('r65 persistent completion witness missing '+q)
    for bad in ('volatile_write32(qh+24','volatile_write32(qh+16','volatile_write32(td+8','cmd=set_flag(cmd,16)','cmd=clear_flag(cmd,16)','volatile_write32(op+20'):
        if bad in tick: raise SystemExit('r65 live QH/schedule ownership violation '+bad)
    if 'v157_ehci_tt_control(xhci_state,2,getreport' in tick: raise SystemExit('r65 control GET_REPORT workaround remains live')
    if s.count('let legacy_info2:u64=1090586113')<1 or s.count('let newsched_info2:u64=1090591745')<1: raise SystemExit('r65 lost dual scheduler references')
    low=(arm+tick).lower()
    if any(x in low for x in ('write(10)','nvme_submit_write','ahci_write','fat_write','block_write')): raise SystemExit('r65 exceeds read-only input scope')
except BaseException:
    out=Path('evidence'); out.mkdir(parents=True,exist_ok=True); (out/'R65-FAILURE.txt').write_text(traceback.format_exc()); raise
