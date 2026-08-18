#!/usr/bin/env python3
from pathlib import Path
import hashlib, subprocess, sys
if len(sys.argv)!=2: raise SystemExit('usage: patch_v108_r46_xhci_periodic_context_proof.py <kernel/main.nx>')
p=Path(sys.argv[1]); here=Path(__file__).parent
base=here/'patch_v108_r45_touchpad_button_isolation_xhci_dcs.py'
subprocess.run([sys.executable,str(base),str(p)],check=True,stdout=subprocess.DEVNULL)
s=p.read_text()
BASE='b22fbc974398bdf6f13302fc1c05589966bad81edb72e83f0ca56b16f60b9b1b'
if hashlib.sha256(s.encode()).hexdigest()!=BASE: raise SystemExit('r46 exact r45 base mismatch '+hashlib.sha256(s.encode()).hexdigest())

def rep(old,new,label,count=1):
    global s
    n=s.count(old)
    if n!=count: raise SystemExit(f'r46 {label} count {n}, expected {count}')
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

# r45 physical evidence after sustained USB mouse movement:
#   A=1 D=0 C=1 H=1 V=0 M=0 B=0.
# The TD remained armed, hardware/software cycle state agreed, but the Intel
# controller never advanced the HID dequeue pointer, emitted a Transfer Event,
# or DMA-wrote a report. r46 is deliberately passive: read back the endpoint
# context the controller actually accepted after Configure Endpoint and expose
# its periodic-scheduling fields without touching the known-good touchpad path.
fnrep('v144_hid_forensic_snapshot',r'''fn v144_hid_forensic_snapshot(xhci_state:u64) -> u64 {
    if xhci_state==0 || volatile_read64(xhci_state+416)!=1 { return 0; }
    let buffer=volatile_read64(xhci_state+432); var packed:u64=0;
    if buffer!=0 { packed=volatile_read8(buffer)+(volatile_read8(buffer+1)*256)+(volatile_read8(buffer+2)*65536)+(volatile_read8(buffer+3)*16777216); }
    let sw_cycle=volatile_read64(xhci_state+800); let hw_dcs=volatile_read64(xhci_state+2832);
    var ep_state:u64=255; var ep_interval:u64=255; var ep_type:u64=255; var ep_burst:u64=255; var ep_mps:u64=0; var ep_avg:u64=0; var ep_esit:u64=0;
    let output=volatile_read64(xhci_state+160); let ctxsize=volatile_read64(xhci_state+176); let dci=volatile_read64(xhci_state+352);
    if output!=0 && ctxsize!=0 && dci>=2 && dci<=31 {
        let ep=output+(dci*ctxsize); let dw0=volatile_read32(ep); let dw1=volatile_read32(ep+4); let dw4=volatile_read32(ep+16);
        ep_state=dw0%8; ep_interval=(dw0/65536)%256; ep_type=(dw1/8)%8; ep_burst=(dw1/256)%256; ep_mps=(dw1/65536)%65536; ep_avg=dw4%65536; ep_esit=((dw4/65536)%65536)+(((dw0/16777216)%256)*65536);
    }
    unsafe {
        volatile_write64(xhci_state+3280,packed); volatile_write64(xhci_state+3344,sw_cycle); volatile_write64(xhci_state+3352,hw_dcs);
        volatile_write64(xhci_state+3360,ep_state); volatile_write64(xhci_state+3368,ep_interval); volatile_write64(xhci_state+3376,ep_type); volatile_write64(xhci_state+3384,ep_burst); volatile_write64(xhci_state+3392,ep_mps); volatile_write64(xhci_state+3400,ep_avg); volatile_write64(xhci_state+3408,ep_esit);
    }
    return 1;
}''')

# R46 S I T B M A E:
# S=hardware output endpoint state, I=accepted interval exponent,
# T=accepted endpoint type, B=accepted Max Burst, M=accepted Max Packet Size,
# A=accepted Average TRB Length, E=accepted Max ESIT Payload.
fnrep('v140_text_wifi_v140',label_fn('v140_text_wifi_v140','R46 S I T B M A E'))
old=r'''    v140_text_wifi_v140(surface,px+10,py+748,white); if xhci!=0 { v108_draw_small_u64(surface,((px+112)*65536)+(py+748),volatile_read64(xhci+808),green); v108_draw_small_u64(surface,((px+150)*65536)+(py+748),volatile_read64(xhci+2824),white); v108_draw_small_u64(surface,((px+188)*65536)+(py+748),volatile_read64(xhci+3344),white); v108_draw_small_u64(surface,((px+226)*65536)+(py+748),volatile_read64(xhci+3352),amber); v108_draw_small_u64(surface,((px+264)*65536)+(py+748),volatile_read64(xhci+3320),green); v108_draw_small_u64(surface,((px+306)*65536)+(py+748),volatile_read64(xhci+3328),green); v108_draw_small_u64(surface,((px+350)*65536)+(py+748),volatile_read64(xhci+3280),white); }'''
new=r'''    v140_text_wifi_v140(surface,px+10,py+748,white); if xhci!=0 { v108_draw_small_u64(surface,((px+112)*65536)+(py+748),volatile_read64(xhci+3360),green); v108_draw_small_u64(surface,((px+150)*65536)+(py+748),volatile_read64(xhci+3368),white); v108_draw_small_u64(surface,((px+188)*65536)+(py+748),volatile_read64(xhci+3376),white); v108_draw_small_u64(surface,((px+226)*65536)+(py+748),volatile_read64(xhci+3384),amber); v108_draw_small_u64(surface,((px+264)*65536)+(py+748),volatile_read64(xhci+3392),white); v108_draw_small_u64(surface,((px+306)*65536)+(py+748),volatile_read64(xhci+3400),white); v108_draw_small_u64(surface,((px+350)*65536)+(py+748),volatile_read64(xhci+3408),white); }'''
rep(old,new,'r46 endpoint-context physical row')

buttons=fn_text('ps2_elan4_buttons_v111')
if 'if typ==1 || typ==2 {' not in buttons or 'if typ>=1 && typ<=3 {' in buttons: raise SystemExit('r46 regressed r45 touchpad button isolation')
if 'return ps2_elan4_motion_v112(input_state,a,b);' not in s: raise SystemExit('r46 lost touchpad motion delivery')
if 'v135_hid_control_fallback_prepare(xhci,phys_state)' in s or 'v135_hid_control_fallback_poll(xhci,input_state)' in s: raise SystemExit('r46 reintroduced rejected EP0 fallback')
if 'if r42_target && state==1' not in s: raise SystemExit('r46 lost persistent interrupt-IN policy')
snap=fn_text('v144_hid_forensic_snapshot')
for q in ('volatile_read32(ep)','volatile_read32(ep+4)','volatile_read32(ep+16)','volatile_write64(xhci_state+3360,ep_state)','volatile_write64(xhci_state+3408,ep_esit)'):
    if q not in snap: raise SystemExit('r46 endpoint-context proof missing '+q)
if 'volatile_write32' in snap or 'v136_xhci_command_endpoint' in snap or 'xhci_control' in snap or 'pit_wait' in snap:
    raise SystemExit('r46 endpoint-context proof became active rather than passive')
if s.count('{')!=s.count('}'): raise SystemExit('r46 brace mismatch')
out=hashlib.sha256(s.encode()).hexdigest()
EXPECTED='8ddc1a93fa4a19e72d0a6a40058d8681ed2ef42b48bcd0ff4644ba8e25c2caf1'
if out!=EXPECTED: raise SystemExit('r46 output sha mismatch '+out)
p.write_text(s)
print(out)
