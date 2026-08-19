#!/usr/bin/env python3
from pathlib import Path
import hashlib, subprocess, sys
if len(sys.argv)!=2: raise SystemExit('usage: patch_v108_r59t2_display_compat.py <kernel/main.nx>')
p=Path(sys.argv[1]); here=Path(__file__).parent
subprocess.run([sys.executable,str(here/'patch_v108_r59t_async_tt_interrupt_probe.py'),str(p)],check=True,stdout=subprocess.DEVNULL)
s=p.read_text(); BASE='8b1c1d40702a35d85e327f50a3e7569c1181352822fa25806349bc55010d8012'
if hashlib.sha256(s.encode()).hexdigest()!=BASE: raise SystemExit('r59t2 exact r59t base mismatch')
rs=s.index('v140_text_wifi_v140(surface,px+10,py+748,white);'); re=s.index('\n    return 1;\n}',rs); row=s[rs:re]
old='let compat=(volatile_read64(xhci+4024))+(volatile_read64(xhci+3984)*0)+(rr/2)%2+(rr/4)%32+(ot/128)%2+(ot/2)%2+(ot/4)%32+(ot/65536)%32768+(ot/2147483648)%2+compat_stage+compat_q+oi+sm+cm+compat_hubproto+compat_ttrc+fls+fi+linked+qmatch+pss; let raw='
new='let packed=volatile_read64(xhci+3992); let xseen=packed%2; let aseen=(packed/2)%2; let minrem=(packed/4)%64; let mmfseen=(packed/131072)%2; let xactseen=(packed/262144)%2; let haltseen=(packed/524288)%2; let compat=(volatile_read64(xhci+4024))+(volatile_read64(xhci+3984)*0)+(rr/2)%2+(rr/4)%32+(ot/128)%2+(ot/2)%2+(ot/4)%32+(ot/65536)%32768+(ot/2147483648)%2+compat_stage+compat_q+oi+sm+cm+compat_hubproto+compat_ttrc+fls+fi+linked+qmatch+pss+xseen+aseen+minrem+mmfseen+xactseen+haltseen; let raw='
if row.count(old)!=1: raise SystemExit('r59t2 display compatibility anchor mismatch '+str(row.count(old)))
row=row.replace(old,new,1); s=s[:rs]+row+s[re:]
for q in ('let mmfseen=(packed/131072)%2','let xactseen=(packed/262144)%2','let haltseen=(packed/524288)%2'):
    if q not in s: raise SystemExit('r59t2 inherited forensic display witness missing '+q)
out=hashlib.sha256(s.encode()).hexdigest(); EXPECTED='74a311e6148d3fae21648bc1a22ddc59f807d04f77137df48ddf37abd91cfb5b'
if out!=EXPECTED: raise SystemExit('r59t2 output sha mismatch '+out)
p.write_text(s); print(out)
