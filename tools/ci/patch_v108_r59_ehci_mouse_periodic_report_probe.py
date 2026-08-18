#!/usr/bin/env python3
from pathlib import Path
import hashlib, subprocess, sys
if len(sys.argv)!=2: raise SystemExit('usage: patch_v108_r59_ehci_mouse_periodic_report_probe.py <kernel/main.nx>')
p=Path(sys.argv[1]); here=Path(__file__).parent
base=here/'patch_v108_r58_ehci_composite_hid_census.py'
subprocess.run([sys.executable,str(base),str(p)],check=True,stdout=subprocess.DEVNULL)
s=p.read_text()
BASE='e8edf7b8d38982b27b997258230ee5f0a51ebd46586bb6cfca679a00aae16f49'
actual=hashlib.sha256(s.encode()).hexdigest()
if actual!=BASE: raise SystemExit('r59 exact r58 base mismatch '+actual)

def rep(old,new,label,count=1):
    global s
    n=s.count(old)
    if n!=count: raise SystemExit(f'r59 {label}: {n} expected {count}')
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

insert=r'''
fn v159_ehci_mouse_periodic_arm(xhci_state:u64,phys_state:u64) -> u64 {
    if xhci_state==0 || phys_state==0 { return 0; }
    if volatile_read64(xhci_state+3920)!=1 || volatile_read64(xhci_state+3928)!=2 { unsafe { volatile_write64(xhci_state+4056,10); } return 10; }
    let kep=volatile_read64(xhci_state+3936); let mep=volatile_read64(xhci_state+3944); let mif=volatile_read64(xhci_state+3952); let mmps=volatile_read64(xhci_state+3960); let hids=volatile_read64(xhci_state+3968); let mint=volatile_read64(xhci_state+3976); let cfg=volatile_read64(xhci_state+4008); let speed=volatile_read64(xhci_state+4024); let dma=volatile_read64(xhci_state+4040);
    if kep==0 || mep<128 || (mep%128)==0 || mif>31 || mmps==0 || mmps>64 || hids<2 || mint==0 || mint>255 || cfg==0 || speed>1 || dma==0 { unsafe { volatile_write64(xhci_state+4056,11); } return 11; }
    let ep0mps:u64=8; unsafe { volatile_write64(xhci_state+3936,ep0mps); }
    let setcfg=2304+(cfg*65536); var rc=v157_ehci_tt_control(xhci_state,2,setcfg,0); if rc!=1 { unsafe { volatile_write64(xhci_state+3936,kep); volatile_write64(xhci_state+4056,12); volatile_write64(xhci_state+4000,rc); } return 12; }
    pit_wait(23864);
    let setproto=33+(11*256)+(mif*4294967296); rc=v157_ehci_tt_control(xhci_state,2,setproto,0); if rc!=1 { unsafe { volatile_write64(xhci_state+3936,kep); volatile_write64(xhci_state+4056,13); volatile_write64(xhci_state+4000,rc); } return 13; }
    unsafe { volatile_write64(xhci_state+3936,kep); }
    let frame=alloc_dma_page(phys_state,4); if frame==0 { unsafe { volatile_write64(xhci_state+4056,14); } return 14; }
    let ebdf=v108_pci_nth_ehci_v121(1); if ebdf==0 { unsafe { volatile_write64(xhci_state+4056,15); } return 15; }
    let base=pci_bar_base(ebdf,0); if base==0 { unsafe { volatile_write64(xhci_state+4056,15); } return 15; }
    let caplen=volatile_read8(base); if caplen<16 || caplen>128 { unsafe { volatile_write64(xhci_state+4056,15); } return 15; }
    let hcc=volatile_read32(base+8); let ac64=hcc%2; let upper=dma/4294967296; let fupper=frame/4294967296; if upper!=fupper || (ac64==0 && upper!=0) { unsafe { volatile_write64(xhci_state+4056,16); } return 16; }
    let op=base+caplen; var cmd=volatile_read32(op); cmd=clear_flag(cmd,32); cmd=clear_flag(cmd,16); unsafe { volatile_write32(op,cmd); }
    var quiet:u64=0; while (((volatile_read32(op+4)/16384)%2)!=0 || ((volatile_read32(op+4)/32768)%2)!=0) && quiet<4000000 { cpu_pause(); quiet=quiet+1; }
    if quiet>=4000000 { unsafe { volatile_write64(xhci_state+4056,17); } return 17; }
    zero_page(frame); zero_page(dma);
    let qh=dma; let qtd=dma+128; let data=dma+256; let qlo=qh%4294967296; let tdlo=qtd%4294967296; let datlo=data%4294967296; let flo=frame%4294967296; let ep=mep%128;
    let info1=2+(ep*256)+(mmps*65536); let info2=1090591745; let token=527744;
    unsafe { volatile_write32(qh+0,1); volatile_write32(qh+4,info1); volatile_write32(qh+8,info2); volatile_write32(qh+12,0); volatile_write32(qh+16,tdlo); volatile_write32(qh+20,1); volatile_write32(qh+24,0); volatile_write32(qtd+0,1); volatile_write32(qtd+4,1); volatile_write32(qtd+8,token); volatile_write32(qtd+12,datlo); volatile_write32(qtd+32,upper); }
    var i:u64=0; while i<1024 { var link:u64=1; if i%mint==0 { link=qlo+2; } unsafe { volatile_write32(frame+(i*4),link); } i=i+1; }
    unsafe { volatile_write32(op+8,0); volatile_write32(op+20,flo); volatile_write32(op+4,63); }
    if ac64!=0 { unsafe { volatile_write32(op+16,upper); } }
    cmd=volatile_read32(op); cmd=clear_flag(cmd,32); cmd=set_flag(cmd,1); cmd=set_flag(cmd,16); unsafe { volatile_write32(op,cmd); }
    var arm:u64=0; while (volatile_read32(op+4)/16384)%2==0 && arm<4000000 { cpu_pause(); arm=arm+1; }
    if arm>=4000000 { cmd=volatile_read32(op); cmd=clear_flag(cmd,16); unsafe { volatile_write32(op,cmd); volatile_write64(xhci_state+4056,18); } return 18; }
    unsafe { volatile_write64(xhci_state+4048,frame); volatile_write64(xhci_state+4056,1); volatile_write64(xhci_state+4064,0); volatile_write64(xhci_state+4072,0); volatile_write64(xhci_state+4080,0); volatile_write64(xhci_state+4088,0); }
    return 1;
}
fn v159_ehci_mouse_periodic_tick(xhci_state:u64) -> u64 {
    if xhci_state==0 || volatile_read64(xhci_state+4056)!=1 { return 0; }
    let dma=volatile_read64(xhci_state+4040); let frame=volatile_read64(xhci_state+4048); if dma==0 || frame==0 { unsafe { volatile_write64(xhci_state+4056,20); } return 0; }
    let ebdf=v108_pci_nth_ehci_v121(1); if ebdf==0 { unsafe { volatile_write64(xhci_state+4056,21); } return 0; }
    let base=pci_bar_base(ebdf,0); if base==0 { unsafe { volatile_write64(xhci_state+4056,21); } return 0; }
    let caplen=volatile_read8(base); if caplen<16 || caplen>128 { unsafe { volatile_write64(xhci_state+4056,21); } return 0; }
    let op=base+caplen; let qh=dma; let qtd=dma+128; let data=dma+256; let tok=volatile_read32(qtd+8);
    if (tok/128)%2!=0 { return 0; }
    let errs=(tok/4)%32; if errs!=0 { var cmd=volatile_read32(op); cmd=clear_flag(cmd,16); unsafe { volatile_write32(op,cmd); volatile_write64(xhci_state+4056,22); } return 0; }
    let rem=(tok/65536)%32768; if rem>8 { unsafe { volatile_write64(xhci_state+4056,23); } return 0; }
    var cmd=volatile_read32(op); cmd=clear_flag(cmd,16); unsafe { volatile_write32(op,cmd); }
    var stop:u64=0; while (volatile_read32(op+4)/16384)%2!=0 && stop<4000000 { cpu_pause(); stop=stop+1; }
    if stop>=4000000 { unsafe { volatile_write64(xhci_state+4056,24); } return 0; }
    let raw=volatile_read64(data); let prev=volatile_read64(xhci_state+4088); unsafe { volatile_write64(xhci_state+4064,volatile_read64(xhci_state+4064)+1); volatile_write64(xhci_state+4080,raw); if raw!=prev { volatile_write64(xhci_state+4072,volatile_read64(xhci_state+4072)+1); volatile_write64(xhci_state+4088,raw); } volatile_write64(data,0); volatile_write32(qtd+0,1); volatile_write32(qtd+4,1); volatile_write32(qtd+8,527744); volatile_write32(qh+16,qtd%4294967296); volatile_write32(qh+20,1); }
    cmd=volatile_read32(op); cmd=set_flag(cmd,1); cmd=set_flag(cmd,16); unsafe { volatile_write32(op,cmd); }
    var arm:u64=0; while (volatile_read32(op+4)/16384)%2==0 && arm<4000000 { cpu_pause(); arm=arm+1; }
    if arm>=4000000 { unsafe { volatile_write64(xhci_state+4056,25); } return 0; }
    return 1;
}
'''
_,_,cfg_end=(lambda name: (lambda st,op: (lambda d=0: None))(0,0))('unused') if False else (None,None,None)
# insert after the existing xhci_configure_boot_hid function without disturbing inherited r55-r58 scope slices
st=s.index('fn xhci_configure_boot_hid'); op=s.index('{',st); d=0; cfg_end=0
for i in range(op,len(s)):
    if s[i]=='{': d+=1
    elif s[i]=='}':
        d-=1
        if d==0: cfg_end=i+1; break
