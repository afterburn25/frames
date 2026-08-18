#!/usr/bin/env python3
from pathlib import Path
import hashlib, subprocess, sys
if len(sys.argv)!=2: raise SystemExit('usage: patch_v108_r50_device_endpoint_status_proof.py <kernel/main.nx>')
p=Path(sys.argv[1]); here=Path(__file__).parent
base=here/'patch_v108_r49_xhci_root_port_slot_proof.py'
subprocess.run([sys.executable,str(base),str(p)],check=True,stdout=subprocess.DEVNULL)
s=p.read_text()
BASE='8fb90cb36157c9efaec61983105de52834d62e912f4bd709de97ec0deee4991a'
if hashlib.sha256(s.encode()).hexdigest()!=BASE: raise SystemExit('r50 exact r49 base mismatch '+hashlib.sha256(s.encode()).hexdigest())

def rep(old,new,label,count=1):
    global s
    n=s.count(old)
    if n!=count: raise SystemExit(f'r50 {label} count {n}, expected {count}')
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

# r49 physical evidence on the ASUS/Intel 8086:8c31 host:
#   P=2 R=2 C=1 E=1 L=0 S=1 A=1.
# Frames and the hardware Slot Context agree on root port 2; PORTSC says the
# port is connected, enabled and in U0 at full speed; the hardware-assigned USB
# address is non-zero.  The remaining failure is therefore device/endpoint-side:
# no interrupt Transfer Event arrives even though the host path is live.
# r50 performs one bounded EP0 state proof before the interrupt TD is armed:
# GET_CONFIGURATION, GET_INTERFACE, and endpoint GET_STATUS.  If the device
# itself reports ENDPOINT_HALT, clear that standard USB feature exactly once and
# verify it.  No continuous EP0 polling is introduced.
cfg=fn_text('xhci_configure_boot_hid')
anchor='''    let idle_setup=2593+(64000*65536)+(interface_num*4294967296); var idle_ok:u64=0; if xhci_control_no_data_out(xhci_state,idle_setup)!=0 { idle_ok=1; } unsafe { volatile_write64(xhci_state+2960,idle_ok); }'''
insert=anchor+r'''
    let dci_probe=volatile_read64(xhci_state+352); var ep_addr:u64=0;
    if dci_probe>=2 && dci_probe<=31 { if dci_probe%2==1 { ep_addr=128+((dci_probe-1)/2); } else { ep_addr=dci_probe/2; } }
    var cfg_val:u64=255; var alt_val:u64=255; var halt_before:u64=255; var halt_after:u64=255; var clear_result:u64=0;
    let cfg_setup=usb_setup_length_v113(usb_setup_value_v113(128,8,0,0),1); let cfg_buf=xhci_control_get(xhci_state,phys_state,cfg_setup,1); if cfg_buf!=0 { cfg_val=volatile_read8(cfg_buf); }
    let alt_setup=usb_setup_length_v113(usb_setup_value_v113(129,10,0,interface_num),1); let alt_buf=xhci_control_get(xhci_state,phys_state,alt_setup,1); if alt_buf!=0 { alt_val=volatile_read8(alt_buf); }
    if ep_addr!=0 {
        let st_setup=usb_setup_length_v113(usb_setup_value_v113(130,0,0,ep_addr),2); let st_buf=xhci_control_get(xhci_state,phys_state,st_setup,2);
        if st_buf!=0 { halt_before=volatile_read8(st_buf)%2; halt_after=halt_before;
            if halt_before==1 { clear_result=2; let clear_setup=usb_setup_value_v113(2,1,0,ep_addr); if xhci_control_no_data_out(xhci_state,clear_setup)!=0 { let st2=xhci_control_get(xhci_state,phys_state,st_setup,2); if st2!=0 { halt_after=volatile_read8(st2)%2; if halt_after==0 { clear_result=1; } } } }
        }
    }
    let sw_speed=volatile_read64(xhci_state+184); let sw_port=volatile_read64(xhci_state+112); let op_probe=volatile_read64(xhci_state+8); var port_speed:u64=0;
    if op_probe!=0 && sw_port>=1 && sw_port<=32 { port_speed=(volatile_read32(op_probe+1024+((sw_port-1)*16))/1024)%16; }
    unsafe { volatile_write64(xhci_state+3624,cfg_val); volatile_write64(xhci_state+3632,alt_val); volatile_write64(xhci_state+3640,ep_addr); volatile_write64(xhci_state+3648,halt_before); volatile_write64(xhci_state+3656,clear_result); volatile_write64(xhci_state+3664,halt_after); volatile_write64(xhci_state+3672,sw_speed); volatile_write64(xhci_state+3680,port_speed); }
'''
if cfg.count(anchor)!=1: raise SystemExit('r50 device-status insertion anchor mismatch')
fnrep('xhci_configure_boot_hid',cfg.replace(anchor,insert,1))

