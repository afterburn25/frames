#!/usr/bin/env python3
from pathlib import Path
import json, re, sys, hashlib

ROOT=Path('.')
OUT=ROOT/'out'
OUT.mkdir(exist_ok=True)

# Discover the exact Nexus kernel unit by the known physical EHCI function set.
candidates=[]
for p in ROOT.rglob('*.nx'):
    try: s=p.read_text(errors='ignore')
    except Exception: continue
    score=sum(x in s for x in (
        'fn v159_ehci_mouse_periodic_arm',
        'fn v159_ehci_mouse_periodic_tick',
        'v108_pci_nth_ehci_v121',
        'let info2=1090591745',
        'mint!=4',
    ))
    if score>=3: candidates.append((score,p,s))
if not candidates:
    raise SystemExit('r66 FAIL-CLOSED: physical EHCI Nexus unit not found')
candidates.sort(key=lambda x:(-x[0],str(x[1])))
score,p,s=candidates[0]

# Inventory possible low-level PCI/config helpers without guessing a call ABI.
fn_names=re.findall(r'\bfn\s+([A-Za-z0-9_]+)\s*\(',s)
pci_helpers=sorted({n for n in fn_names if 'pci' in n.lower() and any(k in n.lower() for k in ('read','cfg','config'))})
io_helpers=sorted({n for n in fn_names if any(k in n.lower() for k in ('in32','out32','io_read','io_write','port'))})

# Proven endpoint timing/split witnesses. Full-speed bInterval=4 means four frames,
# independently of S/C masks within each selected frame.
witness={
  'kernel_unit':str(p),
  'source_sha256':hashlib.sha256(s.encode()).hexdigest(),
  'ehci_arm': 'fn v159_ehci_mouse_periodic_arm' in s,
  'ehci_tick': 'fn v159_ehci_mouse_periodic_tick' in s,
  'endpoint_interval_4': ('mint!=4' in s or 'mint==4' in s),
  'smask_cmask_01_1c': ('1090591745' in s),
  'ehci2_selector': ('v108_pci_nth_ehci_v121(1)' in s),
  'pci_read_helpers':pci_helpers,
  'io_helpers':io_helpers,
  'required_xhci':'8086:8c31',
  'required_ehci2':'8086:8c2d',
  'required_hub':'8087:8008',
  'required_receiver':'248a:10ab',
  'required_ep':'0x82',
  'required_mps':8,
  'required_interval_frames':4,
  'required_smask':'0x01',
  'required_cmask':'0x1c',
  'routing_registers':{'XUSB2PR':'0xD0','USB2PRM':'0xD4'},
  'ehci_legacy':'EECP -> USBLEGSUP BIOS/OS semaphore -> USBLEGCTLSTS',
  'policy':'read routing registers only; never alter XUSB2PR/USB2PRM in r66',
}
(OUT/'R66-LYNXPOINT-DISCOVERY.json').write_text(json.dumps(witness,indent=2)+'\n')

for key in ('ehci_arm','ehci_tick','endpoint_interval_4','smask_cmask_01_1c','ehci2_selector'):
    if not witness[key]:
        raise SystemExit('r66 FAIL-CLOSED: missing witness '+key)

# Add a source-level contract marker next to the existing reference geometry.
# This is intentionally non-invasive: no PCI routing write is introduced here.
anchor='let r61_ref_info2=1+(28*256)+(1*65536)'
if anchor in s and 'R66_FS_PERIOD_FRAMES' not in s:
    s=s.replace(anchor,'let R66_FS_PERIOD_FRAMES=4; '+anchor,1)
elif 'R66_FS_PERIOD_FRAMES' not in s:
    # r64/newer source may have renamed the r61 variable; bind the marker at the
    # known encoded geometry without changing the encoded QH value.
    anchor2='let info2=1090591745'
    if anchor2 not in s:
        raise SystemExit('r66 FAIL-CLOSED: split-geometry insertion anchor missing')
    s=s.replace(anchor2,'let R66_FS_PERIOD_FRAMES=4; '+anchor2,1)

# Add compile-time constants for the read-only Lynx Point forensic profile.
# Runtime PCI reads are only enabled by a follow-up transform after helper ABI
# discovery; this avoids guessing function signatures or writing routing state.
marker='fn v159_ehci_mouse_periodic_arm'
profile='''// R66_LYNXPOINT_FORENSICS: read-only hardware profile\n// XHCI 8086:8c31; EHCI2 8086:8c2d; hub 8087:8008; receiver 248a:10ab\n// XUSB2PR=0xD0 USB2PRM=0xD4; FS EP82 MPS8 period=4 frames; S=01 C=1c\n'''
if profile not in s:
    s=s.replace(marker,profile+marker,1)

p.write_text(s)
print('R66_KERNEL='+str(p))
print('R66_PCI_HELPERS='+','.join(pci_helpers))
print('R66_IO_HELPERS='+','.join(io_helpers))
print('R66_DISCOVERED_SHA='+hashlib.sha256(s.encode()).hexdigest())
