#!/usr/bin/env python3
from pathlib import Path
import hashlib, subprocess, sys
if len(sys.argv)!=2: raise SystemExit('usage: patch_v108_r36_nonblocking_interrupt_recovery.py <kernel/main.nx>')
p=Path(sys.argv[1])
base=Path(__file__).with_name('patch_v108_r35b_g750jm_hm87_hid_interval.py')
subprocess.run([sys.executable,str(base),str(p)],check=True,stdout=subprocess.DEVNULL)
s=p.read_text()
BASE='a9761e17e71d803df703a7cfe6b4461a6d02ea6c398d2299c1f0fd72f48f8b28'
if hashlib.sha256(s.encode()).hexdigest()!=BASE: raise SystemExit('r35b base mismatch')

def rep(old,new,label):
    global s
    n=s.count(old)
    if n!=1: raise SystemExit(f'{label} count {n}')
    s=s.replace(old,new,1)

def label_fn(name,text):
    out=f'fn {name}(surface:u64,x:u64,y:u64,color:u64) -> u64 {{'
    for i,ch in enumerate(text):
        out+=f' if gui_draw_char_scaled(surface,((x+{i*6})*65536)+y,({ord(ch)}*65536)+1,color)==0 {{ return 0; }}'
    return out+' return 1; }\n'

# USB errors must never tear down the entire desktop input runtime. r35b physical
# evidence showed the PS/2 touchpad disappearing while the mouse EP0 fallback was
# repeatedly timing out. Make interrupt-HID fail open and retain the last transfer
# completion code/residue for physical diagnosis.
old='''fn xhci_hid_poll_continuous(xhci_state:u64,input_state:u64) -> u64 {
    if xhci_state==0 || input_state==0 || volatile_read64(xhci_state+808)==0 { return 1; }
    let slot=volatile_read64(xhci_state+136); let dci=volatile_read64(xhci_state+352); let packet=volatile_read64(xhci_state+360); var code:u64=0; var residue:u64=0; var matched:u64=0;
    let queued=xhci_event_mailbox_take_v127(xhci_state,slot,dci);
    if queued!=0 { let packed=queued-1; code=packed/16777216; residue=packed%16777216; matched=1; }
    if matched==0 {
        let event_ring=volatile_read64(xhci_state+24); let index=volatile_read64(xhci_state+96); let cycle=volatile_read64(xhci_state+104); if event_ring==0 { return 0; }
        let trb=event_ring+(index*16); let control=volatile_read32(trb+12); if control%2!=cycle { return 1; }
        let typ=(control/1024)%64; if typ!=32 { xhci_event_advance(xhci_state); return 1; }
        let status=volatile_read32(trb+8); code=(status/16777216)%256; residue=status%16777216; let event_ep=(control/65536)%32; let event_slot=(control/16777216)%256; xhci_event_advance(xhci_state);
        if event_slot!=slot || event_ep!=dci { xhci_event_mailbox_put_v127(xhci_state,event_slot,event_ep,(code*16777216)+residue); return 1; }
    }
    unsafe { volatile_write64(xhci_state+808,0); }
    if (code!=1 && code!=13) || residue>packet { return 0; }
    let actual=packet-residue; let protocol=volatile_read64(xhci_state+336); if actual==0 || (protocol==1 && actual<8) || (protocol==2 && actual<3) { return 0; }
    let buffer=volatile_read64(xhci_state+432); let checksum=nvme_read_checksum(buffer,actual); unsafe { volatile_write64(xhci_state+440,actual); volatile_write64(xhci_state+448,checksum); volatile_write64(xhci_state+456,volatile_read8(buffer)); volatile_write64(xhci_state+464,volatile_read8(buffer+1)); volatile_write64(xhci_state+472,1); volatile_write64(xhci_state+816,volatile_read64(xhci_state+816)+1); }
    if input_decode_boot_hid(xhci_state,input_state)==0 { return 0; }
    if volatile_read64(xhci_state+824)==0 { unsafe { volatile_write64(xhci_state+824,1); } serial_marker_devprev_usb_report_ok(); }
    return xhci_hid_arm_continuous(xhci_state,0);
}'''
new='''fn xhci_hid_poll_continuous(xhci_state:u64,input_state:u64) -> u64 {
    if xhci_state==0 || input_state==0 || volatile_read64(xhci_state+808)==0 { return 1; }
    let slot=volatile_read64(xhci_state+136); let dci=volatile_read64(xhci_state+352); let packet=volatile_read64(xhci_state+360); var code:u64=0; var residue:u64=0; var matched:u64=0;
    let queued=xhci_event_mailbox_take_v127(xhci_state,slot,dci);
    if queued!=0 { let packed=queued-1; code=packed/16777216; residue=packed%16777216; matched=1; }
    if matched==0 {
        let event_ring=volatile_read64(xhci_state+24); let index=volatile_read64(xhci_state+96); let cycle=volatile_read64(xhci_state+104); if event_ring==0 { unsafe { volatile_write64(xhci_state+2800,volatile_read64(xhci_state+2800)+1); } return 1; }
        let trb=event_ring+(index*16); let control=volatile_read32(trb+12); if control%2!=cycle { return 1; }
        let typ=(control/1024)%64; if typ!=32 { xhci_event_advance(xhci_state); return 1; }
        let status=volatile_read32(trb+8); code=(status/16777216)%256; residue=status%16777216; let event_ep=(control/65536)%32; let event_slot=(control/16777216)%256; xhci_event_advance(xhci_state);
        if event_slot!=slot || event_ep!=dci { xhci_event_mailbox_put_v127(xhci_state,event_slot,event_ep,(code*16777216)+residue); return 1; }
    }
    unsafe { volatile_write64(xhci_state+808,0); volatile_write64(xhci_state+2784,code); volatile_write64(xhci_state+2792,residue); }
    if (code!=1 && code!=13) || residue>packet { unsafe { volatile_write64(xhci_state+2800,volatile_read64(xhci_state+2800)+1); } return 1; }
    let actual=packet-residue; let protocol=volatile_read64(xhci_state+336); if actual==0 || (protocol==1 && actual<8) || (protocol==2 && actual<3) { unsafe { volatile_write64(xhci_state+2800,volatile_read64(xhci_state+2800)+1); } return 1; }
    let buffer=volatile_read64(xhci_state+432); let checksum=nvme_read_checksum(buffer,actual); unsafe { volatile_write64(xhci_state+440,actual); volatile_write64(xhci_state+448,checksum); volatile_write64(xhci_state+456,volatile_read8(buffer)); volatile_write64(xhci_state+464,volatile_read8(buffer+1)); volatile_write64(xhci_state+472,1); volatile_write64(xhci_state+816,volatile_read64(xhci_state+816)+1); }
    if input_decode_boot_hid(xhci_state,input_state)==0 { unsafe { volatile_write64(xhci_state+2800,volatile_read64(xhci_state+2800)+1); } return 1; }
    if volatile_read64(xhci_state+824)==0 { unsafe { volatile_write64(xhci_state+824,1); } serial_marker_devprev_usb_report_ok(); }
    if xhci_hid_arm_continuous(xhci_state,0)==0 { unsafe { volatile_write64(xhci_state+2800,volatile_read64(xhci_state+2800)+1); } }
    return 1;
}'''
rep(old,new,'interrupt HID fail-open')

