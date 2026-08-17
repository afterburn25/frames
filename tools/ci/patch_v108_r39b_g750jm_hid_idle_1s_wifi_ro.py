#!/usr/bin/env python3
from pathlib import Path
import hashlib, subprocess, sys
if len(sys.argv)!=2: raise SystemExit('usage: patch_v108_r39b_g750jm_hid_idle_1s_wifi_ro.py <kernel/main.nx>')
p=Path(sys.argv[1])
base=Path(__file__).with_name('patch_v108_r39_g750jm_hid_idle_disabled_wifi_ro.py')
subprocess.run([sys.executable,str(base),str(p)],check=True,stdout=subprocess.DEVNULL)
s=p.read_text()
BASE='ba873c5bcfb810faa6210f440832ad359c5e91c012541fc2431c2bd1acb3a8d1'
if hashlib.sha256(s.encode()).hexdigest()!=BASE: raise SystemExit('r39 base mismatch')
old='let idle_setup=2593+(2048*65536)+(interface_num*4294967296)'
new='let idle_setup=2593+(64000*65536)+(interface_num*4294967296)'
if s.count(old)!=1: raise SystemExit(f'r39b SET_IDLE anchor count {s.count(old)}')
s=s.replace(old,new,1)
out=hashlib.sha256(s.encode()).hexdigest()
EXPECTED='7ca4e51896453e0bcaa131d7f4497e64e95556cb96941c599fa4151eb71bbea5'
if out!=EXPECTED: raise SystemExit(f'r39b output sha mismatch {out}')
p.write_text(s)
print(out)
