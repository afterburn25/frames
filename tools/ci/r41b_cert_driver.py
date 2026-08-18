#!/usr/bin/env python3
from pathlib import Path
import traceback
here=Path(__file__).parent
base=here/'r41_cert_driver.py'
src=base.read_text()

def one(old,new,label):
    global src
    n=src.count(old)
    if n!=1: raise SystemExit(f'r41b cert anchor {label} count {n}')
    src=src.replace(old,new,1)

def alln(old,new,count,label):
    global src
    n=src.count(old)
    if n!=count: raise SystemExit(f'r41b cert anchor {label} count {n}, expected {count}')
    src=src.replace(old,new)

one("'patch_v108_r41_maxxter_ls_hid_babble_protocol.py'","'patch_v108_r41b_maxxter_usb1_hid_babble_protocol.py'",'patch target')
one('kernel-r41.nx','kernel-r41b.nx','kernel evidence target')
alln('2e201d05458889915040ad726cbd756c41a5429199bee0738f32dd9fe8a9aed4','17139d64aafd6d797bab85fc925da51cf13fc0849cfa4f2a3191fcc3e686c814',2,'exact kernel identity')
one("'Frames-0.9.98-v108-r41-Maxxter-LS-HID-Babble-Protocol-Recovery-Rufus-UEFI.iso'","'Frames-0.9.98-v108-r41b-Maxxter-USB1-HID-Babble-Protocol-Recovery-Rufus-UEFI.iso'",'ISO target')
one("'R41-SHA.txt'","'R41B-SHA.txt'",'SHA evidence target')
one("'R25K-R41.patch'","'R25K-R41B.patch'",'patch evidence target')
one("'FRAMES_V108_R41'","'FRAMES_V108_R41B'",'ISO label target')
one('R41-AGGREGATE.json','R41B-AGGREGATE.json','aggregate target')
one("'frames-0.9.98-v108-r41-maxxter-low-speed-hid-babble-protocol-recovery'","'frames-0.9.98-v108-r41b-maxxter-usb1-hid-babble-protocol-recovery'",'profile target')
one("'Frames 0.9.98 v108 r41 — Maxxter Low-Speed HID Babble + Protocol Recovery'","'Frames 0.9.98 v108 r41b — Maxxter USB1 HID Babble + Protocol Recovery'",'cert title target')
one('R41 PASS_VM_PENDING_PHYSICAL','R41B PASS_VM_PENDING_PHYSICAL','PASS target')
alln('R41-FAILURE.txt','R41B-FAILURE.txt',2,'failure target')
one("'physical_r41':'PENDING'","'physical_r41':'SUPERSEDED_BEFORE_PHYSICAL_BY_USB1_SPEED_SCOPE','physical_r41b':'PENDING'",'physical history target')
one("'speed==2 && vid==9354 && pid==4267 && protocol==2'","'(speed==1 || speed==2) && vid==9354 && pid==4267 && protocol==2'",'USB1 scope compatibility')

anchor="    req('if request<16 { next=16; }' in s and 'if request<32 { next=32; }' in s and 'adaptive<=32' in s,'r41 babble recovery is not bounded to 32 bytes')"
extra=anchor+"""
    req(r37_sha=='17139d64aafd6d797bab85fc925da51cf13fc0849cfa4f2a3191fcc3e686c814','r41b exact kernel identity mismatch '+r37_sha)
    req('(speed==1 || speed==2) && vid==9354 && pid==4267 && protocol==2' in s,'r41b USB1 exact-device scope missing')
    req('speed==2 && vid==9354 && pid==4267 && protocol==2' not in s,'r41b retained low-speed-only poll scope')
"""
if src.count(anchor)!=1: raise SystemExit(f'r41b model-gate injection anchor count {src.count(anchor)}')
src=src.replace(anchor,extra,1)

ns={'__name__':'__main__','__file__':str(base)}
try:
    exec(compile(src,str(base),'exec'),ns,ns)
except BaseException:
    out=Path('evidence'); out.mkdir(parents=True,exist_ok=True)
    (out/'R41B-FAILURE.txt').write_text(traceback.format_exc())
    raise
