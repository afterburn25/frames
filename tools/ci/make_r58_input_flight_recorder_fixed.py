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
with tempfile.NamedTemporaryFile('w', suffix='.py', delete=False) as f:
    f.write(fixed)
    temp = f.name
subprocess.check_call([sys.executable, temp, sys.argv[1]])
