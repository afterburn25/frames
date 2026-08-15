#!/usr/bin/env python3
from pathlib import Path
import re, sys

if len(sys.argv) != 2:
    raise SystemExit('usage: decouple_v72_network_from_filesystem.py PATH_TO_kernel_main.nx')

p = Path(sys.argv[1])
s = p.read_text()
pat = re.compile(r'fn network_core_gate\(state:u64,process:u64\) -> u64 \{.*?return passed; \}', re.S)
m = pat.search(s)
if not m:
    raise SystemExit('network_core_gate not found')
old = m.group(0)
new = old
new = re.sub(r' let fsg=volatile_read64\(process\+544\); if fsg!=0 && volatile_read64\(fsg\+24\)==1 \{ score=score\+1; \}', '', new, count=1)
new = new.replace('if score==10 { passed=1; }', 'if score==9 { passed=1; }', 1)
new = new.replace('volatile_write64(state+16,10)', 'volatile_write64(state+16,9)', 1)
if new == old:
    raise SystemExit('network_core_gate matched but no expected dependency was changed')
if 'process+544' in new:
    raise SystemExit('filesystem dependency still present in network_core_gate')
if 'score==9' not in new or 'state+16,9' not in new:
    raise SystemExit('network gate expected-count update missing')
s = s[:m.start()] + new + s[m.end():]
p.write_text(s)
print('patched network_core_gate: removed filesystem aggregate prerequisite; preserved 9 network-specific checks')
