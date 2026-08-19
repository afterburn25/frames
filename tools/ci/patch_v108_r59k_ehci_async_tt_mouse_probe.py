#!/usr/bin/env python3
from pathlib import Path
import hashlib, subprocess, sys
if len(sys.argv)!=2: raise SystemExit('usage: patch_v108_r59k_ehci_async_tt_mouse_probe.py <kernel/main.nx>')
p=Path(sys.argv[1]); here=Path(__file__).parent
base=here/'patch_v108_r59j_correct_split_schedule_overlay.py'
subprocess.run([sys.executable,str(base),str(p)],check=True,stdout=subprocess.DEVNULL)
s=p.read_text()
BASE='69168127d829d3b182ab874fef9bbdd1c734ecffca9e5457f94f8d53b012fc54'
actual=hashlib.sha256(s.encode()).hexdigest()
if actual!=BASE: raise SystemExit('r59k exact r59j base mismatch '+actual)

def rep(old,new,label,count=1):
    global s
    n=s.count(old)
    if n!=count: raise SystemExit('r59k '+label+': '+str(n)+' expected '+str(count))
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
    out='fn '+name+'(surface:u64,x:u64,y:u64,color:u64) -> u64 {'
    for i,ch in enumerate(text):
        out+=' if gui_draw_char_scaled(surface,((x+'+str(i*6)+')*65536)+y,('+str(ord(ch))+'*65536)+1,color)==0 { return 0; }'
    return out+' return 1; }'

