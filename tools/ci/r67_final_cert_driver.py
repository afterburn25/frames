#!/usr/bin/env python3
# r67 final certification trigger after workflow registration
from pathlib import Path
import traceback
here=Path(__file__).parent
base=here/'r67_cert_driver.py'
src=base.read_text()
old='80b2fa96a6b3fbc6c2f41d2e5f7e7a7d6c152a29fb32ed1351a1bf59f1813397'
new='38c72fb0302ae49abd8315f26712e31f0c92ac8a2ce1c21783ada9461c548b66'
n=src.count(old)
if n<2: raise SystemExit('r67 final identity anchors missing '+str(n))
src=src.replace(old,new)
ns={'__name__':'__main__','__file__':str(base)}
try:
    exec(compile(src,str(base),'exec'),ns,ns)
except BaseException:
    out=Path('evidence'); out.mkdir(parents=True,exist_ok=True)
    (out/'R67-FAILURE.txt').write_text(traceback.format_exc())
    raise
