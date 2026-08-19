#!/usr/bin/env python3
from pathlib import Path
import hashlib, traceback
here=Path(__file__).parent
base=here/'r66_cert_driver.py'
src=base.read_text()

def repl(text,old,new,label,count=None):
    n=text.count(old)
    if count is not None and n!=count: raise SystemExit(f'r67 direct anchor {label} count {n}, expected {count}')
    if count is None and n<1: raise SystemExit(f'r67 direct anchor {label} missing')
    return text.replace(old,new)

# Transform the already-green r66 certification identity to the exact r67
# kernel. This carries forward r66's r59h/r61 presentation compatibility
# adapters instead of reconstructing them from the older r65 layer.
src=repl(src,"'patch_v108_r66_intel_8000_profile_unlock.py'","'patch_v108_r67_persistent_newsched_cmask.py'",'patch target',1)
src=repl(src,'kernel-r66.nx','kernel-r67.nx','kernel evidence',2)
src=repl(src,'49748e4fb2fd2d0ec73cca7ef396719aef5fd13cf63bb69e83e96d892f38e700','fb92da0f8bd6f5fa66912b6ad6b63c700a47bdb353fe3bb349d3fdc7e2e92570','kernel identity')
src=repl(src,"'Frames-0.9.98-v108-r66-Intel-8000-Persistent-TT-QH-Rufus-UEFI.iso'","'Frames-0.9.98-v108-r67-Persistent-NewSched-TT-QH-Rufus-UEFI.iso'",'ISO target',1)
src=repl(src,"'R66-SHA.txt'","'R67-SHA.txt'",'SHA evidence',1)
src=repl(src,"'R25K-R66.patch'","'R25K-R67.patch'",'patch evidence',1)
src=repl(src,"'FRAMES_V108_R66'","'FRAMES_V108_R67'",'ISO label',1)
src=repl(src,'R66-AGGREGATE.json','R67-AGGREGATE.json','aggregate',1)
src=repl(src,"'frames-0.9.98-v108-r66-intel-8000-persistent-tt-qh'","'frames-0.9.98-v108-r67-persistent-newsched-tt-qh'",'profile',1)
src=repl(src,"'Frames 0.9.98 v108 r66 — Intel 8087:8000 Persistent TT QH Lifecycle'","'Frames 0.9.98 v108 r67 — Persistent Intel TT QH + Linux New-Scheduler Geometry'",'title',1)
src=repl(src,'R66 PASS_VM_PENDING_PHYSICAL','R67 PASS_VM_PENDING_PHYSICAL','PASS label',1)
src=repl(src,"'R66-FAILURE.txt'","'R67-FAILURE.txt'",'failure label',2)
src=repl(src,'r66 exact kernel identity mismatch','r67 exact kernel identity mismatch','identity message',1)
src=repl(src,"'physical_r65':'PHYSICAL_PROFILE_GATE_REJECT_8087_8000','physical_r65_telemetry':'R65_32903_32768_0_0_0_0_0_0','physical_r66':'PENDING'","'physical_r65':'PHYSICAL_PROFILE_GATE_REJECT_8087_8000','physical_r65_telemetry':'R65_32903_32768_0_0_0_0_0_0','physical_r66':'PHYSICAL_PROFILE_OK_LEGACY_PERSISTENT_FIRST_QTD_ACTIVE_NO_PROGRESS','physical_r66_telemetry':'R66_P1_M6_N0_D0_A1_T0_R8_E0','physical_r67':'PENDING'",'physical continuation',1)

# r66's final direct assertions describe its live legacy geometry. r67 keeps
# exactly the same persistent QH/qTD ownership model but changes only the live
# C-mask to the other Linux reference configuration, 0x1c.
src=repl(src,"'let gap_uf:u64=1','let legacy_cmask=3*power2_u64(gap_uf)','let info2=1090586113',","'let gap_uf:u64=1','let legacy_cmask=3*power2_u64(gap_uf)','let info2=1090591745',",'r66 final live geometry',1)
src=repl(src,"'cmd=set_flag(cmd,16)','volatile_write64(xhci_state+3984,profile)','volatile_write64(xhci_state+3992,6)'):","'cmd=set_flag(cmd,16)','volatile_write64(xhci_state+3984,profile)','volatile_write64(xhci_state+3992,28)'):",'r66 final mode',1)

