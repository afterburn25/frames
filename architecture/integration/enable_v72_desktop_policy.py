#!/usr/bin/env python3
from pathlib import Path
import re, sys

if len(sys.argv) != 2:
    raise SystemExit('usage: enable_v72_desktop_policy.py PATH_TO_frames_boot.c')

p = Path(sys.argv[1])
s = p.read_text()
found = []
for pat in [r'(boot_policy_flags\s*=\s*)(\d+)(\s*;)', r'(boot_policy_flags\s*:\s*u64\s*=\s*)(\d+)(\s*;)']:
    for m in re.finditer(pat, s):
        old = int(m.group(2))
        if old < 2048:
            found.append((m.start(), m.end(), m.group(1), old, m.group(3)))
if not found:
    print('No patchable boot_policy_flags assignment found')
    for i, line in enumerate(s.splitlines(), 1):
        if 'boot_policy_flags' in line:
            print(i, line)
    raise SystemExit(2)
start, end, prefix, old, suffix = found[-1]
new = old | 1 | 2048
s = s[:start] + prefix + str(new) + suffix + s[end:]
p.write_text(s)
print(f'patched boot_policy_flags {old} -> {new}')
