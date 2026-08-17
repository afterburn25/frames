#!/usr/bin/env python3
from pathlib import Path
base=Path(__file__).with_name('patch_v108_r28_ep0_address_evaluate.py')
src=base.read_text()
old="expected='1d165f9aac5eeb40519d17920a019e586495a3b37c7a394fe17b221f9d702108'"
new="expected='f35bf73ef6c28f3a0e58416071a4b231bcf3b9ca632fdff23078a3ef1e479af7'"
if src.count(old)!=1: raise SystemExit(f'r28 identity wrapper anchor mismatch {src.count(old)}')
src=src.replace(old,new,1)
ns={'__name__':'__main__','__file__':str(base)}
exec(compile(src,str(base),'exec'),ns,ns)
