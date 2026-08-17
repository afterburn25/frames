#!/usr/bin/env python3
from pathlib import Path
import hashlib, subprocess, sys
if len(sys.argv)!=2: raise SystemExit('usage: patch_v108_r35_hid_control_poll_fallback.py <kernel/main.nx>')
p=Path(sys.argv[1])
base=Path(__file__).with_name('patch_v108_r34_late_reroute_reinit.py')
subprocess.run([sys.executable,str(base),str(p)],check=True,stdout=subprocess.DEVNULL)
s=p.read_text()
BASE='faed1632f131333e4e2c81c393b1e0df6a7940fde2c8506605e9b8964e7c5621'
if hashlib.sha256(s.encode()).hexdigest()!=BASE: raise SystemExit('r34 base mismatch')

def rep(old,new,label,count=1):
    global s
    n=s.count(old)
    if n!=count: raise SystemExit(f'{label} count {n}')
    s=s.replace(old,new,count)

def label_fn(name,text):
    out=f'fn {name}(surface:u64,x:u64,y:u64,color:u64) -> u64 {{'
    for i,ch in enumerate(text):
        out+=f' if gui_draw_char_scaled(surface,((x+{i*6})*65536)+y,({ord(ch)}*65536)+1,color)==0 {{ return 0; }}'
    return out+' return 1; }\n'

# Reusable, bounded EP0 IN helper. Unlike xhci_control_get, it reuses a caller-owned
# DMA page and does not allocate a page for every live HID sample.
anchor='''fn xhci_finalize_address_and_descriptor(xhci_state:u64, phys_state:u64) -> u64 {'''
insert='''fn v135_xhci_wait_ep0_bounded(xhci_state:u64,slot:u64) -> u64 {
    let event_ring=volatile_read64(xhci_state+24); if event_ring==0 { return 0; } var spins:u64=0;
    while spins<600000 {
        let queued=xhci_event_mailbox_take_v127(xhci_state,slot,1);
        if queued!=0 { let packed=queued-1; let code=packed/16777216; let remain=packed%16777216; unsafe { volatile_write64(xhci_state+504,code); volatile_write64(xhci_state+512,slot); volatile_write64(xhci_state+520,1); volatile_write64(xhci_state+576,remain); } if code==1 || code==13 { return code; } return 0; }
        let index=volatile_read64(xhci_state+96); let cycle=volatile_read64(xhci_state+104); let trb=event_ring+(index*16); let control=volatile_read32(trb+12);
        if control%2==cycle {
            let typ=(control/1024)%64;
            if typ==32 { let status=volatile_read32(trb+8); let code=(status/16777216)%256; let remain=status%16777216; let event_ep=(control/65536)%32; let event_slot=(control/16777216)%256; xhci_event_advance(xhci_state); if event_slot==slot && event_ep==1 { unsafe { volatile_write64(xhci_state+504,code); volatile_write64(xhci_state+512,event_slot); volatile_write64(xhci_state+520,event_ep); volatile_write64(xhci_state+576,remain); } if code==1 || code==13 { return code; } return 0; } xhci_event_mailbox_put_v127(xhci_state,event_slot,event_ep,(code*16777216)+remain); }
            else { xhci_event_advance(xhci_state); }
        }
        cpu_pause(); spins=spins+1;
    }
    unsafe { volatile_write64(xhci_state+504,255); volatile_write64(xhci_state+512,0); volatile_write64(xhci_state+520,0); volatile_write64(xhci_state+576,0); } return 0;
}
fn v135_xhci_control_get_into(xhci_state:u64,setup_value:u64,length:u64,buffer:u64) -> u64 {
    if xhci_state==0 || buffer==0 || length==0 || length>4096 { return 0; }
    let ring=volatile_read64(xhci_state+168); let slot=volatile_read64(xhci_state+136); let doorbells=volatile_read64(xhci_state+88); if ring==0 || slot==0 { return 0; }
    var tail=volatile_read64(xhci_state+200); var cycle=volatile_read64(xhci_state+208); if tail>251 { tail=0; if cycle==1 { cycle=0; } else { cycle=1; } }
    zero_page(buffer);
    let setup=ring+(tail*16); unsafe { volatile_write64(setup,setup_value); volatile_write32(setup+8,8); volatile_write32(setup+12,198720+cycle); }
    let data=setup+16; unsafe { volatile_write64(data,buffer); volatile_write32(data+8,length); volatile_write32(data+12,68608+cycle); }
    let status=data+16; unsafe { volatile_write64(status,0); volatile_write32(status+8,0); volatile_write32(status+12,4128+cycle); }
    tail=tail+3; unsafe { volatile_write64(xhci_state+200,tail); volatile_write64(xhci_state+208,cycle); volatile_write32(doorbells+(slot*4),1); }
    let code=v135_xhci_wait_ep0_bounded(xhci_state,slot); if code==0 { return 0; }
    let remain=volatile_read64(xhci_state+576); if remain>length { return 0; } return length-remain;
}
'''+anchor
rep(anchor,insert,'ep0 fallback helper anchor')

