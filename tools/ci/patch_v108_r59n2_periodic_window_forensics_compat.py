#!/usr/bin/env python3
from pathlib import Path
import hashlib, subprocess, sys
if len(sys.argv)!=2: raise SystemExit('usage: patch_v108_r59n2_periodic_window_forensics_compat.py <kernel/main.nx>')
p=Path(sys.argv[1]); here=Path(__file__).parent
base=here/'patch_v108_r59n_periodic_window_forensics.py'
subprocess.run([sys.executable,str(base),str(p)],check=True,stdout=subprocess.DEVNULL)
s=p.read_text()
BASE='eff364295a51eae11757d39d05f406934ebfe16be84e733ee5a2120e3635de08'
actual=hashlib.sha256(s.encode()).hexdigest()
if actual!=BASE: raise SystemExit('r59n2 exact r59n base mismatch '+actual)
old='let compat=(rr/2)%2+(rr/4)%32+(ot/2)%2+(ot/4)%32'
new='let compat=(rr/2)%2+(rr/4)%32+(ot/128)%2+(ot/2)%2+(ot/4)%32'
if s.count(old)!=1: raise SystemExit('r59n2 overlay witness anchor mismatch '+str(s.count(old)))
s=s.replace(old,new,1)
for q in ('(ot/128)%2','while transitions<64','volatile_write64(xhci_state+3984,hit)','volatile_write64(xhci_state+3992,packed)'):
    if q not in s: raise SystemExit('r59n2 required witness missing '+q)
out=hashlib.sha256(s.encode()).hexdigest()
EXPECTED='733b8f94d26360494c0035236c840a31e18c1dfa5af7eaf638823e04fc6d2ba7'
if out!=EXPECTED: raise SystemExit('r59n2 output sha mismatch '+out)
p.write_text(s)
print(out)
