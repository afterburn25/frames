#!/usr/bin/env python3
from pathlib import Path
import hashlib,subprocess,sys

if len(sys.argv)!=2:
    raise SystemExit('usage: patch_v108_r10_compat_runner.py <kernel/main.nx>')
p=Path(sys.argv[1])
script=Path(__file__).with_name('patch_v108_physical_input_r10_hwdecode.py')
rc=subprocess.run([sys.executable,str(script),str(p)]).returncode
actual=hashlib.sha256(p.read_bytes()).hexdigest()
expected='b2dee4fc2c1ca3ad68d4428febf564a2143948ee797ea74ee532ac87b2c14ab6'
if actual!=expected:
    raise SystemExit(f'r10 compatibility runner: output SHA mismatch {actual}; patch rc={rc}')
print(actual)