# Prepare the already-configured HID device for boot-protocol control polling.
# The normal interrupt endpoint remains configured/armed; this is a fallback only.
anchor='''fn serial_marker_usb_hid_report_ok() -> void {'''
insert='''fn v135_hid_control_fallback_prepare(xhci_state:u64,phys_state:u64) -> u64 {
    if xhci_state==0 || phys_state==0 || volatile_read64(xhci_state+416)!=1 { return 0; }
    if volatile_read64(xhci_state+2560)==1 { return 1; }
    var k:u64=0; var m:u64=0; if volatile_read64(xhci_state+1104)!=0 { k=1; } if volatile_read64(xhci_state+1152)!=0 { m=1; } if k==0 && m==0 { unsafe { volatile_write64(xhci_state+2616,1); } return 0; }
    let buffer=alloc_dma_page(phys_state,3); if buffer==0 { unsafe { volatile_write64(xhci_state+2616,2); } return 0; } zero_page(buffer);
    let primary=volatile_read64(xhci_state+336); var kready=k; var mready=m; var err:u64=0;
    if k!=0 && primary!=1 { let ki=volatile_read64(xhci_state+1096); let ks=usb_setup_length_v113(usb_setup_value_v113(33,11,0,ki),0); if xhci_control_no_data_out(xhci_state,ks)==0 { kready=0; err=3; } }
    if m!=0 && primary!=2 { let mi=volatile_read64(xhci_state+1144); let ms=usb_setup_length_v113(usb_setup_value_v113(33,11,0,mi),0); if xhci_control_no_data_out(xhci_state,ms)==0 { mready=0; if err==0 { err=4; } } }
    if kready==0 && mready==0 { unsafe { volatile_write64(xhci_state+2568,k); volatile_write64(xhci_state+2576,m); volatile_write64(xhci_state+2616,err); volatile_write64(xhci_state+2624,buffer); } return 0; }
    unsafe { volatile_write64(xhci_state+2560,1); volatile_write64(xhci_state+2568,kready); volatile_write64(xhci_state+2576,mready); volatile_write64(xhci_state+2584,0); volatile_write64(xhci_state+2592,0); volatile_write64(xhci_state+2600,0); volatile_write64(xhci_state+2608,0); volatile_write64(xhci_state+2616,err); volatile_write64(xhci_state+2624,buffer); volatile_write64(xhci_state+2632,0); volatile_write64(xhci_state+2640,0); volatile_write64(xhci_state+2648,0); volatile_write64(xhci_state+2656,0); }
    return 1;
}
'''+anchor
rep(anchor,insert,'fallback prepare anchor')

