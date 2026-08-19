#!/usr/bin/env python3
from pathlib import Path
import traceback, hashlib
here=Path(__file__).parent
base=here/'r59t_cert_driver.py'
src=base.read_text()

def one(old,new,label):
    global src
    n=src.count(old)
    if n!=1: raise SystemExit(f'r59t2 cert anchor {label} count {n}')
    src=src.replace(old,new,1)
def alln(old,new,count,label):
    global src
    n=src.count(old)
    if n!=count: raise SystemExit(f'r59t2 cert anchor {label} count {n}, expected {count}')
    src=src.replace(old,new)

one("'patch_v108_r59t_async_tt_interrupt_probe.py'","'patch_v108_r59t2_display_compat.py'",'patch target')
alln('kernel-r59t.nx','kernel-r59t2.nx',2,'kernel evidence target')
alln('8b1c1d40702a35d85e327f50a3e7569c1181352822fa25806349bc55010d8012','74a311e6148d3fae21648bc1a22ddc59f807d04f77137df48ddf37abd91cfb5b',2,'exact r59t2 identity target')
one("'Frames-0.9.98-v108-r59t-Async-TT-Interrupt-Probe-Rufus-UEFI.iso'","'Frames-0.9.98-v108-r59t2-Async-TT-Interrupt-Probe-Rufus-UEFI.iso'",'ISO target')
one("'R59T-SHA.txt'","'R59T2-SHA.txt'",'SHA evidence target')
one("'R25K-R59T.patch'","'R25K-R59T2.patch'",'patch evidence target')
one("'FRAMES_V108_R59T'","'FRAMES_V108_R59T2'",'ISO label target')
one('R59T-AGGREGATE.json','R59T2-AGGREGATE.json','aggregate target')
one("'frames-0.9.98-v108-r59t-async-tt-interrupt-probe'","'frames-0.9.98-v108-r59t2-async-tt-interrupt-probe'",'profile target')
one("'Frames 0.9.98 v108 r59t — EHCI Async TT Interrupt-IN Compatibility Probe'","'Frames 0.9.98 v108 r59t2 — EHCI Async TT Interrupt-IN Compatibility Probe'",'cert title target')
one('R59T PASS_VM_PENDING_PHYSICAL','R59T2 PASS_VM_PENDING_PHYSICAL','PASS target')
alln('R59T-FAILURE.txt','R59T2-FAILURE.txt',2,'failure target')
one('r59t exact kernel identity mismatch','r59t2 exact kernel identity mismatch','identity label')
one("'physical_r59t':'PENDING'","'physical_r59t':'CERT_ONLY_NOT_PHYSICAL','physical_r59t2':'PENDING'",'r59t2 physical pending')

ns={'__name__':'__main__','__file__':str(base)}
try:
    exec(compile(src,str(base),'exec'),ns,ns)
    k=Path('evidence/kernel-r59t2.nx')
    if not k.exists(): raise SystemExit('r59t2 evidence kernel missing')
    s=k.read_text()
    if hashlib.sha256(s.encode()).hexdigest()!='74a311e6148d3fae21648bc1a22ddc59f807d04f77137df48ddf37abd91cfb5b':
        raise SystemExit('r59t2 evidence kernel SHA mismatch')
    for q in ('let mmfseen=(packed/131072)%2','let xactseen=(packed/262144)%2','let haltseen=(packed/524288)%2'):
        if q not in s: raise SystemExit('r59t2 inherited display witness missing '+q)
except BaseException:
    out=Path('evidence'); out.mkdir(parents=True,exist_ok=True)
    (out/'R59T2-FAILURE.txt').write_text(traceback.format_exc())
    raise
