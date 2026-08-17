#!/usr/bin/env python3
from pathlib import Path
import sys
if len(sys.argv)!=2: raise SystemExit('usage: patch_v108_r26b_identity.py <kernel/main.nx>')
base=Path(__file__).with_name('patch_v108_r26_iso_native_log.py')
src=base.read_text()
old='5dc6c6b04f7103a3981287d048264c94b75bfb12fd50538ca0a285979aa001fc'
new='7c8967f78588b37663db22c78f727bfa8685056045e88b7c126ffcd56a0cc66f'
if src.count(old)!=1: raise SystemExit(f'r26 stale identity anchor mismatch {src.count(old)}')
src=src.replace(old,new,1)
ns={'__name__':'__main__','__file__':str(base)}
exec(compile(src,str(base),'exec'),ns,ns)
