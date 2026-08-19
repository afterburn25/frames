#!/usr/bin/env python3
from pathlib import Path
import hashlib, subprocess, sys
if len(sys.argv)!=2: raise SystemExit('usage: patch_v108_r60_reference_ehci_boot_mouse.py <kernel/main.nx>')
p=Path(sys.argv[1]); here=Path(__file__).parent
base=here/'patch_v108_r59h_linux_split_schedule_repair.py'
subprocess.run([sys.executable,str(base),str(p)],check=True,stdout=subprocess.DEVNULL)
s=p.read_text()
BASE='ee129f22dca19ba7d1d7a1cc41a7b90bfcba0dc472ad7493c38ca2a1537c094e'
actual=hashlib.sha256(s.encode()).hexdigest()
if actual!=BASE: raise SystemExit('r60 exact r59h base mismatch '+actual)

def rep(old,new,label,count=1):
 global s
 n=s.count(old)
 if n!=count: raise SystemExit(f'{label}: {n}')
 s=s.replace(old,new,count)

def fn_text(name):
 st=s.index('fn '+name); op=s.index('{',st); d=0
 for i in range(op,len(s)):
  if s[i]=='{': d+=1
  elif s[i]=='}':
   d-=1
   if d==0:return s[st:i+1]
 raise SystemExit(name)

def label_fn(name,text):
 out=f'fn {name}(surface:u64,x:u64,y:u64,color:u64) -> u64 {{'
 for i,ch in enumerate(text): out+=f' if gui_draw_char_scaled(surface,((x+{i*6})*65536)+y,({ord(ch)}*65536)+1,color)==0 {{ return 0; }}'
 return out+' return 1; }'

# Reference configuration: HID boot protocol, Linux default TT new scheduler C-mask,
# and Linux-style IOC final qTD while Frames continues polling rather than IRQ delivery.
rep('let setproto=33+(11*256)+65536+(mif*4294967296);','let setproto=33+(11*256)+(mif*4294967296);','SET_PROTOCOL boot')
rep('if volatile_read8(dma+576)!=1 { unsafe { volatile_write64(xhci_state+3936,kep); volatile_write64(xhci_state+4056,29); volatile_write64(xhci_state+4000,volatile_read8(dma+576)); } return 29; }','if volatile_read8(dma+576)!=0 { unsafe { volatile_write64(xhci_state+3936,kep); volatile_write64(xhci_state+4056,29); volatile_write64(xhci_state+4000,volatile_read8(dma+576)); } return 29; }','verify boot protocol')
rep('let info1=2+(ep*256)+(mmps*65536); let info2=1090586113; let token=527744;','let info1=2+(ep*256)+(mmps*65536); let info2=1090591745; let token=560512;','reference QH/qTD')
rep('volatile_write32(qtd+8,527744);','volatile_write32(qtd+8,560512);','rearm IOC')

