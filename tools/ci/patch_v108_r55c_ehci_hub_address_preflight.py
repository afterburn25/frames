#!/usr/bin/env python3
from pathlib import Path
import hashlib, subprocess, sys
if len(sys.argv)!=2: raise SystemExit('usage: patch_v108_r55c_ehci_hub_address_preflight.py <kernel/main.nx>')
p=Path(sys.argv[1]); here=Path(__file__).parent
base=here/'patch_v108_r55b_ehci_intel_hub_discovery_4param.py'
subprocess.run([sys.executable,str(base),str(p)],check=True,stdout=subprocess.DEVNULL)
s=p.read_text()
BASE='038e9e9e930c8d9ae160925d474b13b2919681ed42e17f9584ebbe23f8f5faf2'
actual=hashlib.sha256(s.encode()).hexdigest()
if actual!=BASE: raise SystemExit('r55c exact r55b base mismatch '+actual)

def rep(old,new,label,count=1):
    global s
    n=s.count(old)
    if n!=count: raise SystemExit(f'{label}: {n} expected {count}')
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

old='''    let dma=alloc_dma_page(phys_state,3); if dma==0 { unsafe { volatile_write64(xhci_state+3920,3); } return 3; } unsafe { volatile_write64(xhci_state+4040,dma); }
    var rc=v155_ehci_control(xhci_state,0,66816,0); if rc!=1 { unsafe { volatile_write64(xhci_state+3920,3); volatile_write64(xhci_state+4000,rc); } return 3; }'''
new='''    let dma=volatile_read64(xhci_state+3848); if dma==0 { unsafe { volatile_write64(xhci_state+3920,30); } return 30; } unsafe { volatile_write64(xhci_state+4040,dma); }
    var rc=v155_ehci_control(xhci_state,0,2251799830464128,8); if rc!=1 { unsafe { volatile_write64(xhci_state+3920,20+rc); volatile_write64(xhci_state+4000,rc); } return 20+rc; }
    let pdata=dma+576; if volatile_read8(pdata)<8 || volatile_read8(pdata+1)!=1 || volatile_read8(pdata+7)!=64 { unsafe { volatile_write64(xhci_state+3920,29); } return 29; }
    rc=v155_ehci_control(xhci_state,0,66816,0); if rc!=1 { unsafe { volatile_write64(xhci_state+3920,30+rc); volatile_write64(xhci_state+4000,rc); } return 30+rc; }'''
rep(old,new,'r55c DMA reuse / address preflight')
fnrep('v140_text_wifi_v140',label_fn('v140_text_wifi_v140','R5C S N C E B F T'))

r55c=s[s.index('fn v155_ehci_control'):s.index('fn xhci_configure_boot_hid')]
for q in ('volatile_read64(xhci_state+3848)','2251799830464128','volatile_read8(pdata+7)!=64','30+rc'):
    if q not in r55c: raise SystemExit('r55c model missing '+q)
if 'alloc_dma_page(phys_state,3)' in r55c: raise SystemExit('r55c unexpectedly allocates second DMA page')
if r55c.count('cmd=set_flag(cmd,32)')!=1 or r55c.count('cmd=clear_flag(cmd,32)')<2: raise SystemExit('r55c async schedule bounds changed')
if 'set_flag(cmd,16)' in r55c: raise SystemExit('r55c periodic schedule unexpectedly enabled')
if s.count('{')!=s.count('}'): raise SystemExit('r55c brace mismatch')
out=hashlib.sha256(s.encode()).hexdigest()
EXPECTED='8341c00a24f8dad89dec417dcaa93c1ff648344652cd6fda4ef47afd459f4595'
if out!=EXPECTED: raise SystemExit('r55c output sha mismatch '+out)
p.write_text(s)
print(out)
