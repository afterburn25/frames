#!/usr/bin/env python3
from pathlib import Path
import hashlib, subprocess, sys
if len(sys.argv)!=2: raise SystemExit('usage: patch_v108_r58_ehci_composite_hid_census.py <kernel/main.nx>')
p=Path(sys.argv[1]); here=Path(__file__).parent
base=here/'patch_v108_r57_ehci_tt_child_hid_probe.py'
subprocess.run([sys.executable,str(base),str(p)],check=True,stdout=subprocess.DEVNULL)
s=p.read_text()
BASE='bb436345a163096d52a04605c7bfb09cf756f90c06be6830b9ed130bb52e2c36'
actual=hashlib.sha256(s.encode()).hexdigest()
if actual!=BASE: raise SystemExit('r58 exact r57 base mismatch '+actual)

def rep(old,new,label,count=1):
    global s
    n=s.count(old)
    if n!=count: raise SystemExit(f'r58 {label}: {n} expected {count}')
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

old_vars='var off:u64=0; var active:u64=0; var iface:u64=0; var proto:u64=0; var ep:u64=0; var epm:u64=0; var interval:u64=0;'
new_vars='var off:u64=0; var active:u64=0; var active_iface:u64=0; var active_proto:u64=0; var hid_count:u64=0; var k_iface:u64=0; var k_ep:u64=0; var k_mps:u64=0; var k_int:u64=0; var m_iface:u64=0; var m_ep:u64=0; var m_mps:u64=0; var m_int:u64=0;'
rep(old_vars,new_vars,'composite HID locals')
old_if='if dt==4 && dl>=9 { let ic=volatile_read8(data+off+5); let sub=volatile_read8(data+off+6); let pr=volatile_read8(data+off+7); active=0; if ic==3 && sub==1 && (pr==1 || pr==2) { active=1; iface=volatile_read8(data+off+2); proto=pr; } }'
new_if='if dt==4 && dl>=9 { let ic=volatile_read8(data+off+5); let sub=volatile_read8(data+off+6); let pr=volatile_read8(data+off+7); active=0; active_proto=0; active_iface=volatile_read8(data+off+2); if ic==3 && sub==1 && (pr==1 || pr==2) { active=1; active_proto=pr; hid_count=hid_count+1; } }'
rep(old_if,new_if,'interface census')
old_ep='if dt==5 && dl>=7 && active!=0 && ep==0 { let ea=volatile_read8(data+off+2); let attr=volatile_read8(data+off+3); if ea>=128 && attr%4==3 { ep=ea; epm=volatile_read8(data+off+4)+(volatile_read8(data+off+5)*256); interval=volatile_read8(data+off+6); } }'
new_ep='if dt==5 && dl>=7 && active!=0 { let ea=volatile_read8(data+off+2); let attr=volatile_read8(data+off+3); let mx=volatile_read8(data+off+4)+(volatile_read8(data+off+5)*256); let iv=volatile_read8(data+off+6); if ea>=128 && attr%4==3 { if active_proto==1 && k_ep==0 { k_iface=active_iface; k_ep=ea; k_mps=mx; k_int=iv; } else { if active_proto==2 && m_ep==0 { m_iface=active_iface; m_ep=ea; m_mps=mx; m_int=iv; } } } }'
rep(old_ep,new_ep,'split keyboard/mouse endpoint capture')
old_tail='unsafe { volatile_write64(xhci_state+3960,proto); volatile_write64(xhci_state+3968,ep); volatile_write64(xhci_state+3976,epm); volatile_write64(xhci_state+3984,interval); volatile_write64(xhci_state+3992,iface); }\n    if proto==0 || ep==0 || epm==0 { unsafe { volatile_write64(xhci_state+3920,22); } return 22; }\n    unsafe { volatile_write64(xhci_state+3920,1); } return 1;'
new_tail='unsafe { volatile_write64(xhci_state+3936,k_ep); volatile_write64(xhci_state+3944,m_ep); volatile_write64(xhci_state+3952,m_iface); volatile_write64(xhci_state+3960,m_mps); volatile_write64(xhci_state+3968,hid_count); volatile_write64(xhci_state+3976,m_int); volatile_write64(xhci_state+3984,k_iface); volatile_write64(xhci_state+3992,k_mps); }\n    if k_ep==0 && m_ep==0 { unsafe { volatile_write64(xhci_state+3920,22); } return 22; }\n    if m_ep==0 { unsafe { volatile_write64(xhci_state+3920,23); } return 23; }\n    if m_mps==0 { unsafe { volatile_write64(xhci_state+3920,24); } return 24; }\n    unsafe { volatile_write64(xhci_state+3920,1); } return 1;'
rep(old_tail,new_tail,'composite HID result storage')
fnrep('v140_text_wifi_v140',label_fn('v140_text_wifi_v140','R58 S P K M I L C'))

r58=s[s.index('fn v157_ehci_child_hid_probe'):s.index('fn xhci_configure_boot_hid')]
for q in ('hid_count=hid_count+1','active_proto==1 && k_ep==0','active_proto==2 && m_ep==0','volatile_write64(xhci_state+3936,k_ep)','volatile_write64(xhci_state+3944,m_ep)','volatile_write64(xhci_state+3952,m_iface)','volatile_write64(xhci_state+3960,m_mps)','volatile_write64(xhci_state+3968,hid_count)','if m_ep==0','volatile_write64(xhci_state+3920,23)'):
    if q not in r58: raise SystemExit('r58 composite HID model missing '+q)
for bad in ('write(10)','nvme_submit_write','ahci_write','fat_write','block_write'):
    if bad in r58.lower(): raise SystemExit('r58 exceeds read-only descriptor scope '+bad)
if s.count('{')!=s.count('}'): raise SystemExit('r58 brace mismatch')
out=hashlib.sha256(s.encode()).hexdigest()
EXPECTED='e8edf7b8d38982b27b997258230ee5f0a51ebd46586bb6cfca679a00aae16f49'
if out!=EXPECTED: raise SystemExit('r58 output sha mismatch '+out)
p.write_text(s)
print(out)
