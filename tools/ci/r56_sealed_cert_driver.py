#!/usr/bin/env python3
from pathlib import Path
here=Path(__file__).parent

# r54 adapted r52's historic physical-row assertion to recognize the r54
# descriptor overlay. r56 replaces that row again with second-hub census
# telemetry while retaining the same underlying Intel route-before/after
# evidence fields. Extend only that display-shape compatibility assertion.
r54p=here/'r54_cert_driver.py'
r54src=r54p.read_text()
oldseg="or ('volatile_read64(xhci+3792)' in s and 'volatile_read64(xhci+3800)' in s and 'volatile_read64(xhci+3808)' in s and 'volatile_read64(xhci+3816)' in s and 'volatile_read64(xhci+3824)' in s and 'volatile_read64(xhci+3832)' in s and 'volatile_read64(xhci+3840)' in s)) and"
newseg="or ('volatile_read64(xhci+3792)' in s and 'volatile_read64(xhci+3800)' in s and 'volatile_read64(xhci+3808)' in s and 'volatile_read64(xhci+3816)' in s and 'volatile_read64(xhci+3824)' in s and 'volatile_read64(xhci+3832)' in s and 'volatile_read64(xhci+3840)' in s) or ('volatile_read64(xhci+3920)' in s and 'volatile_read64(xhci+3928)' in s and 'volatile_read64(xhci+3936)' in s and 'volatile_read64(xhci+3944)' in s and 'volatile_read64(xhci+3960)' in s and 'volatile_read64(xhci+3968)' in s and 'volatile_read64(xhci+3976)' in s)) and"
if r54src.count(oldseg)!=1: raise SystemExit(f'r56 r54 row-compat anchor count {r54src.count(oldseg)}')
r54p.write_text(r54src.replace(oldseg,newseg,1))

base=here/'r56_cert_driver.py'
src=base.read_text()

def one(old,new,label):
    global src
    n=src.count(old)
    if n!=1: raise SystemExit(f'r56 sealed cert anchor {label} count {n}')
    src=src.replace(old,new,1)

one("'patch_v108_r56_ehci_second_hub_census.py'","'patch_v108_r56_ehci_second_hub_census_sealed.py'",'sealed patch target')
one('0000000000000000000000000000000000000000000000000000000000000000','156c10d74ab7513c1eb72630cdcf425eeaa79d85d4fde463c5f0d9b695199654','sealed exact kernel identity')
ns={'__name__':'__main__','__file__':str(base)}
exec(compile(src,str(base),'exec'),ns,ns)
