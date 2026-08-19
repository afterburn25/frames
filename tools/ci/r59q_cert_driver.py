#!/usr/bin/env python3
from pathlib import Path
import traceback

here=Path(__file__).parent
base=here/'r59p_cert_driver.py'
src=base.read_text()

def one(old,new,label):
    global src
    n=src.count(old)
    if n!=1:
        raise SystemExit(f'r59q cert anchor {label} count {n}')
    src=src.replace(old,new,1)

def alln(old,new,count,label):
    global src
    n=src.count(old)
    if n!=count:
        raise SystemExit(f'r59q cert anchor {label} count {n}, expected {count}')
    src=src.replace(old,new)

one("'patch_v108_r59p_longitudinal_split_forensics.py'","'patch_v108_r59q_csplit_window_trace.py'",'patch target')
alln('kernel-r59p.nx','kernel-r59q.nx',2,'kernel evidence target')
one('74014535e483d0fbc8ad41558b07df7435a4d082f4a6fb7b01989135f52f596e','0a607d7281065ab76102a9a3986ca3ee2713a88b112e8ccf99201e3d09ff5870','exact r59q identity target')
one("'Frames-0.9.98-v108-r59p-Longitudinal-Split-Forensics-Rufus-UEFI.iso'","'Frames-0.9.98-v108-r59q-CSplit-Window-Trace-Rufus-UEFI.iso'",'ISO target')
one("'R59P-SHA.txt'","'R59Q-SHA.txt'",'SHA evidence target')
one("'R25K-R59P.patch'","'R25K-R59Q.patch'",'patch evidence target')
one("'FRAMES_V108_R59P'","'FRAMES_V108_R59Q'",'ISO label target')
one('R59P-AGGREGATE.json','R59Q-AGGREGATE.json','aggregate target')
one("'frames-0.9.98-v108-r59p-longitudinal-split-forensics'","'frames-0.9.98-v108-r59q-csplit-window-trace'",'profile target')
one("'Frames 0.9.98 v108 r59p — Longitudinal EHCI Split Completion Forensics'","'Frames 0.9.98 v108 r59q — EHCI Complete-Split Window Trace'",'cert title target')
one('R59P PASS_VM_PENDING_PHYSICAL','R59Q PASS_VM_PENDING_PHYSICAL','PASS target')
alln('R59P-FAILURE.txt','R59Q-FAILURE.txt',2,'failure target')
one('r59p exact kernel identity mismatch','r59q exact kernel identity mismatch','identity label')

# r59q removes r59p's tick sample counter because +3984 is now the sealed
# Start-Split-window count from the bounded trace. Adapt the inherited private
# witness machinery without weakening historical r59n/r59o/r59p sources.
alln("'volatile_write64(xhci_state+3984,volatile_read64(xhci_state+3984)+1)'","'volatile_write64(xhci_state+3984,tr_s)'",3,'r59p hit-counter witness to r59q trace witness')

# r59p embeds the replacement gate it writes into r59n2 as a triple-quoted
# source string. Remove only the r59p tick-counter witness from that embedded
# gate; r59q keeps every other inherited longitudinal state/error witness.
ng_start=src.index('new_gate = """')
ng_body=ng_start+len('new_gate = """')
ng_end=src.index('"""',ng_body)
ng=src[ng_body:ng_end]
old_ng=",'volatile_write64(xhci_state+3984,tr_s)'"
if ng.count(old_ng)!=1:
    raise SystemExit('r59q embedded r59n2 tick gate witness count '+str(ng.count(old_ng)))
ng=ng.replace(old_ng,'',1)
src=src[:ng_body]+ng+src[ng_end:]

one("'physical_r59p':'PENDING'",
    "'physical_r59p':'PHYSICAL_PERSISTENT_SPLIT_ACTIVE_NO_ERROR_NO_COMPLETION','physical_r59p_telemetry':'R5P_X1_A1_M0_T0_H0_R8_N0','physical_r59q':'PENDING'",
    'physical r59p result + r59q pending')

# r57 privately broadens the historical r52/r54 physical-row assertion as
# later builds replace the bottom telemetry row. r59q replaces that row again,
# but retains the route-before/after writes and exposes its trace state at
# +3984/+3992/+4064/+4072/+4080/+4088. Teach the inherited private adapter to
# accept this new overlay shape without modifying any historical cert source.
r57p=here/'r57_cert_driver.py'
r57src=r57p.read_text()
r57_old="or ('volatile_read64(xhci+3920)' in s and 'volatile_read64(xhci+3928)' in s and 'volatile_read64(xhci+3936)' in s and 'volatile_read64(xhci+3944)' in s and 'volatile_read64(xhci+3952)' in s and 'volatile_read64(xhci+3960)' in s and 'volatile_read64(xhci+3968)' in s)) and 'volatile_write64(xhci_state+3752,before_bit)' in s"
r57_new="or ('volatile_read64(xhci+3920)' in s and 'volatile_read64(xhci+3928)' in s and 'volatile_read64(xhci+3936)' in s and 'volatile_read64(xhci+3944)' in s and 'volatile_read64(xhci+3952)' in s and 'volatile_read64(xhci+3960)' in s and 'volatile_read64(xhci+3968)' in s) or ('volatile_read64(xhci+3984)' in s and 'volatile_read64(xhci+3992)' in s and 'volatile_read64(xhci+4064)' in s and 'volatile_read64(xhci+4072)' in s and 'volatile_read64(xhci+4080)' in s and 'volatile_read64(xhci+4088)' in s)) and 'volatile_write64(xhci_state+3752,before_bit)' in s"
if r57src.count(r57_old)==1:
    r57p.write_text(r57src.replace(r57_old,r57_new,1))