# r65 is the layer that adapts r61/r60 model assertions for the persistent-QH
# architecture. Rewrite only its runner-local geometry expectations so they
# describe the r67 live new-scheduler case while retaining 0x06 as a reference.
r65p=here/'r65_cert_driver.py'; r65=r65p.read_text()
r65=repl(r65,"new=\"'let info2=1090586113','let newsched_info2:u64=1090591745','let token=560512'\"","new=\"'let info2=1090591745','let legacy_info2:u64=1090586113','let token=560512'\"",'r65->r61 geometry adapter',1)
r65=repl(r65,"new=\"'volatile_write64(xhci_state+3984,profile)','volatile_write64(xhci_state+3992,6)','volatile_write64(xhci_state+4000,ttrc)'\"","new=\"'volatile_write64(xhci_state+3984,profile)','volatile_write64(xhci_state+3992,28)','volatile_write64(xhci_state+4000,ttrc)'\"",'r65->r61 mode adapter',1)
r65=repl(r65,"new=\"newgeom=\\\"    req('let info2=1090586113' in r59gfn and 'let newsched_info2:u64=1090591745' in r59gfn,'r60/r65 retained Linux legacy/new split geometries missing')\\\"\"","new=\"newgeom=\\\"    req('let info2=1090591745' in r59gfn and 'let legacy_info2:u64=1090586113' in r59gfn,'r60/r67 live new-scheduler plus legacy reference missing')\\\"\"",'r65->r60 inherited geometry adapter',1)
r65=repl(r65,"new=\"('let info2=1090586113' in r60fn and 'let newsched_info2:u64=1090591745' in r60fn,'r60/r65 Linux split geometry references missing'),\"","new=\"('let info2=1090591745' in r60fn and 'let legacy_info2:u64=1090586113' in r60fn,'r60/r67 Linux split geometry references missing'),\"",'r65->r60 final geometry adapter',1)
r65=repl(r65,"'let gap_uf:u64=1','let legacy_cmask=3*power2_u64(gap_uf)','let info2=1090586113',","'let gap_uf:u64=1','let legacy_cmask=3*power2_u64(gap_uf)','let info2=1090591745',",'r65 final live geometry',1)
r65=repl(r65,"'cmd=set_flag(cmd,16)','volatile_write64(xhci_state+3984,profile)','volatile_write64(xhci_state+3992,6)'):","'cmd=set_flag(cmd,16)','volatile_write64(xhci_state+3984,profile)','volatile_write64(xhci_state+3992,28)'):",'r65 final mode',1)
r65p.write_text(r65)

ns={'__name__':'__main__','__file__':str(base)}
try:
    exec(compile(src,str(base),'exec'),ns,ns)
    k=Path('evidence/kernel-r67.nx')
    if not k.exists(): raise SystemExit('r67 evidence kernel missing')
    s=k.read_text()
    if hashlib.sha256(s.encode()).hexdigest()!='fb92da0f8bd6f5fa66912b6ad6b63c700a47bdb353fe3bb349d3fdc7e2e92570': raise SystemExit('r67 evidence kernel SHA mismatch')
    arm=s[s.index('fn v159_ehci_mouse_periodic_arm'):s.index('fn v159_ehci_mouse_periodic_tick')]
    tick=s[s.index('fn v159_ehci_mouse_periodic_tick'):s.index('fn v162_r61_periodic_reference_arm')]
    for q in ('hubvid==32903','hubpid==32768 || hubpid==32776','hubproto==1','hubchars==9','port==2','thinkbits==8','let legacy_info2:u64=1090586113','let newsched_info2:u64=1090591745','let info2=1090591745','let qcount:u64=24','volatile_write32(qtd+8,560512)','volatile_write32(dummy+8,64)','volatile_write64(xhci_state+3992,28)'):
        if q not in arm: raise SystemExit('r67 persistent new-scheduler witness missing '+q)
    for q in ('let idx=volatile_read64(xhci_state+4080)','let tok=volatile_read32(td+8)','let otok=volatile_read32(qh+24)','input_push(input_state,4,0,buttons)','input_push(input_state,5,0,dx)','input_push(input_state,6,0,dy)','volatile_write64(xhci_state+4080,idx+1)'):
        if q not in tick: raise SystemExit('r67 completion witness missing '+q)
    for q in ('volatile_read64(xhci+3976)','volatile_read64(xhci+3984)','volatile_read64(xhci+3992)','volatile_read64(xhci+4000)','volatile_read64(xhci+4064)','(rr/2)%2','sm=qi%256','cm=(qi/256)%256','x=(ot/2)%2'):
        if q not in s: raise SystemExit('r67 visible/route witness missing '+q)
    for bad in ('volatile_write32(qh+24','volatile_write32(qh+16','volatile_write32(td+8','cmd=set_flag(cmd,16)','cmd=clear_flag(cmd,16)','volatile_write32(op+20'):
        if bad in tick: raise SystemExit('r67 live QH/schedule ownership violation '+bad)
    low=(arm+tick).lower()
    if any(x in low for x in ('write(10)','nvme_submit_write','ahci_write','fat_write','block_write')): raise SystemExit('r67 exceeds read-only input scope')
except BaseException:
    out=Path('evidence'); out.mkdir(parents=True,exist_ok=True)
    (out/'R67-FAILURE.txt').write_text(traceback.format_exc())
    raise
