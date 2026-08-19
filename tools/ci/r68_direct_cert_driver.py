#!/usr/bin/env python3
from pathlib import Path
import hashlib, traceback
here=Path(__file__).parent
base=here/'r67_direct_cert_driver.py'
src=base.read_text()

def repl(old,new,label,count=None):
    global src
    n=src.count(old)
    if count is not None and n!=count: raise SystemExit(f'r68 cert anchor {label} count {n}, expected {count}')
    if count is None and n<1: raise SystemExit(f'r68 cert anchor {label} missing')
    src=src.replace(old,new)

repl("'patch_v108_r67_persistent_newsched_cmask.py'","'patch_v108_r68_ehci_bios_handoff.py'",'patch target',1)
repl('kernel-r67.nx','kernel-r68.nx','kernel evidence',2)
repl('fb92da0f8bd6f5fa66912b6ad6b63c700a47bdb353fe3bb349d3fdc7e2e92570','b20e7b5414dd0059c451e64ecf2ec8a918d05b8e099dec712ee0e745dd7d2fbf','kernel identity')
repl("'Frames-0.9.98-v108-r67-Persistent-NewSched-TT-QH-Rufus-UEFI.iso'","'Frames-0.9.98-v108-r68-EHCI-BIOS-Handoff-Persistent-TT-QH-Rufus-UEFI.iso'",'ISO target',1)
repl("'R67-SHA.txt'","'R68-SHA.txt'",'SHA evidence',1)
repl("'R25K-R67.patch'","'R25K-R68.patch'",'patch evidence',1)
repl("'FRAMES_V108_R67'","'FRAMES_V108_R68'",'ISO label',1)
repl('R67-AGGREGATE.json','R68-AGGREGATE.json','aggregate',1)
repl("'frames-0.9.98-v108-r67-persistent-newsched-tt-qh'","'frames-0.9.98-v108-r68-ehci-bios-handoff-persistent-tt-qh'",'profile',1)
repl("'Frames 0.9.98 v108 r67 — Persistent Intel TT QH + Linux New-Scheduler Geometry'","'Frames 0.9.98 v108 r68 — EHCI Legacy BIOS Handoff + Persistent Intel TT QH'",'title',1)
repl('R67 PASS_VM_PENDING_PHYSICAL','R68 PASS_VM_PENDING_PHYSICAL','PASS label',1)
repl("'R67-FAILURE.txt'","'R68-FAILURE.txt'",'failure label',2)
repl('r67 exact kernel identity mismatch','r68 exact kernel identity mismatch','identity message',1)
repl("physical_r67':'PENDING","physical_r67':'PHYSICAL_NEWSCHED_PERSISTENT_FIRST_QTD_ACTIVE_NO_PROGRESS','physical_r67_telemetry':'R67_M28_N0_D0_X0_A1_T0_R8_E0','physical_r68':'PENDING",'physical continuation',1)

ns={'__name__':'__main__','__file__':str(base)}
try:
    exec(compile(src,str(base),'exec'),ns,ns)
    k=Path('evidence/kernel-r68.nx')
    if not k.exists(): raise SystemExit('r68 evidence kernel missing')
    s=k.read_text()
    if hashlib.sha256(s.encode()).hexdigest()!='b20e7b5414dd0059c451e64ecf2ec8a918d05b8e099dec712ee0e745dd7d2fbf': raise SystemExit('r68 evidence kernel SHA mismatch')
    arm=s[s.index('fn v159_ehci_mouse_periodic_arm'):s.index('fn v159_ehci_mouse_periodic_tick')]
    tick=s[s.index('fn v159_ehci_mouse_periodic_tick'):s.index('fn v162_r61_periodic_reference_arm')]
    for q in (
        'let h_hcc=volatile_read32(h_base+8)','var leg_off=(h_hcc/256)%256','leg_cap%256==1',
        'bios_before=(leg_cap/65536)%2','os_before=(leg_cap/16777216)%2',
        'pci_cfg_write32(h_ebdf,leg_off,leg_cap+16777216)','pci_cfg_write32(h_ebdf,leg_off+4,0)',
        'handoff_code=1','handoff_code=2','volatile_write64(xhci_state+3984,handoff_code)',
        'hubpid==32768 || hubpid==32776','let info2=1090591745','let qcount:u64=24'):
        if q not in arm: raise SystemExit('r68 ownership/persistent witness missing '+q)
    for q in ('let idx=volatile_read64(xhci_state+4080)','let tok=volatile_read32(td+8)','let otok=volatile_read32(qh+24)','input_push(input_state,4,0,buttons)','input_push(input_state,5,0,dx)','input_push(input_state,6,0,dy)'):
        if q not in tick: raise SystemExit('r68 completion witness missing '+q)
    if 'pci_cfg_write32(h_ebdf,208' in s or 'pci_cfg_write32(h_ebdf,212' in s: raise SystemExit('r68 xHCI route write forbidden')
    low=(arm+tick).lower()
    if any(x in low for x in ('write(10)','nvme_submit_write','ahci_write','fat_write','block_write')): raise SystemExit('r68 exceeds read-only storage policy')
except BaseException:
    out=Path('evidence'); out.mkdir(parents=True,exist_ok=True)
    (out/'R68-FAILURE.txt').write_text(traceback.format_exc())
    raise
