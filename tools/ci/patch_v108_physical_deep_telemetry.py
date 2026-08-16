#!/usr/bin/env python3
from pathlib import Path
import hashlib,sys

p=Path(sys.argv[1]); raw=p.read_bytes()
expected='8cf33253489331e200643fa004992fece4eaf86b6feccaa3e00c06883927f675'
actual=hashlib.sha256(raw).hexdigest()
if actual!=expected:
    raise SystemExit(f'unexpected v108 physical-input-r2 kernel hash: {actual}')
s=raw.decode()
for off in range(3192,3330,8):
    if f'input_state+{off}' in s:
        raise SystemExit(f'deep telemetry state offset already used: {off}')

def text_fn(name,text):
    ops=[]
    for i,c in enumerate(text):
        ops.append(f'if gui_draw_char_scaled(surface,((x+{i*6})*65536)+y,({ord(c)}*65536)+1,color)==0 {{ return 0; }}')
    return f"fn {name}(surface:u64,x:u64,y:u64,color:u64) -> u64 {{ {' '.join(ops)} return 1; }}\n"

old='''var usb_scan_start:u64=0; var usb_scan_tries:u64=0;
                while usb_hid_configured==0 && usb_scan_tries<8 {
                    xhci_port_ready=xhci_reset_connected_port_from(xhci_state,usb_scan_start);
                    if xhci_port_ready==0 { usb_scan_tries=8; }
                    else {
                        usb_scan_start=xhci_port_ready; usb_scan_tries=usb_scan_tries+1;
                        xhci_slot_ready=xhci_enable_slot(xhci_state);
                        if xhci_slot_ready!=0 {
                            xhci_default_ready=xhci_address_default_device(xhci_state,phys_state);
                            if xhci_default_ready!=0 {
                                xhci_descriptor8_ready=xhci_get_device_descriptor8(xhci_state,phys_state);
                                if xhci_descriptor8_ready!=0 {
                                    xhci_addressed_ready=xhci_finalize_address_and_descriptor(xhci_state,phys_state);
                                    if xhci_addressed_ready!=0 {
                                        usb_hid_found=xhci_discover_boot_hid(xhci_state,phys_state);
                                        if usb_hid_found!=0 {
                                            usb_hid_configured=xhci_configure_boot_hid(xhci_state,phys_state);
                                            if usb_hid_configured!=0 { usb_hid_report_ready=1; }
                                        }
                                    }
                                }
                            }
                        }
                    }
                }'''
new='''var usb_scan_start:u64=0; var usb_scan_tries:u64=0;
                unsafe { volatile_write64(input_state+3192,1); volatile_write64(input_state+3200,0); volatile_write64(input_state+3208,0); volatile_write64(input_state+3216,0); }
                while usb_hid_configured==0 && usb_scan_tries<8 {
                    xhci_port_ready=xhci_reset_connected_port_from(xhci_state,usb_scan_start);
                    if xhci_port_ready==0 { usb_scan_tries=8; unsafe { volatile_write64(input_state+3200,usb_scan_tries); } }
                    else {
                        usb_scan_start=xhci_port_ready; usb_scan_tries=usb_scan_tries+1;
                        unsafe { volatile_write64(input_state+3192,2); volatile_write64(input_state+3200,usb_scan_tries); volatile_write64(input_state+3208,xhci_port_ready); }
                        xhci_slot_ready=xhci_enable_slot(xhci_state);
                        if xhci_slot_ready!=0 {
                            unsafe { volatile_write64(input_state+3192,3); }
                            xhci_default_ready=xhci_address_default_device(xhci_state,phys_state);
                            if xhci_default_ready!=0 {
                                unsafe { volatile_write64(input_state+3192,4); }
                                xhci_descriptor8_ready=xhci_get_device_descriptor8(xhci_state,phys_state);
                                if xhci_descriptor8_ready!=0 {
                                    unsafe { volatile_write64(input_state+3192,5); }
                                    xhci_addressed_ready=xhci_finalize_address_and_descriptor(xhci_state,phys_state);
                                    if xhci_addressed_ready!=0 {
                                        let v108_desc=volatile_read64(xhci_state+264); var v108_class:u64=0; if v108_desc!=0 { v108_class=volatile_read8(v108_desc+4); }
                                        unsafe { volatile_write64(input_state+3192,6); volatile_write64(input_state+3216,v108_class); }
                                        usb_hid_found=xhci_discover_boot_hid(xhci_state,phys_state);
                                        if usb_hid_found!=0 {
                                            unsafe { volatile_write64(input_state+3192,7); }
                                            usb_hid_configured=xhci_configure_boot_hid(xhci_state,phys_state);
                                            if usb_hid_configured!=0 { usb_hid_report_ready=1; unsafe { volatile_write64(input_state+3192,8); } }
                                        }
                                    }
                                }
                            }
                        }
                    }
                }'''
