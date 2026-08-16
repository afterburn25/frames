#!/usr/bin/env python3
from pathlib import Path
import re, sys

if len(sys.argv) != 2:
    raise SystemExit('usage: instrument_v72_gui_app_host.py PATH_TO_kernel_main.nx')

p = Path(sys.argv[1])
s = p.read_text()
pat = re.compile(r'fn gui_app_host_init\(state:u64,wm:u64,table:u64,count:u64\) -> u64 \{.*?\n\}\nfn gui_app_launch', re.S)
new = '''fn gui_app_host_init(state:u64,wm:u64,table:u64,count:u64) -> u64 {
    serial_desktop_diag(70,count);
    if state==0 { serial_desktop_diag(71,0); return 0; } else { serial_desktop_diag(71,1); }
    if wm==0 { serial_desktop_diag(72,0); return 0; } else { serial_desktop_diag(72,1); }
    if table==0 { serial_desktop_diag(73,0); return 0; } else { serial_desktop_diag(73,1); }
    if count<2 { serial_desktop_diag(74,count); return 0; }
    let mod=table+64;
    let kind=volatile_read64(mod); serial_desktop_diag(75,kind); if kind!=2 { return 0; }
    let flags=volatile_read64(mod+8); serial_desktop_diag(76,flags); if flags%8!=7 { return 0; }
    let fex=volatile_read64(mod+16); serial_desktop_diag(77,fex); if fex==0 { return 0; }
    let size=volatile_read64(mod+24); serial_desktop_diag(78,size); if size<=128 { return 0; }
    let valid=fex_validate_image(fex,size); serial_desktop_diag(79,valid); if valid==0 { return 0; }
    unsafe { volatile_write64(state,1); volatile_write64(state+8,table); volatile_write64(state+16,count); volatile_write64(state+24,fex); volatile_write64(state+32,size); volatile_write64(state+40,0); volatile_write64(state+48,0); volatile_write64(state+136,1); }
    serial_marker_gui_app_contract_ok(); return 1;
}
fn gui_app_launch'''
ns, n = pat.subn(new, s, count=1)
if n != 1:
    raise SystemExit(f'gui_app_host_init replacement count={n}')
p.write_text(ns)
print('instrumented gui_app_host_init contract checks stages 70-79')
