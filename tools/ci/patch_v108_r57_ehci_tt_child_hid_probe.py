#!/usr/bin/env python3
from pathlib import Path
import hashlib, subprocess, sys
if len(sys.argv)!=2: raise SystemExit('usage: patch_v108_r57_ehci_tt_child_hid_probe.py <kernel/main.nx>')
p=Path(sys.argv[1]); here=Path(__file__).parent
base=here/'patch_v108_r56_ehci_second_hub_census_sealed.py'
subprocess.run([sys.executable,str(base),str(p)],check=True,stdout=subprocess.DEVNULL)
s=p.read_text()
BASE='156c10d74ab7513c1eb72630cdcf425eeaa79d85d4fde463c5f0d9b695199654'
actual=hashlib.sha256(s.encode()).hexdigest()
if actual!=BASE: raise SystemExit('r57 exact r56 base mismatch '+actual)

def rep(old,new,label,count=1):
    global s
    n=s.count(old)
    if n!=count: raise SystemExit(f'r57 {label}: {n} expected {count}')
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
fn v157_ehci_tt_control(xhci_state:u64,addr:u64,setupv:u64,length:u64) -> u64 {
    if xhci_state==0 { return 2; }
    let ord=volatile_read64(xhci_state+3800); let dma=volatile_read64(xhci_state+4040); let port=volatile_read64(xhci_state+3928); let speed=volatile_read64(xhci_state+4024); let mps=volatile_read64(xhci_state+3936);
    if ord!=2 || dma==0 || port==0 || port>15 || speed>1 || mps==0 || mps>64 { return 2; }
    let ebdf=v108_pci_nth_ehci_v121(1); if ebdf==0 { return 2; }
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
    let info1=1208008704+(mps*65536)+(speed*4096)+addr; let info2=1073807360+(port*8388608);
    unsafe { volatile_write32(qh+0,qlo+2); volatile_write32(qh+4,info1); volatile_write32(qh+8,info2); volatile_write32(qh+12,0); volatile_write32(qh+16,qslo); volatile_write32(qh+20,1); volatile_write32(qh+24,0); volatile_write32(op+8,0); volatile_write32(op+24,qlo); volatile_write32(op+4,63); }
    if ac64!=0 { unsafe { volatile_write32(op+16,upper); } }
    var cmd=volatile_read32(op); cmd=clear_flag(cmd,16); cmd=clear_flag(cmd,64); cmd=set_flag(cmd,1); cmd=set_flag(cmd,32); unsafe { volatile_write32(op,cmd); }
    var arm:u64=0; while (volatile_read32(op+4)/32768)%2==0 && arm<4000000 { cpu_pause(); arm=arm+1; }
    if arm>=4000000 { cmd=volatile_read32(op); cmd=clear_flag(cmd,32); unsafe { volatile_write32(op,cmd); } return 4; }
    var spins:u64=0; while (volatile_read32(qt+8)/128)%2!=0 && spins<16000000 { cpu_pause(); spins=spins+1; }
    cmd=volatile_read32(op); cmd=clear_flag(cmd,32); unsafe { volatile_write32(op,cmd); }
    var stop:u64=0; while (volatile_read32(op+4)/32768)%2!=0 && stop<4000000 { cpu_pause(); stop=stop+1; }
    let stok=volatile_read32(qt+8); let qstok=volatile_read32(qs+8); let serr=(stok/64)%2; let qerr=(qstok/64)%2;
    if serr!=0 || qerr!=0 || ((stok/4)%16)!=0 || ((qstok/4)%16)!=0 { return 6; }
    if spins>=16000000 || (stok/128)%2!=0 { return 5; }
    if length!=0 { let dtok=volatile_read32(qd+8); if (dtok/64)%2!=0 || ((dtok/4)%16)!=0 || (dtok/128)%2!=0 || ((dtok/65536)%32768)!=0 { return 6; } }
    return 1;
}
fn v157_ehci_child_hid_probe(xhci_state:u64) -> u64 {
    if xhci_state==0 { return 0; }
    if volatile_read64(xhci_state+3920)!=1 || volatile_read64(xhci_state+3928)!=2 || volatile_read64(xhci_state+3944)==0 { return volatile_read64(xhci_state+3920); }
    let dma=volatile_read64(xhci_state+4040); let port=volatile_read64(xhci_state+3968); let speed=volatile_read64(xhci_state+3976);
    if dma==0 || port==0 || port>15 || speed>1 { unsafe { volatile_write64(xhci_state+3920,10); } return 10; }
    unsafe { volatile_write64(xhci_state+3920,9); volatile_write64(xhci_state+3928,port); volatile_write64(xhci_state+3936,8); volatile_write64(xhci_state+3944,0); volatile_write64(xhci_state+3952,0); volatile_write64(xhci_state+3960,0); volatile_write64(xhci_state+3968,0); volatile_write64(xhci_state+3976,0); volatile_write64(xhci_state+3984,0); volatile_write64(xhci_state+3992,0); volatile_write64(xhci_state+4000,0); volatile_write64(xhci_state+4008,0); volatile_write64(xhci_state+4016,0); volatile_write64(xhci_state+4024,speed); volatile_write64(xhci_state+4032,0); }
    let reset_req=262947+(port*4294967296); var rc=v155_ehci_control(xhci_state,1,reset_req,0); if rc!=1 { unsafe { volatile_write64(xhci_state+3920,11); volatile_write64(xhci_state+4000,rc); } return 11; }
    pit_wait(119320); let status_req=1125899906842787+(port*4294967296); var ready:u64=0; var tries:u64=0;
    while tries<20 && ready==0 { rc=v155_ehci_control(xhci_state,1,status_req,4); if rc!=1 { unsafe { volatile_write64(xhci_state+3920,12); volatile_write64(xhci_state+4000,rc); } return 12; } let st=volatile_read8(dma+576)+(volatile_read8(dma+577)*256); unsafe { volatile_write64(xhci_state+4032,st); } if st%2!=0 && (st/2)%2!=0 && (st/16)%2==0 { ready=1; } else { pit_wait(23864); } tries=tries+1; }
    if ready==0 { unsafe { volatile_write64(xhci_state+3920,13); } return 13; }
    rc=v157_ehci_tt_control(xhci_state,0,2251799830464128,8); if rc!=1 { unsafe { volatile_write64(xhci_state+3920,14); volatile_write64(xhci_state+4000,rc); } return 14; }
    let data=dma+576; let dlen=volatile_read8(data); let dtype=volatile_read8(data+1); let mps=volatile_read8(data+7);
    if dlen<8 || dtype!=1 || (mps!=8 && mps!=16 && mps!=32 && mps!=64) { unsafe { volatile_write64(xhci_state+3920,15); } return 15; }
    unsafe { volatile_write64(xhci_state+3936,mps); }
    rc=v157_ehci_tt_control(xhci_state,0,132352,0); if rc!=1 { unsafe { volatile_write64(xhci_state+3920,16); volatile_write64(xhci_state+4000,rc); } return 16; }
    pit_wait(23864);
    rc=v157_ehci_tt_control(xhci_state,2,5066549597570688,18); if rc!=1 { unsafe { volatile_write64(xhci_state+3920,17); volatile_write64(xhci_state+4000,rc); } return 17; }
    let fdlen=volatile_read8(data); let fdtype=volatile_read8(data+1); let vid=volatile_read8(data+8)+(volatile_read8(data+9)*256); let pid=volatile_read8(data+10)+(volatile_read8(data+11)*256);
    if fdlen<18 || fdtype!=1 { unsafe { volatile_write64(xhci_state+3920,18); } return 18; }
    unsafe { volatile_write64(xhci_state+3944,vid); volatile_write64(xhci_state+3952,pid); }
    rc=v157_ehci_tt_control(xhci_state,2,2533274823952000,9); if rc!=1 { unsafe { volatile_write64(xhci_state+3920,19); volatile_write64(xhci_state+4000,rc); } return 19; }
    let clen=volatile_read8(data); let ctype=volatile_read8(data+1); let total=volatile_read8(data+2)+(volatile_read8(data+3)*256); let cfg=volatile_read8(data+5);
    if clen<9 || ctype!=2 || total<9 || total>256 || cfg==0 { unsafe { volatile_write64(xhci_state+3920,20); } return 20; }
    unsafe { volatile_write64(xhci_state+4008,cfg); volatile_write64(xhci_state+4016,total); }
    let full_setup=usb_setup_length_v113(usb_setup_value_v113(128,6,512,0),total); rc=v157_ehci_tt_control(xhci_state,2,full_setup,total); if rc!=1 { unsafe { volatile_write64(xhci_state+3920,21); volatile_write64(xhci_state+4000,rc); } return 21; }
    var off:u64=0; var active:u64=0; var iface:u64=0; var proto:u64=0; var ep:u64=0; var epm:u64=0; var interval:u64=0;
    while off+2<=total {
        let dl=volatile_read8(data+off); let dt=volatile_read8(data+off+1); if dl<2 || off+dl>total { off=total; } else {
            if dt==4 && dl>=9 { let ic=volatile_read8(data+off+5); let sub=volatile_read8(data+off+6); let pr=volatile_read8(data+off+7); active=0; if ic==3 && sub==1 && (pr==1 || pr==2) { active=1; iface=volatile_read8(data+off+2); proto=pr; } }
            if dt==5 && dl>=7 && active!=0 && ep==0 { let ea=volatile_read8(data+off+2); let attr=volatile_read8(data+off+3); if ea>=128 && attr%4==3 { ep=ea; epm=volatile_read8(data+off+4)+(volatile_read8(data+off+5)*256); interval=volatile_read8(data+off+6); } }
            off=off+dl;
        }
    }
    unsafe { volatile_write64(xhci_state+3960,proto); volatile_write64(xhci_state+3968,ep); volatile_write64(xhci_state+3976,epm); volatile_write64(xhci_state+3984,interval); volatile_write64(xhci_state+3992,iface); }
    if proto==0 || ep==0 || epm==0 { unsafe { volatile_write64(xhci_state+3920,22); } return 22; }
    unsafe { volatile_write64(xhci_state+3920,1); } return 1;
}
'''
pos=s.index('fn xhci_configure_boot_hid')
s=s[:pos]+insert+s[pos:]
rep('v155_ehci_intel_hub_discovery(xhci,phys_state); v156_ehci_second_hub_census(xhci);','v155_ehci_intel_hub_discovery(xhci,phys_state); v156_ehci_second_hub_census(xhci); if volatile_read64(xhci+3920)==1 && volatile_read64(xhci+3928)==2 { v157_ehci_child_hid_probe(xhci); }','r57 child probe call')
fnrep('v140_text_wifi_v140',label_fn('v140_text_wifi_v140','R57 S P M V D R E'))
oldrow='    v140_text_wifi_v140(surface,px+10,py+748,white); if xhci!=0 { v108_draw_small_u64(surface,((px+112)*65536)+(py+748),volatile_read64(xhci+3920),green); v108_draw_small_u64(surface,((px+150)*65536)+(py+748),volatile_read64(xhci+3928),amber); v108_draw_small_u64(surface,((px+188)*65536)+(py+748),volatile_read64(xhci+3936),white); v108_draw_small_u64(surface,((px+226)*65536)+(py+748),volatile_read64(xhci+3944),green); v108_draw_small_u64(surface,((px+264)*65536)+(py+748),volatile_read64(xhci+3960),amber); v108_draw_small_u64(surface,((px+306)*65536)+(py+748),volatile_read64(xhci+3968),white); v108_draw_small_u64(surface,((px+350)*65536)+(py+748),volatile_read64(xhci+3976),white); }'
newrow='    v140_text_wifi_v140(surface,px+10,py+748,white); if xhci!=0 { v108_draw_small_u64(surface,((px+112)*65536)+(py+748),volatile_read64(xhci+3920),green); v108_draw_small_u64(surface,((px+150)*65536)+(py+748),volatile_read64(xhci+3928),amber); v108_draw_small_u64(surface,((px+188)*65536)+(py+748),volatile_read64(xhci+3936),white); v108_draw_small_u64(surface,((px+226)*65536)+(py+748),volatile_read64(xhci+3944),green); v108_draw_small_u64(surface,((px+264)*65536)+(py+748),volatile_read64(xhci+3952),amber); v108_draw_small_u64(surface,((px+306)*65536)+(py+748),volatile_read64(xhci+3960),white); v108_draw_small_u64(surface,((px+350)*65536)+(py+748),volatile_read64(xhci+3968),white); }'
rep(oldrow,newrow,'r57 display row')
if s.count('{')!=s.count('}'): raise SystemExit('r57 brace mismatch')
for q in ['fn v157_ehci_tt_control','1208008704+(mps*65536)+(speed*4096)+addr','1073807360+(port*8388608)','262947+(port*4294967296)','v157_ehci_tt_control(xhci_state,0,2251799830464128,8)','v157_ehci_tt_control(xhci_state,0,132352,0)','usb_setup_value_v113(128,6,512,0)','ic==3 && sub==1 && (pr==1 || pr==2)']:
    if q not in s: raise SystemExit('r57 model missing '+q)
out=hashlib.sha256(s.encode()).hexdigest()
EXPECTED='bb436345a163096d52a04605c7bfb09cf756f90c06be6830b9ed130bb52e2c36'
if out!=EXPECTED: raise SystemExit('r57 output sha mismatch '+out)
p.write_text(s)
print(out)