if s.count(old)!=1: raise SystemExit(f'USB scan anchor mismatch: {s.count(old)}')
s=s.replace(old,new,1)

old='''fn ps2_mouse_resync_v108(input_state:u64,data:u64) -> u64 {
    if (data/8)%2!=0 { unsafe { volatile_write64(input_state+3152,data%256); volatile_write64(input_state+3144,1); } }
    else { unsafe { volatile_write64(input_state+3144,0); } }
    return 1;
}'''
new='''fn ps2_mouse_resync_v108(input_state:u64,data:u64) -> u64 {
    if (data/8)%2!=0 { unsafe { volatile_write64(input_state+3152,data%256); volatile_write64(input_state+3144,1); volatile_write64(input_state+3264,volatile_read64(input_state+3264)+1); } }
    else { unsafe { volatile_write64(input_state+3144,0); volatile_write64(input_state+3272,volatile_read64(input_state+3272)+1); } }
    return 1;
}'''
if s.count(old)!=1: raise SystemExit(f'PS2 resync anchor mismatch: {s.count(old)}')
s=s.replace(old,new,1)

old='''    let header=volatile_read64(input_state+3152)%256; let dx=volatile_read64(input_state+3160)%256; let dy=byte;
    unsafe { volatile_write64(input_state+3144,0); }
    if (header/8)%2==0 || (header/64)%2!=0 || (header/128)%2!=0 { return ps2_mouse_resync_v108(input_state,dy); }
    let xsign=(header/16)%2; let ysign=(header/32)%2;
    if xsign!=(dx/128)%2 || ysign!=(dy/128)%2 { return ps2_mouse_resync_v108(input_state,dy); }'''
new='''    let header=volatile_read64(input_state+3152)%256; let dx=volatile_read64(input_state+3160)%256; let dy=byte;
    unsafe { volatile_write64(input_state+3144,0); volatile_write64(input_state+3296,header); volatile_write64(input_state+3304,dx); volatile_write64(input_state+3312,dy); }
    if (header/8)%2==0 || (header/64)%2!=0 || (header/128)%2!=0 { unsafe { volatile_write64(input_state+3280,volatile_read64(input_state+3280)+1); } return ps2_mouse_resync_v108(input_state,dy); }
    let xsign=(header/16)%2; let ysign=(header/32)%2;
    if xsign!=(dx/128)%2 || ysign!=(dy/128)%2 { unsafe { volatile_write64(input_state+3288,volatile_read64(input_state+3288)+1); } return ps2_mouse_resync_v108(input_state,dy); }'''
if s.count(old)!=1: raise SystemExit(f'PS2 decoder anchor mismatch: {s.count(old)}')
s=s.replace(old,new,1)

