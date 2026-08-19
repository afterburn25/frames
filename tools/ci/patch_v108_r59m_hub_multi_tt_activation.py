#!/usr/bin/env python3
from pathlib import Path
import hashlib, subprocess, sys
if len(sys.argv)!=2: raise SystemExit('usage: patch_v108_r59m_hub_multi_tt_activation.py <kernel/main.nx>')
p=Path(sys.argv[1]); here=Path(__file__).parent
base=here/'patch_v108_r59l_periodic_fls_frindex_forensics.py'
subprocess.run([sys.executable,str(base),str(p)],check=True,stdout=subprocess.DEVNULL)
s=p.read_text()
BASE='2c4734c29577a4710b27577ec2dfa33dcf6f117a25e21607dff5ee6b9632a6de'
actual=hashlib.sha256(s.encode()).hexdigest()
if actual!=BASE: raise SystemExit('r59m exact r59l base mismatch '+actual)

def rep(old,new,label,count=1):
    global s
    n=s.count(old)
    if n!=count: raise SystemExit(f'r59m {label}: {n} expected {count}')
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

# Linux-compatible high-speed hub TT selection: capture bDeviceProtocol while
# the hub is still at the proven r56 enumeration stage. Protocol 2 advertises
# multiple TTs; request hub interface 0 alternate setting 1. Any failure is
# non-fatal and retains the already-working single-TT fallback.
old='let data=dma+576; let dlen=volatile_read8(data); let dtype=volatile_read8(data+1); let cls=volatile_read8(data+4); let mps=volatile_read8(data+7); let vid=volatile_read8(data+8)+(volatile_read8(data+9)*256); let pid=volatile_read8(data+10)+(volatile_read8(data+11)*256);'
new='let data=dma+576; let dlen=volatile_read8(data); let dtype=volatile_read8(data+1); let cls=volatile_read8(data+4); let hubproto=volatile_read8(data+6); let mps=volatile_read8(data+7); let vid=volatile_read8(data+8)+(volatile_read8(data+9)*256); let pid=volatile_read8(data+10)+(volatile_read8(data+11)*256);'
rep(old,new,'hub protocol capture')
old='let setcfg=2304+(cfg*65536); rc=v155_ehci_control(xhci_state,1,setcfg,0); if rc!=1 { unsafe { volatile_write64(xhci_state+3920,25); volatile_write64(xhci_state+4000,rc); } return 25; }\n    pit_wait(23864);\n    rc=v155_ehci_control(xhci_state,1,2533275478263456,9);'
new='let setcfg=2304+(cfg*65536); rc=v155_ehci_control(xhci_state,1,setcfg,0); if rc!=1 { unsafe { volatile_write64(xhci_state+3920,25); volatile_write64(xhci_state+4000,rc); } return 25; }\n    pit_wait(23864);\n    var ttrc:u64=0; if hubproto==2 { ttrc=v155_ehci_control(xhci_state,1,68353,0); pit_wait(23864); } unsafe { volatile_write64(xhci_state+3880,hubproto); volatile_write64(xhci_state+3888,ttrc); }\n    rc=v155_ehci_control(xhci_state,1,2533275478263456,9);'
rep(old,new,'multi-TT activation')

# Keep every r59l frame-list forensic computation as a compatibility witness,
# but show the new TT decision plus the high-value periodic state.
fnrep('v140_text_wifi_v140',label_fn('v140_text_wifi_v140','R5M H T F Q N A P'))
rep('v108_draw_small_u64(surface,((px+112)*65536)+(py+748),fls+(compat*0),green);','v108_draw_small_u64(surface,((px+112)*65536)+(py+748),volatile_read64(xhci+3880)+(compat*0),green);','H telemetry')
rep('v108_draw_small_u64(surface,((px+150)*65536)+(py+748),fi,amber);','v108_draw_small_u64(surface,((px+150)*65536)+(py+748),volatile_read64(xhci+3888),amber);','T telemetry')
rep('v108_draw_small_u64(surface,((px+188)*65536)+(py+748),linked,white);','v108_draw_small_u64(surface,((px+188)*65536)+(py+748),fls,white);','F telemetry')

r56=fn_text('v156_ehci_second_hub_census')
for q in ('let hubproto=volatile_read8(data+6)','if hubproto==2','v155_ehci_control(xhci_state,1,68353,0)','volatile_write64(xhci_state+3880,hubproto)','volatile_write64(xhci_state+3888,ttrc)'):
    if q not in r56: raise SystemExit('r59m multi-TT model missing '+q)
r59=fn_text('v159_ehci_mouse_periodic_arm')
for q in ('let info2=1090591745','cmd=clear_flag(cmd,4)','cmd=clear_flag(cmd,8)','volatile_write32(op+20,flo)','cmd=set_flag(cmd,16)'):
    if q not in r59: raise SystemExit('r59m lost r59l invariant '+q)
for q in ('fls=(c/4)%4','fi=(fri59l/8)%1024','volatile_read32(frame+(fi*4))==qlo+2','volatile_read32(dm+12)==tdlo','volatile_read64(xhci+3880)','volatile_read64(xhci+3888)'):
    if q not in s: raise SystemExit('r59m telemetry/model missing '+q)
for bad in ('write(10)','nvme_submit_write','ahci_write','fat_write','block_write','input_push('):
    if bad in (r56+r59).lower(): raise SystemExit('r59m exceeds diagnostic/read-only scope '+bad)
if s.count('{')!=s.count('}'): raise SystemExit('r59m brace mismatch')
out=hashlib.sha256(s.encode()).hexdigest()
EXPECTED='8b236b8b21a181e5db9fbeec3c5b64840df0d3158980bde3176647e6cf651bc8'
if out!=EXPECTED: raise SystemExit('r59m output sha mismatch '+out)
p.write_text(s)
print(out)
