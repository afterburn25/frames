#!/usr/bin/env python3
from pathlib import Path
import re, subprocess, sys

if len(sys.argv) != 3:
    raise SystemExit('usage: wire_v72_gui_fapp_into_esp.py SOURCE_ROOT ESP_IMAGE')
root = Path(sys.argv[1])
esp = Path(sys.argv[2])
loader = root / 'boot/uefi/frames_boot.c'
s = loader.read_text(errors='replace')

# Discover the exact optional .fapp path requested by this loader.
paths = re.findall(r'load_file\(bs,image,L"([^"\n]*\\.fapp)"', s, flags=re.I)
if not paths:
    # Some revisions spell the literal with escaped backslashes in generated source.
    paths = re.findall(r'L"([^"\n]*[Ff][Aa][Pp][Pp][^"\n]*\.fapp)"', s)
if not paths:
    raise SystemExit('no loader .fapp path found')
expected = paths[0].replace('\\\\','\\')
print(f'loader_fapp_path={expected}')

# Prefer an already-built/package-authenticated FAPP produced by the supplied source.
candidates = []
for p in root.rglob('*.fapp'):
    if p.is_file() and p.stat().st_size > 0:
        candidates.append(p)
for p in root.rglob('*.FAPP'):
    if p.is_file() and p.stat().st_size > 0 and p not in candidates:
        candidates.append(p)
if not candidates:
    raise SystemExit('no .fapp package exists in supplied/built v72 source')

def score(p: Path):
    n = p.name.lower()
    path = str(p).lower()
    return (('helloframes' in n) * 100 + ('hello' in n) * 50 + ('build' in path) * 10, p.stat().st_size)

candidate = sorted(candidates, key=score, reverse=True)[0]
print(f'candidate_fapp={candidate}')
print(f'candidate_size={candidate.stat().st_size}')

# Translate UEFI path (\\Frames\\Foo.fapp) to mtools ::/Frames/Foo.fapp.
uefi = expected.replace('\\','/').lstrip('/')
parts = [x for x in uefi.split('/') if x]
if len(parts) < 2:
    raise SystemExit(f'unexpected loader FAPP path: {expected}')
cur = '::'
for d in parts[:-1]:
    cur = cur + '/' + d
    subprocess.run(['mmd','-i',str(esp),cur], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
dest = '::/' + '/'.join(parts)
subprocess.check_call(['mcopy','-o','-i',str(esp),str(candidate),dest])
# Prove the package is physically present at the exact path the loader will request.
subprocess.check_call(['mdir','-i',str(esp),'::/' + '/'.join(parts[:-1])])
print(f'wired_fapp={dest}')
