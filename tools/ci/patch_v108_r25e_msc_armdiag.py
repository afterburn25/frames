#!/usr/bin/env python3
from pathlib import Path
import hashlib, subprocess, sys

if len(sys.argv)!=2:
    raise SystemExit('usage: patch_v108_r25e_msc_armdiag.py <kernel/main.nx>')
p=Path(sys.argv[1])
base=Path(__file__).with_name('patch_v108_r25d_structfix.py')
subprocess.run([sys.executable,str(base),str(p)],check=True,stdout=subprocess.DEVNULL)
s=p.read_text()
if hashlib.sha256(s.encode()).hexdigest()!='9a2d5a32837841d591fed2102f087efafbc664a135d80e16727e7ddf20a2bb25':
    raise SystemExit('r25d input identity mismatch')

def span(name):
    st=s.index('fn '+name); op=s.index('{',st); d=0
    for i in range(op,len(s)):
        if s[i]=='{': d+=1
        elif s[i]=='}':
            d-=1
            if d==0: return st,i+1
    raise SystemExit('unterminated '+name)
def repl(name,new):
    global s
    a,b=span(name); s=s[:a]+new+s[b:]

repl('usb_msc_capacity_v125',r'''fn usb_msc_capacity_v125(xhci_state:u64) -> u64 {
    if xhci_state==0 || volatile_read64(xhci_state+664)!=1 { serial_usb_msc_diag(21,0); return 0; } var tag:u64=65; serial_usb_msc_diag(22,tag);
    if usb_msc_bot_tur(xhci_state,tag)==0 { tag=tag+1; let sense=usb_msc_bot_in(xhci_state,tag,3,18); if sense==0 { serial_usb_msc_diag(23,tag); return 0; } let sk=volatile_read8(sense+2)%16; serial_usb_msc_diag(24,sk); tag=tag+1; if usb_msc_bot_tur(xhci_state,tag)==0 { serial_usb_msc_diag(25,tag); return 0; } }
    tag=tag+1; let cap=usb_msc_bot_in(xhci_state,tag,37,8); if cap==0 { serial_usb_msc_diag(26,tag); return 0; } let last=usb_read_be32(cap); let block=usb_read_be32(cap+4); if block!=512 { serial_usb_msc_diag(27,(block*4294967296)+last); return 0; } unsafe { volatile_write64(xhci_state+680,block); volatile_write64(xhci_state+688,last); } serial_usb_msc_diag(28,last); return 1;
}''')

repl('flight_log_arm_v125',r'''fn flight_log_arm_v125(fr:u64,msc:u64) -> u64 {
    serial_usb_msc_diag(30,0);
    if fr==0 || msc==0 || volatile_read64(fr)!=1 || volatile_read64(msc+664)!=1 { serial_usb_msc_diag(31,volatile_read64(msc+664)); return 0; } if usb_msc_capacity_v125(msc)==0 { flight_record_v125(fr,262401,1,0); serial_usb_msc_diag(32,0); return 0; }
    if volatile_read64(msc+680)!=512 || volatile_read64(msc+688)!=524287 { flight_record_v125(fr,262401,2,volatile_read64(msc+688)); serial_usb_msc_diag(33,volatile_read64(msc+688)); return 0; }
    let data=usb_msc_bot_read10(msc,73,133132,1); if data==0 { flight_record_v125(fr,262401,3,0); serial_usb_msc_diag(34,73); return 0; }
    if volatile_read64(data)!=2391787741383512646 || volatile_read64(data+8)!=1 || volatile_read64(data+16)!=524288 || volatile_read64(data+24)!=512 || volatile_read64(data+32)!=133120 || volatile_read64(data+72)!=133132 || volatile_read64(data+80)!=3545795563478602310 { flight_record_v125(fr,262401,4,volatile_read64(data)); serial_usb_msc_diag(35,volatile_read64(data)); return 0; }
    let start=volatile_read64(data+40); let end=volatile_read64(data+48); if start<133152 || end<start || end>=395264 || end-start+1>8192 { flight_record_v125(fr,262401,5,start); serial_usb_msc_diag(36,start); return 0; }
    unsafe { volatile_write64(fr+64,1); volatile_write64(fr+72,start); volatile_write64(fr+80,end); volatile_write64(fr+88,start); volatile_write64(fr+120,1); volatile_write64(fr+128,3545795563478602310); }
    flight_record_v125(fr,262400,start,end); serial_usb_msc_diag(37,start); serial_marker_controlled_usb_log_r25(); return 1;
}''')

if s.count('{')!=s.count('}'):
    raise SystemExit('r25e brace imbalance')
expected='fd99d34b262328db9ee3b80755a0f35508f6e5d861504786e39d5417d57367c5'
actual=hashlib.sha256(s.encode()).hexdigest()
if actual!=expected:
    raise SystemExit(f'r25e identity mismatch {actual}')
p.write_text(s)
print(actual)
