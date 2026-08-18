#!/usr/bin/env python3
from pathlib import Path
import hashlib, subprocess, sys
if len(sys.argv)!=2: raise SystemExit('usage: patch_v108_r53_ehci_port_reset_companion_classifier.py <kernel/main.nx>')
p=Path(sys.argv[1]); here=Path(__file__).parent
base=here/'patch_v108_r52_intel_ehci_companion_wake.py'
subprocess.run([sys.executable,str(base),str(p)],check=True,stdout=subprocess.DEVNULL)
s=p.read_text()
BASE='7f854b564c7ddee71382ebe616ec1dd70dad3ce679684b1babd1550ac40ffcf3'
actual=hashlib.sha256(s.encode()).hexdigest()
if actual!=BASE: raise SystemExit('r53 exact r52 base mismatch '+actual)

def rep(old,new,label,count=1):
    global s
    n=s.count(old)
    if n!=count: raise SystemExit(f'r53 {label} count {n}, expected {count}')
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

# r52 physical evidence: W1 E1 P1 C1 R2 F2 V6147.  The Intel route bit moved,
# both EHCI controllers reached running, both CONFIGFLAGs asserted, and EHCI #1
# port 1 observed the receiver.  But raw PORTSC 0x1803 is pre-reset state: CCS
# and power are present while PE is still clear.  Standard EHCI decides whether
# a root-port device is high-speed only during port reset; non-high-speed root
# devices are handed to a USB1 companion controller.  Do that bounded decision
# now, without programming any EHCI/UHCI/OHCI transfer schedule.
classifier=r'''fn v153_pci_count_usb_prog(prog:u64) -> u64 {
    var count:u64=0; var bus:u64=0;
    while bus<256 { var dev:u64=0; while dev<32 { var fun:u64=0; while fun<8 {
        let id=pci_cfg_read32(bus,dev,fun,0); if id%65536!=65535 { let cr=pci_cfg_read32(bus,dev,fun,8); if cr/16777216==12 && (cr/65536)%256==3 && (cr/256)%256==prog { count=count+1; } }
        fun=fun+1; } dev=dev+1; } bus=bus+1; }
    return count;
}
fn v153_intel_ehci_port_reset_companion_classifier(xhci_state:u64) -> u64 {
    if xhci_state==0 { return 0; }
    let prior=volatile_read64(xhci_state+3696); if prior!=0 { return prior; }
    unsafe { volatile_write64(xhci_state+3696,6); volatile_write64(xhci_state+3704,0); volatile_write64(xhci_state+3712,0); volatile_write64(xhci_state+3720,0); volatile_write64(xhci_state+3728,0); volatile_write64(xhci_state+3736,0); volatile_write64(xhci_state+3744,0); volatile_write64(xhci_state+3752,0); volatile_write64(xhci_state+3760,1); volatile_write64(xhci_state+3768,0); volatile_write64(xhci_state+3776,0); volatile_write64(xhci_state+3784,0); }
    let bdf=volatile_read64(xhci_state+1280); if bdf==0 { return 6; }
    let bus=bdf/65536; let dev=(bdf/256)%256; let fun=bdf%256; let id=pci_cfg_read32(bus,dev,fun,0); let vendor=id%65536; let device=(id/65536)%65536;
    let vid=volatile_read64(xhci_state+272); let pid=volatile_read64(xhci_state+280); let sw_port=volatile_read64(xhci_state+112); let speed=volatile_read64(xhci_state+184); let ep=volatile_read64(xhci_state+3640);
    if vendor!=32902 || device!=35889 || vid!=9354 || pid!=4267 || sw_port!=2 || speed!=1 || ep!=130 { return 6; }
    let mask=power2_u64(sw_port-1); if mask==0 { return 6; }
    let u2m=pci_cfg_read32(bus,dev,fun,212); let before=pci_cfg_read32(bus,dev,fun,208); let before_bit=(before/mask)%2; unsafe { volatile_write64(xhci_state+3752,before_bit); }
    if u2m==0 || u2m==4294967295 || (u2m/mask)%2==0 || before_bit==0 { unsafe { volatile_write64(xhci_state+3696,4); } return 4; }
    pci_cfg_write32(bdf,208,before-mask); let after=pci_cfg_read32(bus,dev,fun,208); let after_bit=(after/mask)%2; unsafe { volatile_write64(xhci_state+3760,after_bit); }
    if after_bit!=0 { unsafe { volatile_write64(xhci_state+3696,4); } return 4; }
    pit_wait(119320);
    var ord:u64=0; var running:u64=0;
    while ord<2 {
        let ebdf=v108_pci_nth_ehci_v121(ord); if ebdf!=0 { let base=pci_bar_base(ebdf,0); if base!=0 { let caplen=volatile_read8(base); if caplen>=16 && caplen<=128 { let hcs=volatile_read32(base+4); let ports=hcs%16; let op=base+caplen; if ports!=0 && ports<=15 {
            unsafe { volatile_write32(op+8,0); }
            var cmd=volatile_read32(op); cmd=clear_flag(cmd,16); cmd=clear_flag(cmd,32); cmd=clear_flag(cmd,64); unsafe { volatile_write32(op,cmd); volatile_write32(op+64,1); }
            if (hcs/16)%2!=0 { var pp:u64=0; while pp<ports { let ps=volatile_read32(op+68+(pp*4)); if (ps/4096)%2==0 { var pw=ps; pw=clear_flag(pw,2); pw=clear_flag(pw,8); pw=clear_flag(pw,32); pw=set_flag(pw,4096); unsafe { volatile_write32(op+68+(pp*4),pw); } } pp=pp+1; } }
            cmd=volatile_read32(op); cmd=clear_flag(cmd,16); cmd=clear_flag(cmd,32); cmd=clear_flag(cmd,64); cmd=set_flag(cmd,1); unsafe { volatile_write32(op,cmd); }
            var spins:u64=0; while (volatile_read32(op+4)/4096)%2!=0 && spins<4000000 { cpu_pause(); spins=spins+1; }
            if (volatile_read32(op+4)/4096)%2==0 { running=running+1; }
        } } } }
        ord=ord+1;
    }
    if running==0 { unsafe { volatile_write64(xhci_state+3696,5); } return 5; }
    pit_wait(1193200);
    ord=0; var found_ord:u64=0; var found_port:u64=0; var found_ps:u64=0;
    while ord<2 && found_ord==0 {
        let ebdf=v108_pci_nth_ehci_v121(ord); if ebdf!=0 { let base=pci_bar_base(ebdf,0); if base!=0 { let caplen=volatile_read8(base); if caplen>=16 && caplen<=128 { let ports=volatile_read32(base+4)%16; let op=base+caplen; var p:u64=1; while p<=ports && p<=15 && found_ord==0 { let ps=volatile_read32(op+68+((p-1)*4)); if ps%2!=0 { found_ord=ord+1; found_port=p; found_ps=ps; } p=p+1; } } } }
        ord=ord+1;
    }
    if found_ord==0 || found_port==0 || found_ps%2==0 { unsafe { volatile_write64(xhci_state+3696,5); } return 5; }
    let ebdf=v108_pci_nth_ehci_v121(found_ord-1); let ebase=pci_bar_base(ebdf,0); if ebase==0 { unsafe { volatile_write64(xhci_state+3696,5); } return 5; }
    let caplen=volatile_read8(ebase); let hcs=volatile_read32(ebase+4); let ncc=(hcs/4096)%16; let op=ebase+caplen; let preg=op+68+((found_port-1)*4);
    var pre=volatile_read32(preg); var wr=pre; wr=clear_flag(wr,2); wr=clear_flag(wr,8); wr=clear_flag(wr,32); wr=set_flag(wr,256); unsafe { volatile_write32(preg,wr); }
    pit_wait(59660);
    var mid=volatile_read32(preg); wr=mid; wr=clear_flag(wr,2); wr=clear_flag(wr,8); wr=clear_flag(wr,32); wr=clear_flag(wr,256); unsafe { volatile_write32(preg,wr); }
    var rs:u64=0; while (volatile_read32(preg)/256)%2!=0 && rs<4000000 { cpu_pause(); rs=rs+1; }
    if rs>=4000000 { unsafe { volatile_write64(xhci_state+3696,5); } return 5; }
    pit_wait(11932);
    var done=volatile_read32(preg); if done%2==0 { unsafe { volatile_write64(xhci_state+3696,5); } return 5; }
    var ped=(done/4)%2; var owner=(done/8192)%2;
    if ped==0 && owner==0 && ncc!=0 {
        var ow=done; ow=clear_flag(ow,2); ow=clear_flag(ow,8); ow=clear_flag(ow,32); ow=set_flag(ow,8192); unsafe { volatile_write32(preg,ow); }
        pit_wait(119320); done=volatile_read32(preg); owner=(done/8192)%2; ped=(done/4)%2;
    }
    let uhci=v153_pci_count_usb_prog(0); let ohci=v153_pci_count_usb_prog(16); let line=(done/1024)%4;
    var state:u64=4;
    if ped==1 && owner==0 { state=1; }
    else { if ped==0 && owner==1 { state=2; } else { if ped==0 && owner==0 && ncc==0 { state=3; } } }
    unsafe { volatile_write64(xhci_state+3704,found_ord); volatile_write64(xhci_state+3712,found_port); volatile_write64(xhci_state+3720,ped); volatile_write64(xhci_state+3728,owner); volatile_write64(xhci_state+3736,uhci); volatile_write64(xhci_state+3744,ohci); volatile_write64(xhci_state+3768,done); volatile_write64(xhci_state+3776,ncc); volatile_write64(xhci_state+3784,line); volatile_write64(xhci_state+3696,state); }
    return state;
}'''
fnrep('v152_intel_ehci_companion_wake_probe',classifier)
rep('v152_intel_ehci_companion_wake_probe(xhci);','v153_intel_ehci_port_reset_companion_classifier(xhci);','classifier call')
rep('if xhci!=0 && volatile_read64(xhci+808)!=0 && volatile_read64(xhci+3696)!=1 && volatile_read64(xhci+3696)!=4 && volatile_read64(xhci+3696)!=5 { xhci_hid_poll_continuous(xhci,input_state); }','if xhci!=0 && volatile_read64(xhci+808)!=0 && volatile_read64(xhci+3760)!=0 { xhci_hid_poll_continuous(xhci,input_state); }','post-route xHCI poll guard')
rep('if xhci!=0 { if volatile_read64(xhci+3696)!=1 && volatile_read64(xhci+3696)!=4 && volatile_read64(xhci+3696)!=5 { v136_hid_interrupt_recovery_tick(xhci); } v144_hid_forensic_snapshot(xhci); }','if xhci!=0 { if volatile_read64(xhci+3760)!=0 { v136_hid_interrupt_recovery_tick(xhci); } v144_hid_forensic_snapshot(xhci); }','post-route xHCI recovery guard')
fnrep('v140_text_wifi_v140',label_fn('v140_text_wifi_v140','R53 S E P D O U H'))
oldrow=r'''    v140_text_wifi_v140(surface,px+10,py+748,white); if xhci!=0 { v108_draw_small_u64(surface,((px+112)*65536)+(py+748),volatile_read64(xhci+3696),green); v108_draw_small_u64(surface,((px+150)*65536)+(py+748),volatile_read64(xhci+3704),amber); v108_draw_small_u64(surface,((px+188)*65536)+(py+748),volatile_read64(xhci+3712),white); v108_draw_small_u64(surface,((px+226)*65536)+(py+748),volatile_read64(xhci+3720),green); v108_draw_small_u64(surface,((px+264)*65536)+(py+748),volatile_read64(xhci+3728),green); v108_draw_small_u64(surface,((px+306)*65536)+(py+748),volatile_read64(xhci+3736),green); v108_draw_small_u64(surface,((px+350)*65536)+(py+748),volatile_read64(xhci+3744),white); }'''
newrow=r'''    v140_text_wifi_v140(surface,px+10,py+748,white); if xhci!=0 { v108_draw_small_u64(surface,((px+112)*65536)+(py+748),volatile_read64(xhci+3696),green); v108_draw_small_u64(surface,((px+150)*65536)+(py+748),volatile_read64(xhci+3704),amber); v108_draw_small_u64(surface,((px+188)*65536)+(py+748),volatile_read64(xhci+3712),white); v108_draw_small_u64(surface,((px+226)*65536)+(py+748),volatile_read64(xhci+3720),green); v108_draw_small_u64(surface,((px+264)*65536)+(py+748),volatile_read64(xhci+3728),amber); v108_draw_small_u64(surface,((px+306)*65536)+(py+748),volatile_read64(xhci+3736),white); v108_draw_small_u64(surface,((px+350)*65536)+(py+748),volatile_read64(xhci+3744),white); }'''
rep(oldrow,newrow,'r53 classifier row')

