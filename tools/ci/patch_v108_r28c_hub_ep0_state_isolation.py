#!/usr/bin/env python3
from pathlib import Path
import hashlib,subprocess,sys
if len(sys.argv)!=2: raise SystemExit('usage: patch_v108_r28c_hub_ep0_state_isolation.py <kernel/main.nx>')
p=Path(sys.argv[1]); base=Path(__file__).with_name('patch_v108_r28b_ep0_identity.py')
subprocess.run([sys.executable,str(base),str(p)],check=True,stdout=subprocess.DEVNULL)
s=p.read_text()
BASE='f35bf73ef6c28f3a0e58416071a4b231bcf3b9ca632fdff23078a3ef1e479af7'
if hashlib.sha256(s.encode()).hexdigest()!=BASE: raise SystemExit('r28b base mismatch')
# The new root-port LS/FS address-first flag must never leak into the existing
# specialized hub-child BSR enumeration path. A hub child owns a separate slot
# and its r27-compatible address flow must start with an explicitly clean EP0
# mode. This restores the certified VM hub topology while preserving the new
# root LS/FS Address Device + Evaluate Context recovery.
old='volatile_write64(xhci_state+248,0); volatile_write64(xhci_state+256,0); volatile_write64(xhci_state+296,0); volatile_write64(xhci_state+384,0); volatile_write64(xhci_state+416,0);'
new='volatile_write64(xhci_state+248,0); volatile_write64(xhci_state+256,0); volatile_write64(xhci_state+296,0); volatile_write64(xhci_state+384,0); volatile_write64(xhci_state+416,0); volatile_write64(xhci_state+1848,0); volatile_write64(xhci_state+1880,0); volatile_write64(xhci_state+1888,0);'
if s.count(old)!=1: raise SystemExit(f'r28c hub state anchor mismatch {s.count(old)}')
s=s.replace(old,new,1)
# Structural regression contracts.
a=s.index('fn xhci_address_hub_child_v113'); b=s.index('fn serial_marker_usb_hub_keyboard_skipped_v114',a); hub=s[a:b]
for q in ('volatile_write64(xhci_state+1848,0)','volatile_write64(xhci_state+1880,0)','volatile_write64(xhci_state+1888,0)'):
    if q not in hub: raise SystemExit('r28c hub isolation missing '+q)
if 'fn xhci_command_submit_evaluate_v128' not in s or 'if speed<=2 { bsr=0; address_first=1; }' not in s:
    raise SystemExit('r28 root EP0 recovery regression')
if 'fn xhci_event_mailbox_put_v127' not in s or 'fn xhci_event_mailbox_take_v127' not in s:
    raise SystemExit('r27 mailbox regression')
expected='8e1401d483bcff3a5e67caf3c6183fdafe370a3de742675ca0adc255c67d13b5'
actual=hashlib.sha256(s.encode()).hexdigest()
if actual!=expected: raise SystemExit(f'r28c identity mismatch {actual}')
p.write_text(s); print(actual)
