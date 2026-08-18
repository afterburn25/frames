#!/usr/bin/env python3
from pathlib import Path
import hashlib, subprocess, sys
if len(sys.argv)!=2: raise SystemExit('usage: patch_v108_r59g_ehci_split_state_control_report.py <kernel/main.nx>')
p=Path(sys.argv[1]); here=Path(__file__).parent
base=here/'patch_v108_r59f_hid_report_protocol_periodic.py'
subprocess.run([sys.executable,str(base),str(p)],check=True,stdout=subprocess.DEVNULL)
s=p.read_text()
BASE='51103efecc88695f2f75cb786d273d7379c5628424e9f1f391853bdb5e81198e'
actual=hashlib.sha256(s.encode()).hexdigest()
if actual!=BASE: raise SystemExit('r59g exact r59f base mismatch '+actual)

def rep(old,new,label,count=1):
    global s
    n=s.count(old)
    if n!=count: raise SystemExit(f'r59g {label}: {n} expected {count}')
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

fnrep('v140_text_wifi_v140',label_fn('v140_text_wifi_v140','R5G S N I X G M C'))
old='''    if volatile_read8(dma+576)!=1 { unsafe { volatile_write64(xhci_state+3936,kep); volatile_write64(xhci_state+4056,29); volatile_write64(xhci_state+4000,volatile_read8(dma+576)); } return 29; }\n    unsafe { volatile_write64(xhci_state+3936,kep); }'''
new='''    if volatile_read8(dma+576)!=1 { unsafe { volatile_write64(xhci_state+3936,kep); volatile_write64(xhci_state+4056,29); volatile_write64(xhci_state+4000,volatile_read8(dma+576)); } return 29; }\n    let greq=161+(1*256)+(256*65536)+(mif*4294967296)+(8*281474976710656); let grc=v157_ehci_tt_control(xhci_state,2,greq,8); var grow:u64=0; if grc==1 { grow=volatile_read64(dma+576); } unsafe { volatile_write64(xhci_state+3984,grc); volatile_write64(xhci_state+3992,grow); }\n    unsafe { volatile_write64(xhci_state+3936,kep); }'''
rep(old,new,'HID GET_REPORT control probe')
oldrow='''    v140_text_wifi_v140(surface,px+10,py+748,white); if xhci!=0 { let rr=volatile_read64(xhci+4080); let fm=volatile_read64(xhci+4088); v108_draw_small_u64(surface,((px+112)*65536)+(py+748),volatile_read64(xhci+4056),green); v108_draw_small_u64(surface,((px+150)*65536)+(py+748),volatile_read64(xhci+4064),amber); v108_draw_small_u64(surface,((px+188)*65536)+(py+748),fm%16384,white); v108_draw_small_u64(surface,((px+226)*65536)+(py+748),volatile_read64(xhci+4072),green); v108_draw_small_u64(surface,((px+264)*65536)+(py+748),(rr/128)%2,amber); v108_draw_small_u64(surface,((px+306)*65536)+(py+748),(rr/4)%32,white); v108_draw_small_u64(surface,((px+350)*65536)+(py+748),(fm/16384)%2,white); }'''
newrow='''    v140_text_wifi_v140(surface,px+10,py+748,white); if xhci!=0 { let rr=volatile_read64(xhci+4080); let dm=volatile_read64(xhci+4040); var sm:u64=0; var cm:u64=0; if dm!=0 { let qi=volatile_read32(dm+8); sm=qi%256; cm=(qi/256)%256; } v108_draw_small_u64(surface,((px+112)*65536)+(py+748),volatile_read64(xhci+4056),green); v108_draw_small_u64(surface,((px+150)*65536)+(py+748),volatile_read64(xhci+4064),amber); v108_draw_small_u64(surface,((px+188)*65536)+(py+748),volatile_read64(xhci+3976),white); v108_draw_small_u64(surface,((px+226)*65536)+(py+748),(rr/2)%2,green); v108_draw_small_u64(surface,((px+264)*65536)+(py+748),volatile_read64(xhci+3984),amber); v108_draw_small_u64(surface,((px+306)*65536)+(py+748),sm,white); v108_draw_small_u64(surface,((px+350)*65536)+(py+748),cm,white); }'''
rep(oldrow,newrow,'split-state geometry row')

r59g=s[s.index('fn v159_ehci_mouse_periodic_arm'):s.index('fn v135_hid_control_fallback_prepare')]
for q in ['161+(1*256)+(256*65536)+(mif*4294967296)+(8*281474976710656)','volatile_write64(xhci_state+3984,grc)','volatile_write64(xhci_state+3992,grow)','volatile_read64(xhci_state+3976)','(rr/2)%2','sm=qi%256','cm=(qi/256)%256']:
    if q not in s: raise SystemExit('r59g forensic model missing '+q)
for bad in ('write(10)','nvme_submit_write','ahci_write','fat_write','block_write','input_push('):
    if bad in r59g.lower(): raise SystemExit('r59g exceeds diagnostic/read-only scope '+bad)
if s.count('{')!=s.count('}'): raise SystemExit('r59g brace mismatch')
out=hashlib.sha256(s.encode()).hexdigest()
EXPECTED='4381aec1a83db1eeb7baa55e803aacecff30e7b6154238bff892a51fbf0e1dd7'
if out!=EXPECTED: raise SystemExit('r59g output sha mismatch '+out)
p.write_text(s)
print(out)
