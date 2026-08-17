#!/usr/bin/env python3
from pathlib import Path
import sys, subprocess, hashlib

if len(sys.argv)!=2:
    raise SystemExit('usage: patch_v108_physical_input_r24b_fixbrace.py <kernel/main.nx>')
p=Path(sys.argv[1])
base=Path(__file__).with_name('patch_v108_physical_input_r24_elan_frame_xhci_reset.py')
subprocess.run([sys.executable,str(base),str(p)],check=True,stdout=subprocess.DEVNULL)
s=p.read_text()
old='volatile_write64(hardware_state+632,volatile_read64(xhci_state+1672)); } if port==0 { tries=32; }'
new='volatile_write64(hardware_state+632,volatile_read64(xhci_state+1672)); } } if port==0 { tries=32; }'
if s.count(old)!=1:
    raise SystemExit(f'r24 reset telemetry brace anchor mismatch: {s.count(old)}')
s=s.replace(old,new,1)
if s.count('{')!=s.count('}'):
    raise SystemExit(f'r24 kernel brace imbalance: open={s.count("{")} close={s.count("}")}')
p.write_text(s)
print(hashlib.sha256(s.encode()).hexdigest())
