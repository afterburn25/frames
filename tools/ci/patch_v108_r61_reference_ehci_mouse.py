#!/usr/bin/env python3
from pathlib import Path
import hashlib, subprocess, sys

BASE='10a1a6550abafe7c593d059eeb983d6a576b19ab46c1dcde6ec71888aa6d4a03'
FINAL='9233c5f6d895aa88c2ad6e0262b133c41d093b8ef0091065f68ac27c471ad512'
if len(sys.argv)!=2:
    raise SystemExit('usage: patch_v108_r61_reference_ehci_mouse.py <kernel/main.nx>')
p=Path(sys.argv[1]); here=Path(__file__).parent
subprocess.run([sys.executable,str(here/'patch_v108_r59s_qh_current_completion_gate.py'),str(p)],check=True,stdout=subprocess.DEVNULL)
got=hashlib.sha256(p.read_bytes()).hexdigest()
if got!=BASE:
    raise SystemExit('r61 exact r59s base mismatch '+got)
subprocess.run([sys.executable,str(here/'r61_compat_transform.py'),str(p)],check=True,stdout=subprocess.DEVNULL)
got=hashlib.sha256(p.read_bytes()).hexdigest()
if got!=FINAL:
    raise SystemExit('r61 exact output identity mismatch '+got)
print(got)
