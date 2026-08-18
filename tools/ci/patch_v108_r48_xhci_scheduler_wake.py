#!/usr/bin/env python3
from pathlib import Path
import hashlib, subprocess, sys
if len(sys.argv)!=2: raise SystemExit('usage: patch_v108_r48_xhci_scheduler_wake.py <kernel/main.nx>')
p=Path(sys.argv[1]); here=Path(__file__).parent
base=here/'patch_v108_r47_xhci_doorbell_flush_probe.py'
subprocess.run([sys.executable,str(base),str(p)],check=True,stdout=subprocess.DEVNULL)
s=p.read_text()
BASE='5037199d0ea3bde3a050ac648d2f91ef2c92e225ae303113b683cf7e453b90fa'
if hashlib.sha256(s.encode()).hexdigest()!=BASE: raise SystemExit('r48 exact r47 base mismatch '+hashlib.sha256(s.encode()).hexdigest())

def rep(old,new,label,count=1):
    global s
    n=s.count(old)
    if n!=count: raise SystemExit(f'r48 {label} count {n}, expected {count}')
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

# r47 physical evidence on the ASUS/Intel 8086:8c31 host:
#   H=1 F=1 M=0 R=0 Q=0 V=0 B=0.
# The software-owned Normal TRB became controller-owned exactly and the endpoint
# doorbell path executed, but MFINDEX never proved that the periodic scheduler
# advanced, the endpoint dequeue stayed at index 0, no Transfer Event appeared,
# and the HID DMA buffer remained zero.  r48 therefore fixes the handoff boundary
# rather than changing the accepted endpoint context again:
#   * serialize WB DMA writes before the MMIO doorbell with CPUID,
#   * flush the posted doorbell by reading USBSTS (not the doorbell register),
#   * wait boundedly for MFINDEX to advance,
#   * if it stays static and the controller has no HSE/HCE, reassert Run when
#     needed and re-ring the endpoint once, then test MFINDEX again.
arm=fn_text('xhci_hid_arm_continuous')
old=r'''    let runtime=volatile_read64(xhci_state+80); var mf:u64=0; if runtime!=0 { mf=volatile_read32(runtime)%16384; }
    let db=doorbells+(slot*4);
    tail=tail+1;
    unsafe {
        volatile_write64(xhci_state+3416,1); volatile_write64(xhci_state+3432,mf);
        volatile_write64(xhci_state+408,tail); volatile_write64(xhci_state+800,cycle); volatile_write64(xhci_state+808,1);
        volatile_write32(db,dci);
    }
    let db_flush=volatile_read32(db); unsafe { volatile_write64(xhci_state+3424,1); }
'''
new=r'''    let runtime=volatile_read64(xhci_state+80); let op=volatile_read64(xhci_state+8); var mf:u64=0; if runtime!=0 { mf=volatile_read32(runtime)%16384; }
    var cmd_before:u64=0; var sts_before:u64=0; if op!=0 { cmd_before=volatile_read32(op); sts_before=volatile_read32(op+4); }
    let order_barrier=cpuid_eax(0,0);
    let db=doorbells+(slot*4);
    tail=tail+1;
    unsafe {
        volatile_write64(xhci_state+3416,1); volatile_write64(xhci_state+3432,mf);
        volatile_write64(xhci_state+408,tail); volatile_write64(xhci_state+800,cycle); volatile_write64(xhci_state+808,1);
        volatile_write32(db,dci);
    }
    var sts_flush:u64=0; if op!=0 { sts_flush=volatile_read32(op+4); unsafe { volatile_write64(xhci_state+3424,1); } }
    var mf_after=mf; var moved:u64=0; var spins:u64=0;
    while moved==0 && spins<2000000 {
        if runtime!=0 { mf_after=volatile_read32(runtime)%16384; if mf_after!=mf { moved=1; } }
        cpu_pause(); spins=spins+1;
    }
    var wake:u64=0;
    if moved==0 && op!=0 {
        wake=1;
        var live_cmd=volatile_read32(op); let live_sts=volatile_read32(op+4); let hse=(live_sts/4)%2; let hce=(live_sts/4096)%2;
        if hse==0 && hce==0 && (live_cmd%2==0 || live_sts%2!=0) {
            live_cmd=set_flag(live_cmd,1); unsafe { volatile_write32(op,live_cmd); }
            var rs:u64=0; while volatile_read32(op+4)%2!=0 && rs<2000000 { cpu_pause(); rs=rs+1; }
        }
        let wake_barrier=cpuid_eax(0,0); unsafe { volatile_write32(db,dci); }
        sts_flush=volatile_read32(op+4); spins=0;
        while moved==0 && spins<2000000 {
            if runtime!=0 { mf_after=volatile_read32(runtime)%16384; if mf_after!=mf { moved=1; } }
            cpu_pause(); spins=spins+1;
        }
    }
    var cmd_after:u64=0; var sts_after:u64=0; if op!=0 { cmd_after=volatile_read32(op); sts_after=volatile_read32(op+4); }
    unsafe {
        volatile_write64(xhci_state+3464,moved); volatile_write64(xhci_state+3472,cmd_after%2); volatile_write64(xhci_state+3480,sts_after%2);
        volatile_write64(xhci_state+3488,(sts_after/4)%2); volatile_write64(xhci_state+3496,(sts_after/4096)%2); volatile_write64(xhci_state+3504,wake);
        volatile_write64(xhci_state+3512,mf_after); volatile_write64(xhci_state+3520,sts_flush); volatile_write64(xhci_state+3528,cmd_before);
        volatile_write64(xhci_state+3536,sts_before);
    }
'''
if arm.count(old)!=1: raise SystemExit('r48 r47 arm boundary anchor mismatch')
fnrep('xhci_hid_arm_continuous',arm.replace(old,new,1))

