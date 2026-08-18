#!/usr/bin/env python3
from pathlib import Path
import hashlib
import subprocess, sys
if len(sys.argv)!=2: raise SystemExit('usage: patch_v108_r55_ehci_intel_hub_discovery.py <kernel/main.nx>')
p=Path(sys.argv[1]); here=Path(__file__).parent
base=here/'patch_v108_r54_ehci_root_descriptor_probe.py'
subprocess.run([sys.executable,str(base),str(p)],check=True,stdout=subprocess.DEVNULL)
s=p.read_text()
BASE='ebcf7baf18422cc72804eec9e18a317ed5daf1baee65330528be66c07d599c19'
actual=hashlib.sha256(s.encode()).hexdigest()
if actual!=BASE: raise SystemExit('r55 exact r54 base mismatch '+actual)

def rep(old,new,label,count=1):
    global s
    n=s.count(old)
    if n!=count: raise SystemExit(f'{label}: {n} expected {count}')
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
fn v155_ehci_control(xhci_state:u64,ord:u64,addr:u64,dma:u64,setupv:u64,length:u64) -> u64 {
    if xhci_state==0 || ord==0 || dma==0 { return 2; }
    let ebdf=v108_pci_nth_ehci_v121(ord-1); if ebdf==0 { return 2; }
    let base=pci_bar_base(ebdf,0); if base==0 { return 2; }
    let caplen=volatile_read8(base); if caplen<16 || caplen>128 { return 2; }
    let hcc=volatile_read32(base+8); let ac64=hcc%2; let upper=dma/4294967296; if ac64==0 && upper!=0 { return 3; }
    let op=base+caplen; zero_page(dma);
    let qh=dma; let qs=dma+128; let qd=dma+192; let qt=dma+256; let setup=dma+512; let data=dma+576;
    let qlo=qh%4294967296; let qslo=qs%4294967296; let qdlo=qd%4294967296; let qtlo=qt%4294967296; let setlo=setup%4294967296; let datlo=data%4294967296;
    unsafe { volatile_write64(setup,setupv); }
    if length==0 {
        unsafe { volatile_write32(qs+0,qtlo); volatile_write32(qs+4,1); volatile_write32(qs+8,528000); volatile_write32(qs+12,setlo); volatile_write32(qs+32,upper); volatile_write32(qt+0,1); volatile_write32(qt+4,1); volatile_write32(qt+8,2147519872); }
    } else {
        unsafe { volatile_write32(qs+0,qdlo); volatile_write32(qs+4,1); volatile_write32(qs+8,528000); volatile_write32(qs+12,setlo); volatile_write32(qs+32,upper); volatile_write32(qd+0,qtlo); volatile_write32(qd+4,qtlo); volatile_write32(qd+8,2147487104+(length*65536)); volatile_write32(qd+12,datlo); volatile_write32(qd+32,upper); volatile_write32(qt+0,1); volatile_write32(qt+4,1); volatile_write32(qt+8,2147519616); }
    }
    unsafe { volatile_write32(qh+0,qlo+2); volatile_write32(qh+4,1077993472+addr); volatile_write32(qh+8,1073741824); volatile_write32(qh+12,0); volatile_write32(qh+16,qslo); volatile_write32(qh+20,1); volatile_write32(qh+24,0); volatile_write32(op+8,0); volatile_write32(op+24,qlo); volatile_write32(op+4,63); }
    if ac64!=0 { unsafe { volatile_write32(op+16,upper); } }
    var cmd=volatile_read32(op); cmd=clear_flag(cmd,16); cmd=clear_flag(cmd,64); cmd=set_flag(cmd,1); cmd=set_flag(cmd,32); unsafe { volatile_write32(op,cmd); }
    var arm:u64=0; while (volatile_read32(op+4)/32768)%2==0 && arm<4000000 { cpu_pause(); arm=arm+1; }
    if arm>=4000000 { cmd=volatile_read32(op); cmd=clear_flag(cmd,32); unsafe { volatile_write32(op,cmd); } return 4; }
    var spins:u64=0; while (volatile_read32(qt+8)/128)%2!=0 && spins<12000000 { cpu_pause(); spins=spins+1; }
    cmd=volatile_read32(op); cmd=clear_flag(cmd,32); unsafe { volatile_write32(op,cmd); }
    var stop:u64=0; while (volatile_read32(op+4)/32768)%2!=0 && stop<4000000 { cpu_pause(); stop=stop+1; }
    let stok=volatile_read32(qt+8); let qstok=volatile_read32(qs+8); let serr=(stok/64)%2; let qerr=(qstok/64)%2;
    if serr!=0 || qerr!=0 || ((stok/4)%16)!=0 || ((qstok/4)%16)!=0 { return 6; }
    if spins>=12000000 || (stok/128)%2!=0 { return 5; }
    if length!=0 { let dtok=volatile_read32(qd+8); if (dtok/64)%2!=0 || ((dtok/4)%16)!=0 || (dtok/128)%2!=0 || ((dtok/65536)%32768)!=0 { return 6; } }
    return 1;
}
fn v155_ehci_intel_hub_discovery(xhci_state:u64,phys_state:u64) -> u64 {
    if xhci_state==0 || phys_state==0 { return 0; }
    let prior=volatile_read64(xhci_state+3920); if prior!=0 { return prior; }
    if volatile_read64(xhci_state+3792)!=1 || volatile_read64(xhci_state+3816)!=9 || volatile_read64(xhci_state+3832)!=32903 || volatile_read64(xhci_state+3840)!=32776 { return 0; }
    unsafe { volatile_write64(xhci_state+3920,9); volatile_write64(xhci_state+3928,0); volatile_write64(xhci_state+3936,0); volatile_write64(xhci_state+3944,0); volatile_write64(xhci_state+3952,0); volatile_write64(xhci_state+3960,0); volatile_write64(xhci_state+3968,0); volatile_write64(xhci_state+3976,0); volatile_write64(xhci_state+3984,0); volatile_write64(xhci_state+3992,0); volatile_write64(xhci_state+4000,0); volatile_write64(xhci_state+4008,0); volatile_write64(xhci_state+4016,0); volatile_write64(xhci_state+4024,0); volatile_write64(xhci_state+4032,0); }
    let ord=volatile_read64(xhci_state+3800); if ord==0 { unsafe { volatile_write64(xhci_state+3920,2); } return 2; }
    let dma=alloc_dma_page(phys_state,3); if dma==0 { unsafe { volatile_write64(xhci_state+3920,3); } return 3; }
    var rc=v155_ehci_control(xhci_state,ord,0,dma,66816,0); if rc!=1 { unsafe { volatile_write64(xhci_state+3920,3); volatile_write64(xhci_state+4000,rc); } return 3; }
    pit_wait(23864); unsafe { volatile_write64(xhci_state+3928,1); }
    rc=v155_ehci_control(xhci_state,ord,1,dma,2533274823952000,9); if rc!=1 { unsafe { volatile_write64(xhci_state+3920,4); volatile_write64(xhci_state+4000,rc); } return 4; }
    let data=dma+576; let clen=volatile_read8(data); let ctype=volatile_read8(data+1); let cfg=volatile_read8(data+5); if clen<9 || ctype!=2 || cfg==0 { unsafe { volatile_write64(xhci_state+3920,5); } return 5; }
    let setcfg=2304+(cfg*65536); rc=v155_ehci_control(xhci_state,ord,1,dma,setcfg,0); if rc!=1 { unsafe { volatile_write64(xhci_state+3920,4); volatile_write64(xhci_state+4000,rc); } return 4; }
    pit_wait(23864); unsafe { volatile_write64(xhci_state+3992,cfg); }
    rc=v155_ehci_control(xhci_state,ord,1,dma,2533275478263456,9); if rc!=1 { unsafe { volatile_write64(xhci_state+3920,4); volatile_write64(xhci_state+4000,rc); } return 4; }
    let hlen=volatile_read8(data); let htype=volatile_read8(data+1); let nports=volatile_read8(data+2); let chars=volatile_read8(data+3)+(volatile_read8(data+4)*256); let pgood=volatile_read8(data+5);
    if hlen<7 || htype!=41 || nports==0 || nports>15 { unsafe { volatile_write64(xhci_state+3920,5); } return 5; }
    unsafe { volatile_write64(xhci_state+3936,nports); volatile_write64(xhci_state+4008,chars); volatile_write64(xhci_state+4016,hlen); volatile_write64(xhci_state+4024,htype); }
    let power_mode=chars%4; var p:u64=1; var power_cmds:u64=0;
    if power_mode!=2 { while p<=nports { let req=525091+(p*4294967296); rc=v155_ehci_control(xhci_state,ord,1,dma,req,0); if rc==1 { power_cmds=power_cmds+1; } p=p+1; } let delay=(pgood*2387)+23864; pit_wait(delay); }
    var connected:u64=0; var enabled:u64=0; var powered:u64=0; var bitmap:u64=0; var first:u64=0; var first_speed:u64=3; var change_bitmap:u64=0; p=1;
    while p<=nports {
        let req=1125899906842787+(p*4294967296); rc=v155_ehci_control(xhci_state,ord,1,dma,req,4); if rc!=1 { unsafe { volatile_write64(xhci_state+3920,6); volatile_write64(xhci_state+4000,rc); volatile_write64(xhci_state+4032,p); } return 6; }
        let st=volatile_read8(data)+(volatile_read8(data+1)*256); let ch=volatile_read8(data+2)+(volatile_read8(data+3)*256); let conn=st%2; let ena=(st/2)%2; let pwr=(st/256)%2;
        if ch!=0 { change_bitmap=change_bitmap+power2_u64(p-1); }
        if conn!=0 { connected=connected+1; bitmap=bitmap+power2_u64(p-1); if first==0 { first=p; let low=(st/512)%2; let high=(st/1024)%2; if high!=0 { first_speed=2; } else { if low!=0 { first_speed=1; } else { first_speed=0; } } unsafe { volatile_write64(xhci_state+3984,st); } } }
        if ena!=0 { enabled=enabled+1; } if pwr!=0 { powered=powered+1; }
        p=p+1;
    }
    unsafe { volatile_write64(xhci_state+3944,connected); volatile_write64(xhci_state+3952,enabled); volatile_write64(xhci_state+3960,bitmap); volatile_write64(xhci_state+3968,first); volatile_write64(xhci_state+3976,first_speed); volatile_write64(xhci_state+4016,powered); volatile_write64(xhci_state+4024,power_cmds); volatile_write64(xhci_state+4032,change_bitmap); }
    if connected==0 { unsafe { volatile_write64(xhci_state+3920,7); } return 7; }
    unsafe { volatile_write64(xhci_state+3920,1); } return 1;
}
'''
pos=s.index('fn xhci_configure_boot_hid')
s=s[:pos]+insert+s[pos:]
rep('if xhci!=0 { v153_intel_ehci_port_reset_companion_classifier(xhci); if volatile_read64(xhci+3696)==1 { v154_ehci_root_descriptor_probe(xhci,phys_state); } }','if xhci!=0 { v153_intel_ehci_port_reset_companion_classifier(xhci); if volatile_read64(xhci+3696)==1 { v154_ehci_root_descriptor_probe(xhci,phys_state); if volatile_read64(xhci+3792)==1 { v155_ehci_intel_hub_discovery(xhci,phys_state); } } }','r55 call')
fnrep('v140_text_wifi_v140',label_fn('v140_text_wifi_v140','R55 S N C E B F T'))
oldrow='    v140_text_wifi_v140(surface,px+10,py+748,white); if xhci!=0 { v108_draw_small_u64(surface,((px+112)*65536)+(py+748),volatile_read64(xhci+3792),green); v108_draw_small_u64(surface,((px+150)*65536)+(py+748),volatile_read64(xhci+3800),amber); v108_draw_small_u64(surface,((px+188)*65536)+(py+748),volatile_read64(xhci+3808),white); v108_draw_small_u64(surface,((px+226)*65536)+(py+748),volatile_read64(xhci+3816),green); v108_draw_small_u64(surface,((px+264)*65536)+(py+748),volatile_read64(xhci+3824),amber); v108_draw_small_u64(surface,((px+306)*65536)+(py+748),volatile_read64(xhci+3832),white); v108_draw_small_u64(surface,((px+350)*65536)+(py+748),volatile_read64(xhci+3840),white); }'
newrow='    v140_text_wifi_v140(surface,px+10,py+748,white); if xhci!=0 { v108_draw_small_u64(surface,((px+112)*65536)+(py+748),volatile_read64(xhci+3920),green); v108_draw_small_u64(surface,((px+150)*65536)+(py+748),volatile_read64(xhci+3936),amber); v108_draw_small_u64(surface,((px+188)*65536)+(py+748),volatile_read64(xhci+3944),white); v108_draw_small_u64(surface,((px+226)*65536)+(py+748),volatile_read64(xhci+3952),green); v108_draw_small_u64(surface,((px+264)*65536)+(py+748),volatile_read64(xhci+3960),amber); v108_draw_small_u64(surface,((px+306)*65536)+(py+748),volatile_read64(xhci+3968),white); v108_draw_small_u64(surface,((px+350)*65536)+(py+748),volatile_read64(xhci+3976),white); }'
rep(oldrow,newrow,'r55 row')
r55=s[s.index('fn v155_ehci_control'):s.index('fn xhci_configure_boot_hid')]
for q in ['setupv','cmd=set_flag(cmd,32)','cmd=clear_flag(cmd,32)','2533275478263456','525091+(p*4294967296)','1125899906842787+(p*4294967296)','volatile_read64(xhci_state+3792)!=1','volatile_read64(xhci_state+3832)!=32903','volatile_read64(xhci_state+3840)!=32776']:
    if q not in r55: raise SystemExit('missing '+q)
for bad in ['set_flag(cmd,16)','periodiclistbase','interrupt endpoint','nvme_submit_write','ahci_write','write(10)']:
    if bad in r55.lower(): raise SystemExit('forbidden '+bad)
if s.count('{')!=s.count('}'): raise SystemExit('brace mismatch')
out=hashlib.sha256(s.encode()).hexdigest()
EXPECTED='7f3aebe8d7ac75cada7b32dcffd4074c84651e1dd22c179bc2e34e0375fbc4d7'
if out!=EXPECTED: raise SystemExit('r55 output sha mismatch '+out)
p.write_text(s)
print(out)
