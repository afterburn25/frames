#!/usr/bin/env python3
from pathlib import Path
import traceback

here = Path(__file__).parent
base = here / 'r59n2_cert_driver.py'
src = base.read_text()

def one(old, new, label):
    global src
    n = src.count(old)
    if n != 1:
        raise SystemExit(f'r59n3 cert anchor {label} count {n}')
    src = src.replace(old, new, 1)

# r59n2 already certifies the exact bounded source identity. r59n3 changes the
# handoff/certification identity only; it must not attempt to apply the bounded
# edit a second time.
one("'patch_v108_r59n2_periodic_window_forensics_compat.py'", "'patch_v108_r59n3_bounded_periodic_window.py'", 'patch target')
identity = '24df5ece713f2eac409899296ccc34f8843332194e28e981d771bd01ad1db4f4'
if src.count(identity) != 1:
    raise SystemExit(f'r59n3 cert anchor exact bounded identity count {src.count(identity)}')

one("'Frames-0.9.98-v108-r59n-Periodic-Window-Forensics-Rufus-UEFI.iso'", "'Frames-0.9.98-v108-r59n3-Bounded-Periodic-Window-Forensics-Rufus-UEFI.iso'", 'ISO target')
one("'R59N-SHA.txt'", "'R59N3-SHA.txt'", 'SHA evidence target')
one("'R25K-R59N.patch'", "'R25K-R59N3.patch'", 'patch evidence target')
one("'FRAMES_V108_R59N'", "'FRAMES_V108_R59N3'", 'ISO label target')
one('R59N-AGGREGATE.json', 'R59N3-AGGREGATE.json', 'aggregate target')
one("'frames-0.9.98-v108-r59n-periodic-window-forensics'", "'frames-0.9.98-v108-r59n3-bounded-periodic-window-forensics'", 'profile target')
one("'Frames 0.9.98 v108 r59n — High-Resolution EHCI Periodic Window Forensics'", "'Frames 0.9.98 v108 r59n3 — Bounded EHCI Periodic Window Forensics'", 'cert title target')
one('R59N PASS_VM_PENDING_PHYSICAL', 'R59N3 PASS_VM_PENDING_PHYSICAL', 'PASS target')

# Keep inherited failure wiring private while exposing the r59n3 layer.
src = src.replace("'R59N-FAILURE.txt'", "'R59N3-FAILURE.txt'")

# The inherited r59n2 gate must already contain both halves of the bounded
# sampling condition. This is a verifier, not another source transformation.
for witness in ("'while transitions<32'", "'spins<500000'"):
    if witness not in src:
        raise SystemExit('r59n3 inherited bounded cert witness missing ' + witness)
if "'while transitions<64'" in src:
    raise SystemExit('r59n3 inherited unbounded cert witness remains')

# Carry the earlier physical chain forward and mark this new sealed candidate
# pending real-hardware proof.
if "'physical_r59n':'PENDING'" not in src:
    raise SystemExit('r59n3 physical pending anchor missing')
src = src.replace("'physical_r59n':'PENDING'", "'physical_r59n3':'PENDING'", 1)

ns = {'__name__': '__main__', '__file__': str(base)}
try:
    exec(compile(src, str(base), 'exec'), ns, ns)
    k = Path('evidence/kernel-r59n.nx')
    if not k.exists():
        raise SystemExit('r59n3 evidence kernel missing')
    s = k.read_text()
    for q in (
        'while transitions<32 && spins<500000',
        'volatile_write64(xhci_state+3984,hit)',
        'volatile_write64(xhci_state+3992,packed)',
        'let frame_index=(now_fri/8)%1024',
        'let uframe=now_fri%8',
        'let live_tok=volatile_read32(qh+24)',
        'fi=(fri59n/8)%1024',
    ):
        if q not in s:
            raise SystemExit('r59n3 bounded sampling witness missing ' + q)
    if 'while transitions<64 && spins<4000000' in s:
        raise SystemExit('r59n unbounded sampling loop remains')
    tick = s[s.index('fn v159_ehci_mouse_periodic_tick'):s.index('fn v135_hid_control_fallback_prepare')]
    low = tick.lower()
    if any(x in low for x in ('write(10)', 'nvme_submit_write', 'ahci_write', 'fat_write', 'block_write', 'input_push(')):
        raise SystemExit('r59n3 exceeds forensic/read-only scope')
except BaseException:
    out = Path('evidence')
    out.mkdir(parents=True, exist_ok=True)
    (out / 'R59N3-FAILURE.txt').write_text(traceback.format_exc())
    raise
