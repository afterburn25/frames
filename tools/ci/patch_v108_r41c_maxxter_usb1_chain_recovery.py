#!/usr/bin/env python3
from pathlib import Path
import hashlib, subprocess, sys
if len(sys.argv)!=2: raise SystemExit('usage: patch_v108_r41c_maxxter_usb1_chain_recovery.py <kernel/main.nx>')
p=Path(sys.argv[1])
here=Path(__file__).parent
# Reproduce the exact certified r40 transform first. r41 is intentionally a
# delta against that exact kernel and retains its own r40 SHA guard.
subprocess.run([sys.executable,str(here/'patch_v108_r40_usb_hid_identity_wifi_pci_detail_ro.py'),str(p)],check=True,stdout=subprocess.DEVNULL)
if hashlib.sha256(p.read_bytes()).hexdigest()!='ae9598872e6806907e8bb623050f4314dbdda140ecd6b9c620f36e1c669b4c6c':
    raise SystemExit('r41c certified r40 chain mismatch')
subprocess.run([sys.executable,str(here/'patch_v108_r41_maxxter_ls_hid_babble_protocol.py'),str(p)],check=True,stdout=subprocess.DEVNULL)
s=p.read_text()
BASE='2e201d05458889915040ad726cbd756c41a5429199bee0738f32dd9fe8a9aed4'
if hashlib.sha256(s.encode()).hexdigest()!=BASE: raise SystemExit('r41c r41 layer mismatch')

def rep(old,new,label,count=1):
    global s
    n=s.count(old)
    if n!=count: raise SystemExit(f'{label} count {n}, expected {count}')
    s=s.replace(old,new,count)
def fn_text(name):
    st=s.index('fn '+name); op=s.index('{',st); d=0
    for i in range(op,len(s)):
        if s[i]=='{': d+=1
        elif s[i]=='}':
            d-=1
            if d==0:return s[st:i+1]
    raise SystemExit('unterminated '+name)
def label_fn(name,text):
    out=f'fn {name}(surface:u64,x:u64,y:u64,color:u64) -> u64 {{'
    for i,ch in enumerate(text): out+=f' if gui_draw_char_scaled(surface,((x+{i*6})*65536)+y,({ord(ch)}*65536)+1,color)==0 {{ return 0; }}'
    return out+' return 1; }'

# Exact 248A:10AB receiver only. USB xHCI Port Speed ID 1=full, 2=low.
rep('speed==2 && vid==9354 && pid==4267 && proto==2','(speed==1 || speed==2) && vid==9354 && pid==4267 && proto==2','r41c USB1 arm scope')
rep('speed==2 && vid==9354 && pid==4267 && protocol==2','(speed==1 || speed==2) && vid==9354 && pid==4267 && protocol==2','r41c USB1 poll scope')
old=fn_text('v141_text_r41_v141')
rep(old,label_fn('v141_text_r41_v141','R41C G P D L B E'),'r41c physical row label')
out=hashlib.sha256(s.encode()).hexdigest()
EXPECTED='a69444cce8b96a3564016938cd770f8d16e8a7c0136c106574ac0416d7c36bee'
# Expected is updated only after deterministic local/CI transform verification.
# Print candidate SHA when the semantic transform is otherwise valid.
if out!=EXPECTED: raise SystemExit('r41c output sha mismatch '+out)
p.write_text(s); print(out)