old='''fn ps2_poll_fallback(input_state:u64) -> u64 {
    if input_state==0 || volatile_read64(input_state+32)!=1 { return 0; }
    let status=io_read8(100); if status%2==0 { return 0; } let data=io_read8(96);
    if (status/32)%2!=0 { ps2_mouse_decode_v108(input_state,data); } else { input_push(input_state,7,data,1); }
    unsafe { volatile_write64(input_state+56,1); } return 1;
}'''
new='''fn ps2_poll_fallback(input_state:u64) -> u64 {
    if input_state==0 || volatile_read64(input_state+32)!=1 { return 0; }
    let status=io_read8(100); if status%2==0 { return 0; } let data=io_read8(96);
    unsafe { volatile_write64(input_state+3224,volatile_read64(input_state+3224)+1); volatile_write64(input_state+3248,status); volatile_write64(input_state+3256,data); }
    if (status/32)%2!=0 { unsafe { volatile_write64(input_state+3232,volatile_read64(input_state+3232)+1); } ps2_mouse_decode_v108(input_state,data); }
    else { unsafe { volatile_write64(input_state+3240,volatile_read64(input_state+3240)+1); } input_push(input_state,7,data,1); }
    unsafe { volatile_write64(input_state+56,1); } return 1;
}'''
if s.count(old)!=1: raise SystemExit(f'PS2 poll anchor mismatch: {s.count(old)}')
s=s.replace(old,new,1)

anchor='fn v108_input_overlay_draw(surface:u64,state:u64,input_state:u64,xhci:u64) -> u64 {'
if s.count(anchor)!=1: raise SystemExit(f'overlay anchor mismatch: {s.count(anchor)}')
labels=(text_fn('v108_text_us2','USB S T C')+
        text_fn('v108_text_p2raw','P2 O A K')+
        text_fn('v108_text_p2dec','P2 R PH PK')+
        text_fn('v108_text_p2rej','P2 SY R1 R2')+
        text_fn('v108_text_p2lst','P2 B0 B1 B2'))
s=s.replace(anchor,labels+anchor,1)

