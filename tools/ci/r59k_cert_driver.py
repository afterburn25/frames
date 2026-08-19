#!/usr/bin/env python3
from pathlib import Path
import traceback
here=Path(__file__).parent

# r59k intentionally routes the live desktop probe through the asynchronous
# TT engine while retaining the original periodic engine as certified source
# evidence. Widen only the inherited r59 live-hook assertion in this checkout.
r59p=here/'r59_cert_driver.py'
r59src=r59p.read_text()
r59old="    req('r59_redraw=v159_ehci_mouse_periodic_tick(xhci)' in s and 'var telemetry_redraw:u64=r59_redraw' in s,'r59 live desktop polling/redraw hook missing')"
r59new="    req((('r59_redraw=v159_ehci_mouse_periodic_tick(xhci)' in s) or ('r59_redraw=v160_ehci_mouse_async_tick(xhci)' in s)) and 'var telemetry_redraw:u64=r59_redraw' in s,'r59/r59k live desktop polling/redraw hook missing')"
if r59src.count(r59old)==1:
    r59p.write_text(r59src.replace(r59old,r59new,1))
elif r59src.count(r59new)!=1:
    raise SystemExit('r59k inherited r59 live-hook compatibility anchor missing')

# r59j's forensic display gate required the full periodic overlay row. r59k
# still reads the live overlay Active/error fields, but intentionally replaces
# split/remaining/toggle display columns with raw mouse buttons/X/Y. Accept
# either the complete r59j row or the explicit r59k async-report row.
r59jp=here/'r59j_cert_driver.py'
r59jsrc=r59jp.read_text()
old_overlay="'volatile_read32(dm+24)' in s and '(ot/128)%2' in s and '(ot/2)%2' in s and '(ot/4)%32' in s and '(ot/65536)%32768' in s and '(ot/2147483648)%2' in s"
new_overlay="(('volatile_read32(dm+24)' in s and '(ot/128)%2' in s and '(ot/2)%2' in s and '(ot/4)%32' in s and '(ot/65536)%32768' in s and '(ot/2147483648)%2' in s) or ('volatile_read32(dm+24)' in s and '(ot/128)%2' in s and '(ot/4)%32' in s and 'rr%256' in s and '(rr/256)%256' in s and '(rr/65536)%256' in s))"
if r59jsrc.count(old_overlay)==1:
    r59jp.write_text(r59jsrc.replace(old_overlay,new_overlay,1))
elif r59jsrc.count(new_overlay)!=1:
    raise SystemExit('r59k inherited r59j overlay compatibility anchor missing')

base=here/'r59j_cert_driver.py'
src=base.read_text()

def one(old,new,label):
    global src
    n=src.count(old)
    if n!=1: raise SystemExit(f'r59k cert anchor {label} count {n}')
    src=src.replace(old,new,1)
def alln(old,new,count,label):
    global src
    n=src.count(old)
    if n!=count: raise SystemExit(f'r59k cert anchor {label} count {n}, expected {count}')
    src=src.replace(old,new)

one("'patch_v108_r59j_correct_split_schedule_overlay.py'","'patch_v108_r59k_ehci_async_tt_mouse_probe.py'",'patch target')
one('kernel-r59j.nx','kernel-r59k.nx','kernel evidence target')
one('69168127d829d3b182ab874fef9bbdd1c734ecffca9e5457f94f8d53b012fc54','5f836f2ae10743c967aa64bccf555cf45804a75a0e17f123ad4c0583c004b0bf','exact r59k identity target')
one("'Frames-0.9.98-v108-r59j-Correct-Split-Schedule-Overlay-Rufus-UEFI.iso'","'Frames-0.9.98-v108-r59k-EHCI-Async-TT-Mouse-Probe-Rufus-UEFI.iso'",'ISO target')
one("'R59J-SHA.txt'","'R59K-SHA.txt'",'SHA evidence target')
one("'R25K-R59J.patch'","'R25K-R59K.patch'",'patch evidence target')
one("'FRAMES_V108_R59J'","'FRAMES_V108_R59K'",'ISO label target')
one('R59J-AGGREGATE.json','R59K-AGGREGATE.json','aggregate target')
one("'frames-0.9.98-v108-r59j-correct-split-schedule-overlay'","'frames-0.9.98-v108-r59k-ehci-async-tt-mouse-probe'",'profile target')
one("'Frames 0.9.98 v108 r59j — Correct EHCI Split Schedule + Live Overlay'","'Frames 0.9.98 v108 r59k — EHCI Async TT Mouse Report Probe'",'cert title target')
one('R59J PASS_VM_PENDING_PHYSICAL','R59K PASS_VM_PENDING_PHYSICAL','PASS target')
alln('R59J-FAILURE.txt','R59K-FAILURE.txt',2,'failure target')
one('r59j exact kernel identity mismatch','r59k exact kernel identity mismatch','identity label')
one("'physical_r59j':'PENDING'",
    "'physical_r59j':'PHYSICAL_QH_ACTIVE_NO_SPLIT_NO_PROGRESS','physical_r59j_telemetry':'R5J_S1_N0_A1_X0_E0_R8_D0','physical_r59k':'PENDING'",
    'physical r59j result + r59k pending')

needle="ns={'__name__':'__main__','__file__':str(base)}"
model="""
# r59k asynchronous TT alternative-path model gates are enforced by the exact
# patch SHA plus these source literals retained in the generated kernel.
"""
one(needle,model+needle,'r59k model marker')

ns={'__name__':'__main__','__file__':str(base)}
try:
    exec(compile(src,str(base),'exec'),ns,ns)
    k=Path('evidence/kernel-r59k.nx')
    if not k.exists(): raise SystemExit('r59k evidence kernel missing')
    s=k.read_text()
    for q in ('fn v160_ehci_mouse_async_arm','fn v160_ehci_mouse_async_tick','let info1=1073774592+2+(ep*256)+(mmps*65536)','let info2=1073807360+(port*8388608)','v160_ehci_mouse_async_arm(xhci)','v160_ehci_mouse_async_tick(xhci)'):
        if q not in s: raise SystemExit('r59k async TT source gate missing '+q)
    if 'input_push(' in s[s.index('fn v160_ehci_mouse_async_arm'):s.index('fn v135_hid_control_fallback_prepare')].lower():
        raise SystemExit('r59k diagnostic scope unexpectedly injects input')
except BaseException:
    out=Path('evidence'); out.mkdir(parents=True,exist_ok=True)
    (out/'R59K-FAILURE.txt').write_text(traceback.format_exc())
    raise
