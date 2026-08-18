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

# r55 normally extends that r54 assertion to its own 3920-series overlay. The
# r56-aware r54 assertion above already contains those fields plus r56's EHCI
# ordinal field, so let the old r55 transformer become idempotent rather than
# treating an already-newer assertion as corruption.
r55p=here/'r55_cert_driver.py'
r55src=r55p.read_text()
oldcheck="if src.count(needle)!=1: raise SystemExit(f'r55 r52/r54 row compatibility anchor count {src.count(needle)}')\nsrc=src.replace(needle,replacement,1)"
newcheck="if src.count(needle)==1:\n    src=src.replace(needle,replacement,1)\nelif 'volatile_read64(xhci+3928)' not in src:\n    raise SystemExit(f'r55/r56 r52-r54 row compatibility anchor count {src.count(needle)}')"
if r55src.count(oldcheck)!=1: raise SystemExit(f'r56 r55 idempotent-row anchor count {r55src.count(oldcheck)}')
r55p.write_text(r55src.replace(oldcheck,newcheck,1))

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
