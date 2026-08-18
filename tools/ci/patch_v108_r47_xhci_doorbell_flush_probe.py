#!/usr/bin/env python3
from pathlib import Path
import hashlib, subprocess, sys
if len(sys.argv)!=2: raise SystemExit('usage: patch_v108_r47_xhci_doorbell_flush_probe.py <kernel/main.nx>')
p=Path(sys.argv[1]); here=Path(__file__).parent
base=here/'patch_v108_r46_xhci_periodic_context_proof.py'
subprocess.run([sys.executable,str(base),str(p)],check=True,stdout=subprocess.DEVNULL)
s=p.read_text()
BASE='8ddc1a93fa4a19e72d0a6a40058d8681ed2ef42b48bcd0ff4644ba8e25c2caf1'
if hashlib.sha256(s.encode()).hexdigest()!=BASE: raise SystemExit('r47 exact r46 base mismatch '+hashlib.sha256(s.encode()).hexdigest())

def rep(old,new,label,count=1):
    global s
    n=s.count(old)
    if n!=count: raise SystemExit(f'r47 {label} count {n}, expected {count}')
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

# r46 physical evidence: the Intel controller accepted a fully sane output
# endpoint context (S1 I5 T7 B0 M8 A8 E8) on the direct-root low-speed receiver,
# but the armed TD still produced no report. Move one layer later: make ownership
# handoff explicit, verify the TRB from memory before release, then flush the
# posted endpoint-doorbell MMIO write with a readback. This mirrors the ordering
# discipline used by mature xHCI stacks without touching endpoint configuration,
# Stop Endpoint, Set TR Dequeue, EP0 fallback, HID decode, or the r45 touchpad fix.
fnrep('xhci_hid_arm_continuous',r'''fn xhci_hid_arm_continuous(xhci_state:u64,phys_state:u64) -> u64 {
    if xhci_state==0 || volatile_read64(xhci_state+416)!=1 { return 0; }
    if volatile_read64(xhci_state+808)!=0 { return 1; }
    let ring=volatile_read64(xhci_state+392); var buffer=volatile_read64(xhci_state+432); let packet=volatile_read64(xhci_state+360); let slot=volatile_read64(xhci_state+136); let dci=volatile_read64(xhci_state+352); let doorbells=volatile_read64(xhci_state+88);
    if buffer==0 { if phys_state==0 { return 0; } buffer=alloc_dma_page(phys_state,3); if buffer==0 { return 0; } zero_page(buffer); unsafe { volatile_write64(xhci_state+432,buffer); } }
    if ring==0 || buffer==0 || packet==0 || packet>1024 || slot==0 || dci<2 || dci>31 || doorbells==0 { return 0; }
    var request=packet; let speed=volatile_read64(xhci_state+184); let vid=volatile_read64(xhci_state+272); let pid=volatile_read64(xhci_state+280); let proto=volatile_read64(xhci_state+336);
    if (speed==1 || speed==2) && vid==9354 && pid==4267 && proto==2 { let adaptive=volatile_read64(xhci_state+3192); if adaptive>=packet && adaptive<=32 { request=adaptive; } }
    var tail=volatile_read64(xhci_state+408); var cycle=volatile_read64(xhci_state+800); if cycle>1 { return 0; }
    if tail>=255 { tail=0; if cycle==1 { cycle=0; } else { cycle=1; } }
    zero_page(buffer); let trb=ring+(tail*16); let control=1060+cycle; var hidden:u64=1; if cycle==1 { hidden=0; } let inactive=1060+hidden;
    unsafe {
        volatile_write64(xhci_state+3416,0); volatile_write64(xhci_state+3424,0);
        volatile_write64(xhci_state+3256,trb); volatile_write64(xhci_state+3264,request); volatile_write64(xhci_state+3272,tail);
        volatile_write64(trb,buffer); volatile_write32(trb+8,request); volatile_write32(trb+12,inactive); volatile_write64(xhci_state+3192,request);
    }
    if volatile_read64(trb)!=buffer || volatile_read32(trb+8)!=request || volatile_read32(trb+12)!=inactive { return 0; }
    unsafe { volatile_write32(trb+12,control); }
    if volatile_read64(trb)!=buffer || volatile_read32(trb+8)!=request || volatile_read32(trb+12)!=control { return 0; }
    let runtime=volatile_read64(xhci_state+80); var mf:u64=0; if runtime!=0 { mf=volatile_read32(runtime)%16384; }
    let db=doorbells+(slot*4);
    tail=tail+1;
    unsafe {
        volatile_write64(xhci_state+3416,1); volatile_write64(xhci_state+3432,mf);
        volatile_write64(xhci_state+408,tail); volatile_write64(xhci_state+800,cycle); volatile_write64(xhci_state+808,1);
        volatile_write32(db,dci);
    }
    let db_flush=volatile_read32(db); unsafe { volatile_write64(xhci_state+3424,1); }
    if volatile_read64(xhci_state+832)==0 { unsafe { volatile_write64(xhci_state+832,1); } serial_marker_devprev_usb_poll_armed(); }
    return 1;
}''')