if cfg_end==0: raise SystemExit('r59 xhci_configure_boot_hid boundary missing')
s=s[:cfg_end]+'\n'+insert+s[cfg_end:]
fnrep('v140_text_wifi_v140',label_fn('v140_text_wifi_v140','R59 S N C B X Y W'))
oldrow='    v140_text_wifi_v140(surface,px+10,py+748,white); if xhci!=0 { v108_draw_small_u64(surface,((px+112)*65536)+(py+748),volatile_read64(xhci+3920),green); v108_draw_small_u64(surface,((px+150)*65536)+(py+748),volatile_read64(xhci+3928),amber); v108_draw_small_u64(surface,((px+188)*65536)+(py+748),volatile_read64(xhci+3936),white); v108_draw_small_u64(surface,((px+226)*65536)+(py+748),volatile_read64(xhci+3944),green); v108_draw_small_u64(surface,((px+264)*65536)+(py+748),volatile_read64(xhci+3952),amber); v108_draw_small_u64(surface,((px+306)*65536)+(py+748),volatile_read64(xhci+3960),white); v108_draw_small_u64(surface,((px+350)*65536)+(py+748),volatile_read64(xhci+3968),white); }'
newrow='    v140_text_wifi_v140(surface,px+10,py+748,white); if xhci!=0 { let rr=volatile_read64(xhci+4080); v108_draw_small_u64(surface,((px+112)*65536)+(py+748),volatile_read64(xhci+4056),green); v108_draw_small_u64(surface,((px+150)*65536)+(py+748),volatile_read64(xhci+4064),amber); v108_draw_small_u64(surface,((px+188)*65536)+(py+748),volatile_read64(xhci+4072),white); v108_draw_small_u64(surface,((px+226)*65536)+(py+748),rr%256,green); v108_draw_small_u64(surface,((px+264)*65536)+(py+748),(rr/256)%256,amber); v108_draw_small_u64(surface,((px+306)*65536)+(py+748),(rr/65536)%256,white); v108_draw_small_u64(surface,((px+350)*65536)+(py+748),(rr/16777216)%256,white); }'
rep(oldrow,newrow,'runtime row')
rep('if volatile_read64(xhci+3920)==1 && volatile_read64(xhci+3928)==2 { v157_ehci_child_hid_probe(xhci); }','if volatile_read64(xhci+3920)==1 && volatile_read64(xhci+3928)==2 { v157_ehci_child_hid_probe(xhci); if volatile_read64(xhci+3920)==1 && volatile_read64(xhci+3944)!=0 { v159_ehci_mouse_periodic_arm(xhci,phys_state); } }','arm hook')
rep('        if xhci!=0 { if volatile_read64(xhci+3760)!=0 { v136_hid_interrupt_recovery_tick(xhci); } v144_hid_forensic_snapshot(xhci); }\n        var telemetry_redraw:u64=0;','        if xhci!=0 { if volatile_read64(xhci+3760)!=0 { v136_hid_interrupt_recovery_tick(xhci); } v144_hid_forensic_snapshot(xhci); }\n        var r59_redraw:u64=0; if xhci!=0 { r59_redraw=v159_ehci_mouse_periodic_tick(xhci); }\n        var telemetry_redraw:u64=r59_redraw;','live tick hook')
if s.count('{')!=s.count('}'): raise SystemExit('r59 brace mismatch')
r59=s[s.index('fn v159_ehci_mouse_periodic_arm'):s.index('fn v135_hid_control_fallback_prepare')]
for q in ['v157_ehci_tt_control(xhci_state,2,setcfg,0)','v157_ehci_tt_control(xhci_state,2,setproto,0)','alloc_dma_page(phys_state,4)','volatile_write32(op+20,flo)','cmd=set_flag(cmd,16)','while i<1024','i%mint==0','info2=1090591745','token=527744','v159_ehci_mouse_periodic_tick','volatile_write64(xhci_state+4064','volatile_write64(xhci_state+4072','volatile_write64(xhci_state+4080','volatile_write64(xhci_state+4088']:
    if q not in r59: raise SystemExit('r59 model missing '+q)
for bad in ('write(10)','nvme_submit_write','ahci_write','fat_write','block_write','input_push('):
    if bad in r59.lower(): raise SystemExit('r59 exceeds diagnostic scope '+bad)
out=hashlib.sha256(s.encode()).hexdigest()
EXPECTED='38544595b9ce8c1d7775319247b9d544adadf16b2526d6ca9dbfb41fa0f7a9b7'
if out!=EXPECTED: raise SystemExit('r59 output sha mismatch '+out)
p.write_text(s)
print(out)
