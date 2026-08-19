#!/usr/bin/env python3
from pathlib import Path
import traceback

here=Path(__file__).parent
base=here/'r59q_cert_driver.py'
src=base.read_text()

def one(old,new,label):
    global src
    n=src.count(old)
    if n!=1:
        raise SystemExit(f'r59r cert anchor {label} count {n}')
    src=src.replace(old,new,1)

def alln(old,new,count,label):
    global src
    n=src.count(old)
    if n!=count:
        raise SystemExit(f'r59r cert anchor {label} count {n}, expected {count}')
    src=src.replace(old,new)

one("'patch_v108_r59q_csplit_window_trace.py'","'patch_v108_r59r_qh_overlay_completion_capture.py'",'patch target')
alln('kernel-r59q.nx','kernel-r59r.nx',2,'kernel evidence target')
alln('430f84d61833452acabea47fa5616725a067b7244fde913039d076678dc3f62f','cb5144a7abb7e610cf893f942360e1b9321fd402494f77e07513cbdcb231a324',2,'exact r59r identity target')
one("'Frames-0.9.98-v108-r59q-CSplit-Window-Trace-Rufus-UEFI.iso'","'Frames-0.9.98-v108-r59r-QH-Overlay-Completion-Capture-Rufus-UEFI.iso'",'ISO target')
one("'R59Q-SHA.txt'","'R59R-SHA.txt'",'SHA evidence target')
one("'R25K-R59Q.patch'","'R25K-R59R.patch'",'patch evidence target')
one("'FRAMES_V108_R59Q'","'FRAMES_V108_R59R'",'ISO label target')
one('R59Q-AGGREGATE.json','R59R-AGGREGATE.json','aggregate target')
one("'frames-0.9.98-v108-r59q-csplit-window-trace'","'frames-0.9.98-v108-r59r-qh-overlay-completion-capture'",'profile target')
one("'Frames 0.9.98 v108 r59q — EHCI Complete-Split Window Trace'","'Frames 0.9.98 v108 r59r — EHCI QH Overlay Completion Capture'",'cert title target')
one('R59Q PASS_VM_PENDING_PHYSICAL','R59R PASS_VM_PENDING_PHYSICAL','PASS target')
alln('R59Q-FAILURE.txt','R59R-FAILURE.txt',2,'failure target')
one('r59q exact kernel identity mismatch','r59r exact kernel identity mismatch','identity label')
one("'physical_r59q':'PENDING'","'physical_r59q':'PHYSICAL_QH_OVERLAY_COMPLETED_ZERO_REMAINING_STALE_QTD_GATE','physical_r59q_telemetry':'R5Q_S15_C10_D1_X1_A0_E0_R0_N0_INFERRED','physical_r59r':'PENDING'",'physical r59q result + r59r pending')

# r59's original structural gate assumes the qTD memory token is the
# authoritative completion status. r59q physical evidence proves this target
# controller advances the QH overlay while the original qTD token stays stale.
# Broaden only that private certification predicate; retain Active, error, and
# remaining-byte status requirements for either valid status source.
r59p=here/'r59_cert_driver.py'
r59src=r59p.read_text()
old_poll="    req('(tok/128)%2' in r59fn and 'let errs=(tok/4)%32' in r59fn,'r59 qTD completion/error polling missing')"
new_poll="    req(((('(tok/128)%2' in r59fn and 'let errs=(tok/4)%32' in r59fn)) or (('(live_tok/128)%2' in r59fn and 'let errs=(live_tok/4)%32' in r59fn and 'let rem=(live_tok/65536)%32768' in r59fn))),'r59/r59r qTD-or-QH-overlay completion/error polling missing')"
if r59src.count(old_poll)==1:
    r59p.write_text(r59src.replace(old_poll,new_poll,1))
elif r59src.count(new_poll)!=1:
    raise SystemExit('r59r r59 completion-status compatibility anchor missing')

