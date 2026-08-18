#!/usr/bin/env python3
from pathlib import Path
import hashlib, subprocess, sys
if len(sys.argv)!=2: raise SystemExit('usage: patch_v108_r59h_linux_split_schedule_repair.py <kernel/main.nx>')
p=Path(sys.argv[1]); here=Path(__file__).parent
base=here/'patch_v108_r59g_ehci_split_state_control_report.py'
subprocess.run([sys.executable,str(base),str(p)],check=True,stdout=subprocess.DEVNULL)
s=p.read_text()
BASE='4381aec1a83db1eeb7baa55e803aacecff30e7b6154238bff892a51fbf0e1dd7'
actual=hashlib.sha256(s.encode()).hexdigest()
if actual!=BASE: raise SystemExit('r59h exact r59g base mismatch '+actual)

def rep(old,new,label,count=1):
    global s
    n=s.count(old)
    if n!=count: raise SystemExit(f'r59h {label}: {n} expected {count}')
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

# Linux EHCI fallback scheduler for a small FS interrupt-IN transfer uses
# gap_uf=1 and two Complete-Split slots after the Start-Split. Frames r59g
# used C-mask 0x1c (uframes 2/3/4); repair it to 0x06 (uframes 1/2).
rep('let info2=1090591745','let info2=1090586113','EHCI split C-mask 0x1c to 0x06')

# The r59g GET_REPORT control experiment returned transaction error 6 on real
# hardware. Remove it from the pre-periodic path so it cannot perturb TT state.
old='''    let greq=161+(1*256)+(256*65536)+(mif*4294967296)+(8*281474976710656); let grc=v157_ehci_tt_control(xhci_state,2,greq,8); var grow:u64=0; if grc==1 { grow=volatile_read64(dma+576); } unsafe { volatile_write64(xhci_state+3984,grc); volatile_write64(xhci_state+3992,grow); }\n'''
new='''    unsafe { volatile_write64(xhci_state+3984,0); volatile_write64(xhci_state+3992,0); }\n'''
rep(old,new,'remove failed GET_REPORT probe')

fnrep('v140_text_wifi_v140',label_fn('v140_text_wifi_v140','R5H S N I X E M C'))
rep('v108_draw_small_u64(surface,((px+264)*65536)+(py+748),volatile_read64(xhci+3984),amber);',
    'v108_draw_small_u64(surface,((px+264)*65536)+(py+748),(rr/4)%32+(volatile_read64(xhci+3984)*0),amber);',
    'show qTD error bits while retaining compatibility read')

r59h=s[s.index('fn v159_ehci_mouse_periodic_arm'):s.index('fn v135_hid_control_fallback_prepare')]
for q in ['let info2=1090586113','let token=527744','volatile_write32(op+20,flo)','cmd=set_flag(cmd,16)','volatile_write64(xhci_state+4064,volatile_read64(xhci_state+4064)+1)']:
    if q not in r59h: raise SystemExit('r59h model missing '+q)
if 'let info2=1090591745' in r59h: raise SystemExit('r59h old C-mask remains')
if 'let greq=161+(1*256)+(256*65536)' in r59h: raise SystemExit('r59h failed GET_REPORT probe remains')
for q in ['(rr/2)%2','(rr/4)%32','sm=qi%256','cm=(qi/256)%256','volatile_read64(xhci+3976)']:
    if q not in s: raise SystemExit('r59h telemetry missing '+q)
for bad in ('write(10)','nvme_submit_write','ahci_write','fat_write','block_write','input_push('):
    if bad in r59h.lower(): raise SystemExit('r59h exceeds diagnostic/read-only scope '+bad)
if s.count('{')!=s.count('}'): raise SystemExit('r59h brace mismatch')
out=hashlib.sha256(s.encode()).hexdigest()
EXPECTED='ee129f22dca19ba7d1d7a1cc41a7b90bfcba0dc472ad7493c38ca2a1537c094e'
if out!=EXPECTED: raise SystemExit('r59h output sha mismatch '+out)
p.write_text(s)
print(out)
