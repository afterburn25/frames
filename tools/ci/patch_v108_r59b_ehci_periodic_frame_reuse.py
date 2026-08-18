#!/usr/bin/env python3
from pathlib import Path
import hashlib, subprocess, sys
if len(sys.argv)!=2: raise SystemExit('usage: patch_v108_r59b_ehci_periodic_frame_reuse.py <kernel/main.nx>')
p=Path(sys.argv[1]); here=Path(__file__).parent
base=here/'patch_v108_r59_ehci_mouse_periodic_report_probe.py'
subprocess.run([sys.executable,str(base),str(p)],check=True,stdout=subprocess.DEVNULL)
s=p.read_text()
BASE='38544595b9ce8c1d7775319247b9d544adadf16b2526d6ca9dbfb41fa0f7a9b7'
actual=hashlib.sha256(s.encode()).hexdigest()
if actual!=BASE: raise SystemExit('r59b exact r59 base mismatch '+actual)

def rep(old,new,label,count=1):
    global s
    n=s.count(old)
    if n!=count: raise SystemExit(f'r59b {label}: {n} expected {count}')
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

old='    let frame=alloc_dma_page(phys_state,4); if frame==0 { unsafe { volatile_write64(xhci_state+4056,14); } return 14; }'
new='    var frame=volatile_read64(phys_state+48); if frame!=0 { let ledger=volatile_read64(phys_state+112); if ledger==0 || dma_record(ledger,frame,4)==0 { frame=0; } else { unsafe { volatile_write64(phys_state+48,0); } } } else { frame=alloc_dma_page(phys_state,4); } if frame==0 { unsafe { volatile_write64(xhci_state+4056,14); } return 14; }'
rep(old,new,'reserved frame-list page reuse')
fnrep('v140_text_wifi_v140',label_fn('v140_text_wifi_v140','R5B S N C B X Y W'))

r59b=s[s.index('fn v159_ehci_mouse_periodic_arm'):s.index('fn v135_hid_control_fallback_prepare')]
for q in ['volatile_read64(phys_state+48)','dma_record(ledger,frame,4)','volatile_write64(phys_state+48,0)','volatile_write32(op+20,flo)','cmd=set_flag(cmd,16)','v159_ehci_mouse_periodic_tick']:
    if q not in r59b: raise SystemExit('r59b model missing '+q)
for bad in ('write(10)','nvme_submit_write','ahci_write','fat_write','block_write','input_push('):
    if bad in r59b.lower(): raise SystemExit('r59b exceeds diagnostic scope '+bad)
if s.count('{')!=s.count('}'): raise SystemExit('r59b brace mismatch')
out=hashlib.sha256(s.encode()).hexdigest()
EXPECTED='1a5d41c5693b4e01c16eb724b4894748bb5682cbe4c61b05b7934dc1f2c8d033'
if out!=EXPECTED: raise SystemExit('r59b output sha mismatch '+out)
p.write_text(s)
print(out)
