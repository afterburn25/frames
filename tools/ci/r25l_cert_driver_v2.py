#!/usr/bin/env python3
from pathlib import Path
src=Path(__file__).with_name('r25l_cert_driver.py').read_text()
old="R25L_SHA='01958cc0495a68ff12f399a21e7fb8a25d676e5e4a09e9810814d99bc57ca11d'"
new="R25L_SHA='a27cb9e33e6cf060a4e405e63699e2f079d2e0b6c9c30c7dd06fac13b1077f6d'"
if src.count(old)!=1: raise SystemExit('r25l cert SHA anchor mismatch')
src=src.replace(old,new,1)
# The Nexus x64 backend currently supports no more than four function parameters.
needle="def model_gate(r24,r25l):\n a=pathlib.Path(r24).read_text();s=pathlib.Path(r25l).read_text()"
repl="def model_gate(r24,r25l):\n a=pathlib.Path(r24).read_text();s=pathlib.Path(r25l).read_text()\n import re\n for name in ('flight_fat_le16_v125','flight_fat_le32_v125','flight_fat_name_v125','flight_fat_next_v125','flight_fat32_find_root_v125','flight_fat32_contig_v125','flight_log_arm_v125'):\n  m=re.search(r'fn '+name+r'\\(([^)]*)\\)',s);req(m is not None,'missing helper '+name);args=m.group(1).strip();argc=0 if not args else args.count(',')+1;req(argc<=4,f'Nexus x64 ABI parameter overflow {name}={argc}')"
if src.count(needle)!=1: raise SystemExit('model gate anchor mismatch')
src=src.replace(needle,repl,1)
exec(compile(src,'r25l_cert_driver_v2.py','exec'),{'__name__':'__main__','__file__':str(Path(__file__).with_name('r25l_cert_driver.py'))})
