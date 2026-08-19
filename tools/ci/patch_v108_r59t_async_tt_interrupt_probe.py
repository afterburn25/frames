#!/usr/bin/env python3
from pathlib import Path
import hashlib, subprocess, sys
if len(sys.argv)!=2: raise SystemExit('usage: patch_v108_r59t_async_tt_interrupt_probe.py <kernel/main.nx>')
p=Path(sys.argv[1]); here=Path(__file__).parent
base=here/'patch_v108_r59s_qh_current_completion_gate.py'
subprocess.run([sys.executable,str(base),str(p)],check=True,stdout=subprocess.DEVNULL)
s=p.read_text()
BASE='10a1a6550abafe7c593d059eeb983d6a576b19ab46c1dcde6ec71888aa6d4a03'
actual=hashlib.sha256(s.encode()).hexdigest()
if actual!=BASE: raise SystemExit('r59t exact r59s base mismatch '+actual)

def fn(src,name):
    st=src.index('fn '+name); op=src.index('{',st); d=0
    for i in range(op,len(src)):
        if src[i]=='{': d+=1
        elif src[i]=='}':
            d-=1
            if d==0:return src[st:i+1]
    raise SystemExit('unterminated '+name)

def label(name,text):
    out=f'fn {name}(surface:u64,x:u64,y:u64,color:u64) -> u64 {{'
    for i,ch in enumerate(text): out+=f' if gui_draw_char_scaled(surface,((x+{i*6})*65536)+y,({ord(ch)}*65536)+1,color)==0 {{ return 0; }}'
    return out+' return 1; }'