buttons=fn_text('ps2_elan4_buttons_v111')
if 'if typ==1 || typ==2 {' not in buttons or 'return ps2_elan4_motion_v112(input_state,a,b);' not in s: raise SystemExit('r53 regressed physically accepted touchpad contract')
r53fn=fn_text('v153_intel_ehci_port_reset_companion_classifier')
for q in (
    'vendor!=32902 || device!=35889 || vid!=9354 || pid!=4267 || sw_port!=2 || speed!=1 || ep!=130',
    'pci_cfg_write32(bdf,208,before-mask)',
    'volatile_write32(op+8,0)',
    'cmd=clear_flag(cmd,16); cmd=clear_flag(cmd,32); cmd=clear_flag(cmd,64)',
    'volatile_write32(op+64,1)',
    'wr=set_flag(wr,256)',
    'wr=clear_flag(wr,256)',
    'ow=set_flag(ow,8192)',
    'let ncc=(hcs/4096)%16',
    'v153_pci_count_usb_prog(0)',
    'v153_pci_count_usb_prog(16)',
    'volatile_write64(xhci_state+3760,after_bit)',
):
    if q not in s: raise SystemExit('r53 EHCI reset/companion classifier missing '+q)
for forbidden in ('periodiclistbase','asynclistaddr','qtd','qh_link','ehci_submit','ehci_transfer'):
    if forbidden in r53fn.lower(): raise SystemExit('r53 unexpectedly contains host transfer/schedule logic '+forbidden)
if 'volatile_read64(xhci+3760)!=0' not in s: raise SystemExit('r53 stale xHCI suppression not keyed to actual route ownership')
if s.count('{')!=s.count('}'): raise SystemExit('r53 brace mismatch')
out=hashlib.sha256(s.encode()).hexdigest()
EXPECTED='TBD_R53_SHA'
if out!=EXPECTED: raise SystemExit('r53 output sha mismatch '+out)
p.write_text(s)
print(out)
