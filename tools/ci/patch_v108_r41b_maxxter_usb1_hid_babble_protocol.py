#!/usr/bin/env python3
from pathlib import Path
import hashlib, subprocess, sys
if len(sys.argv)!=2: raise SystemExit('usage: patch_v108_r41b_maxxter_usb1_hid_babble_protocol.py <kernel/main.nx>')
p=Path(sys.argv[1]); here=Path(__file__).parent
# r41b is a self-contained transform from the protected source: reproduce the
# exact certified r40 chain first, then apply the r41 Maxxter delta, then widen
# only the exact receiver to USB 1.x speed IDs 1/2.
r40=here/'patch_v108_r40_usb_hid_identity_wifi_pci_detail_ro.py'
subprocess.run([sys.executable,str(r40),str(p)],check=True,stdout=subprocess.DEVNULL)
R40='ae9598872e6806907e8bb623050f4314dbdda140ecd6b9c620f36e1c669b4c6c'
if hashlib.sha256(p.read_bytes()).hexdigest()!=R40: raise SystemExit('r41b certified r40 chain mismatch')
r41=here/'patch_v108_r41_maxxter_ls_hid_babble_protocol.py'
subprocess.run([sys.executable,str(r41),str(p)],check=True,stdout=subprocess.DEVNULL)
s=p.read_text()
BASE='2e201d05458889915040ad726cbd756c41a5429199bee0738f32dd9fe8a9aed4'
if hashlib.sha256(s.encode()).hexdigest()!=BASE: raise SystemExit('r41 base mismatch')

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

rep('speed==2 && vid==9354 && pid==4267 && proto==2','(speed==1 || speed==2) && vid==9354 && pid==4267 && proto==2','r41b USB1 arm scope')
rep('speed==2 && vid==9354 && pid==4267 && protocol==2','(speed==1 || speed==2) && vid==9354 && pid==4267 && protocol==2','r41b USB1 poll scope')
old=fn_text('v141_text_r41_v141')
rep(old,label_fn('v141_text_r41_v141','R41B G P D L B E'),'r41b physical row label')
out=hashlib.sha256(s.encode()).hexdigest(); EXPECTED='17139d64aafd6d797bab85fc925da51cf13fc0849cfa4f2a3191fcc3e686c814'
if out!=EXPECTED: raise SystemExit('r41b output sha mismatch '+out)
p.write_text(s); print(out)
