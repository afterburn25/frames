#!/usr/bin/env python3
"""r65 parallel EHCI repair transform.

This intentionally fails closed unless the source exposes the known r61/r64
EHCI patch anchors. It does not silently patch an unrelated baseline.

PR synchronization marker: workflow registered on main for pull_request CI.
Synchronization pulse 4: retrigger after removing pull_request path filters.
"""
from pathlib import Path
import os, sys

root = Path('.')
flags = {
    'overlay_authority': os.environ.get('OVERLAY_AUTHORITY') == '1',
    'preserve_toggle': os.environ.get('PRESERVE_TOGGLE') == '1',
    'persistent_periodic_qh': os.environ.get('PERSISTENT_PERIODIC_QH') == '1',
    'dummy_qtd': os.environ.get('DUMMY_QTD') == '1',
}

candidates = list(root.rglob('*.c')) + list(root.rglob('*.h')) + list(root.rglob('*.nex'))
anchor_file = None
for p in candidates:
    try:
        s = p.read_text(errors='ignore')
    except Exception:
        continue
    if 'volatile_read32(qh+24)' in s and ('qtd+8' in s or 'qTD' in s):
        anchor_file = p
        break

if anchor_file is None:
    sys.exit('r65: FAIL-CLOSED: live QH/qTD anchor not found; refusing to patch uncertain source')

s = anchor_file.read_text(errors='ignore')
original = s

if flags['overlay_authority']:
    s = s.replace('tok=volatile_read32(qtd+8)', 'tok=otok /* r65: live QH overlay authoritative after completion */')

if flags['preserve_toggle']:
    s = s.replace('volatile_write32(qh+24,0)', 'volatile_write32(qh+24,(otok & 0x80000000u)) /* r65 preserve DATA toggle */')

if flags['persistent_periodic_qh']:
    old = s
    s = s.replace('v121_ehci_periodic_stop();', '/* r65 persistent periodic QH: no global PSE stop */')
    s = s.replace('v121_ehci_periodic_start();', '/* r65 persistent periodic QH: already running */')
    if s == old:
        sys.exit('r65C/D: FAIL-CLOSED: periodic stop/start anchors not found')

if flags['dummy_qtd']:
    hooks = ('dummy_qtd', 'dummyqtd', 'QH_UNLINK_DUMMY_OVERLAY')
    if not any(h in s for h in hooks):
        sys.exit('r65D: FAIL-CLOSED: no dummy-qTD hook in source; descriptor-layout change requires explicit implementation')

if s == original:
    sys.exit('r65: no source mutation occurred; refusing false-positive build')
anchor_file.write_text(s)
print('r65 patched', anchor_file, flags)
