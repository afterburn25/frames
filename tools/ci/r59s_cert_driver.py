#!/usr/bin/env python3
from pathlib import Path
import traceback, hashlib

here=Path(__file__).parent
base=here/'r59r_cert_driver.py'
src=base.read_text()

def one(old,new,label):
    global src
    n=src.count(old)
    if n!=1: raise SystemExit(f'r59s cert anchor {label} count {n}')
    src=src.replace(old,new,1)
def alln(old,new,count,label):
    global src
    n=src.count(old)
    if n!=count: raise SystemExit(f'r59s cert anchor {label} count {n}, expected {count}')
    src=src.replace(old,new)

one("'patch_v108_r59r_qh_overlay_completion_capture.py'","'patch_v108_r59s_qh_current_completion_gate.py'",'patch target')
alln('kernel-r59r.nx','kernel-r59s.nx',2,'kernel evidence target')
alln('cb5144a7abb7e610cf893f942360e1b9321fd402494f77e07513cbdcb231a324','dde4777ee5be0e925c2ec487310008343e27cba2b30ba881c996b9cfcad1cb14',2,'exact r59s identity target')
one("'Frames-0.9.98-v108-r59r-QH-Overlay-Completion-Capture-Rufus-UEFI.iso'","'Frames-0.9.98-v108-r59s-QH-Current-Completion-Gate-Rufus-UEFI.iso'",'ISO target')
one("'R59R-SHA.txt'","'R59S-SHA.txt'",'SHA evidence target')
one("'R25K-R59R.patch'","'R25K-R59S.patch'",'patch evidence target')
one("'FRAMES_V108_R59R'","'FRAMES_V108_R59S'",'ISO label target')
one('R59R-AGGREGATE.json','R59S-AGGREGATE.json','aggregate target')
one("'frames-0.9.98-v108-r59r-qh-overlay-completion-capture'","'frames-0.9.98-v108-r59s-qh-current-completion-gate'",'profile target')
one("'Frames 0.9.98 v108 r59r — EHCI QH Overlay Completion Capture'","'Frames 0.9.98 v108 r59s — EHCI QH Current-Only Completion Gate'",'cert title target')
one('R59R PASS_VM_PENDING_PHYSICAL','R59S PASS_VM_PENDING_PHYSICAL','PASS target')
alln('R59R-FAILURE.txt','R59S-FAILURE.txt',2,'failure target')
one('r59r exact kernel identity mismatch','r59s exact kernel identity mismatch','identity label')
one("'physical_r59r':'PENDING'","'physical_r59r':'PHYSICAL_COMPLETION_COUNTER_ZERO_RAW_REPORT_ZERO','physical_r59r_telemetry':'R5R_N0_B0_0_B1_0_B2_0_B3_0_B4_0_B5_0_B6_0_B7_0','physical_r59s':'PENDING'",'physical r59r result + r59s pending')

# Adapt the inherited r59r structural assertion to this repair: QH.Current
# remains mandatory, QH.Next is observed and encoded but is no longer a gate.
one("        'if cur!=qtdlo || next!=1 { return 0; }',","        'if cur!=qtdlo { return 0; }',",'r59r next-gate witness')

ns={'__name__':'__main__','__file__':str(base)}
try:
    exec(compile(src,str(base),'exec'),ns,ns)
    k=Path('evidence/kernel-r59s.nx')
    if not k.exists(): raise SystemExit('r59s evidence kernel missing')
    s=k.read_text()
    if hashlib.sha256(s.encode()).hexdigest()!='dde4777ee5be0e925c2ec487310008343e27cba2b30ba881c996b9cfcad1cb14':
        raise SystemExit('r59s evidence kernel SHA mismatch')
    arm=s[s.index('fn v159_ehci_mouse_periodic_arm'):s.index('fn v159_ehci_mouse_periodic_tick')]
    tick=s[s.index('fn v159_ehci_mouse_periodic_tick'):s.index('fn v135_hid_control_fallback_prepare')]
    for q in (
        'var qmatch:u64=0; if cur==qtdlo { qmatch=1; }',
        'let nterm=next%2',
        'let active=(live_tok/128)%2',
        'let errs=(live_tok/4)%32',
        'let rem=(live_tok/65536)%32768',
        'volatile_write64(xhci_state+3984,gate)',
        'if cur!=qtdlo { return 0; }',
        'let raw=volatile_read64(data)',
        'volatile_write64(xhci_state+4088,raw)',
        'volatile_write32(qh+16,qtdlo)',
    ):
        if q not in tick: raise SystemExit('r59s completion repair witness missing '+q)
    if 'if cur!=qtdlo || next!=1 { return 0; }' in tick:
        raise SystemExit('r59s redundant QH.Next gate remains')
    for q in (
        'volatile_write64(xhci_state+3984,tr_s)',
        'volatile_write64(xhci_state+4072,tr_c)',
        'volatile_write64(xhci_state+4088,tr_changes)',
    ):
        if q not in arm: raise SystemExit('r59s lost inherited split-trace witness '+q)
    for q in ('R5S' not in s, 'raw%256' in s, '(raw/256)%256' in s, '(raw/65536)%256' in s, '(raw/16777216)%256' in s):
        if not q: raise SystemExit('r59s visible gate/report row witness missing')
    low=(arm+tick).lower()
    if any(x in low for x in ('write(10)','nvme_submit_write','ahci_write','fat_write','block_write','input_push(')):
        raise SystemExit('r59s exceeds raw diagnostic/read-only scope')
except BaseException:
    out=Path('evidence'); out.mkdir(parents=True,exist_ok=True)
    (out/'R59S-FAILURE.txt').write_text(traceback.format_exc())
    raise
