#!/usr/bin/env python3
from pathlib import Path
import hashlib, subprocess, sys

if len(sys.argv) != 2:
    raise SystemExit('usage: patch_v108_r59n3_bounded_periodic_window.py <kernel/main.nx>')

p = Path(sys.argv[1])
here = Path(__file__).parent
base = here / 'patch_v108_r59n2_periodic_window_forensics_compat.py'
subprocess.run([sys.executable, str(base), str(p)], check=True, stdout=subprocess.DEVNULL)
s = p.read_text()

# r59n2 already contains the compiler-clean bounded 32-microframe / 500k-spin
# sampling window. r59n3 is the sealed physical-handoff certification layer
# for that exact source; do not try to re-apply the already-present edit.
EXPECTED = '24df5ece713f2eac409899296ccc34f8843332194e28e981d771bd01ad1db4f4'
actual = hashlib.sha256(s.encode()).hexdigest()
if actual != EXPECTED:
    raise SystemExit('r59n3 exact bounded r59n2 base mismatch ' + actual)

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
        raise SystemExit('r59n3 bounded forensic witness missing ' + q)

if 'while transitions<64 && spins<4000000' in s:
    raise SystemExit('r59n3 unbounded sampling loop remains')

out = hashlib.sha256(s.encode()).hexdigest()
if out != EXPECTED:
    raise SystemExit('r59n3 output sha mismatch ' + out)
p.write_text(s)
print(out)
