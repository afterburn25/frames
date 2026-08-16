#!/usr/bin/env python3
from pathlib import Path
import sys

if len(sys.argv) != 3:
    raise SystemExit('usage: inspect_v72_post_phase7_gate.py PATH_TO_kernel_main.nx OUTPUT')

src = Path(sys.argv[1])
out = Path(sys.argv[2])
text = src.read_text(errors='replace')

# Emit the result of every component after Phase 7. The existing phase markers
# already prove chrome and theme; these values identify the first later failure.
items=[
    ('file_manager_ready','file_manager_phase1_compose',80),
    ('settings_ready','settings_phase1_compose',81),
    ('notification_ready','notification_phase1_compose',82),
    ('session_shell_ready','session_shell_phase1_compose',83),
    ('gui_polish_ready','gui_polish_integrated_compose',84),
]
for var,fn,stage in items:
    needle=f'{var}={fn}('
    pos=text.find(needle)
    if pos < 0:
        raise SystemExit(f'missing post-phase7 call {needle}')
    end=text.find(';',pos)
    if end < 0:
        raise SystemExit(f'missing semicolon for {needle}')
    ins=f' serial_desktop_diag({stage},{var});'
    if text[end+1:end+1+len(ins)] != ins:
        text=text[:end+1]+ins+text[end+1:]
src.write_text(text)

lines = text.splitlines()
needles = [
    'serial_marker_desktop_phase7_ok',
    'serial_marker_desktop_cert_fail',
    'serial_marker_integrated_gui_ok',
    'FRAMES_DESKTOP_PHASE7_OK',
    'FRAMES_DESKTOP_CERT_FAIL',
    'FRAMES_INTEGRATED_GUI_OK',
]
hits=[]
for i,line in enumerate(lines):
    if any(n in line for n in needles):
        hits.append(i)

chunks=[]
seen=set()
for i in hits:
    lo=max(0,i-70); hi=min(len(lines),i+110)
    key=(lo,hi)
    if key in seen: continue
    seen.add(key)
    chunks.append(f'===== lines {lo+1}-{hi} =====')
    for j in range(lo,hi):
        chunks.append(f'{j+1:06d}: {lines[j]}')

for token in ['phase7','integrated_gui','desktop_cert','theme_runtime','file_manager','settings_ready','notification_ready','session_shell_ready','gui_polish_ready','compose']:
    chunks.append(f'===== token {token} =====')
    for i,line in enumerate(lines):
        if token.lower() in line.lower():
            chunks.append(f'{i+1:06d}: {line}')

out.write_text('\n'.join(chunks)+'\n')
print(f'wrote {out} hits={len(hits)} lines={len(chunks)}; instrumented stages 80-84')
if not hits:
    raise SystemExit('no post-phase7/certification markers found in source')
