#!/usr/bin/env python3
from pathlib import Path

base=Path(__file__).with_name('r24_cert_driver.py')
s=base.read_text()
old_sha="R24_SHA='4cb9eb6b00e05917f6eb3ea4cf69649420b1e14c9c165761097cab64c40c5f16'"
new_sha="R24_SHA='1b56b621de728aabdbbe8c100f92816564369e984f1fc2b5e4815080011aedaf'"
if s.count(old_sha)!=1:
    raise SystemExit('r24 v2 SHA anchor mismatch')
s=s.replace(old_sha,new_sha,1)
old_patch='patch_v108_physical_input_r24_elan_frame_xhci_reset.py'
new_patch='patch_v108_physical_input_r24b_fixbrace.py'
if s.count(old_patch)!=1:
    raise SystemExit('r24 v2 patch anchor mismatch')
s=s.replace(old_patch,new_patch,1)
ns={'__name__':'__main__','__file__':str(base)}
exec(compile(s,str(base),'exec'),ns,ns)