# Nonblocking endpoint recovery. Read the hardware-owned output endpoint context,
# periodically re-kick a Running endpoint that has not produced a report, and for
# Halted/Stopped states perform a bounded Reset/Set-TR-Dequeue repair. No EP0 polling
# is used here, so PS/2 fallback remains continuously serviced.
anchor='''fn ps2_set1_ascii_v112(sc:u64,shift:u64,caps:u64) -> u64 {'''
insert='''fn v136_xhci_endpoint_snapshot(xhci_state:u64) -> u64 {
    if xhci_state==0 { return 0; }
    let output=volatile_read64(xhci_state+160); let ctxsize=volatile_read64(xhci_state+176); let dci=volatile_read64(xhci_state+352); if output==0 || ctxsize==0 || dci<2 || dci>31 { return 0; }
    let ep=output+(dci*ctxsize); let dw0=volatile_read32(ep); let dw1=volatile_read32(ep+4); let state=dw0%8; let interval=(dw0/65536)%256; let mps=(dw1/65536)%65536;
    unsafe { volatile_write64(xhci_state+2696,state); volatile_write64(xhci_state+2704,interval); volatile_write64(xhci_state+2712,dci); volatile_write64(xhci_state+2720,mps); }
    return state;
}
fn v136_xhci_hid_next_dequeue(xhci_state:u64) -> u64 {
    let ring=volatile_read64(xhci_state+392); if ring==0 { return 0; } var tail=volatile_read64(xhci_state+408); var cycle=volatile_read64(xhci_state+800); if cycle>1 { return 0; }
    if tail>=255 { tail=0; if cycle==1 { cycle=0; } else { cycle=1; } }
    return ring+(tail*16)+cycle;
}
fn v136_xhci_command_endpoint(xhci_state:u64,typ:u64,param:u64) -> u64 {
    if xhci_state==0 || (typ!=14 && typ!=16) { return 0; }
    let ring=volatile_read64(xhci_state+16); let doorbells=volatile_read64(xhci_state+88); let slot=volatile_read64(xhci_state+136); let dci=volatile_read64(xhci_state+352); if ring==0 || doorbells==0 || slot==0 || dci<2 || dci>31 { return 0; }
    var tail=volatile_read64(xhci_state+64); var cycle=volatile_read64(xhci_state+72); if tail>=255 { tail=0; if cycle==1 { cycle=0; } else { cycle=1; } }
    let trb=ring+(tail*16); unsafe { volatile_write64(trb,param); volatile_write32(trb+8,0); volatile_write32(trb+12,(typ*1024)+cycle+(dci*65536)+(slot*16777216)); }
    tail=tail+1; unsafe { volatile_write64(xhci_state+64,tail); volatile_write64(xhci_state+72,cycle); volatile_write32(doorbells,0); }
    let done=xhci_wait_command_completion(xhci_state); unsafe { volatile_write64(xhci_state+2744,volatile_read64(xhci_state+488)); } if done==slot { return 1; } return 0;
}
fn v136_hid_interrupt_recovery_tick(xhci_state:u64) -> u64 {
    if xhci_state==0 || volatile_read64(xhci_state+416)!=1 { return 1; }
    let state=v136_xhci_endpoint_snapshot(xhci_state); if volatile_read64(xhci_state+816)!=0 { return 1; }
    let now=read_tsc(); let last=volatile_read64(xhci_state+2752); if last!=0 && now>last && now-last<200000000 { return 1; } unsafe { volatile_write64(xhci_state+2752,now); }
    let slot=volatile_read64(xhci_state+136); let dci=volatile_read64(xhci_state+352); let doorbells=volatile_read64(xhci_state+88); if slot==0 || dci<2 || dci>31 || doorbells==0 { return 1; }
    if state==1 {
        if volatile_read64(xhci_state+808)==0 { if xhci_hid_arm_continuous(xhci_state,0)==0 { unsafe { volatile_write64(xhci_state+2800,volatile_read64(xhci_state+2800)+1); } } }
        else { unsafe { volatile_write32(doorbells+(slot*4),dci); volatile_write64(xhci_state+2728,volatile_read64(xhci_state+2728)+1); } }
        return 1;
    }
    if (state==2 || state==3) && volatile_read64(xhci_state+2736)<2 {
        var ok:u64=1; if state==2 { if v136_xhci_command_endpoint(xhci_state,14,0)==0 { ok=0; } }
        let next=v136_xhci_hid_next_dequeue(xhci_state); if next==0 || v136_xhci_command_endpoint(xhci_state,16,next)==0 { ok=0; }
        unsafe { volatile_write64(xhci_state+2736,volatile_read64(xhci_state+2736)+1); volatile_write64(xhci_state+808,0); }
        if ok!=0 { if xhci_hid_arm_continuous(xhci_state,0)==0 { unsafe { volatile_write64(xhci_state+2800,volatile_read64(xhci_state+2800)+1); } } }
        return 1;
    }
    return 1;
}
'''+anchor
rep(anchor,insert,'r36 endpoint recovery helpers')