# r59e's original proof spells the qTD physical address inline. r59r assigns
# that exact address to qtdlo first, then compares QH.current against qtdlo.
# It also records the live QH overlay token in the legacy token telemetry slot.
r59ep=here/'r59e_cert_driver.py'
r59esrc=r59ep.read_text()
old_cur="    req('volatile_read32(qh+12)' in r59efn and 'cur==(qtd%4294967296)' in r59efn,'r59e QH current-qTD fetch proof missing')"
new_cur="    req(('volatile_read32(qh+12)' in r59efn and (('cur==(qtd%4294967296)' in r59efn) or ('let qtdlo=qtd%4294967296' in r59efn and 'cur==qtdlo' in r59efn))),'r59e/r59r QH current-qTD fetch proof missing')"
if r59esrc.count(old_cur)==1:
    r59esrc=r59esrc.replace(old_cur,new_cur,1)
elif r59esrc.count(new_cur)!=1:
    raise SystemExit('r59r r59e current-qTD compatibility anchor missing')
old_tok="    req('volatile_write64(xhci_state+4080,tok)' in r59efn,'r59e qTD token telemetry missing')"
new_tok="    req((('volatile_write64(xhci_state+4080,tok)' in r59efn) or ('volatile_write64(xhci_state+4080,live_tok)' in r59efn)),'r59e/r59r execution-token telemetry missing')"
if r59esrc.count(old_tok)==1:
    r59esrc=r59esrc.replace(old_tok,new_tok,1)
elif r59esrc.count(new_tok)!=1:
    raise SystemExit('r59r r59e token-telemetry compatibility anchor missing')
r59ep.write_text(r59esrc)

ns={'__name__':'__main__','__file__':str(base)}
try:
    exec(compile(src,str(base),'exec'),ns,ns)
    k=Path('evidence/kernel-r59r.nx')
    if not k.exists():
        raise SystemExit('r59r evidence kernel missing')
    s=k.read_text()
    if __import__('hashlib').sha256(s.encode()).hexdigest()!='cb5144a7abb7e610cf893f942360e1b9321fd402494f77e07513cbdcb231a324':
        raise SystemExit('r59r evidence kernel SHA mismatch')
    arm=s[s.index('fn v159_ehci_mouse_periodic_arm'):s.index('fn v159_ehci_mouse_periodic_tick')]
    tick=s[s.index('fn v159_ehci_mouse_periodic_tick'):s.index('fn v135_hid_control_fallback_prepare')]
    for q in (
        'let qtd_tok=volatile_read32(qtd+8)',
        'let cur=volatile_read32(qh+12)',
        'let next=volatile_read32(qh+16)',
        'let live_tok=volatile_read32(qh+24)',
        'if cur!=qtdlo || next!=1 { return 0; }',
        'let errs=(live_tok/4)%32',
        'let rem=(live_tok/65536)%32768',
        'let raw=volatile_read64(data)',
        'volatile_write64(xhci_state+4088,raw)',
        'volatile_write32(qh+16,qtdlo)',
        'volatile_write64(xhci_state+4064,volatile_read64(xhci_state+4064)+1+(compat_done*0))',
    ):
        if q not in tick:
            raise SystemExit('r59r QH-overlay completion witness missing '+q)
    if 'if (qtd_tok/128)%2!=0' in tick or 'let errs=(qtd_tok/4)%32' in tick or 'let rem=(qtd_tok/65536)%32768' in tick:
        raise SystemExit('r59r stale qTD token still gates completion')
    for q in (
        'volatile_write64(xhci_state+3984,tr_s)',
        'volatile_write64(xhci_state+4072,tr_c)',
        'volatile_write64(xhci_state+4088,tr_changes)',
    ):
        if q not in arm:
            raise SystemExit('r59r lost inherited C-split trace witness '+q)
    for q in (
        'let raw=volatile_read64(xhci+4088)',
        'raw%256',
        '(raw/256)%256',
        '(raw/65536)%256',
        '(raw/16777216)%256',
        '(raw/4294967296)%256',
        '(raw/1099511627776)%256',
        '(raw/281474976710656)%256',
        '(raw/72057594037927936)%256',
    ):
        if q not in s:
            raise SystemExit('r59r raw report display witness missing '+q)
    low=(arm+tick).lower()
    if any(x in low for x in ('write(10)','nvme_submit_write','ahci_write','fat_write','block_write','input_push(')):
        raise SystemExit('r59r exceeds raw diagnostic/read-only scope')
except BaseException:
    out=Path('evidence'); out.mkdir(parents=True,exist_ok=True)
    (out/'R59R-FAILURE.txt').write_text(traceback.format_exc())
    raise
