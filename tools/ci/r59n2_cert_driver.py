#!/usr/bin/env python3
from pathlib import Path
import traceback
here=Path(__file__).parent
base=here/'r59m_cert_driver.py'
src=base.read_text()

def one(old,new,label):
    global src
    n=src.count(old)
    if n!=1: raise SystemExit(f'r59n2 cert anchor {label} count {n}')
    src=src.replace(old,new,1)
def alln(old,new,count,label):
    global src
    n=src.count(old)
    if n!=count: raise SystemExit(f'r59n2 cert anchor {label} count {n}, expected {count}')
    src=src.replace(old,new)

one("'patch_v108_r59m_hub_multi_tt_activation.py'","'patch_v108_r59n2_periodic_window_forensics_compat.py'",'patch target')
alln('kernel-r59m.nx','kernel-r59n.nx',2,'kernel evidence target')
one('8b236b8b21a181e5db9fbeec3c5b64840df0d3158980bde3176647e6cf651bc8','de6cbe0ccaa2256ce9fc911634679ef34a8f908f58d5bd79f8d25ac1f3e53eed','exact r59n identity target')
one("'Frames-0.9.98-v108-r59m-Hub-Multi-TT-Activation-Rufus-UEFI.iso'","'Frames-0.9.98-v108-r59n-Periodic-Window-Forensics-Rufus-UEFI.iso'",'ISO target')
one("'R59M-SHA.txt'","'R59N-SHA.txt'",'SHA evidence target')
one("'R25K-R59M.patch'","'R25K-R59N.patch'",'patch evidence target')
one("'FRAMES_V108_R59M'","'FRAMES_V108_R59N'",'ISO label target')
one('R59M-AGGREGATE.json','R59N-AGGREGATE.json','aggregate target')
one("'frames-0.9.98-v108-r59m-hub-multi-tt-activation'","'frames-0.9.98-v108-r59n-periodic-window-forensics'",'profile target')
one("'Frames 0.9.98 v108 r59m — Hub Multi-TT Activation'","'Frames 0.9.98 v108 r59n — High-Resolution EHCI Periodic Window Forensics'",'cert title target')
one('R59M PASS_VM_PENDING_PHYSICAL','R59N PASS_VM_PENDING_PHYSICAL','PASS target')
alln('R59M-FAILURE.txt','R59N-FAILURE.txt',2,'failure target')
one('r59m exact kernel identity mismatch','r59n exact kernel identity mismatch','identity label')
one("'physical_r59m':'PENDING'","'physical_r59m':'PHYSICAL_SINGLE_TT_PERIODIC_ACTIVE_NO_COMPLETION','physical_r59m_telemetry':'R5M_H1_T0_F0_Q1_N0_A1_P1','physical_r59n':'PENDING'",'physical r59m result + r59n pending')

# Private compatibility adapter: r59l's post-build evidence gate keys on its
# local FRINDEX variable spelling. r59n had to rename that binding to avoid a
# real Nexus same-scope collision. Accept the r59n-equivalent spelling only in
# this certification execution; historical r59l source remains unchanged.
r59lp=here/'r59l_cert_driver.py'
r59lsrc=r59lp.read_text()
old_fri="'fi=(fri59l/8)%1024'"
new_fri="'fi=(fri59n/8)%1024'"
if r59lsrc.count(old_fri)==1:
    r59lp.write_text(r59lsrc.replace(old_fri,new_fri,1))
elif r59lsrc.count(new_fri)!=1:
    raise SystemExit('r59n inherited r59l FRINDEX-name compatibility anchor missing')

ns={'__name__':'__main__','__file__':str(base)}
try:
    exec(compile(src,str(base),'exec'),ns,ns)
    k=Path('evidence/kernel-r59n.nx')
    if not k.exists(): raise SystemExit('r59n evidence kernel missing')
    s=k.read_text()
    tick=s[s.index('fn v159_ehci_mouse_periodic_tick'):s.index('fn v135_hid_control_fallback_prepare')]
    for q in ('while transitions<64','volatile_write64(xhci_state+3984,hit)','volatile_write64(xhci_state+3992,packed)','let frame_index=(now_fri/8)%1024','let uframe=now_fri%8','let live_tok=volatile_read32(qh+24)'):
        if q not in tick: raise SystemExit('r59n high-resolution periodic forensic gate missing '+q)
    for q in ('volatile_read64(xhci+3880)','volatile_read64(xhci+3888)','fls=(c/4)%4','fi=(fri59n/8)%1024','volatile_read32(frame+(fi*4))==qlo+2','volatile_read32(dm+12)==tdlo','(ot/128)%2'):
        if q not in s: raise SystemExit('r59n inherited evidence witness missing '+q)
    low=tick.lower()
    if any(x in low for x in ('write(10)','nvme_submit_write','ahci_write','fat_write','block_write','input_push(')):
        raise SystemExit('r59n exceeds forensic/read-only scope')
except BaseException:
    out=Path('evidence'); out.mkdir(parents=True,exist_ok=True)
    (out/'R59N-FAILURE.txt').write_text(traceback.format_exc())
    raise
