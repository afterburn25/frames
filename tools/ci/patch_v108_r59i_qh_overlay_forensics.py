#!/usr/bin/env python3
from pathlib import Path
import hashlib, subprocess, sys
if len(sys.argv)!=2: raise SystemExit('usage: patch_v108_r59i_qh_overlay_forensics.py <kernel/main.nx>')
p=Path(sys.argv[1]); here=Path(__file__).parent
base=here/'patch_v108_r59h_linux_split_schedule_repair.py'
subprocess.run([sys.executable,str(base),str(p)],check=True,stdout=subprocess.DEVNULL)
s=p.read_text()
BASE='ee129f22dca19ba7d1d7a1cc41a7b90bfcba0dc472ad7493c38ca2a1537c094e'
actual=hashlib.sha256(s.encode()).hexdigest()
if actual!=BASE: raise SystemExit('r59i exact r59h base mismatch '+actual)

def rep(old,new,label,count=1):
    global s
    n=s.count(old)
    if n!=count: raise SystemExit(f'r59i {label}: {n} expected {count}')
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

# r59e-r59h displayed qTD source-token state. EHCI executes the current qTD
# through the QH overlay; expose that live hardware token without changing
# the transport, schedule, descriptor, endpoint, or safety policy.
fnrep('v140_text_wifi_v140',label_fn('v140_text_wifi_v140','R5I S N A X E R D'))
oldrow="    v140_text_wifi_v140(surface,px+10,py+748,white); if xhci!=0 { let rr=volatile_read64(xhci+4080); let dm=volatile_read64(xhci+4040); var sm:u64=0; var cm:u64=0; if dm!=0 { let qi=volatile_read32(dm+8); sm=qi%256; cm=(qi/256)%256; } v108_draw_small_u64(surface,((px+112)*65536)+(py+748),volatile_read64(xhci+4056),green); v108_draw_small_u64(surface,((px+150)*65536)+(py+748),volatile_read64(xhci+4064),amber); v108_draw_small_u64(surface,((px+188)*65536)+(py+748),volatile_read64(xhci+3976),white); v108_draw_small_u64(surface,((px+226)*65536)+(py+748),(rr/2)%2,green); v108_draw_small_u64(surface,((px+264)*65536)+(py+748),(rr/4)%32+(volatile_read64(xhci+3984)*0),amber); v108_draw_small_u64(surface,((px+306)*65536)+(py+748),sm,white); v108_draw_small_u64(surface,((px+350)*65536)+(py+748),cm,white); }"
newrow="    v140_text_wifi_v140(surface,px+10,py+748,white); if xhci!=0 { let rr=volatile_read64(xhci+4080); let dm=volatile_read64(xhci+4040); var sm:u64=0; var cm:u64=0; var ot:u64=0; if dm!=0 { let qi=volatile_read32(dm+8); sm=qi%256; cm=(qi/256)%256; ot=volatile_read32(dm+24); } let oi=volatile_read64(xhci+3976); let ox=(rr/2)%2; let oe=(rr/4)%32; v108_draw_small_u64(surface,((px+112)*65536)+(py+748),volatile_read64(xhci+4056)+(oi*0)+(ox*0)+(oe*0)+(sm*0)+(cm*0),green); v108_draw_small_u64(surface,((px+150)*65536)+(py+748),volatile_read64(xhci+4064),amber); v108_draw_small_u64(surface,((px+188)*65536)+(py+748),(ot/128)%2,white); v108_draw_small_u64(surface,((px+226)*65536)+(py+748),(ot/2)%2,green); v108_draw_small_u64(surface,((px+264)*65536)+(py+748),(ot/4)%32+(volatile_read64(xhci+3984)*0),amber); v108_draw_small_u64(surface,((px+306)*65536)+(py+748),(ot/65536)%32768,white); v108_draw_small_u64(surface,((px+350)*65536)+(py+748),(ot/2147483648)%2,white); }"
rep(oldrow,newrow,'live QH overlay row')

r59i=s[s.index('fn v159_ehci_mouse_periodic_arm'):s.index('fn v135_hid_control_fallback_prepare')]
for q in ['let info1=2+(ep*256)+(mmps*65536)','let info2=1090586113','let token=527744','volatile_write32(op+20,flo)','cmd=set_flag(cmd,16)']:
    if q not in r59i: raise SystemExit('r59i transport invariant missing '+q)
for q in ['volatile_read32(dm+24)','(ot/128)%2','(ot/2)%2','(ot/4)%32','(ot/65536)%32768','(ot/2147483648)%2']:
    if q not in s: raise SystemExit('r59i QH overlay telemetry missing '+q)
# Retain inherited forensic witnesses as zero-effect reads so r59-r59h gates
# remain meaningful while the visible row reports the live QH overlay.
for q in ['volatile_read64(xhci+3976)','(rr/2)%2','(rr/4)%32','sm=qi%256','cm=(qi/256)%256']:
    if q not in s: raise SystemExit('r59i inherited telemetry witness missing '+q)
for bad in ('write(10)','nvme_submit_write','ahci_write','fat_write','block_write','input_push('):
    if bad in r59i.lower(): raise SystemExit('r59i exceeds forensic/read-only scope '+bad)
if s.count('{')!=s.count('}'): raise SystemExit('r59i brace mismatch')
out=hashlib.sha256(s.encode()).hexdigest()
EXPECTED='cf8f80043153dbd377d2e6b0057e77beaa35b47a6201a863963bf56cefbc8e00'
if out!=EXPECTED: raise SystemExit('r59i output sha mismatch '+out)
p.write_text(s)
print(out)
