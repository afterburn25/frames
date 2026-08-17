#!/usr/bin/env python3
from pathlib import Path
import hashlib, subprocess, sys
if len(sys.argv)!=2: raise SystemExit('usage: patch_v108_r35b_g750jm_hm87_hid_interval.py <kernel/main.nx>')
p=Path(sys.argv[1])
base=Path(__file__).with_name('patch_v108_r35_hid_control_poll_fallback.py')
subprocess.run([sys.executable,str(base),str(p)],check=True,stdout=subprocess.DEVNULL)
s=p.read_text()
BASE='168f103ae3ba8f6dc403b1fa4c18aab01ab8160bd63387efffd1688ef8532ad0'
if hashlib.sha256(s.encode()).hexdigest()!=BASE: raise SystemExit('r35 base mismatch')

def rep(old,new,label):
    global s
    n=s.count(old)
    if n!=1: raise SystemExit(f'{label} count {n}')
    s=s.replace(old,new,1)

old='''fn xhci_interrupt_interval(speed:u64, binterval:u64) -> u64 {
    if binterval==0 { return 0; }
    if speed>=3 { if binterval>16 { return 0; } return binterval-1; }
    if binterval>255 { return 0; } var v:u64=1; var p:u64=0; while v<binterval { v=v*2; p=p+1; } p=p+3; if p>10 { p=10; } return p;
}'''
new='''fn xhci_interrupt_interval(speed:u64, binterval:u64) -> u64 {
    if binterval==0 { return 0; }
    if speed>=3 { if binterval>16 { return 0; } return binterval-1; }
    if binterval>255 { return 0; }
    // USB low/full-speed interrupt bInterval is in frames. xHCI Interval is an
    // exponent in microframes, so use floor(log2(bInterval*8)), not ceil.
    var v:u64=binterval; var p:u64=0; while v>1 { v=v/2; p=p+1; }
    p=p+3; if p>10 { p=10; } return p;
}'''
rep(old,new,'LS/FS xHCI interval correction')

old='''    let interval=xhci_interrupt_interval(speed,binterval); if slot==0 || output==0 || dci<2 || dci>31 || mps==0 || interval>15 { serial_usb_config_diag(3,(speed*281474976710656)+(dci*1099511627776)+(mps*65536)+interval); return 0; }'''
new='''    let interval=xhci_interrupt_interval(speed,binterval); unsafe { volatile_write64(xhci_state+2664,speed); volatile_write64(xhci_state+2672,binterval); volatile_write64(xhci_state+2680,interval); } if slot==0 || output==0 || dci<2 || dci>31 || mps==0 || interval>15 { serial_usb_config_diag(3,(speed*281474976710656)+(dci*1099511627776)+(mps*65536)+interval); return 0; }'''
rep(old,new,'HID interval physical telemetry')

# ASUS ROG G750JM-class systems use the Lynx Point 8086:8C31 xHCI path already
# present in Frames. Preserve the proven D0/D4/D8/DC routing logic and stamp the
# physically observed HM87 contract (USB2 mask 0x3fff, USB3 mask 0x3f) so later
# evidence can distinguish a true target match from a generic Intel controller.
old='''    let u2r=pci_cfg_read32(bus,dev,fun,208); let u3r=pci_cfg_read32(bus,dev,fun,216); var applied:u64=1;
    if u2m!=0 && u2m!=4294967295 && u2r==u2m { applied=2; }'''
new='''    let u2r=pci_cfg_read32(bus,dev,fun,208); let u3r=pci_cfg_read32(bus,dev,fun,216); var applied:u64=1; var hm87_contract_v135b:u64=0;
    if u2m!=0 && u2m!=4294967295 && u2r==u2m { applied=2; }
    if u2m==16383 && u3m==63 && u2r==u2m && u3r==u3m { hm87_contract_v135b=1; }
    unsafe { volatile_write64(xhci_state+2688,hm87_contract_v135b); }'''
rep(old,new,'G750JM/HM87 Lynx Point contract stamp')

p.write_text(s)
out=hashlib.sha256(s.encode()).hexdigest()
EXPECTED='a9761e17e71d803df703a7cfe6b4461a6d02ea6c398d2299c1f0fd72f48f8b28'
if out!=EXPECTED: raise SystemExit(f'r35b output sha mismatch {out}')
print(out)
