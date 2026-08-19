#!/usr/bin/env python3
from pathlib import Path
import hashlib, traceback
here=Path(__file__).parent
base=here/'r65_cert_driver.py'
src=base.read_text()

def repl(old,new,label,min_count=1):
    global src
    n=src.count(old)
    if n<min_count: raise SystemExit(f'r67 cert anchor {label} count {n}, expected >= {min_count}')
    src=src.replace(old,new)

repl("'patch_v108_r65_persistent_tt_periodic_qh.py'","'patch_v108_r67_persistent_newsched_cmask.py'",'patch target')
repl('kernel-r65.nx','kernel-r67.nx','kernel evidence target',2)
repl('c34e637562aeea6a0156fb7142502d006ced9ea961bac3eccc336e7db4d64785','80b2fa96a6b3fbc6c2f41d2e5f7e7a7d6c152a29fb32ed1351a1bf59f1813397','exact r67 identity target',2)
repl("'Frames-0.9.98-v108-r65-Persistent-TT-Periodic-QH-Rufus-UEFI.iso'","'Frames-0.9.98-v108-r67-Persistent-NewSched-TT-QH-Rufus-UEFI.iso'",'ISO target')
repl("'R65-SHA.txt'","'R67-SHA.txt'",'SHA evidence target')
repl("'R25K-R65.patch'","'R25K-R67.patch'",'patch evidence target')
repl("'FRAMES_V108_R65'","'FRAMES_V108_R67'",'ISO label target')
repl('R65-AGGREGATE.json','R67-AGGREGATE.json','aggregate target')
repl("'frames-0.9.98-v108-r65-persistent-tt-periodic-qh'","'frames-0.9.98-v108-r67-persistent-newsched-tt-qh'",'profile target')
repl("'Frames 0.9.98 v108 r65 — Persistent Intel TT Periodic QH Lifecycle'","'Frames 0.9.98 v108 r67 — Persistent Intel TT QH + Linux New-Scheduler Geometry'",'cert title target')
repl('R65 PASS_VM_PENDING_PHYSICAL','R67 PASS_VM_PENDING_PHYSICAL','PASS target')
repl("'R65-FAILURE.txt'","'R67-FAILURE.txt'",'failure target',2)
repl('r65 exact kernel identity mismatch','r67 exact kernel identity mismatch','identity label')
repl("'physical_r65':'PENDING'","'physical_r65':'PHYSICAL_PROFILE_GATE_REJECT_8087_8000','physical_r65_telemetry':'R65_32903_32768_0_0_0_0_0_0','physical_r66':'PHYSICAL_PROFILE_OK_LEGACY_PERSISTENT_FIRST_QTD_ACTIVE_NO_PROGRESS','physical_r66_telemetry':'R66_P1_M6_N0_D0_A1_T0_R8_E0','physical_r67':'PENDING'",'physical evidence continuation')

# r67 preserves the entire r65 persistent lifecycle but uses the other exact
# Linux reference geometry. Adapt r61's inherited final model assertions to
# expect live new-scheduler 0x1c while retaining legacy 0x06 as a named ref.
repl("new=\"'let info2=1090586113','let newsched_info2:u64=1090591745','let token=560512'\"",
     "new=\"'let info2=1090591745','let legacy_info2:u64=1090586113','let token=560512'\"",
     'r61 new-scheduler geometry adapter')
repl("new=\"'volatile_write64(xhci_state+3984,profile)','volatile_write64(xhci_state+3992,6)','volatile_write64(xhci_state+4000,ttrc)'\"",
     "new=\"'volatile_write64(xhci_state+3984,profile)','volatile_write64(xhci_state+3992,28)','volatile_write64(xhci_state+4000,ttrc)'\"",
     'r61 r67 telemetry adapter')

# Keep r60's new-scheduler requirement, but allow the legacy geometry to remain
# as a named non-live reference constant. The live `let info2` must be 0x1c.
old="new=\"newgeom=\\\"    req('let info2=1090586113' in r59gfn and 'let newsched_info2:u64=1090591745' in r59gfn,'r60/r65 retained Linux legacy/new split geometries missing')\\\"\""
new="new=\"newgeom=\\\"    req('let info2=1090591745' in r59gfn and 'let legacy_info2:u64=1090586113' in r59gfn,'r60/r67 live new-scheduler plus legacy reference missing')\\\"\""
repl(old,new,'r60 transformed newgeom adapter')
old="new=\"('let info2=1090586113' in r60fn and 'let newsched_info2:u64=1090591745' in r60fn,'r60/r65 Linux split geometry references missing'),\""
new="new=\"('let info2=1090591745' in r60fn and 'let legacy_info2:u64=1090586113' in r60fn,'r60/r67 Linux split geometry references missing'),\""
repl(old,new,'r60 transformed final geometry adapter')

