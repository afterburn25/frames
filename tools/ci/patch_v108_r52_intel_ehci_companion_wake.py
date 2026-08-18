#!/usr/bin/env python3
from pathlib import Path
import hashlib, subprocess, sys
if len(sys.argv)!=2: raise SystemExit('usage: patch_v108_r52_intel_ehci_companion_wake.py <kernel/main.nx>')
p=Path(sys.argv[1]); here=Path(__file__).parent
base=here/'patch_v108_r51_intel_ehci_route_probe.py'
subprocess.run([sys.executable,str(base),str(p)],check=True,stdout=subprocess.DEVNULL)
s=p.read_text()
BASE='25f02ab7852059b40c9387f0a139b8407a0e99dbc25038a917594a5f9526975a'
actual=hashlib.sha256(s.encode()).hexdigest()
if actual!=BASE: raise SystemExit('r52 exact r51 base mismatch '+actual)

def rep(old,new,label,count=1):
    global s
    n=s.count(old)
    if n!=count: raise SystemExit(f'r52 {label} count {n}, expected {count}')
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

# r51 physical proof established that the exact Intel XUSB2PR port-2 bit can be
# moved from xHCI to the EHCI fabric, but neither companion exposed CCS while
# both EHCI controllers remained in the intentionally halted post-takeover
# state. r52 therefore wakes only the two existing EHCI companions enough to
# prove controller run state, CONFIGFLAG and PORTSC visibility. EHCI schedules,
# interrupts, port reset/enumeration and transfer submission remain disabled.
wake=r'''fn v152_intel_ehci_companion_wake_probe(xhci_state:u64) -> u64 {
    if xhci_state==0 { return 0; }
    let prior=volatile_read64(xhci_state+3696); if prior!=0 { return prior; }
    unsafe { volatile_write64(xhci_state+3696,2); volatile_write64(xhci_state+3704,0); volatile_write64(xhci_state+3712,0); volatile_write64(xhci_state+3720,0); volatile_write64(xhci_state+3728,0); volatile_write64(xhci_state+3736,0); volatile_write64(xhci_state+3744,0); volatile_write64(xhci_state+3752,0); volatile_write64(xhci_state+3760,0); }
    let bdf=volatile_read64(xhci_state+1280); if bdf==0 { return 2; }
    let bus=bdf/65536; let dev=(bdf/256)%256; let fun=bdf%256; let id=pci_cfg_read32(bus,dev,fun,0); let vendor=id%65536; let device=(id/65536)%65536;
    let vid=volatile_read64(xhci_state+272); let pid=volatile_read64(xhci_state+280); let sw_port=volatile_read64(xhci_state+112); let speed=volatile_read64(xhci_state+184); let ep=volatile_read64(xhci_state+3640);
    if vendor!=32902 || device!=35889 || vid!=9354 || pid!=4267 || sw_port!=2 || speed!=1 || ep!=130 { return 2; }
    let mask=power2_u64(sw_port-1); if mask==0 { return 2; }
    let u2m=pci_cfg_read32(bus,dev,fun,212); let before=pci_cfg_read32(bus,dev,fun,208); let before_bit=(before/mask)%2;
    unsafe { volatile_write64(xhci_state+3752,before_bit); }
    if u2m==0 || u2m==4294967295 || (u2m/mask)%2==0 || before_bit==0 { unsafe { volatile_write64(xhci_state+3696,3); } return 3; }
    pci_cfg_write32(bdf,208,before-mask); let after=pci_cfg_read32(bus,dev,fun,208); let after_bit=(after/mask)%2; unsafe { volatile_write64(xhci_state+3760,after_bit); }
    if after_bit!=0 { unsafe { volatile_write64(xhci_state+3696,3); } return 3; }
    pit_wait(119320);
    var ord:u64=0; var running:u64=0; var flagged:u64=0;
    while ord<2 {
        let ebdf=v108_pci_nth_ehci_v121(ord); if ebdf!=0 {
            let base=pci_bar_base(ebdf,0); if base!=0 {
                let caplen=volatile_read8(base); if caplen>=16 && caplen<=128 {
                    let hcs=volatile_read32(base+4); let ports=hcs%16; let op=base+caplen;
                    if ports!=0 && ports<=15 {
                        unsafe { volatile_write32(op+8,0); }
                        var cmd=volatile_read32(op); cmd=clear_flag(cmd,16); cmd=clear_flag(cmd,32); cmd=clear_flag(cmd,64); unsafe { volatile_write32(op,cmd); volatile_write32(op+64,1); }
                        if (hcs/16)%2!=0 { var pp:u64=0; while pp<ports { let ps=volatile_read32(op+68+(pp*4)); if (ps/4096)%2==0 { unsafe { volatile_write32(op+68+(pp*4),set_flag(ps,4096)); } } pp=pp+1; } }
                        cmd=volatile_read32(op); cmd=clear_flag(cmd,16); cmd=clear_flag(cmd,32); cmd=clear_flag(cmd,64); cmd=set_flag(cmd,1); unsafe { volatile_write32(op,cmd); }
                        var spins:u64=0; while (volatile_read32(op+4)/4096)%2!=0 && spins<4000000 { cpu_pause(); spins=spins+1; }
                        if (volatile_read32(op+4)/4096)%2==0 { running=running+1; }
                        if volatile_read32(op+64)%2!=0 { flagged=flagged+1; }
                    }
                }
            }
        }
        ord=ord+1;
    }
    pit_wait(1193200);
    ord=0; var found_ord:u64=0; var found_port:u64=0; var found_ps:u64=0;
    while ord<2 && found_ord==0 {
        let ebdf=v108_pci_nth_ehci_v121(ord); if ebdf!=0 { let base=pci_bar_base(ebdf,0); if base!=0 { let caplen=volatile_read8(base); if caplen>=16 && caplen<=128 { let ports=volatile_read32(base+4)%16; let op=base+caplen; var p:u64=1; while p<=ports && p<=15 && found_ord==0 { let ps=volatile_read32(op+68+((p-1)*4)); if ps%2!=0 { found_ord=ord+1; found_port=p; found_ps=ps; } p=p+1; } } } }
        ord=ord+1;
    }
    var ccs:u64=0; if found_ps%2!=0 { ccs=1; }
    unsafe { volatile_write64(xhci_state+3704,found_ord); volatile_write64(xhci_state+3712,found_port); volatile_write64(xhci_state+3720,ccs); volatile_write64(xhci_state+3728,running); volatile_write64(xhci_state+3736,flagged); volatile_write64(xhci_state+3744,found_ps); }
    if found_ord!=0 && ccs==1 && running!=0 { unsafe { volatile_write64(xhci_state+3696,1); } return 1; }
    if running!=0 { unsafe { volatile_write64(xhci_state+3696,4); } return 4; }
    unsafe { volatile_write64(xhci_state+3696,5); } return 5;
}'''
fnrep('v151_intel_ehci_route_probe',wake)
rep('v151_intel_ehci_route_probe(xhci);','v152_intel_ehci_companion_wake_probe(xhci);','wake call')
rep('if xhci!=0 && volatile_read64(xhci+808)!=0 && volatile_read64(xhci+3696)!=1 { xhci_hid_poll_continuous(xhci,input_state); }','if xhci!=0 && volatile_read64(xhci+808)!=0 && volatile_read64(xhci+3696)!=1 && volatile_read64(xhci+3696)!=4 && volatile_read64(xhci+3696)!=5 { xhci_hid_poll_continuous(xhci,input_state); }','post-reroute xHCI poll guard')
rep('if xhci!=0 { if volatile_read64(xhci+3696)!=1 { v136_hid_interrupt_recovery_tick(xhci); } v144_hid_forensic_snapshot(xhci); }','if xhci!=0 { if volatile_read64(xhci+3696)!=1 && volatile_read64(xhci+3696)!=4 && volatile_read64(xhci+3696)!=5 { v136_hid_interrupt_recovery_tick(xhci); } v144_hid_forensic_snapshot(xhci); }','post-reroute xHCI recovery guard')
fnrep('v140_text_wifi_v140',label_fn('v140_text_wifi_v140','R52 W E P C R F V'))
oldrow=r'''    v140_text_wifi_v140(surface,px+10,py+748,white); if xhci!=0 { v108_draw_small_u64(surface,((px+112)*65536)+(py+748),volatile_read64(xhci+3696),green); v108_draw_small_u64(surface,((px+150)*65536)+(py+748),volatile_read64(xhci+3704),white); v108_draw_small_u64(surface,((px+188)*65536)+(py+748),volatile_read64(xhci+3712),white); v108_draw_small_u64(surface,((px+226)*65536)+(py+748),volatile_read64(xhci+3720),amber); v108_draw_small_u64(surface,((px+264)*65536)+(py+748),volatile_read64(xhci+3728),amber); v108_draw_small_u64(surface,((px+306)*65536)+(py+748),volatile_read64(xhci+3736),green); v108_draw_small_u64(surface,((px+350)*65536)+(py+748),volatile_read64(xhci+3744),white); }'''
newrow=r'''    v140_text_wifi_v140(surface,px+10,py+748,white); if xhci!=0 { v108_draw_small_u64(surface,((px+112)*65536)+(py+748),volatile_read64(xhci+3696),green); v108_draw_small_u64(surface,((px+150)*65536)+(py+748),volatile_read64(xhci+3704),amber); v108_draw_small_u64(surface,((px+188)*65536)+(py+748),volatile_read64(xhci+3712),white); v108_draw_small_u64(surface,((px+226)*65536)+(py+748),volatile_read64(xhci+3720),green); v108_draw_small_u64(surface,((px+264)*65536)+(py+748),volatile_read64(xhci+3728),green); v108_draw_small_u64(surface,((px+306)*65536)+(py+748),volatile_read64(xhci+3736),green); v108_draw_small_u64(surface,((px+350)*65536)+(py+748),volatile_read64(xhci+3744),white); }'''
rep(oldrow,newrow,'r52 companion wake row')

