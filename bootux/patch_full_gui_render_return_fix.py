#!/usr/bin/env python3
from pathlib import Path
import hashlib, subprocess, sys

if len(sys.argv) != 2:
    raise SystemExit('usage: patch_full_gui_render_return_fix.py PATH_TO_main.nx')
p=Path(sys.argv[1]); s=p.read_text()
start=s.find('fn full_interactive_desktop_compose(')
end=s.find('\nfn appearance_system_phase1_compose(',start)
if start<0 or end<0:
    raise SystemExit('full interactive desktop function span not found')
span=s[start:end]
old='if wm_render_all(wm,surface,dirty)<5 { return 0; }'
new='if wm_render_all(wm,surface,dirty)==0 { return 0; }'
if span.count(old)!=1:
    raise SystemExit(f'full-GUI scoped render gate anchor count={span.count(old)}')
span=span.replace(old,new,1)
s=s[:start]+span+s[end:]
p.write_text(s)
subprocess.run([sys.executable,str(Path(__file__).with_name('patch_full_gui_layout_r2.py')),str(p)],check=True)
print('full_gui_render_return_fix=PASS')
print('patched_kernel_sha256='+hashlib.sha256(p.read_bytes()).hexdigest())
