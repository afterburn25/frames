#!/usr/bin/env python3
from pathlib import Path
import hashlib, sys
p=Path(sys.argv[1])
raw=p.read_bytes()
expected='de8cd41f707268bc0d7bb2ff5ef925ba0e8981650703afdb065b1a62a1d6cca1'
actual=hashlib.sha256(raw).hexdigest()
if actual!=expected:
    raise SystemExit(f'unexpected r6 kernel hash: {actual}')
s=raw.decode()

def rep(old,new,label):
    global s
    n=s.count(old)
    if n!=1: raise SystemExit(f'{label}: expected 1 site, found {n}')
    s=s.replace(old,new,1)

old='''fn xhci_finalize_address_and_descriptor(xhci_state:u64, phys_state:u64) -> u64 {
    if volatile_read64(xhci_state+248)!=1 { return 0; }
    let speed=volatile_read64(xhci_state+184); let raw=volatile_read64(xhci_state+232); let mps=usb_ep0_packet_bytes(speed,raw); if mps==0 { return 0; }
    let input=volatile_read64(xhci_state+152); let ctxsize=volatile_read64(xhci_state+176); let slot=volatile_read64(xhci_state+136); let ep0=input+(ctxsize*2); if input==0 || slot==0 { return 0; }
    unsafe { volatile_write32(ep0+4,(mps*65536)+38); }
    let completed=xhci_command_submit_address(xhci_state,input,slot,0); if completed!=slot { return 0; }
    unsafe { volatile_write64(xhci_state+192,mps); volatile_write64(xhci_state+256,1); } serial_marker_xhci_addressed_ok();
    let full=xhci_control_get(xhci_state,phys_state,5066549597570688,18); if full==0 { return 0; }
    if volatile_read8(full)<18 || volatile_read8(full+1)!=1 { return 0; }
    let vid=volatile_read8(full+8)+(volatile_read8(full+9)*256); let pid=volatile_read8(full+10)+(volatile_read8(full+11)*256); let configs=volatile_read8(full+17); if configs==0 { return 0; }
    unsafe { volatile_write64(xhci_state+264,full); volatile_write64(xhci_state+272,vid); volatile_write64(xhci_state+280,pid); volatile_write64(xhci_state+288,configs); volatile_write64(xhci_state+296,1); }
    serial_marker_xhci_device_descriptor_ok(); return 1;
}'''
new='''fn xhci_finalize_address_and_descriptor(xhci_state:u64, phys_state:u64) -> u64 {
    if volatile_read64(xhci_state+248)!=1 { return 0; }
    let speed=volatile_read64(xhci_state+184); let raw=volatile_read64(xhci_state+232); let mps=usb_ep0_packet_bytes(speed,raw); if mps==0 { return 0; }
    let input=volatile_read64(xhci_state+152); let ctxsize=volatile_read64(xhci_state+176); let slot=volatile_read64(xhci_state+136); let ep0=input+(ctxsize*2); if input==0 || slot==0 { return 0; }
    let ring=volatile_read64(xhci_state+168); let tail=volatile_read64(xhci_state+200); let cycle=volatile_read64(xhci_state+208); if ring==0 { return 0; }
    // r7 physical xHCI repair: descriptor-8 consumed three TRBs.  The second
    // Address Device input context must carry EP0's current software enqueue
    // pointer, not the stale ring-start dequeue pointer from BSR=1 setup.
    unsafe { volatile_write32(input+0,0); volatile_write32(input+4,3); volatile_write32(ep0+4,(mps*65536)+38); volatile_write64(ep0+8,ring+(tail*16)+cycle); volatile_write64(xhci_state+528,ring+(tail*16)+cycle); volatile_write64(xhci_state+536,mps); }
    let completed=xhci_command_submit_address(xhci_state,input,slot,0); if completed!=slot { return 0; }
    unsafe { volatile_write64(xhci_state+192,mps); volatile_write64(xhci_state+256,1); } serial_marker_xhci_addressed_ok();
    let full=xhci_control_get(xhci_state,phys_state,5066549597570688,18); if full==0 { return 0; }
    if volatile_read8(full)<18 || volatile_read8(full+1)!=1 { return 0; }
    let vid=volatile_read8(full+8)+(volatile_read8(full+9)*256); let pid=volatile_read8(full+10)+(volatile_read8(full+11)*256); let configs=volatile_read8(full+17); if configs==0 { return 0; }
    unsafe { volatile_write64(xhci_state+264,full); volatile_write64(xhci_state+272,vid); volatile_write64(xhci_state+280,pid); volatile_write64(xhci_state+288,configs); volatile_write64(xhci_state+296,1); }
    serial_marker_xhci_device_descriptor_ok(); return 1;
}'''
rep(old,new,'xhci finalize repair')

