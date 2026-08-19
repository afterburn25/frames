#!/usr/bin/env python3
from pathlib import Path
import hashlib, subprocess, sys
if len(sys.argv)!=2: raise SystemExit('usage: patch_v108_r67_persistent_newsched_cmask.py <kernel/main.nx>')
p=Path(sys.argv[1]); here=Path(__file__).parent
base=here/'patch_v108_r66_intel_8000_profile_unlock.py'
subprocess.run([sys.executable,str(base),str(p)],check=True,stdout=subprocess.DEVNULL)
s=p.read_text()
BASE='49748e4fb2fd2d0ec73cca7ef396719aef5fd13cf63bb69e83e96d892f38e700'
actual=hashlib.sha256(s.encode()).hexdigest()
if actual!=BASE: raise SystemExit('r67 exact r66 base mismatch '+actual)

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

# r66 physically proved the exact 8087:8000 Single-TT profile, persistent QH,
# hardware-owned overlay/toggle and no-live-rewrite lifecycle, but its first
# qTD remained A=1/R=8/E=0 under Linux legacy S=0x01/C=0x06. Keep that entire
# lifecycle unchanged and perform the clean reference A/B against Linux's
# CONFIG_USB_EHCI_TT_NEWSCHED placement: S=0x01/C=0x1c for uframe 0.
old='let info1=2+(ep*256)+(speed*4096)+(mmps*65536); let info2=1090586113+(newsched_info2*0)+(thinkbits*0); let token=560512;'
new='let info1=2+(ep*256)+(speed*4096)+(mmps*65536); let info2=1090591745+(legacy_info2*0)+(thinkbits*0); let token=560512;'
if s.count(old)!=1: raise SystemExit('r67 live geometry anchor mismatch '+str(s.count(old)))
s=s.replace(old,new,1)
if s.count('volatile_write64(xhci_state+3992,6)')!=1: raise SystemExit('r67 mode telemetry anchor mismatch')
s=s.replace('volatile_write64(xhci_state+3992,6)','volatile_write64(xhci_state+3992,28)',1)

# Expose SplitX again while retaining completion/delivery and hardware-owned
# overlay state. Contract: M/N/D/X/A/T/R/E.
s=s.replace(fn_text(s,'v140_text_wifi_v140'),label_fn('v140_text_wifi_v140','R67 MNDXATRE'),1)
rs=s.index('v140_text_wifi_v140(surface,px+10,py+748,white);')
re=s.index('\n    return 1;\n}',rs)
newrow="v140_text_wifi_v140(surface,px+10,py+748,white); if xhci!=0 { let dm=volatile_read64(xhci+4040); var x:u64=0; var a:u64=0; var t:u64=0; var r:u64=0; var e:u64=0; if dm!=0 { let ot=volatile_read32(dm+24); x=(ot/2)%2; a=(ot/128)%2; t=(ot/2147483648)%2; r=(ot/65536)%32768; e=(ot/4)%32; } let compat=volatile_read64(xhci+4000)+(volatile_read64(xhci+3984)*0); v108_draw_small_u64(surface,((px+100)*65536)+(py+748),volatile_read64(xhci+3992)+(compat*0),green); v108_draw_small_u64(surface,((px+140)*65536)+(py+748),volatile_read64(xhci+4064),amber); v108_draw_small_u64(surface,((px+180)*65536)+(py+748),volatile_read64(xhci+4072),white); v108_draw_small_u64(surface,((px+220)*65536)+(py+748),x,green); v108_draw_small_u64(surface,((px+260)*65536)+(py+748),a,amber); v108_draw_small_u64(surface,((px+300)*65536)+(py+748),t,white); v108_draw_small_u64(surface,((px+340)*65536)+(py+748),r,green); v108_draw_small_u64(surface,((px+380)*65536)+(py+748),e,amber); }"
s=s[:rs]+newrow+s[re:]

arm=fn_text(s,'v159_ehci_mouse_periodic_arm'); tick=fn_text(s,'v159_ehci_mouse_periodic_tick')
for q in ('hubvid==32903','hubpid==32768 || hubpid==32776','hubproto==1','hubchars==9','port==2','thinkbits==8','let legacy_info2:u64=1090586113','let newsched_info2:u64=1090591745','let info2=1090591745','let qcount:u64=24','volatile_write32(qtd+8,560512)','volatile_write32(dummy+8,64)','volatile_write64(xhci_state+3992,28)'):
    if q not in arm: raise SystemExit('r67 persistent newsched witness missing '+q)
for q in ('let idx=volatile_read64(xhci_state+4080)','let tok=volatile_read32(td+8)','let otok=volatile_read32(qh+24)','input_push(input_state,4,0,buttons)','input_push(input_state,5,0,dx)','input_push(input_state,6,0,dy)','volatile_write64(xhci_state+4080,idx+1)'):
    if q not in tick: raise SystemExit('r67 completion witness missing '+q)
for bad in ('volatile_write32(qh+24','volatile_write32(qh+16','volatile_write32(td+8','cmd=set_flag(cmd,16)','cmd=clear_flag(cmd,16)','volatile_write32(op+20'):
    if bad in tick: raise SystemExit('r67 live QH/schedule ownership violation '+bad)
out=hashlib.sha256(s.encode()).hexdigest()
EXPECTED='80b2fa96a6b3fbc6c2f41d2e5f7e7a7d6c152a29fb32ed1351a1bf59f1813397'
if out!=EXPECTED: raise SystemExit('r67 output sha mismatch '+out)
p.write_text(s)
print(out)
