#!/usr/bin/env python3
from pathlib import Path
import hashlib, subprocess, sys
if len(sys.argv)!=2: raise SystemExit('usage: patch_v108_r59n3_bounded_periodic_window.py <kernel/main.nx>')
p=Path(sys.argv[1]); here=Path(__file__).parent
base=here/'patch_v108_r59n2_periodic_window_forensics_compat.py'
subprocess.run([sys.executable,str(base),str(p)],check=True,stdout=subprocess.DEVNULL)
s=p.read_text()
BASE='de6cbe0ccaa2256ce9fc911634679ef34a8f908f58d5bd79f8d25ac1f3e53eed'
actual=hashlib.sha256(s.encode()).hexdigest()
if actual!=BASE: raise SystemExit('r59n3 exact compiler-clean r59n base mismatch '+actual)
old='while transitions<64 && spins<4000000 {'
new='while transitions<32 && spins<500000 {'
if s.count(old)!=1: raise SystemExit('r59n3 sampling-window anchor mismatch '+str(s.count(old)))
s=s.replace(old,new,1)
for q in ('while transitions<32','spins<500000','volatile_write64(xhci_state+3984,hit)','volatile_write64(xhci_state+3992,packed)','let frame_index=(now_fri/8)%1024','let uframe=now_fri%8','let live_tok=volatile_read32(qh+24)'):
    if q not in s: raise SystemExit('r59n3 bounded forensic witness missing '+q)
for bad in ('while transitions<64 && spins<4000000',):
    if bad in s: raise SystemExit('r59n3 unbounded sampling loop remains')
out=hashlib.sha256(s.encode()).hexdigest()
EXPECTED='24df5ece713f2eac409899296ccc34f8843332194e28e981d771bd01ad1db4f4'
if out!=EXPECTED: raise SystemExit('r59n3 output sha mismatch '+out)
p.write_text(s)
print(out)
