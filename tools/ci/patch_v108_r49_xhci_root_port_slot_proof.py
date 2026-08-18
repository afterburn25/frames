#!/usr/bin/env python3
from pathlib import Path
import hashlib, subprocess, sys
if len(sys.argv)!=2: raise SystemExit('usage: patch_v108_r49_xhci_root_port_slot_proof.py <kernel/main.nx>')
p=Path(sys.argv[1]); here=Path(__file__).parent
base=here/'patch_v108_r48_xhci_scheduler_wake.py'
subprocess.run([sys.executable,str(base),str(p)],check=True,stdout=subprocess.DEVNULL)
s=p.read_text()
BASE='0e9a059bcec8ee0a1b7204b39585618418d51fce1ed4daccae67e2c2f877b984'
if hashlib.sha256(s.encode()).hexdigest()!=BASE: raise SystemExit('r49 exact r48 base mismatch '+hashlib.sha256(s.encode()).hexdigest())

def rep(old,new,label,count=1):
    global s
    n=s.count(old)
    if n!=count: raise SystemExit(f'r49 {label} count {n}, expected {count}')
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
    for i,ch in enumerate(text):
        out+=f' if gui_draw_char_scaled(surface,((x+{i*6})*65536)+y,({ord(ch)}*65536)+1,color)==0 {{ return 0; }}'
    return out+' return 1; }'

# r48 physical evidence on the ASUS/Intel 8086:8c31 host:
#   T=1 F=1 M=1 U=1 H=0 W=0 V=0.
# TRB ownership handoff, safe posted-write flush, the xHC Run state and MFINDEX
# scheduler movement are all physically proven, yet no HID Transfer Event is
# produced. Stop tuning endpoint context/cycle/doorbell timing. r49 moves to the
# physical transaction identity boundary and passively correlates the software
# selected root port with the hardware Slot Context plus the current PORTSC.
fnrep('v144_hid_forensic_snapshot',r'''fn v144_hid_forensic_snapshot(xhci_state:u64) -> u64 {
    if xhci_state==0 || volatile_read64(xhci_state+416)!=1 { return 0; }
    let buffer=volatile_read64(xhci_state+432); var packed:u64=0;
    if buffer!=0 { packed=volatile_read8(buffer)+(volatile_read8(buffer+1)*256)+(volatile_read8(buffer+2)*65536)+(volatile_read8(buffer+3)*16777216); }
    let sw_cycle=volatile_read64(xhci_state+800); let hw_dcs=volatile_read64(xhci_state+2832);
    var ep_state:u64=255; var ep_interval:u64=255; var ep_type:u64=255; var ep_burst:u64=255; var ep_mps:u64=0; var ep_avg:u64=0; var ep_esit:u64=0; var route:u64=1048575;
    var hw_root:u64=0; var dev_addr:u64=0; var slot_state:u64=0;
    let output=volatile_read64(xhci_state+160); let ctxsize=volatile_read64(xhci_state+176); let dci=volatile_read64(xhci_state+352);
    if output!=0 && ctxsize!=0 && dci>=2 && dci<=31 {
        let slot0=volatile_read32(output); let slot1=volatile_read32(output+4); let slot3=volatile_read32(output+12); route=slot0%1048576;
        hw_root=(slot1/65536)%256; dev_addr=slot3%256; slot_state=(slot3/134217728)%32;
        let ep=output+(dci*ctxsize); let dw0=volatile_read32(ep); let dw1=volatile_read32(ep+4); let dw4=volatile_read32(ep+16);
        ep_state=dw0%8; ep_interval=(dw0/65536)%256; ep_type=(dw1/8)%8; ep_burst=(dw1/256)%256; ep_mps=(dw1/65536)%65536; ep_avg=dw4%65536; ep_esit=((dw4/65536)%65536)+(((dw0/16777216)%256)*65536);
    }
    let runtime=volatile_read64(xhci_state+80); var mf_now:u64=0; var mf_moved:u64=0;
    if runtime!=0 { mf_now=volatile_read32(runtime)%16384; let mf_arm=volatile_read64(xhci_state+3432); if mf_now!=mf_arm { mf_moved=1; } }
    let sw_port=volatile_read64(xhci_state+112); let op=volatile_read64(xhci_state+8); var portsc:u64=0; var ccs:u64=0; var ped:u64=0; var pls:u64=15; var pspeed:u64=0; var pp:u64=0;
    if op!=0 && sw_port>=1 && sw_port<=32 {
        let port=op+1024+((sw_port-1)*16); portsc=volatile_read32(port); ccs=portsc%2; ped=(portsc/2)%2; pls=(portsc/32)%16; pp=(portsc/512)%2; pspeed=(portsc/1024)%16;
    }
    unsafe {
        volatile_write64(xhci_state+3280,packed); volatile_write64(xhci_state+3344,sw_cycle); volatile_write64(xhci_state+3352,hw_dcs);
        volatile_write64(xhci_state+3360,ep_state); volatile_write64(xhci_state+3368,ep_interval); volatile_write64(xhci_state+3376,ep_type); volatile_write64(xhci_state+3384,ep_burst); volatile_write64(xhci_state+3392,ep_mps); volatile_write64(xhci_state+3400,ep_avg); volatile_write64(xhci_state+3408,ep_esit);
        volatile_write64(xhci_state+3440,mf_now); volatile_write64(xhci_state+3448,mf_moved); volatile_write64(xhci_state+3456,route);
        volatile_write64(xhci_state+3544,sw_port); volatile_write64(xhci_state+3552,hw_root); volatile_write64(xhci_state+3560,ccs); volatile_write64(xhci_state+3568,ped); volatile_write64(xhci_state+3576,pls); volatile_write64(xhci_state+3584,pspeed); volatile_write64(xhci_state+3592,dev_addr); volatile_write64(xhci_state+3600,slot_state); volatile_write64(xhci_state+3608,portsc); volatile_write64(xhci_state+3616,pp);
    }
    return 1;
}''')

