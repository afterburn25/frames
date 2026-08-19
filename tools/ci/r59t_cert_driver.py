#!/usr/bin/env python3
from pathlib import Path
import traceback, hashlib
here=Path(__file__).parent
base=here/'r59s_cert_driver.py'
src=base.read_text()

def one(old,new,label):
    global src
    n=src.count(old)
    if n!=1: raise SystemExit(f'r59t cert anchor {label} count {n}')
    src=src.replace(old,new,1)
def alln(old,new,count,label):
    global src
    n=src.count(old)
    if n!=count: raise SystemExit(f'r59t cert anchor {label} count {n}, expected {count}')
    src=src.replace(old,new)

one("'patch_v108_r59s_qh_current_completion_gate.py'","'patch_v108_r59t_async_tt_interrupt_probe.py'",'patch target')
alln('kernel-r59s.nx','kernel-r59t.nx',2,'kernel evidence target')
alln('10a1a6550abafe7c593d059eeb983d6a576b19ab46c1dcde6ec71888aa6d4a03','8b1c1d40702a35d85e327f50a3e7569c1181352822fa25806349bc55010d8012',2,'exact r59t identity target')
one("'Frames-0.9.98-v108-r59s-QH-Current-Completion-Gate-Rufus-UEFI.iso'","'Frames-0.9.98-v108-r59t-Async-TT-Interrupt-Probe-Rufus-UEFI.iso'",'ISO target')
one("'R59S-SHA.txt'","'R59T-SHA.txt'",'SHA evidence target')
one("'R25K-R59S.patch'","'R25K-R59T.patch'",'patch evidence target')
one("'FRAMES_V108_R59S'","'FRAMES_V108_R59T'",'ISO label target')
one('R59S-AGGREGATE.json','R59T-AGGREGATE.json','aggregate target')
one("'frames-0.9.98-v108-r59s-qh-current-completion-gate'","'frames-0.9.98-v108-r59t-async-tt-interrupt-probe'",'profile target')
one("'Frames 0.9.98 v108 r59s — EHCI QH Current-Only Completion Gate'","'Frames 0.9.98 v108 r59t — EHCI Async TT Interrupt-IN Compatibility Probe'",'cert title target')
one('R59S PASS_VM_PENDING_PHYSICAL','R59T PASS_VM_PENDING_PHYSICAL','PASS target')
alln('R59S-FAILURE.txt','R59T-FAILURE.txt',2,'failure target')
one('r59s exact kernel identity mismatch','r59t exact kernel identity mismatch','identity label')
one("'physical_r59s':'PENDING'","'physical_r59s':'PHYSICAL_QH_CURRENT_MATCH_ACTIVE_REMAINING8_NO_COMPLETION','physical_r59s_telemetry':'R5S_G65761_N0_B0_0_B1_0_B2_0_B3_0','physical_r59t':'PENDING'",'physical r59s result + r59t pending')

# r59t deliberately leaves every historical periodic implementation in source
# for regression certification but switches the live physical hook to the
# already-proven async TT machinery. Broaden only the old hook-shape assertion.
r59p=here/'r59_cert_driver.py'; r59src=r59p.read_text()
old="    req('r59_redraw=v159_ehci_mouse_periodic_tick(xhci)' in s and 'var telemetry_redraw:u64=r59_redraw' in s,'r59 live desktop polling/redraw hook missing')"
new="    req((('r59_redraw=v159_ehci_mouse_periodic_tick(xhci)' in s or 'r59_redraw=v160_ehci_mouse_async_tick(xhci)' in s) and 'var telemetry_redraw:u64=r59_redraw' in s),'r59/r59t live desktop polling/redraw hook missing')"
if r59src.count(old)==1:
    r59p.write_text(r59src.replace(old,new,1))
elif r59src.count(new)!=1:
    raise SystemExit('r59t r59 live-hook compatibility anchor missing')

ns={'__name__':'__main__','__file__':str(base)}
try:
    exec(compile(src,str(base),'exec'),ns,ns)
    k=Path('evidence/kernel-r59t.nx')
    if not k.exists(): raise SystemExit('r59t evidence kernel missing')
    s=k.read_text()
    if hashlib.sha256(s.encode()).hexdigest()!='8b1c1d40702a35d85e327f50a3e7569c1181352822fa25806349bc55010d8012':
        raise SystemExit('r59t evidence kernel SHA mismatch')
    ast=s[s.index('fn v160_ehci_mouse_async_arm'):s.index('fn v160_ehci_mouse_async_tick')]
    tick=s[s.index('fn v160_ehci_mouse_async_tick'):s.index('fn v135_hid_control_fallback_prepare')]
    for q in (
        'let info1=1073774592+2+(ep*256)+(speed*4096)+(mmps*65536)',
        'let info2=1073807360+(port*8388608)',
        'volatile_write32(op+24,qlo)',
        'cmd=set_flag(cmd,32)',
        'cmd=clear_flag(cmd,16)',
        'v157_ehci_tt_control(xhci_state,2,setcfg,0)',
        'v157_ehci_tt_control(xhci_state,2,setproto,0)',
    ):
        if q not in ast: raise SystemExit('r59t async arm witness missing '+q)
    for q in (
        'let qtdtok=volatile_read32(qtd+8)',
        'let qtok=volatile_read32(qh+24)',
        'let ta=(qtdtok/128)%2',
        'let qa=(qtok/128)%2',
        'let sx=(qtok/2)%2',
        'volatile_write64(xhci_state+3984,gate)',
        'let raw=volatile_read64(data)',
        'volatile_write64(xhci_state+4088,raw)',
        'volatile_write32(qtd+8,527744)',
        'cmd=set_flag(cmd,32)',
    ):
        if q not in tick: raise SystemExit('r59t async tick witness missing '+q)
    if 'v160_ehci_mouse_async_arm(xhci,phys_state)' not in s or 'r59_redraw=v160_ehci_mouse_async_tick(xhci)' not in s:
        raise SystemExit('r59t live async hook missing')
    for q in ('fn v159_ehci_mouse_periodic_arm','fn v159_ehci_mouse_periodic_tick','while tr_trans<160 && tr_spins<3000000'):
        if q not in s: raise SystemExit('r59t lost inherited periodic regression model '+q)
    for q in ('raw%256','(raw/256)%256','(raw/65536)%256','(raw/16777216)%256'):
        if q not in s: raise SystemExit('r59t raw report display witness missing '+q)
    low=(ast+tick).lower()
    if any(x in low for x in ('write(10)','nvme_submit_write','ahci_write','fat_write','block_write','input_push(')):
        raise SystemExit('r59t exceeds raw diagnostic/read-only scope')
except BaseException:
    out=Path('evidence'); out.mkdir(parents=True,exist_ok=True)
    (out/'R59T-FAILURE.txt').write_text(traceback.format_exc())
    raise
