#!/usr/bin/env python3
from pathlib import Path
import hashlib, traceback

here=Path(__file__).parent
base=here/'r63_cert_driver.py'
src=base.read_text()

def repl(old,new,label,min_count=1):
    global src
    n=src.count(old)
    if n<min_count:
        raise SystemExit(f'r64 cert anchor {label} count {n}, expected >= {min_count}')
    src=src.replace(old,new)

repl("'patch_v108_r63_boot3_control_poll_mouse.py'","'patch_v108_r64_getreport_qtd_forensics.py'",'patch target')
repl('kernel-r63.nx','kernel-r64.nx','kernel evidence target',2)
repl('8f5b1dbad31aaaf68db45ea53bf73df45ae1ae05d83dc96979d1665485721cfd','db605f05538b796d7553ad45cf9de7881b8e111ee8eda30e034a29821b3fd316','exact r64 identity target',2)
repl("'Frames-0.9.98-v108-r63-Boot3-Control-Poll-Mouse-Recovery-Rufus-UEFI.iso'","'Frames-0.9.98-v108-r64-GETREPORT-qTD-Forensics-Rufus-UEFI.iso'",'ISO target')
repl("'R63-SHA.txt'","'R64-SHA.txt'",'SHA evidence target')
repl("'R25K-R63.patch'","'R25K-R64.patch'",'patch evidence target')
repl("'FRAMES_V108_R63'","'FRAMES_V108_R64'",'ISO label target')
repl('R63-AGGREGATE.json','R64-AGGREGATE.json','aggregate target')
repl("'frames-0.9.98-v108-r63-boot3-control-poll-mouse'","'frames-0.9.98-v108-r64-getreport-qtd-forensics'",'profile target')
repl("'Frames 0.9.98 v108 r63 — Three-Byte Boot Mouse Control Poll Recovery'","'Frames 0.9.98 v108 r64 — HID GET_REPORT qTD Forensics'",'cert title target')
repl('R63 PASS_VM_PENDING_PHYSICAL','R64 PASS_VM_PENDING_PHYSICAL','PASS target')
repl("'R63-FAILURE.txt'","'R64-FAILURE.txt'",'failure target',2)
repl('r63 exact kernel identity mismatch','r64 exact kernel identity mismatch','identity label')
repl("'physical_r63':'PENDING'","'physical_r63':'PHYSICAL_GETREPORT3_RC6_NO_ACCEPTED_POLLS','physical_r63_telemetry':'R63_C6_N0_D0_B0_X0_Y0','physical_r64':'PENDING'",'physical r63 result + r64 pending')

# r37's historical driver contains a direct exact-kernel SHA assertion. Later
# cert layers adapt that assertion to each sealed candidate. r64 is another
# deterministic layer, so adjust only the runner-local historical identity
# witness while leaving every r37 structural requirement intact.
r37p=here/'r37_cert_driver.py'; r37src=r37p.read_text()
old37="03f446845e111e35b8cff6b216c5fee2d214dc0a4d6e25898f8a03b891c0c511"
new37="db605f05538b796d7553ad45cf9de7881b8e111ee8eda30e034a29821b3fd316"
if r37src.count(old37)==1:
    r37p.write_text(r37src.replace(old37,new37,1))
elif r37src.count(new37)!=1:
    raise SystemExit('r64 inherited r37 identity adapter anchor missing')

ns={'__name__':'__main__','__file__':str(base)}
try:
    exec(compile(src,str(base),'exec'),ns,ns)
    k=Path('evidence/kernel-r64.nx')
    if not k.exists(): raise SystemExit('r64 evidence kernel missing')
    s=k.read_text()
    if hashlib.sha256(s.encode()).hexdigest()!='db605f05538b796d7553ad45cf9de7881b8e111ee8eda30e034a29821b3fd316':
        raise SystemExit('r64 evidence kernel SHA mismatch')
    hst=s.index('fn v157_ehci_tt_control'); hend=s.index('fn v157_ehci_child_hid_probe'); helper=s[hst:hend]
    ast=s.index('fn v159_ehci_mouse_periodic_arm'); tst=s.index('fn v159_ehci_mouse_periodic_tick'); rst=s.index('fn v162_r61_periodic_reference_arm')
    arm=s[ast:tst]; tick=s[tst:rst]
    for q in (
        'let getreport=161+(1*256)+(256*65536)+(mif*4294967296)+(3*281474976710656)',
        'v157_ehci_tt_control(xhci_state,2,getreport,3)',
    ):
        if q not in tick: raise SystemExit('r64 lost live three-byte GET_REPORT witness '+q)
    for q in (
        'var is_getreport:u64=0',
        'let dactive=(dtok/128)%2',
        'let dhalt=(dtok/64)%2',
        'let derr=(dtok/4)%16',
        'let drem=(dtok/65536)%32768',
        'volatile_write64(xhci_state+3984,dpack)',
        'volatile_write64(xhci_state+3992,spack)',
        'volatile_write64(xhci_state+4000,qpack)',
        'volatile_write64(xhci_state+4008,raw3)',
    ):
        if q not in helper: raise SystemExit('r64 qTD forensic witness missing '+q)
    for q in ('compat_a%2','(compat_a/2)%2','(compat_a/4)%16','compat_a/64','let raw3=volatile_read64(xhci+4008)'):
        if q not in s: raise SystemExit('r64 visible forensic witness missing '+q)
    if 'if rc!=1 { return 0; }' not in tick:
        raise SystemExit('r64 unexpectedly accepts failed GET_REPORT')
    for forbidden in ('volatile_write32(op+20,flo)','cmd=set_flag(cmd,16)','volatile_write32(qtd+8,560512)'):
        if forbidden in arm or forbidden in tick: raise SystemExit('r64 live path still arms periodic transfer '+forbidden)
    if s.count('v162_r61_periodic_reference_arm(')!=1 or s.count('v162_r61_periodic_reference_tick(')!=1 or s.count('v162_r61_gate_reference(')!=1:
        raise SystemExit('r64 reference helper reachability contract failed')
    active=(arm+tick).lower()
    if any(x in active for x in ('write(10)','nvme_submit_write','ahci_write','fat_write','block_write')):
        raise SystemExit('r64 exceeds read-only forensic input scope')
except BaseException:
    out=Path('evidence'); out.mkdir(parents=True,exist_ok=True)
    (out/'R64-FAILURE.txt').write_text(traceback.format_exc())
    raise