# Keep r46's accepted endpoint-context snapshot and extend it with scheduler and
# direct-root proof. MFINDEX advancing proves the periodic scheduler clock is
# alive; route==0 proves this receiver does not depend on hub TT scheduling.
fnrep('v144_hid_forensic_snapshot',r'''fn v144_hid_forensic_snapshot(xhci_state:u64) -> u64 {
    if xhci_state==0 || volatile_read64(xhci_state+416)!=1 { return 0; }
    let buffer=volatile_read64(xhci_state+432); var packed:u64=0;
    if buffer!=0 { packed=volatile_read8(buffer)+(volatile_read8(buffer+1)*256)+(volatile_read8(buffer+2)*65536)+(volatile_read8(buffer+3)*16777216); }
    let sw_cycle=volatile_read64(xhci_state+800); let hw_dcs=volatile_read64(xhci_state+2832);
    var ep_state:u64=255; var ep_interval:u64=255; var ep_type:u64=255; var ep_burst:u64=255; var ep_mps:u64=0; var ep_avg:u64=0; var ep_esit:u64=0; var route:u64=1048575;
    let output=volatile_read64(xhci_state+160); let ctxsize=volatile_read64(xhci_state+176); let dci=volatile_read64(xhci_state+352);
    if output!=0 && ctxsize!=0 && dci>=2 && dci<=31 {
        let slot0=volatile_read32(output); route=slot0%1048576;
        let ep=output+(dci*ctxsize); let dw0=volatile_read32(ep); let dw1=volatile_read32(ep+4); let dw4=volatile_read32(ep+16);
        ep_state=dw0%8; ep_interval=(dw0/65536)%256; ep_type=(dw1/8)%8; ep_burst=(dw1/256)%256; ep_mps=(dw1/65536)%65536; ep_avg=dw4%65536; ep_esit=((dw4/65536)%65536)+(((dw0/16777216)%256)*65536);
    }
    let runtime=volatile_read64(xhci_state+80); var mf_now:u64=0; var mf_moved:u64=0;
    if runtime!=0 { mf_now=volatile_read32(runtime)%16384; let mf_arm=volatile_read64(xhci_state+3432); if mf_now!=mf_arm { mf_moved=1; } }
    unsafe {
        volatile_write64(xhci_state+3280,packed); volatile_write64(xhci_state+3344,sw_cycle); volatile_write64(xhci_state+3352,hw_dcs);
        volatile_write64(xhci_state+3360,ep_state); volatile_write64(xhci_state+3368,ep_interval); volatile_write64(xhci_state+3376,ep_type); volatile_write64(xhci_state+3384,ep_burst); volatile_write64(xhci_state+3392,ep_mps); volatile_write64(xhci_state+3400,ep_avg); volatile_write64(xhci_state+3408,ep_esit);
        volatile_write64(xhci_state+3440,mf_now); volatile_write64(xhci_state+3448,mf_moved); volatile_write64(xhci_state+3456,route);
    }
    return 1;
}''')

