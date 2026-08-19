#!/usr/bin/env python3
from pathlib import Path
import traceback
here=Path(__file__).parent
base=here/'r59n2_cert_driver.py'
src=base.read_text()

def one(old,new,label):
    global src
    n=src.count(old)
    if n!=1: raise SystemExit(f'r59n3 cert anchor {label} count {n}')
    src=src.replace(old,new,1)

def alln(old,new,count,label):
    global src
    n=src.count(old)
    if n!=count: raise SystemExit(f'r59n3 cert anchor {label} count {n}, expected {count}')
    src=src.replace(old,new)

one("'patch_v108_r59n2_periodic_window_forensics_compat.py'","'patch_v108_r59n3_bounded_periodic_window.py'",'patch target')
one('de6cbe0ccaa2256ce9fc911634679ef34a8f908f58d5bd79f8d25ac1f3e53eed','24df5ece713f2eac409899296ccc34f8843332194e28e981d771bd01ad1db4f4','exact r59n3 identity target')
one("'Frames-0.9.98-v108-r59n-Periodic-Window-Forensics-Rufus-UEFI.iso'","'Frames-0.9.98-v108-r59n3-Bounded-Periodic-Window-Forensics-Rufus-UEFI.iso'",'ISO target')
one("'R59N-SHA.txt'","'R59N3-SHA.txt'",'SHA evidence target')
one("'R25K-R59N.patch'","'R25K-R59N3.patch'",'patch evidence target')
one("'FRAMES_V108_R59N'","'FRAMES_V108_R59N3'",'ISO label target')
one('R59N-AGGREGATE.json','R59N3-AGGREGATE.json','aggregate target')
one("'frames-0.9.98-v108-r59n-periodic-window-forensics'","'frames-0.9.98-v108-r59n3-bounded-periodic-window-forensics'",'profile target')
one("'Frames 0.9.98 v108 r59n — High-Resolution EHCI Periodic Window Forensics'","'Frames 0.9.98 v108 r59n3 — Bounded EHCI Periodic Window Forensics'",'cert title target')
one('R59N PASS_VM_PENDING_PHYSICAL','R59N3 PASS_VM_PENDING_PHYSICAL','PASS target')
# Keep historical r59n failure artifact wiring private but expose r59n3 at this layer.
src=src.replace("'R59N-FAILURE.txt'","'R59N3-FAILURE.txt'")
# r59n3 deliberately bounds the one-shot high-resolution sampling window to
# avoid starving the desktop/PS2 readiness path under single-thread TCG.
one("'while transitions<64'","'while transitions<32'",'bounded transition gate')
anchor="    for q in ('while transitions<32','volatile_write64(xhci_state+3984,hit)'"
if anchor not in src: raise SystemExit('r59n3 bounded gate injection anchor missing')
src=src.replace(anchor,"    for q in ('while transitions<32','spins<500000','volatile_write64(xhci_state+3984,hit)'",1)
# Carry the physical r59m result forward and mark the corrected r59n3 candidate pending.
src=src.replace("'physical_r59n':'PENDING'","'physical_r59n3':'PENDING'")

ns={'__name__':'__main__','__file__':str(base)}
try:
    exec(compile(src,str(base),'exec'),ns,ns)
    k=Path('evidence/kernel-r59n.nx')
    if not k.exists(): raise SystemExit('r59n3 evidence kernel missing')
    s=k.read_text()
    if 'while transitions<32 && spins<500000' not in s: raise SystemExit('r59n3 bounded sampling loop missing')
    if 'while transitions<64 && spins<4000000' in s: raise SystemExit('r59n unbounded sampling loop remains')
    if 'fi=(fri59n/8)%1024' not in s: raise SystemExit('r59n3 FRINDEX lexical compatibility missing')
    tick=s[s.index('fn v159_ehci_mouse_periodic_tick'):s.index('fn v135_hid_control_fallback_prepare')]
    low=tick.lower()
    if any(x in low for x in ('write(10)','nvme_submit_write','ahci_write','fat_write','block_write','input_push(')):
        raise SystemExit('r59n3 exceeds forensic/read-only scope')
except BaseException:
    out=Path('evidence'); out.mkdir(parents=True,exist_ok=True)
    (out/'R59N3-FAILURE.txt').write_text(traceback.format_exc())
    raise
