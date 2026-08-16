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
print(f'patched boot_policy_flags {old} -> {new}')

block = r'''if((boot_policy_flags & 2048ULL)!=0 && !hello_fapp_verified){
        EFI_STATUS appst=load_file(bs,image,L"\\Frames\\HELLO.FAP",&hello_fapp_file,&hello_fapp_size);
        if(EFI_ERROR(appst) || !fapp_extract_verify(hello_fapp_file,hello_fapp_size,&hello_fapp_fex,&hello_fapp_fex_size)) fatal(L"Desktop policy HELLO.FAP verification failed",appst);
        hello_fapp_verified=1;
        boot_policy_flags|=4096ULL;
        print16(L"[DESKTOP] Desktop policy HELLO.FAP verified; module 1 armed\r\n");
    }
    '''

# Inject immediately before the loader's module-table allocation. This accepts
# both the original v72 two-module form and the full v101 product's richer
# HELLO.FAP + theme + appearance module count without rewriting that architecture.
patterns = [
    r'(?m)^[ \t]*(?:UINTN|UINT64|size_t|u64|unsigned\s+long(?:\s+long)?|unsigned\s+int)?[ \t]*mod_count[ \t]*=[^;]*hello_fapp_verified[^;]*;',
    r'(?m)^[ \t]*mod_count[ \t]*=[^;]*hello_fapp_verified[^;]*;',
]
match = None
for pat in patterns:
    match = re.search(pat, s)
    if match:
        break

if not match:
    print('boot-module allocation anchor not found; semantic candidates:')
    for i, line in enumerate(s.splitlines(), 1):
        if 'mod_count' in line or 'hello_fapp_verified' in line:
            print(f'{i}: {line}')
    raise SystemExit('boot-module allocation semantic anchor not found')

# Avoid duplicate injection if a source already contains the desktop-policy block.
pre = s[max(0, match.start()-1200):match.start()]
if 'Desktop policy HELLO.FAP verified; module 1 armed' not in pre:
    s = s[:match.start()] + block + s[match.start():]
    print('patched desktop policy to verify HELLO.FAP before boot-module allocation')
else:
    print('desktop policy HELLO.FAP verification block already present')

p.write_text(s)