# Remove the r35 live EP0 fallback completely and make startup USB arming fail-open.
old='''    if xhci!=0 && volatile_read64(xhci+416)==1 { v135_hid_control_fallback_prepare(xhci,phys_state); if xhci_hid_arm_continuous(xhci,phys_state)==0 { return 0; } }'''
new='''    if xhci!=0 && volatile_read64(xhci+416)==1 { if xhci_hid_arm_continuous(xhci,phys_state)==0 { unsafe { volatile_write64(xhci+2800,volatile_read64(xhci+2800)+1); } } }'''
rep(old,new,'startup USB fail-open')

old='''    var last_raw=volatile_read64(input_state+3224); var last_usb_r=volatile_read64(input_state+3128); var last_src=volatile_read64(input_state+3104); var last_r35_q:u64=0; var last_r35_r:u64=0; var last_r35_e:u64=0; if xhci!=0 { last_r35_q=volatile_read64(xhci+2584); last_r35_r=volatile_read64(xhci+2592); last_r35_e=volatile_read64(xhci+2616); } var raw_budget:u64=0;'''
new='''    var last_raw=volatile_read64(input_state+3224); var last_usb_r=volatile_read64(input_state+3128); var last_src=volatile_read64(input_state+3104); var last_r36_s:u64=0; var last_r36_k:u64=0; var last_r36_e:u64=0; if xhci!=0 { last_r36_s=volatile_read64(xhci+2696); last_r36_k=volatile_read64(xhci+2728); last_r36_e=volatile_read64(xhci+2784); } var raw_budget:u64=0;'''
rep(old,new,'r36 telemetry baselines')

