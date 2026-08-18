#!/usr/bin/env python3
from pathlib import Path
import hashlib, subprocess, sys
if len(sys.argv)!=2: raise SystemExit('usage: patch_v108_r51_intel_ehci_route_probe.py <kernel/main.nx>')
p=Path(sys.argv[1]); here=Path(__file__).parent
base=here/'patch_v108_r50_device_endpoint_status_proof.py'
subprocess.run([sys.executable,str(base),str(p)],check=True,stdout=subprocess.DEVNULL)
s=p.read_text()
BASE='30d8239eb1c91a5b70246744d856e1a7aae77360baeaa024033fb135070fd6f1'
if hashlib.sha256(s.encode()).hexdigest()!=BASE: raise SystemExit('r51 exact r50 base mismatch '+hashlib.sha256(s.encode()).hexdigest())

def rep(old,new,label,count=1):
    global s
    n=s.count(old)
    if n!=count: raise SystemExit(f'r51 {label} count {n}, expected {count}')
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

# r50 physical evidence proves the 248a:10ab receiver is configured, on alt 0,
# endpoint 0x82 is not halted, and both Frames and PORTSC identify full speed,
# yet the xHCI interrupt-IN path still produces no report.  The inherited r33
# evidence also proves two EHCI companions exist and were deliberately halted
# after all USB2 routing bits were moved to xHCI.  Stop tuning xHCI timing and
# perform one tightly-guarded alternate-path experiment: move ONLY the known
# receiver's USB2 port-2 route bit from Intel 8086:8c31 xHCI back to its EHCI
# companion fabric, then passively identify which EHCI root port reports CCS.
# No storage/media write path is touched and no unrelated USB2 route bit moves.
probe=r'''fn v151_intel_ehci_route_probe(xhci_state:u64) -> u64 {
    if xhci_state==0 { return 0; }
    let prior=volatile_read64(xhci_state+3696); if prior!=0 { return prior; }
    unsafe { volatile_write64(xhci_state+3696,2); volatile_write64(xhci_state+3704,0); volatile_write64(xhci_state+3712,0); volatile_write64(xhci_state+3720,0); volatile_write64(xhci_state+3728,0); volatile_write64(xhci_state+3736,0); volatile_write64(xhci_state+3744,0); }
    let bdf=volatile_read64(xhci_state+1280); if bdf==0 { return 2; }
    let bus=bdf/65536; let dev=(bdf/256)%256; let fun=bdf%256; let id=pci_cfg_read32(bus,dev,fun,0); let vendor=id%65536; let device=(id/65536)%65536;
    let vid=volatile_read64(xhci_state+272); let pid=volatile_read64(xhci_state+280); let sw_port=volatile_read64(xhci_state+112); let speed=volatile_read64(xhci_state+184); let ep=volatile_read64(xhci_state+3640);
    if vendor!=32902 || device!=35889 || vid!=9354 || pid!=4267 || sw_port!=2 || speed!=1 || ep!=130 { return 2; }
    let mask=power2_u64(sw_port-1); if mask==0 { return 2; }
    let u2m=pci_cfg_read32(bus,dev,fun,212); let before=pci_cfg_read32(bus,dev,fun,208); let before_bit=(before/mask)%2;
    unsafe { volatile_write64(xhci_state+3704,before_bit); }
    if u2m==0 || u2m==4294967295 || (u2m/mask)%2==0 || before_bit==0 { unsafe { volatile_write64(xhci_state+3696,3); } return 3; }
    pci_cfg_write32(bdf,208,before-mask); let after=pci_cfg_read32(bus,dev,fun,208); let after_bit=(after/mask)%2; unsafe { volatile_write64(xhci_state+3712,after_bit); }
    if after_bit!=0 { unsafe { volatile_write64(xhci_state+3696,3); } return 3; }
    pit_wait(1193200);
    var ord:u64=0; var found_ord:u64=0; var found_port:u64=0; var found_ps:u64=0;
    while ord<2 && found_ord==0 {
        let ebdf=v108_pci_nth_ehci_v121(ord); if ebdf!=0 { let base=pci_bar_base(ebdf,0); if base!=0 { let caplen=volatile_read8(base); if caplen>=16 && caplen<=128 { let ports=volatile_read32(base+4)%16; let op=base+caplen; var p:u64=1; while p<=ports && p<=15 && found_ord==0 { let ps=volatile_read32(op+68+((p-1)*4)); if ps%2!=0 { found_ord=ord+1; found_port=p; found_ps=ps; } p=p+1; } } } }
        ord=ord+1;
    }
    var ccs:u64=0; if found_ps%2!=0 { ccs=1; }
    unsafe { volatile_write64(xhci_state+3720,found_ord); volatile_write64(xhci_state+3728,found_port); volatile_write64(xhci_state+3736,ccs); volatile_write64(xhci_state+3744,found_ps); }
    if found_ord!=0 && ccs==1 { unsafe { volatile_write64(xhci_state+3696,1); } return 1; }
    unsafe { volatile_write64(xhci_state+3696,4); } return 4;
}
'''
rep('fn xhci_configure_boot_hid(xhci_state:u64, phys_state:u64) -> u64 {',probe+'fn xhci_configure_boot_hid(xhci_state:u64, phys_state:u64) -> u64 {','insert EHCI route probe')