# R47 H F M R Q V B:
# H=TRB two-phase handoff readback exact, F=doorbell MMIO readback flush done,
# M=MFINDEX advanced after arm, R=slot route string, Q=hardware dequeue index,
# V=direct Transfer Events, B=first four HID DMA bytes.
fnrep('v140_text_wifi_v140',label_fn('v140_text_wifi_v140','R47 H F M R Q V B'))
old=r'''    v140_text_wifi_v140(surface,px+10,py+748,white); if xhci!=0 { v108_draw_small_u64(surface,((px+112)*65536)+(py+748),volatile_read64(xhci+3360),green); v108_draw_small_u64(surface,((px+150)*65536)+(py+748),volatile_read64(xhci+3368),white); v108_draw_small_u64(surface,((px+188)*65536)+(py+748),volatile_read64(xhci+3376),white); v108_draw_small_u64(surface,((px+226)*65536)+(py+748),volatile_read64(xhci+3384),amber); v108_draw_small_u64(surface,((px+264)*65536)+(py+748),volatile_read64(xhci+3392),white); v108_draw_small_u64(surface,((px+306)*65536)+(py+748),volatile_read64(xhci+3400),white); v108_draw_small_u64(surface,((px+350)*65536)+(py+748),volatile_read64(xhci+3408),white); }'''
new=r'''    v140_text_wifi_v140(surface,px+10,py+748,white); if xhci!=0 { v108_draw_small_u64(surface,((px+112)*65536)+(py+748),volatile_read64(xhci+3416),green); v108_draw_small_u64(surface,((px+150)*65536)+(py+748),volatile_read64(xhci+3424),green); v108_draw_small_u64(surface,((px+188)*65536)+(py+748),volatile_read64(xhci+3448),green); v108_draw_small_u64(surface,((px+226)*65536)+(py+748),volatile_read64(xhci+3456),white); v108_draw_small_u64(surface,((px+264)*65536)+(py+748),volatile_read64(xhci+2824),white); v108_draw_small_u64(surface,((px+306)*65536)+(py+748),volatile_read64(xhci+3320),green); v108_draw_small_u64(surface,((px+350)*65536)+(py+748),volatile_read64(xhci+3280),white); }'''
rep(old,new,'r47 handoff/doorbell physical row')

buttons=fn_text('ps2_elan4_buttons_v111')
if 'if typ==1 || typ==2 {' not in buttons or 'if typ>=1 && typ<=3 {' in buttons: raise SystemExit('r47 regressed r45 touchpad button isolation')
if 'return ps2_elan4_motion_v112(input_state,a,b);' not in s: raise SystemExit('r47 lost touchpad motion delivery')
if 'v135_hid_control_fallback_prepare(xhci,phys_state)' in s or 'v135_hid_control_fallback_poll(xhci,input_state)' in s: raise SystemExit('r47 reintroduced rejected EP0 fallback')
if 'if r42_target && state==1' not in s: raise SystemExit('r47 lost persistent interrupt-IN policy')
arm=fn_text('xhci_hid_arm_continuous')
for q in ('volatile_write32(trb+12,inactive)','volatile_read32(trb+12)!=inactive','volatile_write32(trb+12,control)','volatile_read32(trb+12)!=control','volatile_write32(db,dci)','volatile_read32(db)','volatile_write64(xhci_state+3416,1)','volatile_write64(xhci_state+3424,1)'):
    if q not in arm: raise SystemExit('r47 ordered handoff/doorbell proof missing '+q)
for bad in ('v136_xhci_command_endpoint','xhci_control','pit_wait','v135_hid_control_fallback'):
    if bad in arm: raise SystemExit('r47 arm introduced forbidden recovery '+bad)
snap=fn_text('v144_hid_forensic_snapshot')
for q in ('volatile_read32(runtime)%16384','volatile_write64(xhci_state+3448,mf_moved)','route=slot0%1048576','volatile_write64(xhci_state+3456,route)'):
    if q not in snap: raise SystemExit('r47 scheduler/direct-root proof missing '+q)
if s.count('{')!=s.count('}'): raise SystemExit('r47 brace mismatch')
out=hashlib.sha256(s.encode()).hexdigest()
EXPECTED='5037199d0ea3bde3a050ac648d2f91ef2c92e225ae303113b683cf7e453b90fa'
if out!=EXPECTED: raise SystemExit('r47 output sha mismatch '+out)
p.write_text(s)
print(out)
