#!/usr/bin/env python3
from pathlib import Path
import hashlib, subprocess, sys
if len(sys.argv)!=2: raise SystemExit('usage: patch_v108_r44_hid_ring_forensic.py <kernel/main.nx>')
p=Path(sys.argv[1]); here=Path(__file__).parent
base=here/'patch_v108_r42_hid_persistent_interrupt_in.py'
subprocess.run([sys.executable,str(base),str(p)],check=True,stdout=subprocess.DEVNULL)
s=p.read_text()
BASE='1b293c4c6a23d08786794c16910715cc68638c803fd0248a630daeac1e25c3bf'
if hashlib.sha256(s.encode()).hexdigest()!=BASE: raise SystemExit('r44 exact r42 base mismatch '+hashlib.sha256(s.encode()).hexdigest())

def rep(old,new,label,count=1):
    global s
    n=s.count(old)
    if n!=count: raise SystemExit(f'r44 {label} count {n}, expected {count}')
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

# r43's physical GET_REPORT fallback reproduced the older EP0 regression:
# no USB mouse report and loss of the PS/2 touchpad path. r44 deliberately
# returns to the exact r42 runtime behavior and adds only non-blocking forensic
# telemetry around the already-existing interrupt-IN transfer. No EP0 polling,
# endpoint command, dequeue rewrite, reset, delay or new doorbell is introduced.
old='''    zero_page(buffer); let trb=ring+(tail*16);
    unsafe { volatile_write64(trb,buffer); volatile_write32(trb+8,request); volatile_write32(trb+12,1060+cycle); volatile_write64(xhci_state+3192,request); }'''
new='''    zero_page(buffer); let trb=ring+(tail*16);
    unsafe { volatile_write64(xhci_state+3256,trb); volatile_write64(xhci_state+3264,request); volatile_write64(xhci_state+3272,tail); volatile_write64(trb,buffer); volatile_write32(trb+8,request); volatile_write32(trb+12,1060+cycle); volatile_write64(xhci_state+3192,request); }'''
rep(old,new,'submitted TRB telemetry')

old='''    if queued!=0 { let packed=queued-1; code=packed/16777216; residue=packed%16777216; matched=1; }'''
new='''    if queued!=0 { let packed=queued-1; code=packed/16777216; residue=packed%16777216; matched=1; unsafe { volatile_write64(xhci_state+3336,volatile_read64(xhci_state+3336)+1); } }'''
rep(old,new,'mailbox event counter')

old='''        let trb=event_ring+(index*16); let control=volatile_read32(trb+12); if control%2!=cycle { return 1; }
        let typ=(control/1024)%64; if typ!=32 { xhci_event_advance(xhci_state); return 1; }
        let status=volatile_read32(trb+8); code=(status/16777216)%256; residue=status%16777216; let event_ep=(control/65536)%32; let event_slot=(control/16777216)%256; xhci_event_advance(xhci_state);
        if event_slot!=slot || event_ep!=dci { xhci_event_mailbox_put_v127(xhci_state,event_slot,event_ep,(code*16777216)+residue); return 1; }'''
new='''        let trb=event_ring+(index*16); let control=volatile_read32(trb+12); if control%2!=cycle { return 1; }
        let typ=(control/1024)%64; if typ!=32 { xhci_event_advance(xhci_state); return 1; }
        let event_param=volatile_read64(trb); let status=volatile_read32(trb+8); code=(status/16777216)%256; residue=status%16777216; let event_ep=(control/65536)%32; let event_slot=(control/16777216)%256;
        unsafe { volatile_write64(xhci_state+3296,event_param); volatile_write64(xhci_state+3304,status); volatile_write64(xhci_state+3312,control); volatile_write64(xhci_state+3320,volatile_read64(xhci_state+3320)+1); }
        xhci_event_advance(xhci_state);
        if event_slot!=slot || event_ep!=dci { xhci_event_mailbox_put_v127(xhci_state,event_slot,event_ep,(code*16777216)+residue); return 1; }
        let submitted=volatile_read64(xhci_state+3256); if submitted!=0 && (event_param-(event_param%16))==(submitted-(submitted%16)) { unsafe { volatile_write64(xhci_state+3328,volatile_read64(xhci_state+3328)+1); } }'''
rep(old,new,'raw transfer event telemetry')

