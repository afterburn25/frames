#!/usr/bin/env python3
from pathlib import Path
import hashlib, traceback
here=Path(__file__).parent
base=here/'r65_cert_driver.py'
src=base.read_text()

def repl(old,new,label,min_count=1):
    global src
    n=src.count(old)
    if n<min_count: raise SystemExit(f'r66 cert anchor {label} count {n}, expected >= {min_count}')
    src=src.replace(old,new)

repl("'patch_v108_r65_persistent_tt_periodic_qh.py'","'patch_v108_r66_intel_8000_profile_unlock.py'",'patch target')
repl('kernel-r65.nx','kernel-r66.nx','kernel evidence target',2)
repl('c34e637562aeea6a0156fb7142502d006ced9ea961bac3eccc336e7db4d64785','49748e4fb2fd2d0ec73cca7ef396719aef5fd13cf63bb69e83e96d892f38e700','exact r66 identity target',2)
repl("'Frames-0.9.98-v108-r65-Persistent-TT-Periodic-QH-Rufus-UEFI.iso'","'Frames-0.9.98-v108-r66-Intel-8000-Persistent-TT-QH-Rufus-UEFI.iso'",'ISO target')
repl("'R65-SHA.txt'","'R66-SHA.txt'",'SHA evidence target')
repl("'R25K-R65.patch'","'R25K-R66.patch'",'patch evidence target')
repl("'FRAMES_V108_R65'","'FRAMES_V108_R66'",'ISO label target')
repl('R65-AGGREGATE.json','R66-AGGREGATE.json','aggregate target')
repl("'frames-0.9.98-v108-r65-persistent-tt-periodic-qh'","'frames-0.9.98-v108-r66-intel-8000-persistent-tt-qh'",'profile target')
repl("'Frames 0.9.98 v108 r65 — Persistent Intel TT Periodic QH Lifecycle'","'Frames 0.9.98 v108 r66 — Intel 8087:8000 Persistent TT QH Lifecycle'",'cert title target')
repl('R65 PASS_VM_PENDING_PHYSICAL','R66 PASS_VM_PENDING_PHYSICAL','PASS target')
repl("'R65-FAILURE.txt'","'R66-FAILURE.txt'",'failure target',2)
repl('r65 exact kernel identity mismatch','r66 exact kernel identity mismatch','identity label')
repl("'physical_r65':'PENDING'","'physical_r65':'PHYSICAL_PROFILE_GATE_REJECT_8087_8000','physical_r65_telemetry':'R65_32903_32768_0_0_0_0_0_0','physical_r66':'PENDING'",'physical evidence continuation')

# r59h pinned qTD error telemetry to its old packed rr expression. r66 keeps
# the r65 direct hardware-owned QH-overlay E field; widen only that inherited
# presentation verifier in this runner checkout.
r59hp=here/'r59h_cert_driver.py'; r59h=r59hp.read_text()
old="    req('(rr/4)%32' in s,'r59h qTD error telemetry missing')"
new="    req((('(rr/4)%32' in s) or ('e=(ot/4)%32' in s)),'r59h/r66 EHCI error telemetry missing')"
if r59h.count(old)==1:
    r59hp.write_text(r59h.replace(old,new,1))
elif r59h.count(new)!=1:
    raise SystemExit('r66 r59h error telemetry compatibility anchor missing')

# r61's verifier predates the exact Intel integrated TT profile and direct
# QH-overlay telemetry. Accept the r66 exact-profile model without weakening
# any transport, route, DMA, input-delivery, or write-safety checks.
r61p=here/'r61_cert_driver.py'; r61=r61p.read_text()
old_tt="'if hubproto==2 { ttidx=port; }'"
new_tt="'hubvid==32903','hubpid==32776','hubproto==1','hubchars==9','port==2','thinkbits==8'"
if r61.count(old_tt)==1:
    r61=r61.replace(old_tt,new_tt,1)
elif r61.count(new_tt)!=1:
    raise SystemExit('r66 r61 exact-TT-profile compatibility anchor missing')
old_gate="'gate=1+(ta*2)+(qa*4)+(sx*8)+(er*16)+(rem*1024)+(orem*32768)'"
new_gate="'a=(ot/128)%2'"
if r61.count(old_gate)==1:
    r61=r61.replace(old_gate,new_gate,1)
elif r61.count(new_gate)!=1:
    raise SystemExit('r66 r61 QH-overlay telemetry compatibility anchor missing')
r61p.write_text(r61)

ns={'__name__':'__main__','__file__':str(base)}
try:
    exec(compile(src,str(base),'exec'),ns,ns)
    k=Path('evidence/kernel-r66.nx')
    if not k.exists(): raise SystemExit('r66 evidence kernel missing')
    s=k.read_text()
    if hashlib.sha256(s.encode()).hexdigest()!='49748e4fb2fd2d0ec73cca7ef396719aef5fd13cf63bb69e83e96d892f38e700': raise SystemExit('r66 evidence kernel SHA mismatch')
    arm=s[s.index('fn v159_ehci_mouse_periodic_arm'):s.index('fn v159_ehci_mouse_periodic_tick')]
    tick=s[s.index('fn v159_ehci_mouse_periodic_tick'):s.index('fn v162_r61_periodic_reference_arm')]
    for q in (
        'hubvid==32903','hubpid==32768 || hubpid==32776','hubproto==1','hubchars==9','port==2','thinkbits==8',
        'let gap_uf:u64=1','let legacy_cmask=3*power2_u64(gap_uf)','let info2=1090586113',
        'let legacy_info2:u64=1090586113','let newsched_info2:u64=1090591745',
        'let qcount:u64=24','volatile_write32(qtd+8,560512)','volatile_write32(dummy+8,64)',
        'cmd=set_flag(cmd,16)','volatile_write64(xhci_state+3984,profile)','volatile_write64(xhci_state+3992,6)'):
        if q not in arm: raise SystemExit('r66 persistent periodic arm witness missing '+q)
    for q in (
        'let idx=volatile_read64(xhci_state+4080)','let tok=volatile_read32(td+8)','let otok=volatile_read32(qh+24)',
        'input_push(input_state,4,0,buttons)','input_push(input_state,5,0,dx)','input_push(input_state,6,0,dy)',
        'volatile_write64(xhci_state+4080,idx+1)'):
        if q not in tick: raise SystemExit('r66 persistent completion witness missing '+q)
    for bad in ('volatile_write32(qh+24','volatile_write32(qh+16','volatile_write32(td+8','cmd=set_flag(cmd,16)','cmd=clear_flag(cmd,16)','volatile_write32(op+20'):
        if bad in tick: raise SystemExit('r66 live QH/schedule ownership violation '+bad)
    low=(arm+tick).lower()
    if any(x in low for x in ('write(10)','nvme_submit_write','ahci_write','fat_write','block_write')): raise SystemExit('r66 exceeds read-only input scope')
except BaseException:
    out=Path('evidence'); out.mkdir(parents=True,exist_ok=True); (out/'R66-FAILURE.txt').write_text(traceback.format_exc()); raise