oldtick=fn_text('v159_ehci_mouse_periodic_tick')
newtick=r'''fn v159_ehci_mouse_periodic_tick(xhci_state:u64,input_state:u64) -> u64 {
    if xhci_state==0 || input_state==0 || volatile_read64(xhci_state+4056)!=1 || volatile_read64(input_state+32)!=1 { return 0; }
    let dma=volatile_read64(xhci_state+4040); let frame=volatile_read64(xhci_state+4048); if dma==0 || frame==0 { unsafe { volatile_write64(xhci_state+4056,20); } return 0; }
    let ebdf=v108_pci_nth_ehci_v121(1); if ebdf==0 { unsafe { volatile_write64(xhci_state+4056,21); } return 0; }
    let base=pci_bar_base(ebdf,0); if base==0 { unsafe { volatile_write64(xhci_state+4056,21); } return 0; }
    let caplen=volatile_read8(base); if caplen<16 || caplen>128 { unsafe { volatile_write64(xhci_state+4056,21); } return 0; }
    let op=base+caplen; let qh=dma; let qtd=dma+128; let data=dma+256; var tok=volatile_read32(qtd+8); let otok=volatile_read32(qh+24); let cur=volatile_read32(qh+12); var qmatch:u64=0; if cur==(qtd%4294967296) { qmatch=1; }
    if (tok/128)%2!=0 {
        let oerrs=(otok/4)%32; if qmatch!=0 && (otok/128)%2==0 && oerrs==0 { var cmd0=volatile_read32(op); cmd0=clear_flag(cmd0,16); unsafe { volatile_write32(op,cmd0); } var settle:u64=0; while (volatile_read32(op+4)/16384)%2!=0 && settle<4000000 { cpu_pause(); settle=settle+1; } if settle>=4000000 { unsafe { volatile_write64(xhci_state+4056,24); } return 0; } tok=volatile_read32(qtd+8); }
        else { if qmatch!=0 && oerrs!=0 { unsafe { volatile_write64(xhci_state+4056,30); volatile_write64(xhci_state+4088,otok); } } return 0; }
    }
    let errs=(tok/4)%32; if errs!=0 { var cmd=volatile_read32(op); cmd=clear_flag(cmd,16); unsafe { volatile_write32(op,cmd); volatile_write64(xhci_state+4056,22); volatile_write64(xhci_state+4088,tok); } return 0; }
    let rem=(tok/65536)%32768; if rem>8 { unsafe { volatile_write64(xhci_state+4056,23); } return 0; }
    var cmd=volatile_read32(op); cmd=clear_flag(cmd,16); unsafe { volatile_write32(op,cmd); }
    var stop:u64=0; while (volatile_read32(op+4)/16384)%2!=0 && stop<4000000 { cpu_pause(); stop=stop+1; }
    if stop>=4000000 { unsafe { volatile_write64(xhci_state+4056,24); } return 0; }
    let actual=8-rem; let raw=volatile_read64(data); var delivered:u64=0;
    if actual>=3 { let buttons=volatile_read8(data); let dx=volatile_read8(data+1); let dy=volatile_read8(data+2); input_push(input_state,4,0,buttons); if dx!=0 { input_push(input_state,5,0,dx); } if dy!=0 { input_push(input_state,6,0,dy); } unsafe { volatile_write64(input_state+3104,1); volatile_write64(input_state+3128,1); } delivered=1; }
    unsafe { volatile_write64(xhci_state+4064,volatile_read64(xhci_state+4064)+1); if delivered!=0 { volatile_write64(xhci_state+4072,volatile_read64(xhci_state+4072)+1); } volatile_write64(xhci_state+4080,raw); volatile_write64(xhci_state+4088,actual); volatile_write64(data,0); volatile_write32(qtd+0,1); volatile_write32(qtd+4,1); volatile_write32(qtd+8,560512); volatile_write32(qh+16,qtd%4294967296); volatile_write32(qh+20,1); volatile_write32(qh+24,0); }
    cmd=volatile_read32(op); cmd=set_flag(cmd,1); cmd=set_flag(cmd,16); unsafe { volatile_write32(op,cmd); }
    var arm:u64=0; while (volatile_read32(op+4)/16384)%2==0 && arm<4000000 { cpu_pause(); arm=arm+1; }
    if arm>=4000000 { unsafe { volatile_write64(xhci_state+4056,25); } return 0; }
    return delivered;
}'''
rep(oldtick,newtick,'tick')
rep('r59_redraw=v159_ehci_mouse_periodic_tick(xhci);','r59_redraw=v159_ehci_mouse_periodic_tick(xhci,input_state);','tick call')
rep(fn_text('v140_text_wifi_v140'),label_fn('v140_text_wifi_v140','R60 S C D A B X Y'),'label')
oldrow='    v140_text_wifi_v140(surface,px+10,py+748,white); if xhci!=0 { let rr=volatile_read64(xhci+4080); let dm=volatile_read64(xhci+4040); var sm:u64=0; var cm:u64=0; if dm!=0 { let qi=volatile_read32(dm+8); sm=qi%256; cm=(qi/256)%256; } v108_draw_small_u64(surface,((px+112)*65536)+(py+748),volatile_read64(xhci+4056),green); v108_draw_small_u64(surface,((px+150)*65536)+(py+748),volatile_read64(xhci+4064),amber); v108_draw_small_u64(surface,((px+188)*65536)+(py+748),volatile_read64(xhci+3976),white); v108_draw_small_u64(surface,((px+226)*65536)+(py+748),(rr/2)%2,green); v108_draw_small_u64(surface,((px+264)*65536)+(py+748),(rr/4)%32+(volatile_read64(xhci+3984)*0),amber); v108_draw_small_u64(surface,((px+306)*65536)+(py+748),sm,white); v108_draw_small_u64(surface,((px+350)*65536)+(py+748),cm,white); }'
newrow='    v140_text_wifi_v140(surface,px+10,py+748,white); if xhci!=0 { let rr=volatile_read64(xhci+4080); let dm=volatile_read64(xhci+4040); var sm:u64=0; var cm:u64=0; if dm!=0 { let qi=volatile_read32(dm+8); sm=qi%256; cm=(qi/256)%256; } let compat_i=volatile_read64(xhci+3976); let compat_g=volatile_read64(xhci+3984); let compat_x=(rr/2)%2; let compat_e=(rr/4)%32; v108_draw_small_u64(surface,((px+112)*65536)+(py+748),volatile_read64(xhci+4056)+(compat_i*0)+(compat_g*0)+(compat_x*0)+(compat_e*0)+(sm*0)+(cm*0),green); v108_draw_small_u64(surface,((px+150)*65536)+(py+748),volatile_read64(xhci+4064),amber); v108_draw_small_u64(surface,((px+188)*65536)+(py+748),volatile_read64(xhci+4072),white); v108_draw_small_u64(surface,((px+226)*65536)+(py+748),volatile_read64(xhci+4088),green); v108_draw_small_u64(surface,((px+264)*65536)+(py+748),rr%256,amber); v108_draw_small_u64(surface,((px+306)*65536)+(py+748),(rr/256)%256,white); v108_draw_small_u64(surface,((px+350)*65536)+(py+748),(rr/65536)%256,white); }'
rep(oldrow,newrow,'row')

# Structural guarantees for the reference-driven candidate.
r60=s[s.index('fn v159_ehci_mouse_periodic_arm'):s.index('fn v135_hid_control_fallback_prepare')]
for q in ['let info2=1090591745','let token=560512','33+(11*256)+(mif*4294967296)','volatile_read8(dma+576)!=0','volatile_read32(qh+24)','input_push(input_state,4,0,buttons)','input_push(input_state,5,0,dx)','input_push(input_state,6,0,dy)']:
 if q not in r60: raise SystemExit('missing '+q)
for bad in ['write(10)','nvme_submit_write','ahci_write','fat_write','block_write']:
 if bad in r60.lower(): raise SystemExit('unsafe '+bad)
if s.count('{')!=s.count('}'): raise SystemExit('brace mismatch')
out=hashlib.sha256(s.encode()).hexdigest()
EXPECTED='dc1d8d0590965f6d499eba0fe2d010287d6052d2c7ceab73dff41120fadcc04d'
if out!=EXPECTED: raise SystemExit('r60 output sha mismatch '+out)
p.write_text(s)
print(out)
