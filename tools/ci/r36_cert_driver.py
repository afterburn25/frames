#!/usr/bin/env python3
from pathlib import Path
import hashlib, shutil, subprocess, tempfile, traceback
here=Path(__file__).parent
root=Path.cwd()

def sha(p):
    h=hashlib.sha256()
    with open(p,'rb') as f:
        for b in iter(lambda:f.read(1024*1024),b''): h.update(b)
    return h.hexdigest()

def req(x,msg):
    if not x: raise RuntimeError(msg)

# Derive the exact r36 kernel identity from the protected r21 artifact and the
# deterministic patch chain before the inherited certification driver runs.
r21=root/'r21-candidate/evidence/kernel-r21.nx'
req(r21.is_file(),'exact r21 source missing for r36 identity derivation')
with tempfile.TemporaryDirectory(prefix='r36-ident-') as td:
    k=Path(td)/'kernel-r36.nx'; shutil.copy2(r21,k)
    rr=subprocess.run(['python3',str(here/'patch_v108_r36_nonblocking_interrupt_recovery.py'),str(k)],check=True,text=True,stdout=subprocess.PIPE)
    r36_sha=sha(k); s=k.read_text()
    req(rr.stdout.strip().splitlines()[-1]==r36_sha,'r36 patch stdout identity mismatch')
    req('fn v136_hid_interrupt_recovery_tick' in s,'r36 interrupt recovery tick missing')
    req('fn v136_xhci_endpoint_snapshot' in s and 'volatile_write64(xhci_state+2696,state)' in s,'r36 endpoint output-context snapshot missing')
    req('fn v136_xhci_command_endpoint' in s and '(typ!=14 && typ!=16)' in s,'r36 bounded Reset/Set-TR-Dequeue command path missing')
    req('v135_hid_control_fallback_prepare(xhci,phys_state)' not in s,'r36 startup still invokes blocking EP0 fallback')
    req('v135_hid_control_fallback_poll(xhci,input_state)' not in s,'r36 live loop still invokes blocking EP0 fallback')
    req('if xhci!=0 && volatile_read64(xhci+808)!=0 { xhci_hid_poll_continuous(xhci,input_state); }' in s,'r36 USB poll is not fail-open in desktop loop')
    req('volatile_write64(xhci_state+2784,code)' in s and 'volatile_write64(xhci_state+2792,residue)' in s,'r36 transfer completion telemetry missing')
    req('v108_text_r36_v136' in s and 'volatile_read64(xhci+2696)' in s and 'volatile_read64(xhci+2784)' in s,'r36 physical endpoint telemetry row missing')
    req('ps2_poll_fallback_burst_v112(input_state,24);' in s,'r36 PS/2 fallback service missing')
    req('var v:u64=binterval; var p:u64=0; while v>1 { v=v/2; p=p+1; }' in s,'r36 lost r35b LS/FS interval repair')

# r35 historically required the EP0 fallback to be integrated. Preserve the
# original r35 certifier unchanged and make a private compatibility copy whose
# integration gate now requires the physically justified r36 nonblocking policy.
r35_src=(here/'r35_cert_driver.py').read_text()
old_gate=" req('v135_hid_control_fallback_prepare(xhci,phys_state)' in s and 'v135_hid_control_fallback_poll(xhci,input_state)' in s,'r35 desktop runtime fallback integration missing')"
new_gate=" req('v135_hid_control_fallback_prepare(xhci,phys_state)' not in s and 'v135_hid_control_fallback_poll(xhci,input_state)' not in s,'r36 blocking EP0 fallback remains integrated')"
req(r35_src.count(old_gate)==1,'r36 r35 compatibility gate anchor mismatch')
(here/'r35_r36_compat.py').write_text(r35_src.replace(old_gate,new_gate,1))

# Adapt the already-green r35b wrapper to r36 while retaining every inherited
# VM, interaction, USB, PS/2, logging and safety gate.
base=here/'r35b_cert_driver.py'
src=base.read_text()
repls={
"base=Path(__file__).with_name('r35_cert_driver.py')":"base=Path(__file__).with_name('r35_r36_compat.py')",
"R26_SHA='a9761e17e71d803df703a7cfe6b4461a6d02ea6c398d2299c1f0fd72f48f8b28'":f"R26_SHA='{r36_sha}'",
"patch_v108_r35b_g750jm_hm87_hid_interval.py":"patch_v108_r36_nonblocking_interrupt_recovery.py",
"Frames-0.9.98-v108-r35b-G750JM-HM87-HID-Interval-Recovery-Rufus-UEFI.iso":"Frames-0.9.98-v108-r36-Nonblocking-xHCI-Interrupt-Recovery-Rufus-UEFI.iso",
"R35B-SHA.txt":"R36-SHA.txt",
"R25K-R35B.patch":"R25K-R36.patch",
"FRAMES_V108_R35B":"FRAMES_V108_R36",
"(ROOT/'evidence/R35B-AGGREGATE.json')":"(ROOT/'evidence/R36-AGGREGATE.json')",
"'profile':'frames-0.9.98-v108-r35b-g750jm-hm87-hid-interval-recovery'":"'profile':'frames-0.9.98-v108-r36-nonblocking-xhci-interrupt-recovery'",
"'physical_r35':'NOT_TESTED','physical_r35b':'PENDING'":"'physical_r35':'NOT_TESTED','physical_r35b':'FAIL_USB_PHYSICAL_EP0_MOUSE_TIMEOUT_TOUCHPAD_REGRESSION','physical_r35b_telemetry':'R35_F1_K1_M1_Q270_R78_E12','physical_r36':'PENDING'",
"Frames 0.9.98 v108 r35b — G750JM/HM87 HID Interval Recovery":"Frames 0.9.98 v108 r36 — Nonblocking xHCI Interrupt Recovery",
"print('R35B PASS_VM_PENDING_PHYSICAL',iso_sha)":"print('R36 PASS_VM_PENDING_PHYSICAL',iso_sha)",
"'kernel-r35b.nx'":"'kernel-r36.nx'",
"fail_new=\"(out/'R35B-FAILURE.txt')\"":"fail_new=\"(out/'R36-FAILURE.txt')\"",
"(out/'R35B-FAILURE.txt').write_text(traceback.format_exc())":"(out/'R36-FAILURE.txt').write_text(traceback.format_exc())",
}
for old,new in repls.items():
    n=src.count(old)
    if n!=1: raise SystemExit(f'r36 driver anchor mismatch {old!r}: {n}')
    src=src.replace(old,new,1)
ns={'__name__':'__main__','__file__':str(base)}
try:
    exec(compile(src,str(base),'exec'),ns,ns)
except BaseException:
    out=Path('evidence'); out.mkdir(parents=True,exist_ok=True)
    (out/'R36-FAILURE.txt').write_text(traceback.format_exc())
    raise
