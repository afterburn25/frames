#!/usr/bin/env python3
from pathlib import Path
import subprocess, sys

p=Path(sys.argv[1])
here=Path(__file__).resolve().parent
subprocess.check_call([sys.executable, str(here/'make_r62_physical_xhci_root_port_trace.py'), str(p)])
s=p.read_text()
old='var r62i:u64=0; while r62i<8 { let rv=if diag!=0 { volatile_read64(diag+704+(r62i*8)) } else { 0 }; let lab=80+((49+r62i)*256)+(32*65536)+(32*16777216); pointer_diag_row(surface,(330*65536)+242+(r62i*12),lab,rv); r62i=r62i+1; }'
new='var r62i:u64=0; while r62i<8 { var rv:u64=0; if diag!=0 { rv=volatile_read64(diag+704+(r62i*8)); } let lab=80+((49+r62i)*256)+(32*65536)+(32*16777216); pointer_diag_row(surface,(330*65536)+242+(r62i*12),lab,rv); r62i=r62i+1; }'
if s.count(old)!=1:
    raise SystemExit(f'r62b loop fix: expected 1 site, found {s.count(old)}')
p.write_text(s.replace(old,new,1))