buttons=fn_text('ps2_elan4_buttons_v111')
if 'if typ==1 || typ==2 {' not in buttons or 'return ps2_elan4_motion_v112(input_state,a,b);' not in s: raise SystemExit('r52 regressed physically accepted touchpad contract')
r52fn=fn_text('v152_intel_ehci_companion_wake_probe')
for q in (
    'vendor!=32902 || device!=35889 || vid!=9354 || pid!=4267 || sw_port!=2 || speed!=1 || ep!=130',
    'pci_cfg_write32(bdf,208,before-mask)',
    'volatile_write32(op+8,0)',
    'cmd=clear_flag(cmd,16); cmd=clear_flag(cmd,32); cmd=clear_flag(cmd,64)',
    'volatile_write32(op+64,1)',
    'set_flag(ps,4096)',
    'cmd=set_flag(cmd,1)',
    'volatile_read32(op+4)/4096',
    'v108_pci_nth_ehci_v121(ord)',
    'volatile_write64(xhci_state+3752,before_bit)',
    'volatile_write64(xhci_state+3760,after_bit)',
):
    if q not in r52fn: raise SystemExit('r52 guarded EHCI wake proof missing '+q)
if r52fn.count('pci_cfg_write32(bdf,208,before-mask)')!=1: raise SystemExit('r52 USB2 route mutation is not single-bit bounded')
for forbidden in ('periodiclistbase','asynclistaddr','qtd','qh_link','ehci_submit','ehci_transfer'):
    if forbidden in r52fn.lower(): raise SystemExit('r52 unexpectedly contains EHCI transfer/schedule logic '+forbidden)
for q in ('volatile_read64(xhci+3696)!=4','volatile_read64(xhci+3696)!=5'):
    if q not in s: raise SystemExit('r52 stale xHCI suppression missing '+q)
if s.count('{')!=s.count('}'): raise SystemExit('r52 brace mismatch')
out=hashlib.sha256(s.encode()).hexdigest()
EXPECTED='7f854b564c7ddee71382ebe616ec1dd70dad3ce679684b1babd1550ac40ffcf3'
if out!=EXPECTED: raise SystemExit('r52 output sha mismatch '+out)
p.write_text(s)
print(out)