insert=r'''
fn v160_ehci_mouse_async_arm(xhci_state:u64,phys_state:u64) -> u64 {
    if xhci_state==0 || phys_state==0 { return 0; }
    if volatile_read64(xhci_state+3920)!=1 || volatile_read64(xhci_state+3928)!=2 { unsafe { volatile_write64(xhci_state+4056,40); } return 40; }
    let kep=volatile_read64(xhci_state+3936); let mep=volatile_read64(xhci_state+3944); let mif=volatile_read64(xhci_state+3952); let mmps=volatile_read64(xhci_state+3960); let hids=volatile_read64(xhci_state+3968); let cfg=volatile_read64(xhci_state+4008); let speed=volatile_read64(xhci_state+4024); let dma=volatile_read64(xhci_state+4040); let port=volatile_read64(xhci_state+3928);
    if kep==0 || mep<128 || (mep%128)==0 || mif>31 || mmps==0 || mmps>64 || hids<2 || cfg==0 || speed>1 || dma==0 || port==0 || port>15 { unsafe { volatile_write64(xhci_state+4056,41); } return 41; }
    let ep0mps:u64=8; unsafe { volatile_write64(xhci_state+3936,ep0mps); }
    let setcfg=2304+(cfg*65536); var rc=v157_ehci_tt_control(xhci_state,2,setcfg,0); if rc!=1 { unsafe { volatile_write64(xhci_state+3936,kep); volatile_write64(xhci_state+4056,42); volatile_write64(xhci_state+4000,rc); } return 42; }
    pit_wait(23864);
    let setproto=33+(11*256)+65536+(mif*4294967296); rc=v157_ehci_tt_control(xhci_state,2,setproto,0); if rc!=1 { unsafe { volatile_write64(xhci_state+3936,kep); volatile_write64(xhci_state+4056,43); volatile_write64(xhci_state+4000,rc); } return 43; }
    pit_wait(23864);
    let getproto=161+(3*256)+(mif*4294967296)+(1*281474976710656); rc=v157_ehci_tt_control(xhci_state,2,getproto,1); if rc!=1 || volatile_read8(dma+576)!=1 { unsafe { volatile_write64(xhci_state+3936,kep); volatile_write64(xhci_state+4056,44); volatile_write64(xhci_state+4000,rc); } return 44; }
    unsafe { volatile_write64(xhci_state+3936,kep); }
    let ebdf=v108_pci_nth_ehci_v121(1); if ebdf==0 { unsafe { volatile_write64(xhci_state+4056,45); } return 45; }
    let base=pci_bar_base(ebdf,0); if base==0 { unsafe { volatile_write64(xhci_state+4056,45); } return 45; }
    let caplen=volatile_read8(base); if caplen<16 || caplen>128 { unsafe { volatile_write64(xhci_state+4056,45); } return 45; }
    let hcc=volatile_read32(base+8); let ac64=hcc%2; let upper=dma/4294967296; if ac64==0 && upper!=0 { unsafe { volatile_write64(xhci_state+4056,46); } return 46; }
    let op=base+caplen; var cmd=volatile_read32(op); cmd=clear_flag(cmd,16); cmd=clear_flag(cmd,32); unsafe { volatile_write32(op,cmd); }
    var quiet:u64=0; while (((volatile_read32(op+4)/16384)%2)!=0 || ((volatile_read32(op+4)/32768)%2)!=0) && quiet<4000000 { cpu_pause(); quiet=quiet+1; }
    if quiet>=4000000 { unsafe { volatile_write64(xhci_state+4056,47); } return 47; }
    zero_page(dma);
    let qh=dma; let qtd=dma+128; let data=dma+256; let qlo=qh%4294967296; let tdlo=qtd%4294967296; let datlo=data%4294967296; let ep=mep%128;
    let info1=1073774592+2+(ep*256)+(speed*4096)+(mmps*65536); let info2=1073807360+(port*8388608); let token=527744;
    unsafe { volatile_write32(qh+0,qlo+2); volatile_write32(qh+4,info1); volatile_write32(qh+8,info2); volatile_write32(qh+12,0); volatile_write32(qh+16,tdlo); volatile_write32(qh+20,1); volatile_write32(qh+24,0); volatile_write32(qtd+0,1); volatile_write32(qtd+4,1); volatile_write32(qtd+8,token); volatile_write32(qtd+12,datlo); volatile_write32(qtd+32,upper); volatile_write32(op+8,0); volatile_write32(op+24,qlo); volatile_write32(op+4,63); }
    if ac64!=0 { unsafe { volatile_write32(op+16,upper); } }
    cmd=volatile_read32(op); cmd=clear_flag(cmd,16); cmd=clear_flag(cmd,64); cmd=set_flag(cmd,1); cmd=set_flag(cmd,32); unsafe { volatile_write32(op,cmd); }
    var arm:u64=0; while (volatile_read32(op+4)/32768)%2==0 && arm<4000000 { cpu_pause(); arm=arm+1; }
    if arm>=4000000 { cmd=volatile_read32(op); cmd=clear_flag(cmd,32); unsafe { volatile_write32(op,cmd); volatile_write64(xhci_state+4056,48); } return 48; }
    unsafe { volatile_write64(xhci_state+4056,1); volatile_write64(xhci_state+3984,0); volatile_write64(xhci_state+3992,0); volatile_write64(xhci_state+4064,0); volatile_write64(xhci_state+4072,0); volatile_write64(xhci_state+4080,0); volatile_write64(xhci_state+4088,0); }
    return 1;
}
fn v160_ehci_mouse_async_tick(xhci_state:u64) -> u64 {
    if xhci_state==0 || volatile_read64(xhci_state+4056)!=1 { return 0; }
    let dma=volatile_read64(xhci_state+4040); if dma==0 { unsafe { volatile_write64(xhci_state+4056,50); } return 0; }
    let ebdf=v108_pci_nth_ehci_v121(1); if ebdf==0 { unsafe { volatile_write64(xhci_state+4056,51); } return 0; }
    let base=pci_bar_base(ebdf,0); if base==0 { unsafe { volatile_write64(xhci_state+4056,51); } return 0; }
    let caplen=volatile_read8(base); if caplen<16 || caplen>128 { unsafe { volatile_write64(xhci_state+4056,51); } return 0; }
    let op=base+caplen; let qh=dma; let qtd=dma+128; let data=dma+256; let tdlo=qtd%4294967296; let qtdtok=volatile_read32(qtd+8); let cur=volatile_read32(qh+12); let qtok=volatile_read32(qh+24);
    let ta=(qtdtok/128)%2; let qa=(qtok/128)%2; let sx=(qtok/2)%2; let qe=(qtdtok/4)%32; let oe=(qtok/4)%32; let er=qe+oe; let rem=(qtdtok/65536)%32768; let orem=(qtok/65536)%32768; let gate=1+(ta*2)+(qa*4)+(sx*8)+(er*16)+(rem*1024)+(orem*32768); unsafe { volatile_write64(xhci_state+3984,gate); volatile_write64(xhci_state+4080,qtok); }
    if cur!=tdlo { return 0; }
    if ta!=0 && qa!=0 { return 0; }
    if qe!=0 || oe!=0 { var cmd=volatile_read32(op); cmd=clear_flag(cmd,32); unsafe { volatile_write32(op,cmd); volatile_write64(xhci_state+4056,52); } return 0; }
    if rem>8 || orem>8 { unsafe { volatile_write64(xhci_state+4056,53); } return 0; }
    var cmd=volatile_read32(op); cmd=clear_flag(cmd,32); unsafe { volatile_write32(op,cmd); }
    var stop:u64=0; while (volatile_read32(op+4)/32768)%2!=0 && stop<4000000 { cpu_pause(); stop=stop+1; }
    if stop>=4000000 { unsafe { volatile_write64(xhci_state+4056,54); } return 0; }
    let raw=volatile_read64(data); let prev=volatile_read64(xhci_state+4088);
    unsafe { volatile_write64(xhci_state+4064,volatile_read64(xhci_state+4064)+1); if raw!=prev { volatile_write64(xhci_state+4072,volatile_read64(xhci_state+4072)+1); } volatile_write64(xhci_state+4088,raw); volatile_write64(data,0); volatile_write32(qh+12,0); volatile_write32(qh+16,tdlo); volatile_write32(qh+20,1); volatile_write32(qh+24,0); volatile_write32(qtd+0,1); volatile_write32(qtd+4,1); volatile_write32(qtd+8,527744); }
    cmd=volatile_read32(op); cmd=clear_flag(cmd,16); cmd=set_flag(cmd,1); cmd=set_flag(cmd,32); unsafe { volatile_write32(op,cmd); }
    var arm:u64=0; while (volatile_read32(op+4)/32768)%2==0 && arm<4000000 { cpu_pause(); arm=arm+1; }
    if arm>=4000000 { unsafe { volatile_write64(xhci_state+4056,55); } return 0; }
    return 1;
}
'''
pos=s.index('fn v135_hid_control_fallback_prepare'); s=s[:pos]+insert+'\n'+s[pos:]
a='if volatile_read64(xhci+3920)==1 && volatile_read64(xhci+3944)!=0 { v159_ehci_mouse_periodic_arm(xhci,phys_state); }'; b='if volatile_read64(xhci+3920)==1 && volatile_read64(xhci+3944)!=0 { v160_ehci_mouse_async_arm(xhci,phys_state); }'
if s.count(a)!=1: raise SystemExit('r59t arm hook anchor mismatch')
s=s.replace(a,b,1)
a='var r59_redraw:u64=0; if xhci!=0 { r59_redraw=v159_ehci_mouse_periodic_tick(xhci); }'; b='var r59_redraw:u64=0; if xhci!=0 { r59_redraw=v160_ehci_mouse_async_tick(xhci); }'
if s.count(a)!=1: raise SystemExit('r59t tick hook anchor mismatch')
s=s.replace(a,b,1)
s=s.replace(fn(s,'v140_text_wifi_v140'),label('v140_text_wifi_v140','R5T G N 0 1 2 3'),1)
rs=s.index('v140_text_wifi_v140(surface,px+10,py+748,white);'); re=s.index('\n    return 1;\n}',rs)
newrow="v140_text_wifi_v140(surface,px+10,py+748,white); if xhci!=0 { let dm=volatile_read64(xhci+4040); let frame=volatile_read64(xhci+4048); let rr=volatile_read64(xhci+4080); let oi=volatile_read64(xhci+3976); let compat_stage=volatile_read64(xhci+4056); let compat_q=volatile_read64(xhci+4072); let compat_hubproto=volatile_read64(xhci+3880); let compat_ttrc=volatile_read64(xhci+3888); var sm:u64=0; var cm:u64=0; var fls:u64=3; var fi:u64=0; var linked:u64=0; var qmatch:u64=0; var pss:u64=0; var ot:u64=0; if dm!=0 { let qi=volatile_read32(dm+8); sm=qi%256; cm=(qi/256)%256; ot=volatile_read32(dm+24); if frame!=0 { let eb=v108_pci_nth_ehci_v121(1); if eb!=0 { let bb=pci_bar_base(eb,0); if bb!=0 { let cl=volatile_read8(bb); if cl>=16 && cl<=128 { let op=bb+cl; let c=volatile_read32(op); fls=(c/4)%4; let fri59n=volatile_read32(op+12)%16384; fi=(fri59n/8)%1024; pss=(volatile_read32(op+4)/16384)%2; let qlo=dm%4294967296; let tdlo=(dm+128)%4294967296; if volatile_read32(frame+(fi*4))==qlo+2 { linked=1; } if volatile_read32(dm+12)==tdlo { qmatch=1; } } } } } } let compat=(volatile_read64(xhci+4024))+(volatile_read64(xhci+3984)*0)+(rr/2)%2+(rr/4)%32+(ot/128)%2+(ot/2)%2+(ot/4)%32+(ot/65536)%32768+(ot/2147483648)%2+compat_stage+compat_q+oi+sm+cm+compat_hubproto+compat_ttrc+fls+fi+linked+qmatch+pss; let raw=volatile_read64(xhci+4088); let rawcompat=((raw/4294967296)%256)+((raw/1099511627776)%256)+((raw/281474976710656)%256)+((raw/72057594037927936)%256); v108_draw_small_u64(surface,((px+108)*65536)+(py+748),volatile_read64(xhci+3984)+(compat*0)+(rawcompat*0),green); v108_draw_small_u64(surface,((px+160)*65536)+(py+748),volatile_read64(xhci+4064),amber); v108_draw_small_u64(surface,((px+212)*65536)+(py+748),raw%256,white); v108_draw_small_u64(surface,((px+252)*65536)+(py+748),(raw/256)%256,green); v108_draw_small_u64(surface,((px+292)*65536)+(py+748),(raw/65536)%256,amber); v108_draw_small_u64(surface,((px+332)*65536)+(py+748),(raw/16777216)%256,white); }"
s=s[:rs]+newrow+s[re:]
for q in ('fn v160_ehci_mouse_async_arm','fn v160_ehci_mouse_async_tick','let info1=1073774592+2+(ep*256)+(speed*4096)+(mmps*65536)','let info2=1073807360+(port*8388608)','volatile_write32(op+24,qlo)','cmd=set_flag(cmd,32)','let qtdtok=volatile_read32(qtd+8)','let qtok=volatile_read32(qh+24)','v160_ehci_mouse_async_arm(xhci,phys_state)','r59_redraw=v160_ehci_mouse_async_tick(xhci)'):
    if q not in s: raise SystemExit('r59t witness missing '+q)
scope=s[s.index('fn v160_ehci_mouse_async_arm'):s.index('fn v135_hid_control_fallback_prepare')].lower()
for bad in ('write(10)','nvme_submit_write','ahci_write','fat_write','block_write','input_push('):
    if bad in scope: raise SystemExit('r59t exceeds raw diagnostic/read-only scope '+bad)
if s.count('{')!=s.count('}'): raise SystemExit('r59t brace mismatch')
out=hashlib.sha256(s.encode()).hexdigest(); EXPECTED='8b1c1d40702a35d85e327f50a3e7569c1181352822fa25806349bc55010d8012'
if out!=EXPECTED: raise SystemExit('r59t output sha mismatch '+out)
p.write_text(s); print(out)