old='''fn v108_text_us2(surface:u64,x:u64,y:u64,color:u64) -> u64 { if gui_draw_char_scaled(surface,((x+0)*65536)+y,(85*65536)+1,color)==0 { return 0; } if gui_draw_char_scaled(surface,((x+6)*65536)+y,(83*65536)+1,color)==0 { return 0; } if gui_draw_char_scaled(surface,((x+12)*65536)+y,(66*65536)+1,color)==0 { return 0; } if gui_draw_char_scaled(surface,((x+18)*65536)+y,(32*65536)+1,color)==0 { return 0; } if gui_draw_char_scaled(surface,((x+24)*65536)+y,(83*65536)+1,color)==0 { return 0; } if gui_draw_char_scaled(surface,((x+30)*65536)+y,(32*65536)+1,color)==0 { return 0; } if gui_draw_char_scaled(surface,((x+36)*65536)+y,(84*65536)+1,color)==0 { return 0; } if gui_draw_char_scaled(surface,((x+42)*65536)+y,(32*65536)+1,color)==0 { return 0; } if gui_draw_char_scaled(surface,((x+48)*65536)+y,(67*65536)+1,color)==0 { return 0; } return 1; }'''
new='''fn v108_text_us2(surface:u64,x:u64,y:u64,color:u64) -> u64 { if gui_draw_char_scaled(surface,((x+0)*65536)+y,(85*65536)+1,color)==0 { return 0; } if gui_draw_char_scaled(surface,((x+6)*65536)+y,(83*65536)+1,color)==0 { return 0; } if gui_draw_char_scaled(surface,((x+12)*65536)+y,(66*65536)+1,color)==0 { return 0; } if gui_draw_char_scaled(surface,((x+18)*65536)+y,(32*65536)+1,color)==0 { return 0; } if gui_draw_char_scaled(surface,((x+24)*65536)+y,(83*65536)+1,color)==0 { return 0; } if gui_draw_char_scaled(surface,((x+30)*65536)+y,(32*65536)+1,color)==0 { return 0; } if gui_draw_char_scaled(surface,((x+36)*65536)+y,(84*65536)+1,color)==0 { return 0; } if gui_draw_char_scaled(surface,((x+42)*65536)+y,(32*65536)+1,color)==0 { return 0; } if gui_draw_char_scaled(surface,((x+48)*65536)+y,(67*65536)+1,color)==0 { return 0; } if gui_draw_char_scaled(surface,((x+54)*65536)+y,(32*65536)+1,color)==0 { return 0; } if gui_draw_char_scaled(surface,((x+60)*65536)+y,(69*65536)+1,color)==0 { return 0; } return 1; }'''
rep(old,new,'usb stage label')
rep('''    let usb_r=volatile_read64(input_state+3128);
    v108_draw_small_u64(surface,((px+82)*65536)+(py+28),usb_h,green); v108_draw_small_u64(surface,((px+130)*65536)+(py+28),usb_r,green); v108_draw_small_u64(surface,((px+178)*65536)+(py+28),usb_p,amber);
    v108_text_us2(surface,px+10,py+46,white);
    v108_draw_small_u64(surface,((px+82)*65536)+(py+46),volatile_read64(input_state+3192),amber); v108_draw_small_u64(surface,((px+130)*65536)+(py+46),volatile_read64(input_state+3200),white); v108_draw_small_u64(surface,((px+178)*65536)+(py+46),volatile_read64(input_state+3216),white); v108_draw_small_u64(surface,((px+232)*65536)+(py+46),usb_q,green);''',
'''    let usb_r=volatile_read64(input_state+3128); let usb_cc=volatile_read64(xhci+488);
    v108_draw_small_u64(surface,((px+82)*65536)+(py+28),usb_h,green); v108_draw_small_u64(surface,((px+130)*65536)+(py+28),usb_r,green); v108_draw_small_u64(surface,((px+178)*65536)+(py+28),usb_p,amber);
    v108_text_us2(surface,px+10,py+46,white);
    v108_draw_small_u64(surface,((px+82)*65536)+(py+46),volatile_read64(input_state+3192),amber); v108_draw_small_u64(surface,((px+130)*65536)+(py+46),volatile_read64(input_state+3200),white); v108_draw_small_u64(surface,((px+178)*65536)+(py+46),volatile_read64(input_state+3216),white); v108_draw_small_u64(surface,((px+232)*65536)+(py+46),usb_cc,red);''','usb error telemetry')