# Add live fallback sampler after the normal interrupt path. It alternates available
# keyboard/mouse boot interfaces and routes successful samples through the existing
# boot-HID decoder, preserving normal interrupt endpoint state.
anchor='''fn ps2_set1_ascii_v112(sc:u64,shift:u64,caps:u64) -> u64 {'''
insert='''fn v135_hid_control_fallback_poll(xhci_state:u64,input_state:u64) -> u64 {
    if xhci_state==0 || input_state==0 || volatile_read64(xhci_state+2560)!=1 { return 1; }
    if volatile_read64(xhci_state+816)!=0 { return 1; }
    var tick=volatile_read64(xhci_state+2656)+1; unsafe { volatile_write64(xhci_state+2656,tick); } if tick%256!=0 { return 1; }
    let k=volatile_read64(xhci_state+2568); let m=volatile_read64(xhci_state+2576); var protocol:u64=0;
    if k!=0 && m!=0 { let t=volatile_read64(xhci_state+2648); if t==0 { protocol=1; unsafe { volatile_write64(xhci_state+2648,1); } } else { protocol=2; unsafe { volatile_write64(xhci_state+2648,0); } } }
    else { if k!=0 { protocol=1; } if m!=0 { protocol=2; } }
    if protocol==0 { unsafe { volatile_write64(xhci_state+2616,5); } return 1; }
    var iface:u64=0; var length:u64=8; if protocol==1 { iface=volatile_read64(xhci_state+1096); } else { iface=volatile_read64(xhci_state+1144); }
    let buffer=volatile_read64(xhci_state+2624); if buffer==0 { unsafe { volatile_write64(xhci_state+2616,6); } return 1; }
    let setup=usb_setup_length_v113(usb_setup_value_v113(161,1,256,iface),length); unsafe { volatile_write64(xhci_state+2584,volatile_read64(xhci_state+2584)+1); volatile_write64(xhci_state+2600,protocol); }
    let actual=v135_xhci_control_get_into(xhci_state,setup,length,buffer); unsafe { volatile_write64(xhci_state+2608,actual); }
    if actual==0 { unsafe { volatile_write64(xhci_state+2616,10+protocol); } return 1; }
    if protocol==1 && actual<8 { unsafe { volatile_write64(xhci_state+2616,13); } return 1; }
    if protocol==2 && actual<3 { unsafe { volatile_write64(xhci_state+2616,14); } return 1; }
    if protocol==2 {
        var packed:u64=volatile_read8(buffer)+(volatile_read8(buffer+1)*256)+(volatile_read8(buffer+2)*65536); if actual>3 { packed=packed+(volatile_read8(buffer+3)*16777216); }
        let prev=volatile_read64(xhci_state+2632); unsafe { volatile_write64(xhci_state+2632,packed); } if packed==prev { unsafe { volatile_write64(xhci_state+2592,volatile_read64(xhci_state+2592)+1); volatile_write64(xhci_state+2616,0); } return 1; }
    }
    let oldb=volatile_read64(xhci_state+432); let olda=volatile_read64(xhci_state+440); let oldc=volatile_read64(xhci_state+448); let old0=volatile_read64(xhci_state+456); let old1=volatile_read64(xhci_state+464); let oldv=volatile_read64(xhci_state+472); let oldp=volatile_read64(xhci_state+336);
    let checksum=nvme_read_checksum(buffer,actual); unsafe { volatile_write64(xhci_state+432,buffer); volatile_write64(xhci_state+440,actual); volatile_write64(xhci_state+448,checksum); volatile_write64(xhci_state+456,volatile_read8(buffer)); volatile_write64(xhci_state+464,volatile_read8(buffer+1)); volatile_write64(xhci_state+472,1); volatile_write64(xhci_state+336,protocol); }
    let decoded=input_decode_boot_hid(xhci_state,input_state);
    unsafe { volatile_write64(xhci_state+432,oldb); volatile_write64(xhci_state+440,olda); volatile_write64(xhci_state+448,oldc); volatile_write64(xhci_state+456,old0); volatile_write64(xhci_state+464,old1); volatile_write64(xhci_state+472,oldv); volatile_write64(xhci_state+336,oldp); }
    if decoded==0 { unsafe { volatile_write64(xhci_state+2616,15); } return 1; }
    unsafe { volatile_write64(xhci_state+2592,volatile_read64(xhci_state+2592)+1); volatile_write64(xhci_state+2616,0); } return 1;
}
'''+anchor
rep(anchor,insert,'fallback poll anchor')

# Prepare fallback before the first diagnostic draw and keep normal interrupt HID armed.
old='''    if xhci!=0 && volatile_read64(xhci+416)==1 { if xhci_hid_arm_continuous(xhci,phys_state)==0 { return 0; } }'''
new='''    if xhci!=0 && volatile_read64(xhci+416)==1 { v135_hid_control_fallback_prepare(xhci,phys_state); if xhci_hid_arm_continuous(xhci,phys_state)==0 { return 0; } }'''
rep(old,new,'runtime fallback prepare')

# Add bounded fallback polling and telemetry refresh-on-change to the main loop.
old='''    var last_raw=volatile_read64(input_state+3224); var last_usb_r=volatile_read64(input_state+3128); var last_src=volatile_read64(input_state+3104); var raw_budget:u64=0;
    while true {
        let fr=volatile_read64(hardware_state+648); let msc=volatile_read64(hardware_state+640);
        if xhci!=0 && volatile_read64(xhci+808)!=0 { if xhci_hid_poll_continuous(xhci,input_state)==0 { return 0; } }
        ps2_poll_fallback_burst_v112(input_state,24);
        var telemetry_redraw:u64=0;'''
new='''    var last_raw=volatile_read64(input_state+3224); var last_usb_r=volatile_read64(input_state+3128); var last_src=volatile_read64(input_state+3104); var last_r35_q:u64=0; var last_r35_r:u64=0; var last_r35_e:u64=0; if xhci!=0 { last_r35_q=volatile_read64(xhci+2584); last_r35_r=volatile_read64(xhci+2592); last_r35_e=volatile_read64(xhci+2616); } var raw_budget:u64=0;
    while true {
        let fr=volatile_read64(hardware_state+648); let msc=volatile_read64(hardware_state+640);
        if xhci!=0 && volatile_read64(xhci+808)!=0 { if xhci_hid_poll_continuous(xhci,input_state)==0 { return 0; } }
        if xhci!=0 { v135_hid_control_fallback_poll(xhci,input_state); }
        ps2_poll_fallback_burst_v112(input_state,24);
        var telemetry_redraw:u64=0; if xhci!=0 { let rq=volatile_read64(xhci+2584); let rr=volatile_read64(xhci+2592); let re=volatile_read64(xhci+2616); if rr!=last_r35_r || re!=last_r35_e || (rq!=last_r35_q && rq<=8) { telemetry_redraw=1; } last_r35_q=rq; last_r35_r=rr; last_r35_e=re; }'''
