#!/usr/bin/env python3
from pathlib import Path
import sys

if len(sys.argv) != 3:
    raise SystemExit('usage: inspect_v72_post_phase7_gate.py PATH_TO_kernel_main.nx OUTPUT')

src = Path(sys.argv[1])
out = Path(sys.argv[2])
lines = src.read_text(errors='replace').splitlines()
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

# Also capture likely final-gate variable names around phase 6/7 composition.
for token in ['phase7','integrated_gui','desktop_cert','theme_runtime','gui_chrome','compose']:
    chunks.append(f'===== token {token} =====')
    for i,line in enumerate(lines):
        if token.lower() in line.lower():
            chunks.append(f'{i+1:06d}: {line}')

out.write_text('\n'.join(chunks)+'\n')
print(f'wrote {out} hits={len(hits)} lines={len(chunks)}')
if not hits:
    raise SystemExit('no post-phase7/certification markers found in source')
