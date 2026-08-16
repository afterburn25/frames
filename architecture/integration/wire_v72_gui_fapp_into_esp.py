#!/usr/bin/env python3
from pathlib import Path
import hashlib, json, re, subprocess, sys, zipfile

if len(sys.argv) != 3:
    raise SystemExit('usage: wire_v72_gui_fapp_into_esp.py SOURCE_ROOT ESP_IMAGE')
root = Path(sys.argv[1])
esp = Path(sys.argv[2])
loader = root / 'boot/uefi/frames_boot.c'
s = loader.read_text(errors='replace')

m = re.search(r'load_file\([^\n]*L"([^"\n]*HELLO\.FAP)"', s, re.I)
if m:
    expected = m.group(1).replace('\\\\', '\\')
elif 'HELLO.FAP' in s:
    expected = r'\Frames\HELLO.FAP'
else:
    raise SystemExit('v72 loader does not reference HELLO.FAP')
print(f'loader_fapp_path={expected}')


def packages():
    return [p for p in root.rglob('*') if p.is_file() and p.suffix.lower() in ('.fap','.fapp') and p.stat().st_size > 0]

candidates = packages()
if not candidates:
    fex_candidates = [p for p in root.rglob('*.fex') if p.is_file() and p.stat().st_size >= 128]
    system = root / 'build' / 'System.fex'
    if system.exists() and system.stat().st_size >= 128:
        payload = system
    elif fex_candidates:
        payload = sorted(fex_candidates, key=lambda p: (('hello' in p.name.lower()), p.stat().st_size), reverse=True)[0]
    else:
        raise SystemExit('no valid FEX payload available for HELLO.FAP contract proof')

    digest = hashlib.sha256(payload.read_bytes()).hexdigest()
    manifest = {
        'format': 'FAPP1',
        'app_name': 'HelloFrames',
        'target': 'frames-x64',
        'fex_abi': 1,
        'payload': 'APP.FEX',
        'frames_min': '0.9.62',
        'sha256': digest,
        'purpose': 'v72-desktop-contract-proof'
    }
    manifest_bytes = json.dumps(manifest, separators=(',', ':')).encode('utf-8')
    out = root / 'build' / 'HELLO.FAP'
    with zipfile.ZipFile(out, 'w', compression=zipfile.ZIP_STORED, allowZip64=False) as z:
        zi = zipfile.ZipInfo('APP-MANIFEST.json')
        zi.compress_type = zipfile.ZIP_STORED
        zi.flag_bits = 0
        z.writestr(zi, manifest_bytes)
        zi2 = zipfile.ZipInfo('APP.FEX')
        zi2.compress_type = zipfile.ZIP_STORED
        zi2.flag_bits = 0
        z.writestr(zi2, payload.read_bytes())
    print(f'constructed_contract_fapp={out}')
    print(f'payload_fex={payload}')
    print(f'payload_sha256={digest}')
    candidates = packages()

if not candidates:
    raise SystemExit('HELLO.FAP construction failed')

def score(p: Path):
    n=p.name.lower(); path=str(p).lower()
    return (n == 'hello.fap', 'helloframes' in n, 'build' in path, p.stat().st_size)

candidate = sorted(candidates, key=score, reverse=True)[0]
print(f'candidate_fapp={candidate}')
print(f'candidate_size={candidate.stat().st_size}')

# make_esp.py emits a partitioned disk image, not a bare FAT volume. Find the
# actual FAT32 boot sector and use mtools' image@@byte-offset syntax.
data = esp.read_bytes()
fat_offset = None
for off in range(0, len(data) - 512 + 1, 512):
    sec = data[off:off+512]
    if sec[510:512] != b'\x55\xaa':
        continue
    if sec[82:90] == b'FAT32   ' or sec[54:62] == b'FAT16   ':
        fat_offset = off
        break
if fat_offset is None:
    raise SystemExit('unable to locate FAT boot sector inside ESP disk image')
print(f'fat_partition_offset={fat_offset}')
image_spec = f'{esp}@@{fat_offset}'

uefi = expected.replace('\\','/').lstrip('/')
parts = [x for x in uefi.split('/') if x]
if len(parts) < 2:
    raise SystemExit(f'unexpected loader FAPP path: {expected}')
cur='::'
for d in parts[:-1]:
    cur += '/' + d
    subprocess.run(['mmd','-i',image_spec,cur],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
dest='::/' + '/'.join(parts)
subprocess.check_call(['mcopy','-o','-i',image_spec,str(candidate),dest])
subprocess.check_call(['mdir','-i',image_spec,'::/' + '/'.join(parts[:-1])])
print(f'wired_fapp={dest}')