old='''        if xhci!=0 && volatile_read64(xhci+808)!=0 { if xhci_hid_poll_continuous(xhci,input_state)==0 { return 0; } }
        if xhci!=0 { v135_hid_control_fallback_poll(xhci,input_state); }
        ps2_poll_fallback_burst_v112(input_state,24);
        var telemetry_redraw:u64=0; if xhci!=0 { let rq=volatile_read64(xhci+2584); let rr=volatile_read64(xhci+2592); let re=volatile_read64(xhci+2616); if rr!=last_r35_r || re!=last_r35_e || (rq!=last_r35_q && rq<=8) { telemetry_redraw=1; } last_r35_q=rq; last_r35_r=rr; last_r35_e=re; } var motion_telemetry_redraw:u64=0;'''
new='''        if xhci!=0 && volatile_read64(xhci+808)!=0 { xhci_hid_poll_continuous(xhci,input_state); }
        if xhci!=0 { v136_hid_interrupt_recovery_tick(xhci); }
        ps2_poll_fallback_burst_v112(input_state,24);
        var telemetry_redraw:u64=0; if xhci!=0 { let rs=volatile_read64(xhci+2696); let rk=volatile_read64(xhci+2728); let re=volatile_read64(xhci+2784); if rs!=last_r36_s || rk!=last_r36_k || re!=last_r36_e { telemetry_redraw=1; } last_r36_s=rs; last_r36_k=rk; last_r36_e=re; } var motion_telemetry_redraw:u64=0;'''
rep(old,new,'r36 live loop recovery')

# Reuse the existing final diagnostics row so the panel geometry/smoothness gates do
# not regress. S=endpoint state, I=hardware interval, D=DCI, M=max packet, K=re-kicks,
# E=last xHCI transfer completion code.
anchor='''fn v108_input_overlay_draw(surface:u64,state:u64,input_state:u64,xhci:u64) -> u64 {'''
rep(anchor,label_fn('v108_text_r36_v136','R36 S I D M K E')+anchor,'r36 label insert')
old='''    v108_text_r35_v135(surface,px+10,py+730,white); if xhci!=0 { v108_draw_small_u64(surface,((px+112)*65536)+(py+730),volatile_read64(xhci+2560),green); v108_draw_small_u64(surface,((px+160)*65536)+(py+730),volatile_read64(xhci+2568),green); v108_draw_small_u64(surface,((px+208)*65536)+(py+730),volatile_read64(xhci+2576),green); v108_draw_small_u64(surface,((px+256)*65536)+(py+730),volatile_read64(xhci+2584),white); v108_draw_small_u64(surface,((px+316)*65536)+(py+730),volatile_read64(xhci+2592),green); v108_draw_small_u64(surface,((px+376)*65536)+(py+730),volatile_read64(xhci+2616),red); }'''
new='''    v108_text_r36_v136(surface,px+10,py+730,white); if xhci!=0 { v108_draw_small_u64(surface,((px+112)*65536)+(py+730),volatile_read64(xhci+2696),green); v108_draw_small_u64(surface,((px+160)*65536)+(py+730),volatile_read64(xhci+2704),amber); v108_draw_small_u64(surface,((px+208)*65536)+(py+730),volatile_read64(xhci+2712),white); v108_draw_small_u64(surface,((px+256)*65536)+(py+730),volatile_read64(xhci+2720),white); v108_draw_small_u64(surface,((px+316)*65536)+(py+730),volatile_read64(xhci+2728),green); v108_draw_small_u64(surface,((px+376)*65536)+(py+730),volatile_read64(xhci+2784),red); }'''
rep(old,new,'r36 telemetry row')

p.write_text(s)
out=hashlib.sha256(s.encode()).hexdigest()
print(out)
