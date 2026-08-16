#!/usr/bin/env python3
from pathlib import Path
import hashlib, sys

if len(sys.argv) != 2:
    raise SystemExit('usage: patch_full_gui_render_return_fix.py PATH_TO_main.nx')
p=Path(sys.argv[1]); s=p.read_text()
old='if wm_render_all(wm,surface,dirty)<5 { return 0; }'
new='if wm_render_all(wm,surface,dirty)==0 { return 0; }'
if s.count(old)!=1:
    raise SystemExit(f'full-GUI render gate anchor count={s.count(old)}')
s=s.replace(old,new,1)
p.write_text(s)
print('full_gui_render_return_fix=PASS')
print('patched_kernel_sha256='+hashlib.sha256(p.read_bytes()).hexdigest())
