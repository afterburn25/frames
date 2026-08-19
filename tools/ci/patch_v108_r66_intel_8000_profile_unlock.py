#!/usr/bin/env python3
from pathlib import Path
import hashlib, subprocess, sys
if len(sys.argv)!=2: raise SystemExit('usage: patch_v108_r66_intel_8000_profile_unlock.py <kernel/main.nx>')
p=Path(sys.argv[1]); here=Path(__file__).parent
base=here/'patch_v108_r65_display_compat.py'
subprocess.run([sys.executable,str(base),str(p)],check=True,stdout=subprocess.DEVNULL)
s=p.read_text()
BASE='9a4864e1eb630f531caf60e5c6c8a43cf3ece3169a25bcaab2042818ea8ccee6'
actual=hashlib.sha256(s.encode()).hexdigest()
if actual!=BASE: raise SystemExit('r66 exact r65 base mismatch '+actual)

def fn_text(src,name):
    st=src.index('fn '+name); op=src.index('{',st); d=0
    for i in range(op,len(src)):
        if src[i]=='{': d+=1
        elif src[i]=='}':
            d-=1
            if d==0: return src[st:i+1]
    raise RuntimeError(name)

def label_fn(name,text):
    out=f'fn {name}(surface:u64,x:u64,y:u64,color:u64) -> u64 {{'
    for i,ch in enumerate(text):
        out+=f' if gui_draw_char_scaled(surface,((x+{i*6})*65536)+y,({ord(ch)}*65536)+1,color)==0 {{ return 0; }}'
    return out+' return 1; }'

# r65's physical image proved that the live Intel rate-matching hub on the
# selected mouse path identifies as 8087:8000, not the previously assumed
# sibling 8087:8008.  Both IDs are valid Intel integrated rate-matching hubs.
# Keep every other exact Single-TT characteristic and lifecycle requirement.
old="if hrc==1 && hdrc==1 && hubvid==32903 && hubpid==32776 && hubproto==1 && hubchars==9 && port==2 && thinkbits==8 { profile=1; }"
new="if hrc==1 && hdrc==1 && hubvid==32903 && (hubpid==32768 || hubpid==32776) && hubproto==1 && hubchars==9 && port==2 && thinkbits==8 { profile=1; }"
if s.count(old)!=1: raise SystemExit('r66 Intel 8000/8008 profile anchor mismatch '+str(s.count(old)))
s=s.replace(old,new,1)

# Give the physical row an unambiguous revision identity. Its field contract
# remains P/M/N/D/A/T/R/E; if profile admission fails, the legacy diagnostic
# fail path still exposes raw VID/PID in P/M for immediate diagnosis.
oldfn=fn_text(s,'v140_text_wifi_v140')
s=s.replace(oldfn,label_fn('v140_text_wifi_v140','R66 PMNDATRE'),1)

arm=fn_text(s,'v159_ehci_mouse_periodic_arm')
for q in (
    'hubvid==32903','hubpid==32768 || hubpid==32776','hubproto==1','hubchars==9','port==2','thinkbits==8',
    'let gap_uf:u64=1','let legacy_cmask=3*power2_u64(gap_uf)','let info2=1090586113',
    'let legacy_info2:u64=1090586113','let newsched_info2:u64=1090591745',
    'let qcount:u64=24','volatile_write32(qtd+8,560512)','volatile_write32(dummy+8,64)',
    'cmd=set_flag(cmd,16)','volatile_write64(xhci_state+3984,profile)','volatile_write64(xhci_state+3992,6)'):
    if q not in arm: raise SystemExit('r66 persistent periodic witness missing '+q)
tick=fn_text(s,'v159_ehci_mouse_periodic_tick')
for bad in ('volatile_write32(qh+24','volatile_write32(qh+16','volatile_write32(td+8','cmd=set_flag(cmd,16)','cmd=clear_flag(cmd,16)','volatile_write32(op+20'):
    if bad in tick: raise SystemExit('r66 live QH/schedule ownership violation '+bad)

out=hashlib.sha256(s.encode()).hexdigest()
EXPECTED='49748e4fb2fd2d0ec73cca7ef396719aef5fd13cf63bb69e83e96d892f38e700'
if out!=EXPECTED: raise SystemExit('r66 output sha mismatch '+out)
p.write_text(s)
print(out)