# Exact physical hub admission now includes the observed 8087:8000 sibling.
# Keep these edits targeted so the historical r60 old/new anchor strings are
# not themselves rewritten before r65's runner-local adapter sees them.
repl("'hubpid==32776'","'hubpid==32768 || hubpid==32776'",'dual Intel hub profile witnesses',1)
repl("'let gap_uf:u64=1','let legacy_cmask=3*power2_u64(gap_uf)','let info2=1090586113',",
     "'let gap_uf:u64=1','let legacy_cmask=3*power2_u64(gap_uf)','let info2=1090591745',",
     'r67 final live-info2 witness',1)
repl("'cmd=set_flag(cmd,16)','volatile_write64(xhci_state+3984,profile)','volatile_write64(xhci_state+3992,6)'):",
     "'cmd=set_flag(cmd,16)','volatile_write64(xhci_state+3984,profile)','volatile_write64(xhci_state+3992,28)'):",
     'r67 final mode witness',1)

ns={'__name__':'__main__','__file__':str(base)}
try:
    exec(compile(src,str(base),'exec'),ns,ns)
    k=Path('evidence/kernel-r67.nx')
    if not k.exists(): raise SystemExit('r67 evidence kernel missing')
    s=k.read_text()
    if hashlib.sha256(s.encode()).hexdigest()!='80b2fa96a6b3fbc6c2f41d2e5f7e7a7d6c152a29fb32ed1351a1bf59f1813397': raise SystemExit('r67 evidence kernel SHA mismatch')
    arm=s[s.index('fn v159_ehci_mouse_periodic_arm'):s.index('fn v159_ehci_mouse_periodic_tick')]
    tick=s[s.index('fn v159_ehci_mouse_periodic_tick'):s.index('fn v162_r61_periodic_reference_arm')]
    for q in (
        'hubvid==32903','hubpid==32768 || hubpid==32776','hubproto==1','hubchars==9','port==2','thinkbits==8',
        'let gap_uf:u64=1','let legacy_cmask=3*power2_u64(gap_uf)','let info2=1090591745',
        'let legacy_info2:u64=1090586113','let newsched_info2:u64=1090591745',
        'let qcount:u64=24','volatile_write32(qtd+8,560512)','volatile_write32(dummy+8,64)',
        'cmd=set_flag(cmd,16)','volatile_write64(xhci_state+3984,profile)','volatile_write64(xhci_state+3992,28)'):
        if q not in arm: raise SystemExit('r67 persistent newsched arm witness missing '+q)
    for q in (
        'let idx=volatile_read64(xhci_state+4080)','let tok=volatile_read32(td+8)','let otok=volatile_read32(qh+24)',
        'input_push(input_state,4,0,buttons)','input_push(input_state,5,0,dx)','input_push(input_state,6,0,dy)',
        'volatile_write64(xhci_state+4080,idx+1)'):
        if q not in tick: raise SystemExit('r67 persistent completion witness missing '+q)
    for bad in ('volatile_write32(qh+24','volatile_write32(qh+16','volatile_write32(td+8','cmd=set_flag(cmd,16)','cmd=clear_flag(cmd,16)','volatile_write32(op+20'):
        if bad in tick: raise SystemExit('r67 live QH/schedule ownership violation '+bad)
    if 'v157_ehci_tt_control(xhci_state,2,getreport' in tick: raise SystemExit('r67 control GET_REPORT workaround remains live')
    low=(arm+tick).lower()
    if any(x in low for x in ('write(10)','nvme_submit_write','ahci_write','fat_write','block_write')): raise SystemExit('r67 exceeds read-only input scope')
except BaseException:
    out=Path('evidence'); out.mkdir(parents=True,exist_ok=True); (out/'R67-FAILURE.txt').write_text(traceback.format_exc()); raise
