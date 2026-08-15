#!/usr/bin/env python3
from pathlib import Path
import subprocess, sys, tempfile

here = Path(__file__).resolve().parent
src = here / 'make_r58_input_flight_recorder.py'
text = src.read_text()
old = """rep('if generic_pointer_claim(state,source)==0 { return 1; }\\n    let buttons=packed%256;',
    'if generic_pointer_claim(state,source)==0 { return 1; }\\n    ptrtrace_emit(state,3,source,packed);\\n    let buttons=packed%256;',
    'generic pointer hook')"""
new = """old_gp='if generic_pointer_claim(state,source)==0 { return 1; }\\n    let buttons=packed%256;'
new_gp='if generic_pointer_claim(state,source)==0 { return 1; }\\n    ptrtrace_emit(state,3,source,packed);\\n    let buttons=packed%256;'
_gp_sites=s.count(old_gp)
if _gp_sites!=2:
    raise SystemExit(f'generic pointer hook: expected 2 sites, found {_gp_sites}')
s=s.replace(old_gp,new_gp)"""
if text.count(old) != 1:
    raise SystemExit(f'r58 fixer: expected one source hook block, found {text.count(old)}')
fixed = text.replace(old, new)

# Nexus x64 currently permits at most four function parameters. Rewrite the
# generated WRITE(10) helper from five parameters to four and derive a stable
# BOT tag internally from the target LBA. The caller's local tag bookkeeping may
# remain; it is harmless and keeps the surrounding transformer simple.
old_sig = 'fn usb_msc_bot_write10(xhci_state:u64,tag:u64,lba:u64,blocks:u64,source:u64) -> u64 {\\n    if source==0 { return 0; }\\n    let cbw=usb_msc_prepare_write10_cbw(xhci_state,tag,lba,blocks);'
new_sig = 'fn usb_msc_bot_write10(xhci_state:u64,lba:u64,blocks:u64,source:u64) -> u64 {\\n    if source==0 { return 0; }\\n    let tag=8192+(lba%1048576);\\n    let cbw=usb_msc_prepare_write10_cbw(xhci_state,tag,lba,blocks);'
if fixed.count(old_sig) != 1:
    raise SystemExit(f'r58 fixer: expected one 5-parameter WRITE(10) helper, found {fixed.count(old_sig)}')
fixed = fixed.replace(old_sig, new_sig)
fixed = fixed.replace('usb_msc_bot_write10(xhci_state,tag,log_lba,1,header)', 'usb_msc_bot_write10(xhci_state,log_lba,1,header)')
fixed = fixed.replace('usb_msc_bot_write10(xhci_state,tag,lba,8,page)', 'usb_msc_bot_write10(xhci_state,lba,8,page)')

# Keep the generated transformer beside the chained r57/r56/r55 helpers so
# Path(__file__).with_name(...) inside the transformer resolves correctly.
with tempfile.NamedTemporaryFile('w', suffix='.py', prefix='r58-fixed-', dir=here, delete=False) as f:
    f.write(fixed)
    temp = f.name
try:
    subprocess.check_call([sys.executable, temp, sys.argv[1]])
finally:
    Path(temp).unlink(missing_ok=True)
