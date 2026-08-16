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

# The v72 kernel's desktop Phase-5 host consumes module 1, while the loader only
# publishes module 1 when hello_fapp_verified is true. The normal desktop-policy
# activation used by this proof does not traverse either interactive-preview path
# that ordinarily verifies HELLO.FAP. Bridge that producer/consumer contract here:
# in desktop mode, run the loader's existing verifier on the package before the
# boot-module table is allocated. Nothing unverified is promoted.
anchor = 'UINTN mod_count=hello_fapp_verified?2:1;'
if anchor not in s:
    raise SystemExit('boot-module allocation anchor not found')
block = r'''if((boot_policy_flags & 2048ULL)!=0 && !hello_fapp_verified){
        EFI_STATUS appst=load_file(bs,image,L"\\Frames\\HELLO.FAP",&hello_fapp_file,&hello_fapp_size);
        if(EFI_ERROR(appst) || !fapp_extract_verify(hello_fapp_file,hello_fapp_size,&hello_fapp_fex,&hello_fapp_fex_size)) fatal(L"Desktop policy HELLO.FAP verification failed",appst);
        hello_fapp_verified=1;
        boot_policy_flags|=4096ULL;
        print16(L"[DESKTOP] Desktop policy HELLO.FAP verified; module 1 armed\r\n");
    }
    '''
s = s.replace(anchor, block + anchor, 1)
p.write_text(s)
print('patched desktop policy to verify HELLO.FAP before boot-module allocation')
