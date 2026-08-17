#!/usr/bin/env python3
from pathlib import Path
import hashlib,subprocess,sys
if len(sys.argv)!=2: raise SystemExit('usage: patch_v108_r25i_log_marker_layout.py <kernel/main.nx>')
p=Path(sys.argv[1]);base=Path(__file__).with_name('patch_v108_r25h_restore_bulk_dci.py');subprocess.run([sys.executable,str(base),str(p)],check=True,stdout=subprocess.DEVNULL);s=p.read_text()
if hashlib.sha256(s.encode()).hexdigest()!='c8ccc58f4641f352c21500d62cfa372c623dd070c1ef7b73c515c0f288effd62': raise SystemExit('r25h identity mismatch')
old='volatile_read64(data+72)!=133132 || volatile_read64(data+80)!=3545795563478602310'
new='volatile_read64(data+56)!=133132 || volatile_read64(data+64)!=3545795563478602310'
if s.count(old)!=1: raise SystemExit(f'log marker layout anchor mismatch {s.count(old)}')
s=s.replace(old,new,1)
expected='a8a53408b754fcc83bc611725ba59fde71886f8cdfb0ffa154ccbcaeb4112b4a';actual=hashlib.sha256(s.encode()).hexdigest()
if actual!=expected: raise SystemExit(f'r25i identity mismatch {actual}')
p.write_text(s);print(actual)
