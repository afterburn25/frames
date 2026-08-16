#!/usr/bin/env python3
from pathlib import Path
import sys

if len(sys.argv) != 2:
    raise SystemExit('usage: instrument_v72_post_phase7_pipeline.py PATH_TO_kernel_main.nx')
p=Path(sys.argv[1]); s=p.read_text()
items=[
('file_manager_ready','file_manager_phase1_compose',80),
('settings_ready','settings_phase1_compose',81),
('notification_ready','notification_phase1_compose',82),
('session_shell_ready','session_shell_phase1_compose',83),
('gui_polish_ready','gui_polish_integrated_compose',84),
]
changed=0
for var,fn,stage in items:
    needle=f'{var}={fn}('
    pos=s.find(needle)
    if pos<0: raise SystemExit(f'missing {needle}')
    end=s.find(';',pos)
    if end<0: raise SystemExit(f'missing semicolon for {needle}')
    insert=f' serial_desktop_diag({stage},{var});'
    if s[end+1:end+1+len(insert)] != insert:
        s=s[:end+1]+insert+s[end+1:]; changed+=1
p.write_text(s)
print(f'instrumented post-phase7 pipeline results count={changed} stages=80-84')
