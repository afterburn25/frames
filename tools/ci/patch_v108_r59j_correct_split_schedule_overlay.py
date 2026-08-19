#!/usr/bin/env python3
from pathlib import Path
import hashlib, subprocess, sys
if len(sys.argv)!=2: raise SystemExit('usage: patch_v108_r59j_correct_split_schedule_overlay.py <kernel/main.nx>')
p=Path(sys.argv[1]); here=Path(__file__).parent
base=here/'patch_v108_r59i_qh_overlay_forensics.py'
subprocess.run([sys.executable,str(base),str(p)],check=True,stdout=subprocess.DEVNULL)
s=p.read_text()
BASE='cf8f80043153dbd377d2e6b0057e77beaa35b47a6201a863963bf56cefbc8e00'
actual=hashlib.sha256(s.encode()).hexdigest()
if actual!=BASE: raise SystemExit('r59j exact r59i base mismatch '+actual)

def rep(old,new,label,count=1):
    global s
    n=s.count(old)
    if n!=count: raise SystemExit(f'r59j {label}: {n} expected {count}')
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

# Linux EHCI interrupt scheduling places Complete-Splits two to four
# microframes after a Start-Split.  r59h's 0x06 experiment was too early.
# Restore S-mask 0x01 / C-mask 0x1c while retaining the r59h GET_REPORT
# removal and r59i live-QH-overlay telemetry unchanged.
rep('let info2=1090586113','let info2=1090591745','restore valid EHCI C-mask 0x1c')
fnrep('v140_text_wifi_v140',label_fn('v140_text_wifi_v140','R5J S N A X E R D'))

r59j=s[s.index('fn v159_ehci_mouse_periodic_arm'):s.index('fn v135_hid_control_fallback_prepare')]
for q in ['let info1=2+(ep*256)+(mmps*65536)','let info2=1090591745','let token=527744','volatile_write32(op+20,flo)','cmd=set_flag(cmd,16)']:
    if q not in r59j: raise SystemExit('r59j transport invariant missing '+q)
if 'let info2=1090586113' in r59j: raise SystemExit('r59j invalid C-mask 0x06 remains')
if 'let greq=161+(1*256)+(256*65536)' in r59j: raise SystemExit('r59j failed GET_REPORT probe returned')
for q in ['volatile_read32(dm+24)','(ot/128)%2','(ot/2)%2','(ot/4)%32','(ot/65536)%32768','(ot/2147483648)%2']:
    if q not in s: raise SystemExit('r59j live QH overlay telemetry missing '+q)
for bad in ('write(10)','nvme_submit_write','ahci_write','fat_write','block_write','input_push('):
    if bad in r59j.lower(): raise SystemExit('r59j exceeds forensic/read-only scope '+bad)
if s.count('{')!=s.count('}'): raise SystemExit('r59j brace mismatch')
out=hashlib.sha256(s.encode()).hexdigest()
EXPECTED='69168127d829d3b182ab874fef9bbdd1c734ecffca9e5457f94f8d53b012fc54'
if out!=EXPECTED: raise SystemExit('r59j output sha mismatch '+out)
p.write_text(s)
print(out)