async_code=r"""
fn v160_ehci_mouse_async_arm(xhci_state:u64) -> u64 {
    if xhci_state==0 { return 0; }
    if volatile_read64(xhci_state+3920)!=1 || volatile_read64(xhci_state+3928)!=2 { unsafe { volatile_write64(xhci_state+4056,30); } return 30; }
    let kep=volatile_read64(xhci_state+3936); let mep=volatile_read64(xhci_state+3944); let mif=volatile_read64(xhci_state+3952); let mmps=volatile_read64(xhci_state+3960); let hids=volatile_read64(xhci_state+3968); let cfg=volatile_read64(xhci_state+4008); let speed=volatile_read64(xhci_state+4024); let dma=volatile_read64(xhci_state+4040); let port=volatile_read64(xhci_state+3928);
    if kep==0 || mep<128 || (mep%128)==0 || mif>31 || mmps==0 || mmps>64 || hids<2 || cfg==0 || speed>1 || dma==0 || port==0 || port>15 { unsafe { volatile_write64(xhci_state+4056,31); } return 31; }
    let ep0mps:u64=8; unsafe { volatile_write64(xhci_state+3936,ep0mps); }
    let setcfg=2304+(cfg*65536); var rc=v157_ehci_tt_control(xhci_state,2,setcfg,0); if rc!=1 { unsafe { volatile_write64(xhci_state+3936,kep); volatile_write64(xhci_state+4056,32); volatile_write64(xhci_state+4000,rc); } return 32; }
    pit_wait(23864);
    let setproto=33+(11*256)+65536+(mif*4294967296); rc=v157_ehci_tt_control(xhci_state,2,setproto,0); if rc!=1 { unsafe { volatile_write64(xhci_state+3936,kep); volatile_write64(xhci_state+4056,33); volatile_write64(xhci_state+4000,rc); } return 33; }
    pit_wait(23864);
    let getproto=161+(3*256)+(mif*4294967296)+(1*281474976710656); rc=v157_ehci_tt_control(xhci_state,2,getproto,1); if rc!=1 { unsafe { volatile_write64(xhci_state+3936,kep); volatile_write64(xhci_state+4056,34); volatile_write64(xhci_state+4000,rc); } return 34; }
    if volatile_read8(dma+576)!=1 { unsafe { volatile_write64(xhci_state+3936,kep); volatile_write64(xhci_state+4056,35); volatile_write64(xhci_state+4000,volatile_read8(dma+576)); } return 35; }
    unsafe { volatile_write64(xhci_state+3936,kep); }
    let ebdf=v108_pci_nth_ehci_v121(1); if ebdf==0 { unsafe { volatile_write64(xhci_state+4056,36); } return 36; }
    let base=pci_bar_base(ebdf,0); if base==0 { unsafe { volatile_write64(xhci_state+4056,36); } return 36; }
    let caplen=volatile_read8(base); if caplen<16 || caplen>128 { unsafe { volatile_write64(xhci_state+4056,36); } return 36; }
    let hcc=volatile_read32(base+8); let ac64=hcc%2; let upper=dma/4294967296; if ac64==0 && upper!=0 { unsafe { volatile_write64(xhci_state+4056,37); } return 37; }
    let op=base+caplen; var cmd=volatile_read32(op); cmd=clear_flag(cmd,16); cmd=clear_flag(cmd,32); unsafe { volatile_write32(op,cmd); }
    var quiet:u64=0; while (((volatile_read32(op+4)/16384)%2)!=0 || ((volatile_read32(op+4)/32768)%2)!=0) && quiet<4000000 { cpu_pause(); quiet=quiet+1; }
    if quiet>=4000000 { unsafe { volatile_write64(xhci_state+4056,38); } return 38; }
    zero_page(dma);
    let qh=dma; let qtd=dma+128; let data=dma+256; let qlo=qh%4294967296; let tdlo=qtd%4294967296; let datlo=data%4294967296; let ep=mep%128;
    let info1=1073774592+2+(ep*256)+(mmps*65536); let info2=1073807360+(port*8388608); let token=527744;
    unsafe { volatile_write32(qh+0,qlo+2); volatile_write32(qh+4,info1); volatile_write32(qh+8,info2); volatile_write32(qh+12,0); volatile_write32(qh+16,tdlo); volatile_write32(qh+20,1); volatile_write32(qh+24,0); volatile_write32(qtd+0,1); volatile_write32(qtd+4,1); volatile_write32(qtd+8,token); volatile_write32(qtd+12,datlo); volatile_write32(qtd+32,upper); volatile_write32(op+8,0); volatile_write32(op+24,qlo); volatile_write32(op+4,63); }
    if ac64!=0 { unsafe { volatile_write32(op+16,upper); } }
    cmd=volatile_read32(op); cmd=clear_flag(cmd,16); cmd=set_flag(cmd,1); cmd=set_flag(cmd,32); unsafe { volatile_write32(op,cmd); }
    var arm:u64=0; while (volatile_read32(op+4)/32768)%2==0 && arm<4000000 { cpu_pause(); arm=arm+1; }
    if arm>=4000000 { cmd=volatile_read32(op); cmd=clear_flag(cmd,32); unsafe { volatile_write32(op,cmd); volatile_write64(xhci_state+4056,39); } return 39; }
    unsafe { volatile_write64(xhci_state+4048,0); volatile_write64(xhci_state+4056,1); volatile_write64(xhci_state+4064,0); volatile_write64(xhci_state+4072,0); volatile_write64(xhci_state+4080,0); volatile_write64(xhci_state+4088,0); }
    return 1;
}
fn v160_ehci_mouse_async_tick(xhci_state:u64) -> u64 {
    if xhci_state==0 || volatile_read64(xhci_state+4056)!=1 { return 0; }
    let dma=volatile_read64(xhci_state+4040); if dma==0 { unsafe { volatile_write64(xhci_state+4056,40); } return 0; }
    let ebdf=v108_pci_nth_ehci_v121(1); if ebdf==0 { unsafe { volatile_write64(xhci_state+4056,41); } return 0; }
    let base=pci_bar_base(ebdf,0); if base==0 { unsafe { volatile_write64(xhci_state+4056,41); } return 0; }
    let caplen=volatile_read8(base); if caplen<16 || caplen>128 { unsafe { volatile_write64(xhci_state+4056,41); } return 0; }
    let op=base+caplen; let qh=dma; let qtd=dma+128; let data=dma+256; let ot=volatile_read32(qh+24);
    if (ot/128)%2!=0 { return 0; }
    let errs=(ot/4)%32; if errs!=0 { var ecmd=volatile_read32(op); ecmd=clear_flag(ecmd,32); unsafe { volatile_write32(op,ecmd); volatile_write64(xhci_state+4056,42); volatile_write64(xhci_state+4072,errs); } return 0; }
    let rem=(ot/65536)%32768; if rem>8 { unsafe { volatile_write64(xhci_state+4056,43); } return 0; }
    var cmd=volatile_read32(op); cmd=clear_flag(cmd,32); unsafe { volatile_write32(op,cmd); }
    var stop:u64=0; while (volatile_read32(op+4)/32768)%2!=0 && stop<4000000 { cpu_pause(); stop=stop+1; }
    if stop>=4000000 { unsafe { volatile_write64(xhci_state+4056,44); } return 0; }
    let raw=volatile_read64(data); let prev=volatile_read64(xhci_state+4088); let dt=(ot/2147483648)%2; let upper=dma/4294967296; let qlo=qh%4294967296; let tdlo=qtd%4294967296; let datlo=data%4294967296;
    unsafe { volatile_write64(xhci_state+4064,volatile_read64(xhci_state+4064)+1); volatile_write64(xhci_state+4080,raw); if raw!=prev { volatile_write64(xhci_state+4088,raw); } volatile_write64(data,0); volatile_write32(qh+0,qlo+2); volatile_write32(qh+12,0); volatile_write32(qh+16,tdlo); volatile_write32(qh+20,1); volatile_write32(qh+24,dt*2147483648); volatile_write32(qtd+0,1); volatile_write32(qtd+4,1); volatile_write32(qtd+8,527744); volatile_write32(qtd+12,datlo); volatile_write32(qtd+32,upper); }
    cmd=volatile_read32(op); cmd=set_flag(cmd,1); cmd=set_flag(cmd,32); unsafe { volatile_write32(op,cmd); }
    var arm:u64=0; while (volatile_read32(op+4)/32768)%2==0 && arm<4000000 { cpu_pause(); arm=arm+1; }
    if arm>=4000000 { unsafe { volatile_write64(xhci_state+4056,45); } return 0; }
    return 1;
}
"""
rep('fn v135_hid_control_fallback_prepare',async_code+'\nfn v135_hid_control_fallback_prepare','async TT mouse engine insert')

