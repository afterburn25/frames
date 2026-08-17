#!/usr/bin/env python3
from pathlib import Path
import hashlib, subprocess, sys

if len(sys.argv)!=2:
    raise SystemExit('usage: patch_v108_r25f_msc_inquiry_first.py <kernel/main.nx>')
p=Path(sys.argv[1]); base=Path(__file__).with_name('patch_v108_r25e_msc_armdiag.py')
subprocess.run([sys.executable,str(base),str(p)],check=True,stdout=subprocess.DEVNULL)
s=p.read_text()
if hashlib.sha256(s.encode()).hexdigest()!='fd99d34b262328db9ee3b80755a0f35508f6e5d861504786e39d5417d57367c5': raise SystemExit('r25e identity mismatch')
def span(name):
    st=s.index('fn '+name); op=s.index('{',st); d=0
    for i in range(op,len(s)):
        if s[i]=='{': d+=1
        elif s[i]=='}':
            d-=1
            if d==0:return st,i+1
    raise SystemExit('unterminated '+name)
a,b=span('usb_msc_capacity_v125')
new=r'''fn usb_msc_capacity_v125(xhci_state:u64) -> u64 {
    if xhci_state==0 || volatile_read64(xhci_state+664)!=1 { serial_usb_msc_diag(21,0); return 0; } var tag:u64=65; serial_usb_msc_diag(22,tag);
    let inquiry=usb_msc_bot_in(xhci_state,tag,18,36); if inquiry==0 { serial_usb_msc_diag(23,tag); return 0; } if volatile_read8(inquiry)%32!=0 || volatile_read8(inquiry+4)<31 { serial_usb_msc_diag(24,volatile_read8(inquiry)); return 0; } serial_usb_msc_diag(25,tag); tag=tag+1;
    if usb_msc_bot_tur(xhci_state,tag)==0 { tag=tag+1; let sense=usb_msc_bot_in(xhci_state,tag,3,18); if sense==0 { serial_usb_msc_diag(26,tag); return 0; } let sk=volatile_read8(sense+2)%16; serial_usb_msc_diag(27,sk); tag=tag+1; if usb_msc_bot_tur(xhci_state,tag)==0 { serial_usb_msc_diag(28,tag); return 0; } }
    tag=tag+1; let cap=usb_msc_bot_in(xhci_state,tag,37,8); if cap==0 { serial_usb_msc_diag(29,tag); return 0; } let last=usb_read_be32(cap); let block=usb_read_be32(cap+4); if block!=512 { serial_usb_msc_diag(38,(block*4294967296)+last); return 0; } unsafe { volatile_write64(xhci_state+680,block); volatile_write64(xhci_state+688,last); } serial_usb_msc_diag(39,last); return 1;
}'''
s=s[:a]+new+s[b:]
expected='067a87bc97ae725795bedffd611e4e55dcf9def2f063868768fb4084232c81a5'
actual=hashlib.sha256(s.encode()).hexdigest()
if actual!=expected: raise SystemExit(f'r25f identity mismatch {actual}')
p.write_text(s); print(actual)