anchor='fn v136_xhci_endpoint_snapshot(xhci_state:u64) -> u64 {'
helper='''fn v144_hid_forensic_snapshot(xhci_state:u64) -> u64 {
    if xhci_state==0 || volatile_read64(xhci_state+416)!=1 { return 0; }
    let buffer=volatile_read64(xhci_state+432); var packed:u64=0;
    if buffer!=0 { packed=volatile_read8(buffer)+(volatile_read8(buffer+1)*256)+(volatile_read8(buffer+2)*65536)+(volatile_read8(buffer+3)*16777216); }
    unsafe { volatile_write64(xhci_state+3280,packed); }
    return 1;
}
'''+anchor
rep(anchor,helper,'passive DMA snapshot helper')

old='''        if xhci!=0 { v136_hid_interrupt_recovery_tick(xhci); }
        var telemetry_redraw:u64=0;'''
new='''        if xhci!=0 { v136_hid_interrupt_recovery_tick(xhci); v144_hid_forensic_snapshot(xhci); }
        var telemetry_redraw:u64=0;'''
rep(old,new,'passive snapshot integration')

# Reuse the former read-only W40 row for compact physical transfer-ring proof:
# A=interrupt TD armed, T=submitted TRB index, D=hardware endpoint dequeue
# index, V=direct Transfer Events seen, M=events whose parameter matches the
# submitted TRB, Q=matching events recovered from the mailbox, B=first four
# DMA report bytes packed little-endian. R42's row above still carries the
# completion code and protocol/descriptor evidence.
fnrep('v140_text_wifi_v140',label_fn('v140_text_wifi_v140','R44 A T D V M Q B'))
old='''    v140_text_wifi_v140(surface,px+10,py+748,white); if xhci!=0 { v108_draw_small_u64(surface,((px+112)*65536)+(py+748),volatile_read64(xhci+3016),white); v108_draw_small_u64(surface,((px+170)*65536)+(py+748),volatile_read64(xhci+3024),white); v108_draw_small_u64(surface,((px+232)*65536)+(py+748),volatile_read64(xhci+3072),white); v108_draw_small_u64(surface,((px+300)*65536)+(py+748),volatile_read64(xhci+3080),white); v108_draw_small_u64(surface,((px+376)*65536)+(py+748),volatile_read64(xhci+3064),amber); }'''
new='''    v140_text_wifi_v140(surface,px+10,py+748,white); if xhci!=0 { v108_draw_small_u64(surface,((px+112)*65536)+(py+748),volatile_read64(xhci+808),green); v108_draw_small_u64(surface,((px+150)*65536)+(py+748),volatile_read64(xhci+3272),white); v108_draw_small_u64(surface,((px+188)*65536)+(py+748),volatile_read64(xhci+2824),white); v108_draw_small_u64(surface,((px+226)*65536)+(py+748),volatile_read64(xhci+3320),green); v108_draw_small_u64(surface,((px+270)*65536)+(py+748),volatile_read64(xhci+3328),green); v108_draw_small_u64(surface,((px+314)*65536)+(py+748),volatile_read64(xhci+3336),amber); v108_draw_small_u64(surface,((px+360)*65536)+(py+748),volatile_read64(xhci+3280),white); }'''
rep(old,new,'r44 forensic physical row')

if 'v135_hid_control_fallback_prepare(xhci,phys_state)' in s: raise SystemExit('r44 unexpectedly integrates r43 EP0 fallback prepare')
if 'v135_hid_control_fallback_poll(xhci,input_state)' in s: raise SystemExit('r44 unexpectedly integrates r43 EP0 fallback poll')
if 'if r42_target && state==1' not in s: raise SystemExit('r44 lost r42 persistent interrupt-IN hold')
if 'ps2_poll_fallback_burst_v112(input_state,48);' not in s or 'return ps2_elan4_motion_v112(input_state,a,b);' not in s: raise SystemExit('r44 altered recovered touchpad path')
forensic=fn_text('v144_hid_forensic_snapshot')
if 'volatile_write32' in forensic or 'v136_xhci_command_endpoint' in forensic or 'xhci_control' in forensic or 'pit_wait' in forensic: raise SystemExit('r44 forensic snapshot is not passive')
if s.count('{')!=s.count('}'): raise SystemExit('r44 brace mismatch')
out=hashlib.sha256(s.encode()).hexdigest()
EXPECTED='5fca6164e902f9720bef0d789ca46d2af480b065f32e1a6f61990476066962c1'
if out!=EXPECTED: raise SystemExit('r44 output sha mismatch '+out)
p.write_text(s)
print(out)
