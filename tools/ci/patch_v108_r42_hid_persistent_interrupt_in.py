#!/usr/bin/env python3
from pathlib import Path
import hashlib, subprocess, sys
if len(sys.argv)!=2: raise SystemExit('usage: patch_v108_r42_hid_persistent_interrupt_in.py <kernel/main.nx>')
p=Path(sys.argv[1]); here=Path(__file__).parent
base=here/'patch_v108_r41b_maxxter_usb1_hid_babble_protocol.py'
subprocess.run([sys.executable,str(base),str(p)],check=True,stdout=subprocess.DEVNULL)
s=p.read_text()
BASE='17139d64aafd6d797bab85fc925da51cf13fc0849cfa4f2a3191fcc3e686c814'
if hashlib.sha256(s.encode()).hexdigest()!=BASE: raise SystemExit('r42 exact r41b base mismatch '+hashlib.sha256(s.encode()).hexdigest())

def rep(old,new,label,count=1):
    global s
    n=s.count(old)
    if n!=count: raise SystemExit(f'{label} count {n}, expected {count}')
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

old=fn_text('v136_hid_interrupt_recovery_tick')
anchor='''    let state=v136_xhci_endpoint_snapshot(xhci_state); if volatile_read64(xhci_state+816)!=0 { return 1; }
    let now=read_tsc();'''
insert='''    let state=v136_xhci_endpoint_snapshot(xhci_state); if volatile_read64(xhci_state+816)!=0 { return 1; }
    // r42: a boot HID interrupt-IN endpoint may legitimately remain silent/NAK
    // indefinitely while the user is not moving the mouse.  Do not interpret
    // an outstanding TD on a Running endpoint as a timeout failure.  The old
    // kick/Stop Endpoint/Set TR Dequeue recovery manufactured completion 26
    // before a human physical test could begin.  Scope this first proof to the
    // exact receiver identified by r40/r41b; genuine non-Running/error states
    // continue through the inherited recovery paths below.
    let r42_speed=volatile_read64(xhci_state+184); let r42_vid=volatile_read64(xhci_state+272); let r42_pid=volatile_read64(xhci_state+280); let r42_proto=volatile_read64(xhci_state+336);
    let r42_target=(r42_speed==1 || r42_speed==2) && r42_vid==9354 && r42_pid==4267 && r42_proto==2;
    if r42_target && state==1 {
        unsafe { volatile_write64(xhci_state+3240,1); volatile_write64(xhci_state+3248,volatile_read64(xhci_state+3248)+1); }
        if volatile_read64(xhci_state+808)==0 { if xhci_hid_arm_continuous(xhci_state,0)==0 { unsafe { volatile_write64(xhci_state+2800,volatile_read64(xhci_state+2800)+1); } } }
        return 1;
    }
    let now=read_tsc();'''
if old.count(anchor)!=1: raise SystemExit('r42 recovery insertion anchor mismatch')
new=old.replace(anchor,insert,1)
rep(old,new,'r42 persistent interrupt-IN recovery gate')

# Make the physical build unmistakable while retaining the r41b telemetry
# meanings: G=GET_PROTOCOL ok, P=protocol, D=declared report descriptor length,
# L=current TD length, B=babble count, E=last completion code.
old_label=fn_text('v141_text_r41_v141')
rep(old_label,label_fn('v141_text_r41_v141','R42 G P D L B E'),'r42 physical row label')

# Structural guards: exact target only, no change to recovered PS/2 path, and
# no weakening of the bounded babble logic.
if '(r42_speed==1 || r42_speed==2) && r42_vid==9354 && r42_pid==4267 && r42_proto==2' not in s: raise SystemExit('r42 exact-device persistent-idle scope missing')
if 'if r42_target && state==1' not in s: raise SystemExit('r42 Running endpoint hold missing')
if 'v136_xhci_command_endpoint(xhci_state,15,0)' not in s: raise SystemExit('r42 unexpectedly removed genuine recovery machinery')
if 'if code==3 && target' not in s or 'if request<32 { next=32; }' not in s: raise SystemExit('r42 regressed bounded babble path')
if 'ps2_poll_fallback_burst_v112(input_state,48);' not in s or 'return ps2_elan4_motion_v112(input_state,a,b);' not in s: raise SystemExit('r42 regressed recovered touchpad path')

p.write_text(s)
out=hashlib.sha256(s.encode()).hexdigest()
print(out)