anchor='fn desktop_input_runtime(process:u64,input_state:u64,phys_state:u64,hardware_state:u64) -> u64 {'
if s.count(anchor)!=1: raise SystemExit('desktop runtime anchor mismatch')
helpers='''fn v108_cursor_capture(cursor:u64,surface:u64,x:u64,y:u64) -> u64 {
    if cursor==0 || surface==0 || volatile_read64(surface)!=1 { return 0; }
    let width=volatile_read64(surface+16); let height=volatile_read64(surface+24); let stride=volatile_read64(surface+32); let base=volatile_read64(surface+8); if base==0 || x>=width || y>=height { return 0; }
    var w:u64=8; var h:u64=16; if x+w>width { w=width-x; } if y+h>height { h=height-y; }
    var yy:u64=0; while yy<h { var xx:u64=0; while xx<w { let c=volatile_read32(base+(((y+yy)*stride+(x+xx))*4)); unsafe { volatile_write32(cursor+128+(((yy*8)+xx)*4),c); } xx=xx+1; } yy=yy+1; }
    unsafe { volatile_write64(cursor+64,1); volatile_write64(cursor+72,x); volatile_write64(cursor+80,y); volatile_write64(cursor+88,w); volatile_write64(cursor+96,h); }
    return 1;
}
fn v108_cursor_restore(cursor:u64,surface:u64) -> u64 {
    if cursor==0 || surface==0 || volatile_read64(cursor+64)!=1 || volatile_read64(surface)!=1 { return 0; }
    let x=volatile_read64(cursor+72); let y=volatile_read64(cursor+80); let w=volatile_read64(cursor+88); let h=volatile_read64(cursor+96); let stride=volatile_read64(surface+32); let base=volatile_read64(surface+8); if base==0 { return 0; }
    var yy:u64=0; while yy<h { var xx:u64=0; while xx<w { let c=volatile_read32(cursor+128+(((yy*8)+xx)*4)); unsafe { volatile_write32(base+(((y+yy)*stride+(x+xx))*4),c); } xx=xx+1; } yy=yy+1; }
    return 1;
}
fn v108_cursor_present(process:u64,oldx:u64,oldy:u64,newx:u64,newy:u64) -> u64 {
    let dirty=volatile_read64(process+624); let timing=volatile_read64(process+664); let present=volatile_read64(process+672); if dirty==0 || timing==0 || present==0 { return 0; }
    dirty_add(dirty,(oldx*65536)+oldy,(8*65536)+16,32); dirty_add(dirty,(newx*65536)+newy,(8*65536)+16,32);
    present_enqueue(present,(oldx*65536)+oldy,(8*65536)+16,32); present_enqueue(present,(newx*65536)+newy,(8*65536)+16,32);
    if present_flush(present,volatile_read64(process+616),timing)==0 { return 0; }
    return 1;
}
fn serial_marker_v108_physical_cursor_visible_ok() -> void { serial_putc(70); serial_putc(82); serial_putc(65); serial_putc(77); serial_putc(69); serial_putc(83); serial_putc(95); serial_putc(86); serial_putc(49); serial_putc(48); serial_putc(56); serial_putc(95); serial_putc(80); serial_putc(72); serial_putc(89); serial_putc(83); serial_putc(73); serial_putc(67); serial_putc(65); serial_putc(76); serial_putc(95); serial_putc(67); serial_putc(85); serial_putc(82); serial_putc(83); serial_putc(79); serial_putc(82); serial_putc(95); serial_putc(86); serial_putc(73); serial_putc(83); serial_putc(73); serial_putc(66); serial_putc(76); serial_putc(69); serial_putc(95); serial_putc(79); serial_putc(75); serial_putc(10); return; }
'''
s=s.replace(anchor,helpers+anchor,1)
start=s.index('fn desktop_input_runtime(process:u64,input_state:u64,phys_state:u64,hardware_state:u64) -> u64 {')
i=start; depth=0; end=None
while i<len(s):
    if s[i]=='{': depth+=1
    elif s[i]=='}':
        depth-=1
        if depth==0:
            end=i+1
            if end<len(s) and s[end]=='\n': end+=1
            break
    i+=1