# R50 C I E H X S P:
# C=GET_CONFIGURATION value, I=GET_INTERFACE alternate setting,
# E=selected endpoint address, H=device endpoint-halt state before recovery,
# X=clear-halt result (0 not needed, 1 cleared+verified, 2 attempted/not verified),
# S=Frames speed ID, P=live PORTSC speed ID.
fnrep('v140_text_wifi_v140',label_fn('v140_text_wifi_v140','R50 C I E H X S P'))
oldrow=r'''    v140_text_wifi_v140(surface,px+10,py+748,white); if xhci!=0 { v108_draw_small_u64(surface,((px+112)*65536)+(py+748),volatile_read64(xhci+3544),amber); v108_draw_small_u64(surface,((px+150)*65536)+(py+748),volatile_read64(xhci+3552),white); v108_draw_small_u64(surface,((px+188)*65536)+(py+748),volatile_read64(xhci+3560),green); v108_draw_small_u64(surface,((px+226)*65536)+(py+748),volatile_read64(xhci+3568),green); v108_draw_small_u64(surface,((px+264)*65536)+(py+748),volatile_read64(xhci+3576),amber); v108_draw_small_u64(surface,((px+306)*65536)+(py+748),volatile_read64(xhci+3584),white); v108_draw_small_u64(surface,((px+350)*65536)+(py+748),volatile_read64(xhci+3592),white); }'''
newrow=r'''    v140_text_wifi_v140(surface,px+10,py+748,white); if xhci!=0 { v108_draw_small_u64(surface,((px+112)*65536)+(py+748),volatile_read64(xhci+3624),green); v108_draw_small_u64(surface,((px+150)*65536)+(py+748),volatile_read64(xhci+3632),white); v108_draw_small_u64(surface,((px+188)*65536)+(py+748),volatile_read64(xhci+3640),white); v108_draw_small_u64(surface,((px+226)*65536)+(py+748),volatile_read64(xhci+3648),amber); v108_draw_small_u64(surface,((px+264)*65536)+(py+748),volatile_read64(xhci+3656),amber); v108_draw_small_u64(surface,((px+306)*65536)+(py+748),volatile_read64(xhci+3672),white); v108_draw_small_u64(surface,((px+350)*65536)+(py+748),volatile_read64(xhci+3680),white); }'''
rep(oldrow,newrow,'r50 device endpoint status row')

buttons=fn_text('ps2_elan4_buttons_v111')
if 'if typ==1 || typ==2 {' not in buttons or 'if typ>=1 && typ<=3 {' in buttons: raise SystemExit('r50 regressed r45 touchpad button isolation')
if 'return ps2_elan4_motion_v112(input_state,a,b);' not in s: raise SystemExit('r50 lost touchpad motion delivery')
if 'if r42_target && state==1' not in s: raise SystemExit('r50 lost persistent interrupt-IN policy')
arm=fn_text('xhci_hid_arm_continuous')
for q in ('cpuid_eax(0,0)','sts_flush=volatile_read32(op+4)','mf_after=volatile_read32(runtime)%16384','volatile_write32(db,dci)'):
    if q not in arm: raise SystemExit('r50 lost proven r48 scheduler/handoff '+q)
for q in ('usb_setup_value_v113(128,8,0,0)','usb_setup_value_v113(129,10,0,interface_num)','usb_setup_value_v113(130,0,0,ep_addr)','usb_setup_value_v113(2,1,0,ep_addr)','volatile_write64(xhci_state+3624,cfg_val)','volatile_write64(xhci_state+3680,port_speed)'):
    if q not in s: raise SystemExit('r50 bounded device-status proof missing '+q)
if 'v135_hid_control_fallback_poll' in cfg: raise SystemExit('r50 reintroduced continuous GET_REPORT fallback')
if s.count('{')!=s.count('}'): raise SystemExit('r50 brace mismatch')
out=hashlib.sha256(s.encode()).hexdigest()
EXPECTED='PENDING_IDENTITY_PROBE'
if EXPECTED!='PENDING_IDENTITY_PROBE' and out!=EXPECTED: raise SystemExit('r50 output sha mismatch '+out)
p.write_text(s)
print(out)
