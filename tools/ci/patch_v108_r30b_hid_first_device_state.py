#!/usr/bin/env python3
from pathlib import Path
import hashlib,subprocess,sys
if len(sys.argv)!=2: raise SystemExit('usage: patch_v108_r30b_hid_first_device_state.py <kernel/main.nx>')
p=Path(sys.argv[1]); base=Path(__file__).with_name('patch_v108_r30_hid_first_right_click.py')
subprocess.run([sys.executable,str(base),str(p)],check=True,stdout=subprocess.DEVNULL)
s=p.read_text()
BASE='430399228868e7cef069c5a45bb7c687954cc6e87dc9e461ba8669516e82ea4d'
if hashlib.sha256(s.encode()).hexdigest()!=BASE: raise SystemExit('r30 base mismatch')

def rep(old,new,label):
 global s
 n=s.count(old)
 if n!=1: raise SystemExit(f'{label} count {n}')
 s=s.replace(old,new,1)

# r30 proved that removing the storage setup from the discovery pass entirely
# prevents the controlled log from arming when a HID return exits the scanner.
# Keep HID discovery first for each device; only a non-HID device may then be
# considered as an MSC/log target. This preserves the logging contract without
# putting storage class probing in front of the current device's HID probe.
rep('if volatile_read64(hardware_state+712)==0 { unsafe { volatile_write64(hardware_state+912,volatile_read64(hardware_state+912)+1); } }','', 'remove r30 deferred marker')
rep('} else { if root_class==9 {','} else { if volatile_read64(hardware_state+712)==0 { v108_msc_snapshot_v125(xhci_state,hardware_state,phys_state,fr); } if root_class==9 {','deferred MSC after HID-negative')

# A configured MSC leaves device-specific descriptor/endpoint/interface fields
# in the shared controller scratch object. The hardware controller and command/
# event rings must remain live, but the next slot needs a clean per-device view.
helper='''fn xhci_prepare_new_device_v130(xhci_state:u64) -> u64 {
    if xhci_state==0 { return 0; }
    unsafe {
        volatile_write64(xhci_state+136,0); volatile_write64(xhci_state+144,0); volatile_write64(xhci_state+152,0); volatile_write64(xhci_state+160,0); volatile_write64(xhci_state+168,0); volatile_write64(xhci_state+176,0); volatile_write64(xhci_state+184,0); volatile_write64(xhci_state+192,0); volatile_write64(xhci_state+200,0); volatile_write64(xhci_state+208,0); volatile_write64(xhci_state+216,0); volatile_write64(xhci_state+224,0); volatile_write64(xhci_state+232,0); volatile_write64(xhci_state+240,0); volatile_write64(xhci_state+248,0); volatile_write64(xhci_state+256,0); volatile_write64(xhci_state+264,0); volatile_write64(xhci_state+272,0); volatile_write64(xhci_state+280,0); volatile_write64(xhci_state+288,0); volatile_write64(xhci_state+296,0); volatile_write64(xhci_state+304,0); volatile_write64(xhci_state+312,0); volatile_write64(xhci_state+320,0);
        volatile_write64(xhci_state+384,0); volatile_write64(xhci_state+416,0); volatile_write64(xhci_state+488,0); volatile_write64(xhci_state+504,0); volatile_write64(xhci_state+528,0); volatile_write64(xhci_state+536,0); volatile_write64(xhci_state+544,0); volatile_write64(xhci_state+552,0); volatile_write64(xhci_state+560,0); volatile_write64(xhci_state+568,0); volatile_write64(xhci_state+576,0); volatile_write64(xhci_state+584,0); volatile_write64(xhci_state+592,0); volatile_write64(xhci_state+600,0); volatile_write64(xhci_state+608,0); volatile_write64(xhci_state+616,0); volatile_write64(xhci_state+624,0); volatile_write64(xhci_state+632,0); volatile_write64(xhci_state+640,0); volatile_write64(xhci_state+648,0); volatile_write64(xhci_state+656,0); volatile_write64(xhci_state+664,0); volatile_write64(xhci_state+672,0);
        volatile_write64(xhci_state+1104,0); volatile_write64(xhci_state+1112,0); volatile_write64(xhci_state+1120,0); volatile_write64(xhci_state+1128,0); volatile_write64(xhci_state+1136,0); volatile_write64(xhci_state+1144,0); volatile_write64(xhci_state+1152,0); volatile_write64(xhci_state+1160,0); volatile_write64(xhci_state+1168,0); volatile_write64(xhci_state+1176,0); volatile_write64(xhci_state+1184,0); volatile_write64(xhci_state+1192,0); volatile_write64(xhci_state+1200,0); volatile_write64(xhci_state+1208,0); volatile_write64(xhci_state+1216,0); volatile_write64(xhci_state+1224,0); volatile_write64(xhci_state+1232,0); volatile_write64(xhci_state+1240,0); volatile_write64(xhci_state+1848,0); volatile_write64(xhci_state+1856,0); volatile_write64(xhci_state+1864,0); volatile_write64(xhci_state+1872,0); volatile_write64(xhci_state+1880,0); volatile_write64(xhci_state+1888,0); volatile_write64(xhci_state+1896,0); volatile_write64(xhci_state+1904,0);
    }
    return 1;
}
'''
rep('fn v108_xhci_scan_pointer_v116(hardware_state:u64,phys_state:u64,xhci_state:u64,pml4:u64) -> u64 {',helper+'fn v108_xhci_scan_pointer_v116(hardware_state:u64,phys_state:u64,xhci_state:u64,pml4:u64) -> u64 {','device scratch helper')
rep('let slot_ok=xhci_enable_slot(xhci_state);','xhci_prepare_new_device_v130(xhci_state); let slot_ok=xhci_enable_slot(xhci_state);','device scratch reset before slot')

# Contracts: controller-global command/event-ring state is deliberately not
# zeroed by the helper; MSC is only attempted in the HID-negative branch.
if 'fn xhci_prepare_new_device_v130' not in s: raise SystemExit('r30b helper missing')
if 'xhci_prepare_new_device_v130(xhci_state); let slot_ok=xhci_enable_slot' not in s: raise SystemExit('r30b helper not used')
if 'else { if volatile_read64(hardware_state+712)==0 { v108_msc_snapshot_v125' not in s: raise SystemExit('r30b deferred MSC ordering missing')
for q in ('volatile_write64(xhci_state+16,0)','volatile_write64(xhci_state+64,0)','volatile_write64(xhci_state+72,0)','volatile_write64(xhci_state+96,0)'):
 if q in helper: raise SystemExit('r30b helper clears controller-global ring state '+q)
for q in ('var need:u64=1;','v108_text_x2a_v130','v108_text_x2f_v130','v108_text_rbtn_v130'):
 if q not in s: raise SystemExit('r30 physical/right-click regression '+q)
if s.count('{')!=s.count('}'): raise SystemExit('brace imbalance')
expected='d947d603112369340749e6be8397bfed08bf1de49651a0a0602571afcb754c3b'
actual=hashlib.sha256(s.encode()).hexdigest()
if actual!=expected: raise SystemExit(f'r30b identity mismatch {actual}')
p.write_text(s); print(actual)