# R49 P R C E L S A:
# P=Frames-selected root port, R=hardware Slot Context root-hub port,
# C=PORTSC Current Connect Status, E=Port Enabled/Disabled,
# L=Port Link State, S=PORTSC speed ID, A=hardware USB device address.
# A healthy direct-root low-speed receiver should normally show P==R, C=1,
# E=1, L=0 (U0), S=2, and A!=0.
fnrep('v140_text_wifi_v140',label_fn('v140_text_wifi_v140','R49 P R C E L S A'))
old=r'''    v140_text_wifi_v140(surface,px+10,py+748,white); if xhci!=0 { v108_draw_small_u64(surface,((px+112)*65536)+(py+748),volatile_read64(xhci+3416),green); v108_draw_small_u64(surface,((px+150)*65536)+(py+748),volatile_read64(xhci+3424),green); v108_draw_small_u64(surface,((px+188)*65536)+(py+748),volatile_read64(xhci+3464),green); v108_draw_small_u64(surface,((px+226)*65536)+(py+748),volatile_read64(xhci+3472),green); v108_draw_small_u64(surface,((px+264)*65536)+(py+748),volatile_read64(xhci+3480),red); v108_draw_small_u64(surface,((px+306)*65536)+(py+748),volatile_read64(xhci+3504),amber); v108_draw_small_u64(surface,((px+350)*65536)+(py+748),volatile_read64(xhci+3320),green); }'''
new=r'''    v140_text_wifi_v140(surface,px+10,py+748,white); if xhci!=0 { v108_draw_small_u64(surface,((px+112)*65536)+(py+748),volatile_read64(xhci+3544),amber); v108_draw_small_u64(surface,((px+150)*65536)+(py+748),volatile_read64(xhci+3552),white); v108_draw_small_u64(surface,((px+188)*65536)+(py+748),volatile_read64(xhci+3560),green); v108_draw_small_u64(surface,((px+226)*65536)+(py+748),volatile_read64(xhci+3568),green); v108_draw_small_u64(surface,((px+264)*65536)+(py+748),volatile_read64(xhci+3576),amber); v108_draw_small_u64(surface,((px+306)*65536)+(py+748),volatile_read64(xhci+3584),white); v108_draw_small_u64(surface,((px+350)*65536)+(py+748),volatile_read64(xhci+3592),white); }'''
rep(old,new,'r49 root-port/slot physical row')

buttons=fn_text('ps2_elan4_buttons_v111')
if 'if typ==1 || typ==2 {' not in buttons or 'if typ>=1 && typ<=3 {' in buttons: raise SystemExit('r49 regressed r45 touchpad button isolation')
if 'return ps2_elan4_motion_v112(input_state,a,b);' not in s: raise SystemExit('r49 lost touchpad motion delivery')
if 'if r42_target && state==1' not in s: raise SystemExit('r49 lost persistent interrupt-IN policy')
arm=fn_text('xhci_hid_arm_continuous')
for q in ('cpuid_eax(0,0)','sts_flush=volatile_read32(op+4)','mf_after=volatile_read32(runtime)%16384','volatile_write32(db,dci)'):
    if q not in arm: raise SystemExit('r49 lost proven r48 scheduler/handoff '+q)
snap=fn_text('v144_hid_forensic_snapshot')
for q in ('hw_root=(slot1/65536)%256','dev_addr=slot3%256','slot_state=(slot3/134217728)%32','portsc=volatile_read32(port)','ccs=portsc%2','ped=(portsc/2)%2','pls=(portsc/32)%16','pspeed=(portsc/1024)%16','volatile_write64(xhci_state+3544,sw_port)','volatile_write64(xhci_state+3608,portsc)'):
    if q not in snap: raise SystemExit('r49 root-port/slot proof missing '+q)
for bad in ('volatile_write32(port','xhci_control','v136_xhci_command_endpoint','pit_wait','v135_hid_control_fallback'):
    if bad in snap: raise SystemExit('r49 passive proof became active '+bad)
if s.count('{')!=s.count('}'): raise SystemExit('r49 brace mismatch')
out=hashlib.sha256(s.encode()).hexdigest()
EXPECTED='8fb90cb36157c9efaec61983105de52834d62e912f4bd709de97ec0deee4991a'
if out!=EXPECTED: raise SystemExit('r49 output sha mismatch '+out)
p.write_text(s)
print(out)
