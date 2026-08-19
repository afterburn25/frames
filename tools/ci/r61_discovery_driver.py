#!/usr/bin/env python3
from pathlib import Path
import hashlib, shutil, subprocess, sys, traceback

here=Path(__file__).parent
out=Path('evidence')
out.mkdir(parents=True,exist_ok=True)
try:
    subprocess.run([sys.executable,str(here/'r59s_cert_driver.py')],check=True)
    base=out/'kernel-r59s.nx'
    if not base.exists(): raise SystemExit('r61 discovery exact r59s evidence kernel missing')
    if hashlib.sha256(base.read_bytes()).hexdigest()!='10a1a6550abafe7c593d059eeb983d6a576b19ab46c1dcde6ec71888aa6d4a03':
        raise SystemExit('r61 discovery r59s source identity mismatch')
    target=out/'kernel-r61-discovery.nx'
    shutil.copy2(base,target)
    subprocess.run([sys.executable,str(here/'r61_compat_transform.py'),str(target)],check=True)
    sha=hashlib.sha256(target.read_bytes()).hexdigest()
    (out/'R61-DISCOVERED-SHA.txt').write_text(sha+'  kernel-r61-discovery.nx\n')
    print('R61_DISCOVERED_SHA='+sha)
except BaseException:
    (out/'R61-DISCOVERY-FAILURE.txt').write_text(traceback.format_exc())
    raise
