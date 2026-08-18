#!/usr/bin/env python3
from pathlib import Path
import hashlib, subprocess, sys
if len(sys.argv)!=2: raise SystemExit('usage: patch_v108_r43_hid_control_fallback_live.py <kernel/main.nx>')
p=Path(sys.argv[1]); here=Path(__file__).parent
base=here/'patch_v108_r42_hid_persistent_interrupt_in.py'
subprocess.run([sys.executable,str(base),str(p)],check=True,stdout=subprocess.DEVNULL)
s=p.read_text()
BASE='1b293c4c6a23d08786794c16910715cc68638c803fd0248a630daeac1e25c3bf'
if hashlib.sha256(s.encode()).hexdigest()!=BASE: raise SystemExit('r43 exact r42 base mismatch '+hashlib.sha256(s.encode()).hexdigest())

def rep(old,new,label,count=1):
    global s
    n=s.count(old)
    if n!=count: raise SystemExit(f'r43 {label} count {n}, expected {count}')
    s=s.replace(old,new,count)

def fn_text(name):
    st=s.index('fn '+name); op=s.index('{',st); d=0
    for i in range(op,len(s)):
        if s[i]=='{': d+=1
        elif s[i]=='}':
            d-=1
            if d==0:return s[st:i+1]
    raise SystemExit('unterminated '+name)

def label_fn(name,text):
    out=f'fn {name}(surface:u64,x:u64,y:u64,color:u64) -> u64 {{'
    for i,ch in enumerate(text):
        out+=f' if gui_draw_char_scaled(surface,((x+{i*6})*65536)+y,({ord(ch)}*65536)+1,color)==0 {{ return 0; }}'
    return out+' return 1; }'

# r42 physical evidence proved the exact receiver remains configured and no
# longer manufactures completion 26, but USB live-report readiness is still 0.
# Activate the already-existing HID class-control GET_REPORT fallback only for
# that exact receiver.  The fallback stops itself after a genuine interrupt-IN
# completion (xhci_state+816 != 0), so normal interrupt operation still wins.
old='''    if xhci!=0 && volatile_read64(xhci+416)==1 { if xhci_hid_arm_continuous(xhci,phys_state)==0 { unsafe { volatile_write64(xhci+2800,volatile_read64(xhci+2800)+1); } } }
    unsafe { volatile_write64(process+640,0); } let clean_frame=appearance_render(process);'''
new='''    if xhci!=0 && volatile_read64(xhci+416)==1 { if xhci_hid_arm_continuous(xhci,phys_state)==0 { unsafe { volatile_write64(xhci+2800,volatile_read64(xhci+2800)+1); } }
        let r43_speed=volatile_read64(xhci+184); let r43_vid=volatile_read64(xhci+272); let r43_pid=volatile_read64(xhci+280); let r43_proto=volatile_read64(xhci+336);
        if (r43_speed==1 || r43_speed==2) && r43_vid==9354 && r43_pid==4267 && r43_proto==2 { v135_hid_control_fallback_prepare(xhci,phys_state); }
    }
    unsafe { volatile_write64(process+640,0); } let clean_frame=appearance_render(process);'''
rep(old,new,'control fallback prepare')

old='''        if xhci!=0 && volatile_read64(xhci+808)!=0 { xhci_hid_poll_continuous(xhci,input_state); }
        if xhci!=0 { v136_hid_interrupt_recovery_tick(xhci); }
        var telemetry_redraw:u64=0;'''
new='''        if xhci!=0 && volatile_read64(xhci+808)!=0 { xhci_hid_poll_continuous(xhci,input_state); }
        if xhci!=0 { v136_hid_interrupt_recovery_tick(xhci); if volatile_read64(xhci+2560)==1 { v135_hid_control_fallback_poll(xhci,input_state); } }
        var telemetry_redraw:u64=0;'''
rep(old,new,'control fallback live poll')

# Replace the unrelated W40 row in the input overlay with physical fallback
# telemetry: C=prepared, K=keyboard interface ready, M=mouse interface ready,
# N=successful class-control decodes, A=last GET_REPORT byte count, E=status.
rep(fn_text('v140_text_wifi_v140'),label_fn('v140_text_wifi_v140','R43 C K M N A E'),'r43 telemetry label')
old='''    v140_text_wifi_v140(surface,px+10,py+748,white); if xhci!=0 { v108_draw_small_u64(surface,((px+112)*65536)+(py+748),volatile_read64(xhci+3016),white); v108_draw_small_u64(surface,((px+170)*65536)+(py+748),volatile_read64(xhci+3024),white); v108_draw_small_u64(surface,((px+232)*65536)+(py+748),volatile_read64(xhci+3072),white); v108_draw_small_u64(surface,((px+300)*65536)+(py+748),volatile_read64(xhci+3080),white); v108_draw_small_u64(surface,((px+376)*65536)+(py+748),volatile_read64(xhci+3064),amber); }'''
new='''    v140_text_wifi_v140(surface,px+10,py+748,white); if xhci!=0 { v108_draw_small_u64(surface,((px+112)*65536)+(py+748),volatile_read64(xhci+2560),green); v108_draw_small_u64(surface,((px+154)*65536)+(py+748),volatile_read64(xhci+2568),white); v108_draw_small_u64(surface,((px+196)*65536)+(py+748),volatile_read64(xhci+2576),white); v108_draw_small_u64(surface,((px+244)*65536)+(py+748),volatile_read64(xhci+2592),green); v108_draw_small_u64(surface,((px+300)*65536)+(py+748),volatile_read64(xhci+2608),white); v108_draw_small_u64(surface,((px+356)*65536)+(py+748),volatile_read64(xhci+2616),red); }'''
rep(old,new,'r43 telemetry row')

if '(r43_speed==1 || r43_speed==2) && r43_vid==9354 && r43_pid==4267 && r43_proto==2' not in s: raise SystemExit('r43 exact receiver control fallback scope missing')
if 'v135_hid_control_fallback_prepare(xhci,phys_state)' not in s: raise SystemExit('r43 control fallback prepare missing')
if 'if volatile_read64(xhci+2560)==1 { v135_hid_control_fallback_poll(xhci,input_state); }' not in s: raise SystemExit('r43 control fallback live poll missing')
if 'if volatile_read64(xhci_state+816)!=0 { return 1; }' not in fn_text('v135_hid_control_fallback_poll'): raise SystemExit('r43 fallback no longer yields to genuine interrupt reports')
if 'if r42_target && state==1' not in s: raise SystemExit('r43 regressed r42 Running endpoint hold')
if 'v136_xhci_command_endpoint(xhci_state,15,0)' not in s: raise SystemExit('r43 regressed genuine endpoint recovery')
if 'ps2_poll_fallback_burst_v112(input_state,48);' not in s or 'return ps2_elan4_motion_v112(input_state,a,b);' not in s: raise SystemExit('r43 regressed recovered touchpad path')

p.write_text(s)
out=hashlib.sha256(s.encode()).hexdigest()
EXPECTED='926590a17115ca1e2c9bfa99224f8e8a0d190041bdd700fde411aafe594c2725'
if out!=EXPECTED: raise SystemExit('r43 output sha mismatch '+out)
print(out)