# R48 T F M U H W V:
# T=exact TRB ownership handoff, F=safe USBSTS posted-write flush,
# M=MFINDEX advanced after arm/wake, U=USBCMD.Run live after recovery,
# H=USBSTS.HCHalted, W=bounded scheduler wake/re-ring attempted,
# V=direct Transfer Event count.  Expected healthy idle is 1 1 1 1 0 [0/1] 0;
# moving the USB mouse should make V non-zero and USB R become 1.
fnrep('v140_text_wifi_v140',label_fn('v140_text_wifi_v140','R48 T F M U H W V'))
oldrow=r'''    v140_text_wifi_v140(surface,px+10,py+748,white); if xhci!=0 { v108_draw_small_u64(surface,((px+112)*65536)+(py+748),volatile_read64(xhci+3416),green); v108_draw_small_u64(surface,((px+150)*65536)+(py+748),volatile_read64(xhci+3424),green); v108_draw_small_u64(surface,((px+188)*65536)+(py+748),volatile_read64(xhci+3448),green); v108_draw_small_u64(surface,((px+226)*65536)+(py+748),volatile_read64(xhci+3456),white); v108_draw_small_u64(surface,((px+264)*65536)+(py+748),volatile_read64(xhci+2824),white); v108_draw_small_u64(surface,((px+306)*65536)+(py+748),volatile_read64(xhci+3320),green); v108_draw_small_u64(surface,((px+350)*65536)+(py+748),volatile_read64(xhci+3280),white); }'''
newrow=r'''    v140_text_wifi_v140(surface,px+10,py+748,white); if xhci!=0 { v108_draw_small_u64(surface,((px+112)*65536)+(py+748),volatile_read64(xhci+3416),green); v108_draw_small_u64(surface,((px+150)*65536)+(py+748),volatile_read64(xhci+3424),green); v108_draw_small_u64(surface,((px+188)*65536)+(py+748),volatile_read64(xhci+3464),green); v108_draw_small_u64(surface,((px+226)*65536)+(py+748),volatile_read64(xhci+3472),green); v108_draw_small_u64(surface,((px+264)*65536)+(py+748),volatile_read64(xhci+3480),red); v108_draw_small_u64(surface,((px+306)*65536)+(py+748),volatile_read64(xhci+3504),amber); v108_draw_small_u64(surface,((px+350)*65536)+(py+748),volatile_read64(xhci+3320),green); }'''
rep(oldrow,newrow,'r48 scheduler row')

buttons=fn_text('ps2_elan4_buttons_v111')
if 'if typ==1 || typ==2 {' not in buttons or 'if typ>=1 && typ<=3 {' in buttons: raise SystemExit('r48 regressed r45 touchpad button isolation')
if 'return ps2_elan4_motion_v112(input_state,a,b);' not in s: raise SystemExit('r48 lost touchpad motion delivery')
if 'if r42_target && state==1' not in s: raise SystemExit('r48 lost persistent interrupt-IN policy')
arm=fn_text('xhci_hid_arm_continuous')
for q in ('cpuid_eax(0,0)','sts_flush=volatile_read32(op+4)','mf_after=volatile_read32(runtime)%16384','live_cmd=set_flag(live_cmd,1)','volatile_write32(db,dci)','volatile_write64(xhci_state+3464,moved)','volatile_write64(xhci_state+3504,wake)'):
    if q not in arm: raise SystemExit('r48 scheduler-order recovery missing '+q)
if 'volatile_read32(db)' in arm: raise SystemExit('r48 retained unsafe/write-only doorbell readback flush')
for bad in ('v136_xhci_command_endpoint','xhci_control','pit_wait','v135_hid_control_fallback'):
    if bad in arm: raise SystemExit('r48 arm introduced forbidden recovery '+bad)
if s.count('{')!=s.count('}'): raise SystemExit('r48 brace mismatch')
out=hashlib.sha256(s.encode()).hexdigest()
EXPECTED='0e9a059bcec8ee0a1b7204b39585618418d51fce1ed4daccae67e2c2f877b984'
if out!=EXPECTED: raise SystemExit('r48 output sha mismatch '+out)
p.write_text(s)
print(out)