if end is None: raise SystemExit('runtime end not found')
new_runtime='''fn desktop_input_runtime(process:u64,input_state:u64,phys_state:u64,hardware_state:u64) -> u64 {
    if process==0 || input_state==0 || phys_state==0 || hardware_state==0 { return 0; }
    let state=volatile_read64(process+1080); let wm=volatile_read64(process+1072); let surface=volatile_read64(process+616); let cursor=volatile_read64(process+640); let xhci=volatile_read64(input_state+3008);
    if state==0 || wm==0 || surface==0 || cursor==0 { return 0; }
    if v108_input_backend_prepare(input_state)==0 { return 0; }
    if xhci!=0 && volatile_read64(xhci+416)==1 { if xhci_hid_arm_continuous(xhci,phys_state)==0 { return 0; } }
    if v108_input_overlay_present(process,state,input_state,xhci)==0 { return 0; }
    serial_marker_v108_input_telemetry_ok(); serial_marker_v108_stable_input_diag_ok();
    unsafe { volatile_write64(input_state+3320,volatile_read64(input_state+3224)); volatile_write64(input_state+3336,0); }
    v108_cursor_capture(cursor,surface,volatile_read64(state+8),volatile_read64(state+16));
    var last_usb_r=volatile_read64(input_state+3128); var last_ps2_pk=volatile_read64(input_state+3176); var last_src=volatile_read64(input_state+3104);
    while true {
        if xhci!=0 && volatile_read64(xhci+808)!=0 { if xhci_hid_poll_continuous(xhci,input_state)==0 { return 0; } }
        ps2_poll_fallback(input_state);
        var redraw:u64=0;
        let raw_now=volatile_read64(input_state+3224); if raw_now!=volatile_read64(input_state+3320) { unsafe { volatile_write64(input_state+3320,raw_now); } redraw=1; }
        let usb_now=volatile_read64(input_state+3128); if usb_now!=last_usb_r { last_usb_r=usb_now; redraw=1; }
        let ps2_now=volatile_read64(input_state+3176); if ps2_now!=last_ps2_pk { last_ps2_pk=ps2_now; redraw=1; }
        let src_now=volatile_read64(input_state+3104); if src_now!=last_src { last_src=src_now; redraw=1; }
        let event=input_pop(input_state);
        if event!=0 {
            let kind=volatile_read64(event);
            if kind==4 || kind==5 || kind==6 {
                let oldx=volatile_read64(state+8); let oldy=volatile_read64(state+16);
                if gui_input_dispatch(state,wm,event,surface)!=0 {
                    let newx=volatile_read64(state+8); let newy=volatile_read64(state+16);
                    if (kind==5 || kind==6) && (newx!=oldx || newy!=oldy) {
                        let source=volatile_read64(input_state+3104);
                        if source==1 && volatile_read64(input_state+3112)==0 { unsafe { volatile_write64(input_state+3112,1); } serial_marker_v108_usb_gui_cursor_ok(); }
                        if source==2 && volatile_read64(input_state+3120)==0 { unsafe { volatile_write64(input_state+3120,1); } serial_marker_v108_ps2_gui_cursor_ok(); }
                        v108_cursor_restore(cursor,surface); cursor_move(cursor,surface,(newx*65536)+newy); v108_cursor_capture(cursor,surface,newx,newy); desktop_draw_cursor(surface,newx,newy); v108_cursor_present(process,oldx,oldy,newx,newy);
                        if volatile_read64(input_state+3336)==0 { unsafe { volatile_write64(input_state+3336,1); } serial_marker_v108_physical_cursor_visible_ok(); }
                    }
                    redraw=1;
                }
            }
        }
        if redraw!=0 { if v108_input_overlay_present(process,state,input_state,xhci)==0 { return 0; } }
        cpu_pause();
    }
    return 1;
}
'''
s=s[:start]+new_runtime+s[end:]
p.write_text(s)
out=hashlib.sha256(p.read_bytes()).hexdigest()
print(out)
expected_out='7fc3260909e8b16a64ff39ae51b2eca9f30ec79ebcfbac9e10437a510835d5f6'
if out!=expected_out:
    raise SystemExit(f'unexpected r7 output hash: {out}')
