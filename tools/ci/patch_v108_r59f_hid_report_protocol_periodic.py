#!/usr/bin/env python3
from pathlib import Path
import hashlib, subprocess, sys
if len(sys.argv)!=2: raise SystemExit('usage: patch_v108_r59f_hid_report_protocol_periodic.py <kernel/main.nx>')
p=Path(sys.argv[1]); here=Path(__file__).parent
base=here/'patch_v108_r59e_ehci_periodic_execution_forensics.py'
subprocess.run([sys.executable,str(base),str(p)],check=True,stdout=subprocess.DEVNULL)
s=p.read_text()
BASE='a582d1f5f8464da49f06b67c9ced5fbf755bbde3106b9cae97991f1ff6f406fa'
actual=hashlib.sha256(s.encode()).hexdigest()
if actual!=BASE: raise SystemExit('r59f exact r59e base mismatch '+actual)

def rep(old,new,label,count=1):
    global s
    n=s.count(old)
    if n!=count: raise SystemExit(f'r59f {label}: {n} expected {count}')
    s=s.replace(old,new,count)

def fn_text(name):
    st=s.index('fn '+name); op=s.index('{',st); d=0
    for i in range(op,len(s)):
        if s[i]=='{': d+=1
        elif s[i]=='}':
            d-=1
            if d==0:return s[st:i+1]
    raise SystemExit('unterminated '+name)

def fnrep(name,new): rep(fn_text(name),new,name)

def label_fn(name,text):
    out=f'fn {name}(surface:u64,x:u64,y:u64,color:u64) -> u64 {{'
    for i,ch in enumerate(text): out+=f' if gui_draw_char_scaled(surface,((x+{i*6})*65536)+y,({ord(ch)}*65536)+1,color)==0 {{ return 0; }}'
    return out+' return 1; }'

old='''    let setproto=33+(11*256)+(mif*4294967296); rc=v157_ehci_tt_control(xhci_state,2,setproto,0); if rc!=1 { unsafe { volatile_write64(xhci_state+3936,kep); volatile_write64(xhci_state+4056,13); volatile_write64(xhci_state+4000,rc); } return 13; }\n    unsafe { volatile_write64(xhci_state+3936,kep); }'''
new='''    let setproto=33+(11*256)+65536+(mif*4294967296); rc=v157_ehci_tt_control(xhci_state,2,setproto,0); if rc!=1 { unsafe { volatile_write64(xhci_state+3936,kep); volatile_write64(xhci_state+4056,13); volatile_write64(xhci_state+4000,rc); } return 13; }\n    pit_wait(23864);\n    let getproto=161+(3*256)+(mif*4294967296)+(1*281474976710656); rc=v157_ehci_tt_control(xhci_state,2,getproto,1); if rc!=1 { unsafe { volatile_write64(xhci_state+3936,kep); volatile_write64(xhci_state+4056,28); volatile_write64(xhci_state+4000,rc); } return 28; }\n    if volatile_read8(dma+576)!=1 { unsafe { volatile_write64(xhci_state+3936,kep); volatile_write64(xhci_state+4056,29); volatile_write64(xhci_state+4000,volatile_read8(dma+576)); } return 29; }\n    unsafe { volatile_write64(xhci_state+3936,kep); }'''
rep(old,new,'report protocol select and verification')
fnrep('v140_text_wifi_v140',label_fn('v140_text_wifi_v140','R5F S N F Q A E P'))

r59f=s[s.index('fn v159_ehci_mouse_periodic_arm'):s.index('fn v135_hid_control_fallback_prepare')]
for q in ['33+(11*256)+65536+(mif*4294967296)','let getproto=161+(3*256)+(mif*4294967296)+(1*281474976710656)','volatile_read8(dma+576)!=1','volatile_read32(qh+12)','volatile_read32(op+12)%16384','volatile_read32(op+4)/16384','volatile_write64(xhci_state+4064,volatile_read64(xhci_state+4064)+1)']:
    if q not in r59f: raise SystemExit('r59f model missing '+q)
for bad in ('write(10)','nvme_submit_write','ahci_write','fat_write','block_write','input_push('):
    if bad in r59f.lower(): raise SystemExit('r59f exceeds diagnostic/read-only scope '+bad)
if s.count('{')!=s.count('}'): raise SystemExit('r59f brace mismatch')
out=hashlib.sha256(s.encode()).hexdigest()
EXPECTED='51103efecc88695f2f75cb786d273d7379c5628424e9f1f391853bdb5e81198e'
if out!=EXPECTED: raise SystemExit('r59f output sha mismatch '+out)
p.write_text(s)
print(out)
