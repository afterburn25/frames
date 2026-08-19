#!/usr/bin/env python3
from pathlib import Path
import hashlib, traceback
here=Path(__file__).parent
base=here/'r68_direct_cert_driver.py'
src=base.read_text()

def repl(old,new,label,count=None):
    global src
    n=src.count(old)
    if count is not None and n!=count: raise SystemExit(f'r68b cert anchor {label} count {n}, expected {count}')
    if count is None and n<1: raise SystemExit(f'r68b cert anchor {label} missing')
    src=src.replace(old,new)

repl("'patch_v108_r68_ehci_bios_handoff.py'","'patch_v108_r68b_ehci_bios_handoff_compat.py'",'patch target',1)
repl('kernel-r68.nx','kernel-r68b.nx','kernel evidence',2)
repl('b20e7b5414dd0059c451e64ecf2ec8a918d05b8e099dec712ee0e745dd7d2fbf','d3d29fe3448bcfc781f8dd6634df334ed14066f94df0836f03dec69ae71c5935','kernel identity')
repl("'Frames-0.9.98-v108-r68-EHCI-BIOS-Handoff-Persistent-TT-QH-Rufus-UEFI.iso'","'Frames-0.9.98-v108-r68b-EHCI-BIOS-Handoff-Persistent-TT-QH-Rufus-UEFI.iso'",'ISO target',1)
repl("'R68-SHA.txt'","'R68B-SHA.txt'",'SHA evidence',1)
repl("'R25K-R68.patch'","'R25K-R68B.patch'",'patch evidence',1)
repl("'FRAMES_V108_R68'","'FRAMES_V108_R68B'",'ISO label',1)
repl('R68-AGGREGATE.json','R68B-AGGREGATE.json','aggregate',1)
repl("'frames-0.9.98-v108-r68-ehci-bios-handoff-persistent-tt-qh'","'frames-0.9.98-v108-r68b-ehci-bios-handoff-persistent-tt-qh'",'profile',1)
repl("'Frames 0.9.98 v108 r68 — EHCI Legacy BIOS Handoff + Persistent Intel TT QH'","'Frames 0.9.98 v108 r68b — EHCI Legacy BIOS Handoff + Persistent Intel TT QH'",'title',1)
repl('R68 PASS_VM_PENDING_PHYSICAL','R68B PASS_VM_PENDING_PHYSICAL','PASS label',1)
repl("'R68-FAILURE.txt'","'R68B-FAILURE.txt'",'failure label',2)
repl('r68 exact kernel identity mismatch','r68b exact kernel identity mismatch','identity message',1)
repl("physical_r68':'PENDING","physical_r68':'NOT_PHYSICALLY_TESTED_SUPERSEDED_BY_R68B','physical_r68b':'PENDING",'physical handoff',1)

ns={'__name__':'__main__','__file__':str(base)}
try:
    exec(compile(src,str(base),'exec'),ns,ns)
    k=Path('evidence/kernel-r68b.nx')
    if not k.exists(): raise SystemExit('r68b evidence kernel missing')
    s=k.read_text()
    if hashlib.sha256(s.encode()).hexdigest()!='d3d29fe3448bcfc781f8dd6634df334ed14066f94df0836f03dec69ae71c5935': raise SystemExit('r68b evidence kernel SHA mismatch')
    for q in ('volatile_read64(xhci+3984)','volatile_read64(xhci+3992)','volatile_read64(xhci+4000)','volatile_read64(xhci+4064)','R68 HBOXARE'):
        if q not in s: raise SystemExit('r68b physical telemetry compatibility witness missing '+q)
except BaseException:
    out=Path('evidence'); out.mkdir(parents=True,exist_ok=True)
    (out/'R68B-FAILURE.txt').write_text(traceback.format_exc())
    raise
