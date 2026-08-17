#!/usr/bin/env python3
from pathlib import Path
import hashlib,subprocess,sys
if len(sys.argv)!=2: raise SystemExit('usage: patch_v108_r25h_restore_bulk_dci.py <kernel/main.nx>')
p=Path(sys.argv[1]);base=Path(__file__).with_name('patch_v108_r25g_bulk_event_diag.py');subprocess.run([sys.executable,str(base),str(p)],check=True,stdout=subprocess.DEVNULL);s=p.read_text()
if hashlib.sha256(s.encode()).hexdigest()!='c2c0a71417e40f21e1ab4bc50daa42b8e105a1a22b2e56e046e7a0c51d672f2b': raise SystemExit('r25g identity mismatch')
old='let config=volatile_read64(xhci_state+544); if xhci_control_no_data_out(xhci_state,2304+(config*65536))==0 { serial_usb_msc_diag(4,config); return 0; }\n    unsafe { volatile_write64(xhci_state+608,inring);'
new='let config=volatile_read64(xhci_state+544); if xhci_control_no_data_out(xhci_state,2304+(config*65536))==0 { serial_usb_msc_diag(4,config); return 0; }\n    // Control-transfer completion reuses +576 for residue telemetry. Restore the discovered bulk endpoint DCIs before BOT begins.\n    unsafe { volatile_write64(xhci_state+576,indci); volatile_write64(xhci_state+584,outdci); }\n    unsafe { volatile_write64(xhci_state+608,inring);'
if s.count(old)!=1: raise SystemExit(f'bulk DCI restore anchor mismatch {s.count(old)}')
s=s.replace(old,new,1)
expected='3d2e3a968043db2bf4c4bd2633f7a2263e4ce41167430db71a7db8ea1cdf9f87';actual=hashlib.sha256(s.encode()).hexdigest()
if actual!=expected: raise SystemExit(f'r25h identity mismatch {actual}')
p.write_text(s);print(actual)
