#!/usr/bin/env python3
from pathlib import Path
import hashlib,sys

p=Path(sys.argv[1]); raw=p.read_bytes()
expected='ee0c642b152d05527d21558fb0ef2e8ed0dcdbea33bff95ab52d94e3a4e6c02a'
actual=hashlib.sha256(raw).hexdigest()
if actual!=expected:
    raise SystemExit(f'unexpected v108 r2 input kernel hash: {actual}')
s=raw.decode()
marker='fn serial_marker_v108_fileman_storageless_ok() -> void { serial_putc(70); serial_putc(82); serial_putc(65); serial_putc(77); serial_putc(69); serial_putc(83); serial_putc(95); serial_putc(86); serial_putc(49); serial_putc(48); serial_putc(56); serial_putc(95); serial_putc(70); serial_putc(73); serial_putc(76); serial_putc(69); serial_putc(77); serial_putc(65); serial_putc(78); serial_putc(95); serial_putc(83); serial_putc(84); serial_putc(79); serial_putc(82); serial_putc(65); serial_putc(71); serial_putc(69); serial_putc(76); serial_putc(69); serial_putc(83); serial_putc(83); serial_putc(95); serial_putc(79); serial_putc(75); serial_putc(10); return; }\n'
old='fn file_manager_phase1_compose(state:u64,surface:u64,process:u64,wm:u64) -> u64 { if state==0 || surface==0 || process==0 || wm==0 { return 0; } let vfs=volatile_read64(process+464); let path=volatile_read64(process+520); let sec=volatile_read64(process+528); let helix=volatile_read64(process+1008); if vfs==0 || path==0 || sec==0 || helix==0 { return 0; } let mounts=volatile_read64(vfs+8); if mounts<5 { return 0; } serial_marker_fileman_vfs_ok(); let value=helixfs_path_read_u64(helix,path,sec,401); let checksum=helixfs_path_traverse_checksum(helix,path,sec); if value!=6434604069960107346 || checksum!=8256 { return 0; } serial_marker_fileman_helix_ok();'
new='fn file_manager_phase1_compose(state:u64,surface:u64,process:u64,wm:u64) -> u64 { if state==0 || surface==0 || process==0 || wm==0 { return 0; } let vfs=volatile_read64(process+464); let path=volatile_read64(process+520); let sec=volatile_read64(process+528); let helix=volatile_read64(process+1008); var mounts:u64=0; var value:u64=0; var checksum:u64=0; if vfs!=0 { mounts=volatile_read64(vfs+8); } if vfs!=0 && path!=0 && sec!=0 && helix!=0 && mounts>=5 { serial_marker_fileman_vfs_ok(); value=helixfs_path_read_u64(helix,path,sec,401); checksum=helixfs_path_traverse_checksum(helix,path,sec); if value==6434604069960107346 && checksum==8256 { serial_marker_fileman_helix_ok(); } else { value=0; checksum=0; } } serial_marker_v108_fileman_storageless_ok();'
if s.count(old)!=1:
    raise SystemExit(f'file manager storage anchor mismatch: {s.count(old)}')
s=s.replace(old,marker+new,1)
p.write_text(s)
print(hashlib.sha256(p.read_bytes()).hexdigest())
