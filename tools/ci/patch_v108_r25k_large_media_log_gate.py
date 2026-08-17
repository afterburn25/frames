#!/usr/bin/env python3
from pathlib import Path
import hashlib,subprocess,sys
if len(sys.argv)!=2: raise SystemExit('usage: patch_v108_r25k_large_media_log_gate.py <kernel/main.nx>')
p=Path(sys.argv[1]); base=Path(__file__).with_name('patch_v108_r25j_multidevice_event_dispatch.py'); subprocess.run([sys.executable,str(base),str(p)],check=True,stdout=subprocess.DEVNULL); s=p.read_text()
if hashlib.sha256(s.encode()).hexdigest()!='bccff173bc151d8fbd6e8f8c691e43124b8813bcf34cbae63bd407366d6f55ca': raise SystemExit('r25j identity mismatch')
old='volatile_read64(msc+680)!=512 || volatile_read64(msc+688)!=524287'
new='volatile_read64(msc+680)!=512 || volatile_read64(msc+688)<524287'
if s.count(old)!=1: raise SystemExit(f'large-media capacity anchor mismatch {s.count(old)}')
s=s.replace(old,new,1)
expected='af77b8f648dbb11fa6a31810e2150483818213635c92404dd956db892df9fdb0'; actual=hashlib.sha256(s.encode()).hexdigest()
if actual!=expected: raise SystemExit(f'r25k identity mismatch {actual}')
p.write_text(s); print(actual)