start=s.index('fn v108_input_overlay_draw')
end=s.index('fn v108_input_overlay_present',start)
draw='''fn v108_input_overlay_draw(surface:u64,state:u64,input_state:u64,xhci:u64) -> u64 {
    if surface==0 || state==0 || input_state==0 { return 0; }
    let w=volatile_read64(surface+16); var px:u64=8; if w>430 { px=w-420; }
    let py:u64=8; let bg:u64=4279308561; let edge:u64=4283268350; let white:u64=4294244347; let green:u64=4286644030; let amber:u64=4294934528; let red:u64=4294907956;
    if display_fill_rect(surface,(px*65536)+py,(410*65536)+184,bg)==0 { return 0; }
    display_fill_rect(surface,(px*65536)+py,(410*65536)+2,edge); display_fill_rect(surface,(px*65536)+(py+182),(410*65536)+2,edge);
    v108_text_input(surface,px+10,py+8,white);
    v108_text_usb(surface,px+10,py+28,white);
    var usb_h:u64=0; var usb_p:u64=0; var usb_q:u64=0; if xhci!=0 { usb_h=volatile_read64(xhci+416); usb_p=volatile_read64(xhci+112); usb_q=volatile_read64(xhci+816); }
    let usb_r=volatile_read64(input_state+3128);
    v108_draw_small_u64(surface,((px+82)*65536)+(py+28),usb_h,green); v108_draw_small_u64(surface,((px+130)*65536)+(py+28),usb_r,green); v108_draw_small_u64(surface,((px+178)*65536)+(py+28),usb_p,amber);
    v108_text_us2(surface,px+10,py+46,white);
    v108_draw_small_u64(surface,((px+82)*65536)+(py+46),volatile_read64(input_state+3192),amber); v108_draw_small_u64(surface,((px+130)*65536)+(py+46),volatile_read64(input_state+3200),white); v108_draw_small_u64(surface,((px+178)*65536)+(py+46),volatile_read64(input_state+3216),white); v108_draw_small_u64(surface,((px+232)*65536)+(py+46),usb_q,green);
    v108_text_ps2(surface,px+10,py+64,white); v108_draw_small_u64(surface,((px+82)*65536)+(py+64),volatile_read64(input_state+3136),green); v108_draw_small_u64(surface,((px+142)*65536)+(py+64),volatile_read64(input_state+3176),green);
    v108_text_p2raw(surface,px+10,py+82,white); v108_draw_small_u64(surface,((px+82)*65536)+(py+82),volatile_read64(input_state+3224),white); v108_draw_small_u64(surface,((px+148)*65536)+(py+82),volatile_read64(input_state+3232),green); v108_draw_small_u64(surface,((px+214)*65536)+(py+82),volatile_read64(input_state+3240),red);
    v108_text_p2dec(surface,px+10,py+100,white); v108_draw_small_u64(surface,((px+82)*65536)+(py+100),volatile_read64(input_state+3184),white); v108_draw_small_u64(surface,((px+148)*65536)+(py+100),volatile_read64(input_state+3144),amber); v108_draw_small_u64(surface,((px+214)*65536)+(py+100),volatile_read64(input_state+3176),green);
    v108_text_p2rej(surface,px+10,py+118,white); v108_draw_small_u64(surface,((px+82)*65536)+(py+118),volatile_read64(input_state+3264),white); v108_draw_small_u64(surface,((px+148)*65536)+(py+118),volatile_read64(input_state+3272)+volatile_read64(input_state+3280),red); v108_draw_small_u64(surface,((px+214)*65536)+(py+118),volatile_read64(input_state+3288),red);
    v108_text_p2lst(surface,px+10,py+136,white); v108_draw_small_u64(surface,((px+82)*65536)+(py+136),volatile_read64(input_state+3296),white); v108_draw_small_u64(surface,((px+148)*65536)+(py+136),volatile_read64(input_state+3304),white); v108_draw_small_u64(surface,((px+214)*65536)+(py+136),volatile_read64(input_state+3312),white);
    v108_text_src(surface,px+10,py+154,white); v108_draw_small_u64(surface,((px+58)*65536)+(py+154),volatile_read64(input_state+3104),amber); v108_draw_small_u64(surface,((px+112)*65536)+(py+154),volatile_read64(state+8),white); v108_draw_small_u64(surface,((px+220)*65536)+(py+154),volatile_read64(state+16),white);
    return 1;
}
'''
s=s[:start]+draw+s[end:]

start=s.index('fn v108_input_overlay_present')
end=s.index('fn desktop_input_runtime',start)
present='''fn v108_input_overlay_present(process:u64,state:u64,input_state:u64,xhci:u64) -> u64 {
    let surface=volatile_read64(process+616); if surface==0 { return 0; }
    if v108_input_overlay_draw(surface,state,input_state,xhci)==0 { return 0; }
    let dirty=volatile_read64(process+624); let timing=volatile_read64(process+664); let present=volatile_read64(process+672); let w=volatile_read64(surface+16); var px:u64=8; if w>430 { px=w-420; }
    if dirty==0 || timing==0 || present==0 { return 0; }
    if dirty_add(dirty,(px*65536)+8,(410*65536)+184,16)==0 { return 0; }
    if present_enqueue(present,(px*65536)+8,(410*65536)+184,16)==0 { return 0; }
    if present_flush(present,surface,timing)==0 { return 0; }
    return 1;
}
'''
s=s[:start]+present+s[end:]

old='''        ps2_poll_fallback(input_state);
        let event=input_pop(input_state);'''
new='''        ps2_poll_fallback(input_state);
        let v108_raw_now=volatile_read64(input_state+3224);
        if v108_raw_now!=volatile_read64(input_state+3320) { unsafe { volatile_write64(input_state+3320,v108_raw_now); } if v108_input_overlay_present(process,state,input_state,xhci)==0 { return 0; } }
        let event=input_pop(input_state);'''
if s.count(old)!=1: raise SystemExit(f'raw-refresh runtime anchor mismatch: {s.count(old)}')
s=s.replace(old,new,1)

p.write_text(s)
print(hashlib.sha256(p.read_bytes()).hexdigest())
