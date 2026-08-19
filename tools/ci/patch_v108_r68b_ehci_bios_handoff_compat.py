#!/usr/bin/env python3
from pathlib import Path
import hashlib, subprocess, sys
if len(sys.argv)!=2: raise SystemExit('usage: patch_v108_r68b_ehci_bios_handoff_compat.py <kernel/main.nx>')
p=Path(sys.argv[1]); here=Path(__file__).parent
base=here/'patch_v108_r68_ehci_bios_handoff.py'
subprocess.run([sys.executable,str(base),str(p)],check=True,stdout=subprocess.DEVNULL)
s=p.read_text()
BASE='b20e7b5414dd0059c451e64ecf2ec8a918d05b8e099dec712ee0e745dd7d2fbf'
actual=hashlib.sha256(s.encode()).hexdigest()
if actual!=BASE: raise SystemExit('r68b exact r68 base mismatch '+actual)
old='let compat=old_mint+sm+cm+((rr/2)%2)+t;'
new='let compat=volatile_read64(xhci+4000)+volatile_read64(xhci+3984)+volatile_read64(xhci+4064)+old_mint+sm+cm+((rr/2)%2)+t;'
if s.count(old)!=1: raise SystemExit('r68b inherited physical-row compatibility anchor mismatch '+str(s.count(old)))
s=s.replace(old,new,1)
for q in ('volatile_read64(xhci+3984)','volatile_read64(xhci+3992)','volatile_read64(xhci+4000)','volatile_read64(xhci+4064)','R68 HBOXARE'):
    if q not in s: raise SystemExit('r68b inherited EHCI row witness missing '+q)
out=hashlib.sha256(s.encode()).hexdigest()
EXPECTED='d3d29fe3448bcfc781f8dd6634df334ed14066f94df0836f03dec69ae71c5935'
if out!=EXPECTED: raise SystemExit('r68b output sha mismatch '+out)
p.write_text(s)
print(out)
