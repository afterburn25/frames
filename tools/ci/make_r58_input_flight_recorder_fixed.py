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

# Rewrite the helper text inside the generated transformer. make_r58 stores the
# Nexus helper body in a raw triple-quoted Python string, so these are literal
# newlines here (not the escaped \\n form used by rep() anchors above).
old_sig = """fn usb_msc_bot_write10(xhci_state:u64,tag:u64,lba:u64,blocks:u64,source:u64) -> u64 {
    if source==0 { return 0; }
    let cbw=usb_msc_prepare_write10_cbw(xhci_state,tag,lba,blocks);"""
new_sig = """fn usb_msc_bot_write10(xhci_state:u64,lba:u64,blocks:u64,source:u64) -> u64 {
    if source==0 { return 0; }
    let tag=8192+(lba%1048576);
    let cbw=usb_msc_prepare_write10_cbw(xhci_state,tag,lba,blocks);"""
if fixed.count(old_sig) != 1:
    raise SystemExit(f'r58 fixer: expected one 5-parameter WRITE(10) helper, found {fixed.count(old_sig)}')
fixed = fixed.replace(old_sig, new_sig, 1)

call1 = 'usb_msc_bot_write10(xhci_state,tag,log_lba,1,header)'
call2 = 'usb_msc_bot_write10(xhci_state,tag,lba,8,page)'
if fixed.count(call1) != 1 or fixed.count(call2) != 1:
    raise SystemExit(f'r58 fixer: WRITE(10) callsites unexpected header={fixed.count(call1)} page={fixed.count(call2)}')
fixed = fixed.replace(call1, 'usb_msc_bot_write10(xhci_state,log_lba,1,header)', 1)
fixed = fixed.replace(call2, 'usb_msc_bot_write10(xhci_state,lba,8,page)', 1)

# Keep the generated transformer beside chained r57/r56/r55 helpers.
with tempfile.NamedTemporaryFile('w', suffix='.py', prefix='r58-fixed-', dir=here, delete=False) as f:
    f.write(fixed)
    temp = f.name
try:
    subprocess.check_call([sys.executable, temp, sys.argv[1]])
finally:
    Path(temp).unlink(missing_ok=True)