elif r57src.count(r57_new)!=1:
    raise SystemExit('r59q r57/r52 route-row compatibility anchor missing')

# r59 itself opens r57 and extends that same compatibility expression. Make
# its private adapter recognize the already-expanded r59q expression as an
# idempotent valid state instead of aborting before the inherited chain runs.
r59p=here/'r59_cert_driver.py'
r59src=r59p.read_text()
r59_old="elif r57src.count(new_compat)!=1:\n    raise SystemExit('r59 r57/r52 row compatibility anchor missing')"
r59_new="elif r57src.count(new_compat)==1:\n    pass\nelif 'volatile_read64(xhci+3984)' in r57src and 'volatile_read64(xhci+3992)' in r57src and 'volatile_read64(xhci+4064)' in r57src and 'volatile_read64(xhci+4072)' in r57src and 'volatile_read64(xhci+4080)' in r57src and 'volatile_read64(xhci+4088)' in r57src and 'volatile_write64(xhci_state+3752,before_bit)' in r57src and 'volatile_write64(xhci_state+3760,after_bit)' in r57src:\n    pass\nelse:\n    raise SystemExit('r59/r59q r57/r52 row compatibility anchor missing')"
if r59src.count(r59_old)==1:
    r59p.write_text(r59src.replace(r59_old,r59_new,1))
elif r59src.count(r59_new)!=1:
    raise SystemExit('r59q private r59 adapter anchor missing')

ns={'__name__':'__main__','__file__':str(base)}
try:
    exec(compile(src,str(base),'exec'),ns,ns)
    k=Path('evidence/kernel-r59q.nx')
    if not k.exists():
        raise SystemExit('r59q evidence kernel missing')
    s=k.read_text()
    if __import__('hashlib').sha256(s.encode()).hexdigest()!='0a607d7281065ab76102a9a3986ca3ee2713a88b112e8ccf99201e3d09ff5870':
        raise SystemExit('r59q evidence kernel SHA mismatch')
    arm=s[s.index('fn v159_ehci_mouse_periodic_arm'):s.index('fn v159_ehci_mouse_periodic_tick')]
    tick=s[s.index('fn v159_ehci_mouse_periodic_tick'):s.index('fn v135_hid_control_fallback_prepare')]
    for q in (
        'let info1=2+(ep*256)+(speed*4096)+(mmps*65536)',
        'let info2=1090591745',
        'while tr_trans<160 && tr_spins<3000000',
        'if tr_u==0 { tr_s=tr_s+1; }',
        'if tr_u>=2 && tr_u<=4 { tr_c=tr_c+1; }',
        'if tr_tok!=tr_prev { tr_changes=tr_changes+1; tr_prev=tr_tok; }',
        'volatile_write64(xhci_state+3984,tr_s)',
        'volatile_write64(xhci_state+4072,tr_c)',
        'volatile_write64(xhci_state+4088,tr_changes)',
    ):
        if q not in arm:
            raise SystemExit('r59q arm trace certification witness missing '+q)
    for q in (
        'volatile_write64(xhci_state+3992,packed)',
        'volatile_write64(xhci_state+4080,live_tok)',
        'volatile_write64(xhci_state+4064,volatile_read64(xhci_state+4064)+1+(compat_done*0))',
    ):
        if q not in tick:
            raise SystemExit('r59q longitudinal preservation witness missing '+q)
    if 'volatile_write64(xhci_state+3984,volatile_read64(xhci_state+3984)+1)' in tick:
        raise SystemExit('r59q tick still overwrites Start-Split trace count')
    if 'volatile_write64(xhci_state+4072,qmatch)' in tick or 'volatile_write64(xhci_state+4088,fri+(pss*16384))' in tick:
        raise SystemExit('r59q tick still overwrites C-split/token-change trace counters')
    low=(arm+tick).lower()
    if any(x in low for x in ('write(10)','nvme_submit_write','ahci_write','fat_write','block_write','input_push(')):
        raise SystemExit('r59q exceeds diagnostic/read-only scope')
except BaseException:
    out=Path('evidence'); out.mkdir(parents=True,exist_ok=True)
    (out/'R59Q-FAILURE.txt').write_text(traceback.format_exc())
    raise
