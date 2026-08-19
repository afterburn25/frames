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
        raise SystemExit(f'r59o cert anchor {label} count {n}')
    src = src.replace(old, new, 1)

def alln(old, new, count, label):
    global src
    n = src.count(old)
    if n != count:
        raise SystemExit(f'r59o cert anchor {label} count {n}, expected {count}')
    src = src.replace(old, new)

one("'patch_v108_r59n2_periodic_window_forensics_compat.py'", "'patch_v108_r59o_periodic_endpoint_speed.py'", 'patch target')
alln('kernel-r59n.nx', 'kernel-r59o.nx', 2, 'kernel evidence target')
one('24df5ece713f2eac409899296ccc34f8843332194e28e981d771bd01ad1db4f4', 'b33103bcbe4ad84ded6da2e1f4f85c9437fc2d1b0858ec269a3f505661615972', 'exact r59o identity target')
one("'Frames-0.9.98-v108-r59n-Periodic-Window-Forensics-Rufus-UEFI.iso'", "'Frames-0.9.98-v108-r59o-Periodic-Endpoint-Speed-Rufus-UEFI.iso'", 'ISO target')
one("'R59N-SHA.txt'", "'R59O-SHA.txt'", 'SHA evidence target')
one("'R25K-R59N.patch'", "'R25K-R59O.patch'", 'patch evidence target')
one("'FRAMES_V108_R59N'", "'FRAMES_V108_R59O'", 'ISO label target')
one('R59N-AGGREGATE.json', 'R59O-AGGREGATE.json', 'aggregate target')
one("'frames-0.9.98-v108-r59n-periodic-window-forensics'", "'frames-0.9.98-v108-r59o-periodic-endpoint-speed'", 'profile target')
one("'Frames 0.9.98 v108 r59n — High-Resolution EHCI Periodic Window Forensics'", "'Frames 0.9.98 v108 r59o — EHCI Periodic Endpoint Speed Encoding Repair'", 'cert title target')
one('R59N PASS_VM_PENDING_PHYSICAL', 'R59O PASS_VM_PENDING_PHYSICAL', 'PASS target')
alln('R59N-FAILURE.txt', 'R59O-FAILURE.txt', 2, 'failure target')
one('r59n exact kernel identity mismatch', 'r59o exact kernel identity mismatch', 'identity label')

# Carry the r59n/r59n3 physical finding into the evidence aggregate: the EHCI
# periodic schedule reaches the mouse QH and starts a split, but the 8-byte IN
# qTD remains active with zero completions. The new speed-correct candidate is
# intentionally pending physical proof.
one("'physical_r59m':'PHYSICAL_SINGLE_TT_PERIODIC_ACTIVE_NO_COMPLETION','physical_r59m_telemetry':'R5M_H1_T0_F0_Q1_N0_A1_P1','physical_r59n':'PENDING'",
    "'physical_r59m':'PHYSICAL_SINGLE_TT_PERIODIC_ACTIVE_NO_COMPLETION','physical_r59m_telemetry':'R5M_H1_T0_F0_Q1_N0_A1_P1','physical_r59n3':'PHYSICAL_PERIODIC_EXECUTION_ACTIVE_NO_COMPLETION','physical_r59n3_telemetry':'R5N_H1_X1_U32_A1_R8_N0_P1','physical_r59o':'PENDING'",
    'physical r59n3 result + r59o pending')

# r59o preserves the bounded observer from r59n2/r59n3.
for witness in ("'while transitions<32'", "'spins<500000'"):
    if witness not in src:
        raise SystemExit('r59o inherited bounded cert witness missing ' + witness)
if "'while transitions<64'" in src:
    raise SystemExit('r59o inherited unbounded cert witness remains')

ns = {'__name__': '__main__', '__file__': str(base)}
try:
    exec(compile(src, str(base), 'exec'), ns, ns)
    k = Path('evidence/kernel-r59o.nx')
    if not k.exists():
        raise SystemExit('r59o evidence kernel missing')
    s = k.read_text()
    arm = s[s.index('fn v159_ehci_mouse_periodic_arm'):s.index('fn v159_ehci_mouse_periodic_tick')]
    tick = s[s.index('fn v159_ehci_mouse_periodic_tick'):s.index('fn v135_hid_control_fallback_prepare')]
    for q in (
        'let info1=2+(ep*256)+(speed*4096)+(mmps*65536)',
        'let info2=1090591745',
        'while transitions<32 && spins<500000',
        'volatile_write64(xhci_state+3984,hit)',
        'volatile_write64(xhci_state+3992,packed)',
        'volatile_read64(xhci+4024)',
        'fi=(fri59n/8)%1024',
    ):
        if q not in s:
            raise SystemExit('r59o certification witness missing ' + q)
    if 'let info1=2+(ep*256)+(mmps*65536)' in arm:
        raise SystemExit('r59o full-speed-only periodic QH encoding remains')
    low = (arm + tick).lower()
    if any(x in low for x in ('write(10)', 'nvme_submit_write', 'ahci_write', 'fat_write', 'block_write', 'input_push(')):
        raise SystemExit('r59o exceeds diagnostic/read-only scope')
except BaseException:
    out = Path('evidence')
    out.mkdir(parents=True, exist_ok=True)
    (out / 'R59O-FAILURE.txt').write_text(traceback.format_exc())
    raise
