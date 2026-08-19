#!/usr/bin/env python3
from pathlib import Path
import traceback

here = Path(__file__).parent
base = here / 'r59o_cert_driver.py'
src = base.read_text()

def one(old, new, label):
    global src
    n = src.count(old)
    if n != 1:
        raise SystemExit(f'r59p cert anchor {label} count {n}')
    src = src.replace(old, new, 1)

def alln(old, new, count, label):
    global src
    n = src.count(old)
    if n != count:
        raise SystemExit(f'r59p cert anchor {label} count {n}, expected {count}')
    src = src.replace(old, new)

one("'patch_v108_r59o_periodic_endpoint_speed.py'", "'patch_v108_r59p_longitudinal_split_forensics.py'", 'patch target')
alln('kernel-r59o.nx', 'kernel-r59p.nx', 2, 'kernel evidence target')
one('b33103bcbe4ad84ded6da2e1f4f85c9437fc2d1b0858ec269a3f505661615972', 'fa0a1cbab68bd24d89659f6e85fab19c1b478ff42825654dab4de504ef9b0214', 'exact r59p identity target')
one("'Frames-0.9.98-v108-r59o-Periodic-Endpoint-Speed-Rufus-UEFI.iso'", "'Frames-0.9.98-v108-r59p-Longitudinal-Split-Forensics-Rufus-UEFI.iso'", 'ISO target')
one("'R59O-SHA.txt'", "'R59P-SHA.txt'", 'SHA evidence target')
one("'R25K-R59O.patch'", "'R25K-R59P.patch'", 'patch evidence target')
one("'FRAMES_V108_R59O'", "'FRAMES_V108_R59P'", 'ISO label target')
one('R59O-AGGREGATE.json', 'R59P-AGGREGATE.json', 'aggregate target')
one("'frames-0.9.98-v108-r59o-periodic-endpoint-speed'", "'frames-0.9.98-v108-r59p-longitudinal-split-forensics'", 'profile target')
one("'Frames 0.9.98 v108 r59o — EHCI Periodic Endpoint Speed Encoding Repair'", "'Frames 0.9.98 v108 r59p — Longitudinal EHCI Split Completion Forensics'", 'cert title target')
one('R59O PASS_VM_PENDING_PHYSICAL', 'R59P PASS_VM_PENDING_PHYSICAL', 'PASS target')
alln('R59O-FAILURE.txt', 'R59P-FAILURE.txt', 2, 'failure target')
one('r59o exact kernel identity mismatch', 'r59p exact kernel identity mismatch', 'identity label')

# r59o physical result: full-speed child (S=0) but otherwise identical to
# r59n3 — QH hit, split/active, all 8 bytes remaining, zero completions.
one("'physical_r59n3':'PHYSICAL_PERIODIC_EXECUTION_ACTIVE_NO_COMPLETION','physical_r59n3_telemetry':'R5N_H1_X1_U32_A1_R8_N0_P1','physical_r59o':'PENDING'",
    "'physical_r59n3':'PHYSICAL_PERIODIC_EXECUTION_ACTIVE_NO_COMPLETION','physical_r59n3_telemetry':'R5N_H1_X1_U32_A1_R8_N0_P1','physical_r59o':'PHYSICAL_FULL_SPEED_SPLIT_ACTIVE_NO_COMPLETION','physical_r59o_telemetry':'R5O_S0_H1_X1_A1_R8_N0_P1','physical_r59p':'PENDING'",
    'physical r59o result + r59p pending')

ns = {'__name__': '__main__', '__file__': str(base)}
try:
    exec(compile(src, str(base), 'exec'), ns, ns)
    k = Path('evidence/kernel-r59p.nx')
    if not k.exists():
        raise SystemExit('r59p evidence kernel missing')
    s = k.read_text()
    arm = s[s.index('fn v159_ehci_mouse_periodic_arm'):s.index('fn v159_ehci_mouse_periodic_tick')]
    tick = s[s.index('fn v159_ehci_mouse_periodic_tick'):s.index('fn v135_hid_control_fallback_prepare')]
    for q in (
        'let info1=2+(ep*256)+(speed*4096)+(mmps*65536)',
        'let info2=1090591745',
        'volatile_read32(qh+24)',
        'mmf_seen=(packed/131072)%2',
        'xact_seen=(packed/262144)%2',
        'halt_seen=(packed/524288)%2',
        'volatile_write64(xhci_state+3984,volatile_read64(xhci_state+3984)+1)',
        'let mmfseen=(packed/131072)%2',
    ):
        if q not in s:
            raise SystemExit('r59p certification witness missing ' + q)
    if 'while transitions<32 && spins<500000' in tick:
        raise SystemExit('r59p blocking periodic sampling window remains')
    low = (arm + tick).lower()
    if any(x in low for x in ('write(10)', 'nvme_submit_write', 'ahci_write', 'fat_write', 'block_write', 'input_push(')):
        raise SystemExit('r59p exceeds diagnostic/read-only scope')
except BaseException:
    out = Path('evidence')
    out.mkdir(parents=True, exist_ok=True)
    (out / 'R59P-FAILURE.txt').write_text(traceback.format_exc())
    raise
