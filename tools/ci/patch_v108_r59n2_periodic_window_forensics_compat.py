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
# The enclosing desktop renderer already owns a binding named `fr`. Rename
# only r59n's local FRINDEX telemetry variable; this is lexical-only.
oldfr='let fr=volatile_read32(op+12)%16384; fi=(fr/8)%1024;'
newfr='let fri59n=volatile_read32(op+12)%16384; fi=(fri59n/8)%1024;'
if s.count(oldfr)!=1: raise SystemExit('r59n2 FRINDEX binding anchor mismatch '+str(s.count(oldfr)))
s=s.replace(oldfr,newfr,1)
# Bound the one-shot high-resolution window so TCG cannot starve the desktop
# input/readiness loop. 32 microframes span four full USB frames, enough to
# guarantee one every-fourth-frame schedule opportunity regardless of phase.
oldwin='while transitions<64 && spins<4000000 {'
newwin='while transitions<32 && spins<500000 {'
if s.count(oldwin)!=1: raise SystemExit('r59n2 periodic window bound anchor mismatch '+str(s.count(oldwin)))
s=s.replace(oldwin,newwin,1)
for q in ('(ot/128)%2','while transitions<32','spins<500000','volatile_write64(xhci_state+3984,hit)','volatile_write64(xhci_state+3992,packed)','fi=(fri59n/8)%1024'):
    if q not in s: raise SystemExit('r59n2 required witness missing '+q)
out=hashlib.sha256(s.encode()).hexdigest()
EXPECTED='de6cbe0ccaa2256ce9fc911634679ef34a8f908f58d5bd79f8d25ac1f3e53eed'
if out!=EXPECTED: raise SystemExit('r59n2 output sha mismatch '+out)
p.write_text(s)
print(out)