rep(old,new,'runtime fallback poll')

# Add a compact diagnostic row: F=prepared, K/M=ready boot interfaces,
# Q=control queries, R=valid replies, E=last fallback error.
rep('fn v108_input_overlay_draw(surface:u64,state:u64,input_state:u64,xhci:u64) -> u64 {',label_fn('v108_text_r35_v135','R35 F K M Q R E')+'fn v108_input_overlay_draw(surface:u64,state:u64,input_state:u64,xhci:u64) -> u64 {','r35 label insert')
rep('(410*65536)+742','(410*65536)+760','r35 overlay height',count=s.count('(410*65536)+742'))
rep('cy<570','cy<768','r35 cursor overlay overlap',count=s.count('cy<570'))
old='''    v108_text_r34_v134(surface,px+10,py+712,white); if xhci!=0 { v108_draw_small_u64(surface,((px+112)*65536)+(py+712),volatile_read64(xhci+2496),white); v108_draw_small_u64(surface,((px+166)*65536)+(py+712),volatile_read64(xhci+2504),amber); v108_draw_small_u64(surface,((px+220)*65536)+(py+712),volatile_read64(xhci+2512),green); v108_draw_small_u64(surface,((px+274)*65536)+(py+712),volatile_read64(xhci+2520),green); v108_draw_small_u64(surface,((px+328)*65536)+(py+712),volatile_read64(xhci+2528),green); v108_draw_small_u64(surface,((px+376)*65536)+(py+712),volatile_read64(xhci+2536),red); }
    return 1;'''
new='''    v108_text_r34_v134(surface,px+10,py+712,white); if xhci!=0 { v108_draw_small_u64(surface,((px+112)*65536)+(py+712),volatile_read64(xhci+2496),white); v108_draw_small_u64(surface,((px+166)*65536)+(py+712),volatile_read64(xhci+2504),amber); v108_draw_small_u64(surface,((px+220)*65536)+(py+712),volatile_read64(xhci+2512),green); v108_draw_small_u64(surface,((px+274)*65536)+(py+712),volatile_read64(xhci+2520),green); v108_draw_small_u64(surface,((px+328)*65536)+(py+712),volatile_read64(xhci+2528),green); v108_draw_small_u64(surface,((px+376)*65536)+(py+712),volatile_read64(xhci+2536),red); }
    v108_text_r35_v135(surface,px+10,py+730,white); if xhci!=0 { v108_draw_small_u64(surface,((px+112)*65536)+(py+730),volatile_read64(xhci+2560),green); v108_draw_small_u64(surface,((px+160)*65536)+(py+730),volatile_read64(xhci+2568),green); v108_draw_small_u64(surface,((px+208)*65536)+(py+730),volatile_read64(xhci+2576),green); v108_draw_small_u64(surface,((px+256)*65536)+(py+730),volatile_read64(xhci+2584),white); v108_draw_small_u64(surface,((px+316)*65536)+(py+730),volatile_read64(xhci+2592),green); v108_draw_small_u64(surface,((px+376)*65536)+(py+730),volatile_read64(xhci+2616),red); }
    return 1;'''
rep(old,new,'r35 telemetry row')

# Contract checks.
for q in ('fn v135_xhci_wait_ep0_bounded','fn v135_xhci_control_get_into','fn v135_hid_control_fallback_prepare','fn v135_hid_control_fallback_poll','usb_setup_value_v113(161,1,256,iface)','volatile_write64(xhci_state+2560,1)','v135_hid_control_fallback_prepare(xhci,phys_state)','v135_hid_control_fallback_poll(xhci,input_state)','fn v108_text_r35_v135','volatile_read64(xhci+2592)','py+730'):
    if q not in s: raise SystemExit('r35 contract missing '+q)
if s.count('{')!=s.count('}'): raise SystemExit('brace imbalance')
expected='168f103ae3ba8f6dc403b1fa4c18aab01ab8160bd63387efffd1688ef8532ad0'
actual=hashlib.sha256(s.encode()).hexdigest()
if actual!=expected: raise SystemExit(f'r35 identity mismatch {actual}')
p.write_text(s)
print(actual)
