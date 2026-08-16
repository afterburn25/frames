#!/usr/bin/env python3
from pathlib import Path
import hashlib,sys

if len(sys.argv)!=2:
    raise SystemExit('usage: patch_full_gui_layout_r2.py PATH_TO_main.nx')
p=Path(sys.argv[1]); s=p.read_text()
repls={
'if wm_move(wm,3,(430*65536)+82)==0 || wm_resize(wm,3,(650*65536)+420)==0 { return 0; }':'if wm_move(wm,3,(300*65536)+40)==0 || wm_resize(wm,3,(500*65536)+280)==0 { return 0; }',
'if wm_move(wm,4,(82*65536)+112)==0 || wm_resize(wm,4,(710*65536)+500)==0 { return 0; }':'if wm_move(wm,4,(50*65536)+340)==0 || wm_resize(wm,4,(740*65536)+340)==0 { return 0; }',
'if wm_move(wm,5,(770*65536)+172)==0 || wm_resize(wm,5,(430*65536)+410)==0 { return 0; }':'if wm_move(wm,5,(830*65536)+120)==0 || wm_resize(wm,5,(400*65536)+420)==0 { return 0; }',
'let r5=wm_record(wm,5); if volatile_read64(r5+8)!=770 || volatile_read64(r5+24)!=430 { return 0; }':'let r5=wm_record(wm,5); if volatile_read64(r5+8)!=830 || volatile_read64(r5+24)!=400 { return 0; }',
'var fr:u64=0; while fr<6 {':'var fr:u64=0; while fr<4 {'
}
for old,new in repls.items():
    if s.count(old)!=1: raise SystemExit('full GUI layout anchor mismatch: '+old[:72])
    s=s.replace(old,new,1)
p.write_text(s)
print('full_gui_layout_r3=PASS')
print('layout=nexus(300,40,500,280) fileman(50,340,740,340) settings(830,120,400,420)')
print('patched_kernel_sha256='+hashlib.sha256(p.read_bytes()).hexdigest())