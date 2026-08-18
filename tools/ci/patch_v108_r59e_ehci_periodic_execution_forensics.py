#!/usr/bin/env python3
from pathlib import Path
import hashlib, subprocess, sys
if len(sys.argv)!=2: raise SystemExit('usage: patch_v108_r59e_ehci_periodic_execution_forensics.py <kernel/main.nx>')
p=Path(sys.argv[1]); here=Path(__file__).parent
base=here/'patch_v108_r59d_dma_ledger_capacity.py'
subprocess.run([sys.executable,str(base),str(p)],check=True,stdout=subprocess.DEVNULL)
s=p.read_text()
BASE='0b66bdc0bc1733985f835b86d5ed7862638dea7af682aec703e224b6b3d34f3d'
actual=hashlib.sha256(s.encode()).hexdigest()
if actual!=BASE: raise SystemExit('r59e exact r59d base mismatch '+actual)

def rep(old,new,label,count=1):
    global s
    n=s.count(old)
    if n!=count: raise SystemExit(f'r59e {label}: {n} expected {count}')
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

fnrep('v140_text_wifi_v140',label_fn('v140_text_wifi_v140','R5E S N F Q A E P'))
oldrow='    v140_text_wifi_v140(surface,px+10,py+748,white); if xhci!=0 { let rr=volatile_read64(xhci+4080); v108_draw_small_u64(surface,((px+112)*65536)+(py+748),volatile_read64(xhci+4056),green); v108_draw_small_u64(surface,((px+150)*65536)+(py+748),volatile_read64(xhci+4064),amber); v108_draw_small_u64(surface,((px+188)*65536)+(py+748),volatile_read64(xhci+4072),white); v108_draw_small_u64(surface,((px+226)*65536)+(py+748),rr%256,green); v108_draw_small_u64(surface,((px+264)*65536)+(py+748),(rr/256)%256,amber); v108_draw_small_u64(surface,((px+306)*65536)+(py+748),(rr/65536)%256,white); v108_draw_small_u64(surface,((px+350)*65536)+(py+748),(rr/16777216)%256,white); }'
newrow='    v140_text_wifi_v140(surface,px+10,py+748,white); if xhci!=0 { let rr=volatile_read64(xhci+4080); let fm=volatile_read64(xhci+4088); v108_draw_small_u64(surface,((px+112)*65536)+(py+748),volatile_read64(xhci+4056),green); v108_draw_small_u64(surface,((px+150)*65536)+(py+748),volatile_read64(xhci+4064),amber); v108_draw_small_u64(surface,((px+188)*65536)+(py+748),fm%16384,white); v108_draw_small_u64(surface,((px+226)*65536)+(py+748),volatile_read64(xhci+4072),green); v108_draw_small_u64(surface,((px+264)*65536)+(py+748),(rr/128)%2,amber); v108_draw_small_u64(surface,((px+306)*65536)+(py+748),(rr/4)%32,white); v108_draw_small_u64(surface,((px+350)*65536)+(py+748),(fm/16384)%2,white); }'
rep(oldrow,newrow,'forensic row')
oldactive='    if (tok/128)%2!=0 { return 0; }'
newactive='    if (tok/128)%2!=0 { let cur=volatile_read32(qh+12); var qmatch:u64=0; if cur==(qtd%4294967296) { qmatch=1; } let fri=volatile_read32(op+12)%16384; let pss=(volatile_read32(op+4)/16384)%2; unsafe { volatile_write64(xhci_state+4072,qmatch); volatile_write64(xhci_state+4080,tok); volatile_write64(xhci_state+4088,fri+(pss*16384)); } return 0; }'
rep(oldactive,newactive,'active qTD forensics')
oldcomp='    let raw=volatile_read64(data); let prev=volatile_read64(xhci_state+4088); unsafe { volatile_write64(xhci_state+4064,volatile_read64(xhci_state+4064)+1); volatile_write64(xhci_state+4080,raw); if raw!=prev { volatile_write64(xhci_state+4072,volatile_read64(xhci_state+4072)+1); volatile_write64(xhci_state+4088,raw); } volatile_write64(data,0); volatile_write32(qtd+0,1); volatile_write32(qtd+4,1); volatile_write32(qtd+8,527744); volatile_write32(qh+16,qtd%4294967296); volatile_write32(qh+20,1); }'
newcomp='    let cur=volatile_read32(qh+12); var qmatch:u64=0; if cur==(qtd%4294967296) { qmatch=1; } let fri=volatile_read32(op+12)%16384; let pss=(volatile_read32(op+4)/16384)%2; unsafe { volatile_write64(xhci_state+4064,volatile_read64(xhci_state+4064)+1); volatile_write64(xhci_state+4072,qmatch); volatile_write64(xhci_state+4080,tok); volatile_write64(xhci_state+4088,fri+(pss*16384)); volatile_write64(data,0); volatile_write32(qtd+0,1); volatile_write32(qtd+4,1); volatile_write32(qtd+8,527744); volatile_write32(qh+16,qtd%4294967296); volatile_write32(qh+20,1); }'
rep(oldcomp,newcomp,'completion forensics')

r59e=s[s.index('fn v159_ehci_mouse_periodic_arm'):s.index('fn v135_hid_control_fallback_prepare')]
for q in ['volatile_read32(qh+12)','cur==(qtd%4294967296)','volatile_read32(op+12)%16384','volatile_read32(op+4)/16384','volatile_write64(xhci_state+4072,qmatch)','volatile_write64(xhci_state+4080,tok)','volatile_write64(xhci_state+4088,fri+(pss*16384))','volatile_write64(xhci_state+4064,volatile_read64(xhci_state+4064)+1)']:
    if q not in r59e: raise SystemExit('r59e forensic model missing '+q)
for bad in ('write(10)','nvme_submit_write','ahci_write','fat_write','block_write','input_push('):
    if bad in r59e.lower(): raise SystemExit('r59e exceeds forensic/read-only scope '+bad)
if s.count('{')!=s.count('}'): raise SystemExit('r59e brace mismatch')
out=hashlib.sha256(s.encode()).hexdigest()
EXPECTED='a582d1f5f8464da49f06b67c9ced5fbf755bbde3106b9cae97991f1ff6f406fa'
if out!=EXPECTED: raise SystemExit('r59e output sha mismatch '+out)
p.write_text(s)
print(out)
