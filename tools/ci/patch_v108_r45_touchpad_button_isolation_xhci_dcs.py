#!/usr/bin/env python3
from pathlib import Path
import hashlib, subprocess, sys
if len(sys.argv)!=2: raise SystemExit('usage: patch_v108_r45_touchpad_button_isolation_xhci_dcs.py <kernel/main.nx>')
p=Path(sys.argv[1]); here=Path(__file__).parent
base=here/'patch_v108_r44_hid_ring_forensic.py'
subprocess.run([sys.executable,str(base),str(p)],check=True,stdout=subprocess.DEVNULL)
s=p.read_text()
BASE='5fca6164e902f9720bef0d789ca46d2af480b065f32e1a6f61990476066962c1'
if hashlib.sha256(s.encode()).hexdigest()!=BASE: raise SystemExit('r45 exact r44 base mismatch '+hashlib.sha256(s.encode()).hexdigest())

def rep(old,new,label,count=1):
    global s
    n=s.count(old)
    if n!=count: raise SystemExit(f'r45 {label} count {n}, expected {count}')
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

# r44 physical evidence: USB remained armed with no event/DMA progress, while
# the touchpad moved until motion falsely opened the right-click menu and the
# pointer path then locked.  r37 had broadened the Elantech v4 button decoder
# from packet classes 1/2 to class 3 as well.  Class-3 is retained for relative
# motion, but it must not mutate button state: its upper bits are motion payload
# on this physical stream and can synthesize a false right button.
rep('if typ>=1 && typ<=3 {','if typ==1 || typ==2 {','Elantech typ3 button quarantine')

# Preserve r44's passive DMA/event forensics and add the two cycle values that
# distinguish an idle/NAKing TD from a producer/consumer cycle disagreement.
# This is diagnostic-only: r45 does NOT rewrite the endpoint dequeue pointer or
# force the producer cycle.  A zeroed transfer ring must never be made live with
# cycle 0 merely to match an unexpected hardware DCS.
fnrep('v144_hid_forensic_snapshot','''fn v144_hid_forensic_snapshot(xhci_state:u64) -> u64 {
    if xhci_state==0 || volatile_read64(xhci_state+416)!=1 { return 0; }
    let buffer=volatile_read64(xhci_state+432); var packed:u64=0;
    if buffer!=0 { packed=volatile_read8(buffer)+(volatile_read8(buffer+1)*256)+(volatile_read8(buffer+2)*65536)+(volatile_read8(buffer+3)*16777216); }
    let sw_cycle=volatile_read64(xhci_state+800); let hw_dcs=volatile_read64(xhci_state+2832);
    unsafe { volatile_write64(xhci_state+3280,packed); volatile_write64(xhci_state+3344,sw_cycle); volatile_write64(xhci_state+3352,hw_dcs); }
    return 1;
}''')

# R45 A D C H V M B:
# A=interrupt TD armed, D=hardware dequeue ring index,
# C=software producer cycle, H=hardware endpoint DCS,
# V=direct Transfer Events, M=events matching the submitted TRB,
# B=first four bytes in the HID DMA report buffer.
fnrep('v140_text_wifi_v140',label_fn('v140_text_wifi_v140','R45 A D C H V M B'))
old='''    v140_text_wifi_v140(surface,px+10,py+748,white); if xhci!=0 { v108_draw_small_u64(surface,((px+112)*65536)+(py+748),volatile_read64(xhci+808),green); v108_draw_small_u64(surface,((px+150)*65536)+(py+748),volatile_read64(xhci+3272),white); v108_draw_small_u64(surface,((px+188)*65536)+(py+748),volatile_read64(xhci+2824),white); v108_draw_small_u64(surface,((px+226)*65536)+(py+748),volatile_read64(xhci+3320),green); v108_draw_small_u64(surface,((px+270)*65536)+(py+748),volatile_read64(xhci+3328),green); v108_draw_small_u64(surface,((px+314)*65536)+(py+748),volatile_read64(xhci+3336),amber); v108_draw_small_u64(surface,((px+360)*65536)+(py+748),volatile_read64(xhci+3280),white); }'''
new='''    v140_text_wifi_v140(surface,px+10,py+748,white); if xhci!=0 { v108_draw_small_u64(surface,((px+112)*65536)+(py+748),volatile_read64(xhci+808),green); v108_draw_small_u64(surface,((px+150)*65536)+(py+748),volatile_read64(xhci+2824),white); v108_draw_small_u64(surface,((px+188)*65536)+(py+748),volatile_read64(xhci+3344),white); v108_draw_small_u64(surface,((px+226)*65536)+(py+748),volatile_read64(xhci+3352),amber); v108_draw_small_u64(surface,((px+264)*65536)+(py+748),volatile_read64(xhci+3320),green); v108_draw_small_u64(surface,((px+306)*65536)+(py+748),volatile_read64(xhci+3328),green); v108_draw_small_u64(surface,((px+350)*65536)+(py+748),volatile_read64(xhci+3280),white); }'''
rep(old,new,'r45 DCS physical row')

buttons=fn_text('ps2_elan4_buttons_v111')
if 'if typ==1 || typ==2 {' not in buttons or 'if typ>=1 && typ<=3 {' in buttons: raise SystemExit('r45 typ3 button quarantine missing')
if 'if typ==3 {' not in buttons: raise SystemExit('r45 lost typ3 diagnostic observation')
if 'return ps2_elan4_motion_v112(input_state,a,b);' not in s: raise SystemExit('r45 lost typ3 motion delivery')
if 'v135_hid_control_fallback_prepare(xhci,phys_state)' in s or 'v135_hid_control_fallback_poll(xhci,input_state)' in s: raise SystemExit('r45 reintroduced r43 EP0 fallback')
if 'if r42_target && state==1' not in s: raise SystemExit('r45 lost r42 persistent interrupt-IN policy')
forensic=fn_text('v144_hid_forensic_snapshot')
if 'volatile_write32' in forensic or 'v136_xhci_command_endpoint' in forensic or 'xhci_control' in forensic or 'pit_wait' in forensic: raise SystemExit('r45 forensic snapshot is not passive')
if 'volatile_read64(xhci_state+800)' not in forensic or 'volatile_read64(xhci_state+2832)' not in forensic: raise SystemExit('r45 cycle/DCS proof missing')
if s.count('{')!=s.count('}'): raise SystemExit('r45 brace mismatch')
out=hashlib.sha256(s.encode()).hexdigest()
EXPECTED='b22fbc974398bdf6f13302fc1c05589966bad81edb72e83f0ca56b16f60b9b1b'
if out!=EXPECTED: raise SystemExit('r45 output sha mismatch '+out)
p.write_text(s)
print(out)