old='''    if xhci!=0 && volatile_read64(xhci+416)==1 { if xhci_hid_arm_continuous(xhci,phys_state)==0 { unsafe { volatile_write64(xhci+2800,volatile_read64(xhci+2800)+1); } } }\n    unsafe { volatile_write64(process+640,0); } let clean_frame=appearance_render(process);'''
new='''    if xhci!=0 && volatile_read64(xhci+416)==1 { if xhci_hid_arm_continuous(xhci,phys_state)==0 { unsafe { volatile_write64(xhci+2800,volatile_read64(xhci+2800)+1); } } }\n    if xhci!=0 { v151_intel_ehci_route_probe(xhci); }\n    unsafe { volatile_write64(process+640,0); } let clean_frame=appearance_render(process);'''
rep(old,new,'desktop alternate-path probe call')
rep('if xhci!=0 && volatile_read64(xhci+808)!=0 { xhci_hid_poll_continuous(xhci,input_state); }','if xhci!=0 && volatile_read64(xhci+808)!=0 && volatile_read64(xhci+3696)!=1 { xhci_hid_poll_continuous(xhci,input_state); }','post-route xHCI poll guard')
rep('if xhci!=0 { v136_hid_interrupt_recovery_tick(xhci); v144_hid_forensic_snapshot(xhci); }','if xhci!=0 { if volatile_read64(xhci+3696)!=1 { v136_hid_interrupt_recovery_tick(xhci); } v144_hid_forensic_snapshot(xhci); }','post-route xHCI recovery guard')

# R51 S B A E P C V:
# S=probe state (1 route moved and EHCI CCS found; 2 guard mismatch;
#   3 route write failed; 4 route moved but no EHCI CCS found),
# B=selected XUSB2PR bit before, A=that bit after,
# E=EHCI companion ordinal (1/2), P=EHCI port number,
# C=EHCI Current Connect Status, V=raw EHCI PORTSC.
fnrep('v140_text_wifi_v140',label_fn('v140_text_wifi_v140','R51 S B A E P C V'))
oldrow=r'''    v140_text_wifi_v140(surface,px+10,py+748,white); if xhci!=0 { v108_draw_small_u64(surface,((px+112)*65536)+(py+748),volatile_read64(xhci+3624),green); v108_draw_small_u64(surface,((px+150)*65536)+(py+748),volatile_read64(xhci+3632),white); v108_draw_small_u64(surface,((px+188)*65536)+(py+748),volatile_read64(xhci+3640),white); v108_draw_small_u64(surface,((px+226)*65536)+(py+748),volatile_read64(xhci+3648),amber); v108_draw_small_u64(surface,((px+264)*65536)+(py+748),volatile_read64(xhci+3656),amber); v108_draw_small_u64(surface,((px+306)*65536)+(py+748),volatile_read64(xhci+3672),white); v108_draw_small_u64(surface,((px+350)*65536)+(py+748),volatile_read64(xhci+3680),white); }'''
newrow=r'''    v140_text_wifi_v140(surface,px+10,py+748,white); if xhci!=0 { v108_draw_small_u64(surface,((px+112)*65536)+(py+748),volatile_read64(xhci+3696),green); v108_draw_small_u64(surface,((px+150)*65536)+(py+748),volatile_read64(xhci+3704),white); v108_draw_small_u64(surface,((px+188)*65536)+(py+748),volatile_read64(xhci+3712),white); v108_draw_small_u64(surface,((px+226)*65536)+(py+748),volatile_read64(xhci+3720),amber); v108_draw_small_u64(surface,((px+264)*65536)+(py+748),volatile_read64(xhci+3728),amber); v108_draw_small_u64(surface,((px+306)*65536)+(py+748),volatile_read64(xhci+3736),green); v108_draw_small_u64(surface,((px+350)*65536)+(py+748),volatile_read64(xhci+3744),white); }'''
rep(oldrow,newrow,'r51 alternate-path row')

buttons=fn_text('ps2_elan4_buttons_v111')
if 'if typ==1 || typ==2 {' not in buttons or 'return ps2_elan4_motion_v112(input_state,a,b);' not in s: raise SystemExit('r51 regressed physically accepted touchpad contract')
for q in ('vendor!=32902 || device!=35889','vid!=9354 || pid!=4267','sw_port!=2 || speed!=1 || ep!=130','pci_cfg_write32(bdf,208,before-mask)','v108_pci_nth_ehci_v121(ord)','volatile_read64(xhci+3696)!=1'):
    if q not in s: raise SystemExit('r51 guarded EHCI route proof missing '+q)
if s.count('{')!=s.count('}'): raise SystemExit('r51 brace mismatch')
out=hashlib.sha256(s.encode()).hexdigest()
EXPECTED='25f02ab7852059b40c9387f0a139b8407a0e99dbc25038a917594a5f9526975a'
if out!=EXPECTED: raise SystemExit('r51 output sha mismatch '+out)
p.write_text(s)
print(out)