rep('v159_ehci_mouse_periodic_arm(xhci,phys_state)','v160_ehci_mouse_async_arm(xhci)','boot async mouse arm hook')
rep('v159_ehci_mouse_periodic_tick(xhci)','v160_ehci_mouse_async_tick(xhci)','live async mouse tick hook')
fnrep('v140_text_wifi_v140',label_fn('v140_text_wifi_v140','R5K S N A E B X Y'))

oldrow="    v140_text_wifi_v140(surface,px+10,py+748,white); if xhci!=0 { let rr=volatile_read64(xhci+4080); let dm=volatile_read64(xhci+4040); var sm:u64=0; var cm:u64=0; var ot:u64=0; if dm!=0 { let qi=volatile_read32(dm+8); sm=qi%256; cm=(qi/256)%256; ot=volatile_read32(dm+24); } let oi=volatile_read64(xhci+3976); let ox=(rr/2)%2; let oe=(rr/4)%32; v108_draw_small_u64(surface,((px+112)*65536)+(py+748),volatile_read64(xhci+4056)+(oi*0)+(ox*0)+(oe*0)+(sm*0)+(cm*0),green); v108_draw_small_u64(surface,((px+150)*65536)+(py+748),volatile_read64(xhci+4064),amber); v108_draw_small_u64(surface,((px+188)*65536)+(py+748),(ot/128)%2,white); v108_draw_small_u64(surface,((px+226)*65536)+(py+748),(ot/2)%2,green); v108_draw_small_u64(surface,((px+264)*65536)+(py+748),(ot/4)%32+(volatile_read64(xhci+3984)*0),amber); v108_draw_small_u64(surface,((px+306)*65536)+(py+748),(ot/65536)%32768,white); v108_draw_small_u64(surface,((px+350)*65536)+(py+748),(ot/2147483648)%2,white); }"
newrow="    v140_text_wifi_v140(surface,px+10,py+748,white); if xhci!=0 { let rr=volatile_read64(xhci+4080); let dm=volatile_read64(xhci+4040); var sm:u64=0; var cm:u64=0; var ot:u64=0; if dm!=0 { let qi=volatile_read32(dm+8); sm=qi%256; cm=(qi/256)%256; ot=volatile_read32(dm+24); } let oi=volatile_read64(xhci+3976); let ox=(rr/2)%2; let oe=(rr/4)%32; v108_draw_small_u64(surface,((px+112)*65536)+(py+748),volatile_read64(xhci+4056)+(oi*0)+(ox*0)+(oe*0)+(sm*0)+(cm*0),green); v108_draw_small_u64(surface,((px+150)*65536)+(py+748),volatile_read64(xhci+4064),amber); v108_draw_small_u64(surface,((px+188)*65536)+(py+748),(ot/128)%2,white); v108_draw_small_u64(surface,((px+226)*65536)+(py+748),(ot/4)%32,green); v108_draw_small_u64(surface,((px+264)*65536)+(py+748),rr%256+(volatile_read64(xhci+3984)*0),amber); v108_draw_small_u64(surface,((px+306)*65536)+(py+748),(rr/256)%256,white); v108_draw_small_u64(surface,((px+350)*65536)+(py+748),(rr/65536)%256,white); }"
rep(oldrow,newrow,'async report telemetry row')

for q in ['fn v160_ehci_mouse_async_arm','fn v160_ehci_mouse_async_tick','let info1=1073774592+2+(ep*256)+(mmps*65536)','let info2=1073807360+(port*8388608)','volatile_write32(op+24,qlo)','cmd=set_flag(cmd,32)','v160_ehci_mouse_async_arm(xhci)','v160_ehci_mouse_async_tick(xhci)']:
    if q not in s: raise SystemExit('r59k async TT model missing '+q)
for q in ['fn v159_ehci_mouse_periodic_arm','let info2=1090591745']:
    if q not in s: raise SystemExit('r59k inherited periodic evidence lost '+q)
for bad in ('write(10)','nvme_submit_write','ahci_write','fat_write','block_write','input_push('):
    sec=s[s.index('fn v160_ehci_mouse_async_arm'):s.index('fn v135_hid_control_fallback_prepare')].lower()
    if bad in sec: raise SystemExit('r59k exceeds diagnostic/read-only scope '+bad)
if s.count('{')!=s.count('}'): raise SystemExit('r59k brace mismatch')
out=hashlib.sha256(s.encode()).hexdigest()
EXPECTED='5f836f2ae10743c967aa64bccf555cf45804a75a0e17f123ad4c0583c004b0bf'
if out!=EXPECTED: raise SystemExit('r59k output sha mismatch '+out)
p.write_text(s)
print(out)
