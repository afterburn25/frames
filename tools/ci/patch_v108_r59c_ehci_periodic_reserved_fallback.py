#!/usr/bin/env python3
from pathlib import Path
import hashlib, subprocess, sys
if len(sys.argv)!=2: raise SystemExit('usage: patch_v108_r59c_ehci_periodic_reserved_fallback.py <kernel/main.nx>')
p=Path(sys.argv[1]); here=Path(__file__).parent
base=here/'patch_v108_r59b_ehci_periodic_frame_reuse.py'
subprocess.run([sys.executable,str(base),str(p)],check=True,stdout=subprocess.DEVNULL)
s=p.read_text()
BASE='1a5d41c5693b4e01c16eb724b4894748bb5682cbe4c61b05b7934dc1f2c8d033'
actual=hashlib.sha256(s.encode()).hexdigest()
if actual!=BASE: raise SystemExit('r59c exact r59b base mismatch '+actual)

def rep(old,new,label,count=1):
    global s
    n=s.count(old)
    if n!=count: raise SystemExit(f'r59c {label}: {n} expected {count}')
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

old='    var frame=volatile_read64(phys_state+48); if frame!=0 { let ledger=volatile_read64(phys_state+112); if ledger==0 || dma_record(ledger,frame,4)==0 { frame=0; } else { unsafe { volatile_write64(phys_state+48,0); } } } else { frame=alloc_dma_page(phys_state,4); } if frame==0 { unsafe { volatile_write64(xhci_state+4056,14); } return 14; }'
new='    let ledger=volatile_read64(phys_state+112); if ledger==0 { unsafe { volatile_write64(xhci_state+4056,26); } return 26; } var frame:u64=0; var rslot:u64=0; let rp3=volatile_read64(phys_state+48); let rp2=volatile_read64(phys_state+40); let rp1=volatile_read64(phys_state+32); if rp3!=0 { frame=rp3; rslot=48; } else { if rp2!=0 { frame=rp2; rslot=40; } else { if rp1!=0 { frame=rp1; rslot=32; } } } if frame!=0 { if dma_record(ledger,frame,4)==0 { unsafe { volatile_write64(xhci_state+4056,27); } return 27; } if rslot==48 { unsafe { volatile_write64(phys_state+48,0); } } else { if rslot==40 { unsafe { volatile_write64(phys_state+40,0); } } else { unsafe { volatile_write64(phys_state+32,0); } } } } else { frame=alloc_dma_page(phys_state,4); if frame==0 { unsafe { volatile_write64(xhci_state+4056,14); } return 14; } }'
rep(old,new,'reserved page fallback ladder')
fnrep('v140_text_wifi_v140',label_fn('v140_text_wifi_v140','R5C S N C B X Y W'))

r59c=s[s.index('fn v159_ehci_mouse_periodic_arm'):s.index('fn v135_hid_control_fallback_prepare')]
for q in ['volatile_read64(phys_state+48)','volatile_read64(phys_state+40)','volatile_read64(phys_state+32)','dma_record(ledger,frame,4)','volatile_write64(xhci_state+4056,26)','volatile_write64(xhci_state+4056,27)','volatile_write32(op+20,flo)','cmd=set_flag(cmd,16)','v159_ehci_mouse_periodic_tick']:
    if q not in r59c: raise SystemExit('r59c model missing '+q)
for bad in ('write(10)','nvme_submit_write','ahci_write','fat_write','block_write','input_push('):
    if bad in r59c.lower(): raise SystemExit('r59c exceeds diagnostic scope '+bad)
if s.count('{')!=s.count('}'): raise SystemExit('r59c brace mismatch')
out=hashlib.sha256(s.encode()).hexdigest()
EXPECTED='e1218ffe017749b252b6e939534f9d191bccbc68433f6a478f8f19c1506cb66c'
if out!=EXPECTED: raise SystemExit('r59c output sha mismatch '+out)
p.write_text(s)
print(out)
