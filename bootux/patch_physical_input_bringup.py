#!/usr/bin/env python3
from pathlib import Path
import hashlib, sys

if len(sys.argv) != 2:
    raise SystemExit('usage: patch_physical_input_bringup.py PATH_TO_main.nx')
p=Path(sys.argv[1]); raw=p.read_bytes()
expected='cca9a6021c972c9b54269c9ab678c4c7f5503d14b6472b12ba8fb0c76abc6413'
actual=hashlib.sha256(raw).hexdigest()
if actual!=expected:
    raise SystemExit(f'unexpected full-GUI kernel hash: {actual}')
s=raw.decode()

def rep(old,new,label):
    global s
    n=s.count(old)
    if n!=1:
        raise SystemExit(f'{label}: expected 1 site, found {n}')
    s=s.replace(old,new,1)

def marker(name):
    ops='; '.join(f'serial_putc({ord(c)})' for c in name+'\n')
    return f'fn serial_marker_{name.lower()}() -> void {{ {ops}; return; }}\n'

old='''fn xhci_reset_first_port(xhci_state:u64) -> u64 {\n    if xhci_state==0 || volatile_read64(xhci_state+56)!=1 { return 0; } let base=volatile_read64(xhci_state); let op=volatile_read64(xhci_state+8); let hcs1=volatile_read32(base+4); var ports=(hcs1/16777216)%256; if ports>32 { ports=32; }\n    var p:u64=0; while p<ports { let port=op+1024+(p*16); let ps=volatile_read32(port); if ps%2!=0 { var write=xhci_port_write_base(ps); write=set_flag(write,16); unsafe { volatile_write32(port,write); } var spins:u64=0; while (volatile_read32(port)/16)%2!=0 && spins<5000000 { cpu_pause(); spins=spins+1; } if spins<5000000 { let done=volatile_read32(port); if done%2!=0 { unsafe { volatile_write64(xhci_state+112,p+1); volatile_write64(xhci_state+120,done); volatile_write64(xhci_state+128,1); } serial_marker_xhci_port_ready(); return p+1; } } } p=p+1; }\n    return 0;\n}'''
new='''fn xhci_reset_connected_port_from(xhci_state:u64,start:u64) -> u64 {\n    if xhci_state==0 || volatile_read64(xhci_state+56)!=1 { return 0; }\n    let base=volatile_read64(xhci_state); let op=volatile_read64(xhci_state+8); let hcs1=volatile_read32(base+4); var ports=(hcs1/16777216)%256; if ports>32 { ports=32; }\n    var p=start;\n    while p<ports {\n        let port=op+1024+(p*16); let ps=volatile_read32(port);\n        if ps%2!=0 {\n            var write=xhci_port_write_base(ps); write=set_flag(write,16); unsafe { volatile_write32(port,write); }\n            var spins:u64=0; while (volatile_read32(port)/16)%2!=0 && spins<5000000 { cpu_pause(); spins=spins+1; }\n            if spins<5000000 { let done=volatile_read32(port); if done%2!=0 {\n                unsafe { volatile_write64(xhci_state+112,p+1); volatile_write64(xhci_state+120,done); volatile_write64(xhci_state+128,1); volatile_write64(xhci_state+384,0); volatile_write64(xhci_state+416,0); }\n                serial_marker_xhci_port_ready(); return p+1;\n            } }\n        }\n        p=p+1;\n    }\n    return 0;\n}\nfn xhci_reset_first_port(xhci_state:u64) -> u64 { return xhci_reset_connected_port_from(xhci_state,0); }'''
rep(old,new,'xHCI multi-port helper')

oldboot='''if controller_probe_ready != 0 && xhci_state != 0 && phys_state != 0 && volatile_read64(hardware_state+24) != 0 { xhci_ready = xhci_controller_init(hardware_state,phys_state,xhci_state,kernel_pml4); if xhci_ready != 0 { xhci_port_ready = xhci_reset_first_port(xhci_state); if xhci_port_ready != 0 { xhci_slot_ready = xhci_enable_slot(xhci_state); if xhci_slot_ready != 0 { xhci_default_ready = xhci_address_default_device(xhci_state,phys_state); if xhci_default_ready != 0 { xhci_descriptor8_ready = xhci_get_device_descriptor8(xhci_state,phys_state); if xhci_descriptor8_ready != 0 { xhci_addressed_ready = xhci_finalize_address_and_descriptor(xhci_state,phys_state); if xhci_addressed_ready != 0 { usb_hid_found = xhci_discover_boot_hid(xhci_state,phys_state); if usb_hid_found != 0 { usb_hid_configured = xhci_configure_boot_hid(xhci_state,phys_state); if usb_hid_configured != 0 { usb_hid_report_ready = xhci_read_first_hid_report(xhci_state,phys_state); } } } } } } } } }'''
newboot='''if controller_probe_ready != 0 && xhci_state != 0 && phys_state != 0 && volatile_read64(hardware_state+24) != 0 {\n            xhci_ready=xhci_controller_init(hardware_state,phys_state,xhci_state,kernel_pml4);\n            if xhci_ready!=0 {\n                var usb_scan_start:u64=0; var usb_scan_tries:u64=0;\n                while usb_hid_configured==0 && usb_scan_tries<8 {\n                    xhci_port_ready=xhci_reset_connected_port_from(xhci_state,usb_scan_start);\n                    if xhci_port_ready==0 { usb_scan_tries=8; }\n                    else {\n                        usb_scan_start=xhci_port_ready; usb_scan_tries=usb_scan_tries+1;\n                        xhci_slot_ready=xhci_enable_slot(xhci_state);\n                        if xhci_slot_ready!=0 {\n                            xhci_default_ready=xhci_address_default_device(xhci_state,phys_state);\n                            if xhci_default_ready!=0 {\n                                xhci_descriptor8_ready=xhci_get_device_descriptor8(xhci_state,phys_state);\n                                if xhci_descriptor8_ready!=0 {\n                                    xhci_addressed_ready=xhci_finalize_address_and_descriptor(xhci_state,phys_state);\n                                    if xhci_addressed_ready!=0 {\n                                        usb_hid_found=xhci_discover_boot_hid(xhci_state,phys_state);\n                                        if usb_hid_found!=0 {\n                                            usb_hid_configured=xhci_configure_boot_hid(xhci_state,phys_state);\n                                            if usb_hid_configured!=0 { usb_hid_report_ready=1; }\n                                        }\n                                    }\n                                }\n                            }\n                        }\n                    }\n                }\n            }\n        }'''
rep(oldboot,newboot,'USB boot startup handoff + multi-port scan')

olddecode='if input_queue_ready != 0 { if usb_hid_report_ready != 0 { input_decode_ready = input_decode_boot_hid(xhci_state,input_state); } else { ps2_poll_fallback(input_state); } }'
newdecode='if input_queue_ready != 0 { if usb_hid_report_ready != 0 { input_decode_ready = 1; } else { ps2_poll_fallback(input_state); } }'
rep(olddecode,newdecode,'r46 async input handoff')

insert_anchor='fn ps2_poll_fallback(input_state:u64) -> u64 {'
if s.count(insert_anchor)!=1: raise SystemExit('ps2 insert anchor mismatch')
markers=''.join(marker(x) for x in [
    'FRAMES_LIVE_USB_HID_REPORT_OK','FRAMES_LIVE_PS2_PACKET_OK',
    'FRAMES_LIVE_USB_GUI_CURSOR_OK','FRAMES_LIVE_PS2_GUI_CURSOR_OK',
    'FRAMES_PS2_MOUSE_ENABLE_OK'])
ps2_code=r'''
fn ps2_wait_input_clear_live() -> u64 { var spins:u64=0; while spins<2000000 { if (io_read8(100)/2)%2==0 { return 1; } cpu_pause(); spins=spins+1; } return 0; }
fn ps2_wait_output_live() -> u64 { var spins:u64=0; while spins<2000000 { if io_read8(100)%2!=0 { return 1; } cpu_pause(); spins=spins+1; } return 0; }
fn ps2_mouse_command_live(cmd:u64) -> u64 {
    if ps2_wait_input_clear_live()==0 { return 0; } io_write8(100,212);
    if ps2_wait_input_clear_live()==0 { return 0; } io_write8(96,cmd);
    if ps2_wait_output_live()==0 { return 0; } let ack=io_read8(96); if ack!=250 { return 0; } return 1;
}
fn ps2_mouse_enable_live(input_state:u64) -> u64 {
    if input_state==0 { return 0; } if volatile_read64(input_state+3072)==1 { return 1; }
    if ps2_wait_input_clear_live()!=0 { io_write8(100,168); }
    var defaults=ps2_mouse_command_live(246); var enabled=ps2_mouse_command_live(244);
    if enabled!=0 { unsafe { volatile_write64(input_state+3072,1); } serial_marker_frames_ps2_mouse_enable_ok(); return 1; }
    return 0;
}
fn ps2_mouse_resync_live(input_state:u64,data:u64) -> u64 {
    if data==250 || data==170 { return 1; }
    if (data/8)%2!=0 { unsafe { volatile_write64(input_state+3016,1); volatile_write64(input_state+3024,data); } } else { unsafe { volatile_write64(input_state+3016,0); } }
    return 1;
}
fn ps2_mouse_decode_live(input_state:u64,data:u64) -> u64 {
    if input_state==0 { return 0; } let byte=data%256; unsafe { volatile_write64(input_state+3056,volatile_read64(input_state+3056)+1); }
    if byte==250 || byte==170 { return 1; }
    var phase=volatile_read64(input_state+3016);
    if phase==0 { return ps2_mouse_resync_live(input_state,byte); }
    if phase==1 { unsafe { volatile_write64(input_state+3032,byte); volatile_write64(input_state+3016,2); } return 1; }
    let b0=volatile_read64(input_state+3024)%256; let b1=volatile_read64(input_state+3032)%256; let b2=byte;
    unsafe { volatile_write64(input_state+3016,0); }
    let xsign=(b0/16)%2; let ysign=(b0/32)%2; let xhigh=(b1/128)%2; let yhigh=(b2/128)%2; let xov=(b0/64)%2; let yov=(b0/128)%2;
    if (b0/8)%2==0 || xov!=0 || yov!=0 || xsign!=xhigh || ysign!=yhigh { return ps2_mouse_resync_live(input_state,b2); }
    let buttons=b0%8; let yraw=(256-b2)%256;
    unsafe { volatile_write64(input_state+3064,2); volatile_write64(input_state+3040,volatile_read64(input_state+3040)+1); }
    input_push(input_state,4,0,buttons); input_push(input_state,5,0,b1); input_push(input_state,6,0,yraw);
    if volatile_read64(input_state+3080)==0 { unsafe { volatile_write64(input_state+3080,1); } serial_marker_frames_live_ps2_packet_ok(); }
    return 1;
}
'''
s=s.replace(insert_anchor,markers+ps2_code+insert_anchor,1)

oldpoll='''fn ps2_poll_fallback(input_state:u64) -> u64 {\n    if input_state==0 || volatile_read64(input_state+32)!=1 { return 0; } let status=io_read8(100); if status%2==0 { return 0; } let data=io_read8(96); if (status/32)%2!=0 { input_push(input_state,8,0,data); } else { input_push(input_state,7,data,1); } unsafe { volatile_write64(input_state+56,1); } return 1;\n}'''
newpoll='''fn ps2_poll_fallback(input_state:u64) -> u64 {\n    if input_state==0 || volatile_read64(input_state+32)!=1 { return 0; } let status=io_read8(100); if status%2==0 { return 0; } let data=io_read8(96); if (status/32)%2!=0 { ps2_mouse_decode_live(input_state,data); } else { input_push(input_state,7,data,1); } unsafe { volatile_write64(input_state+56,1); } return 1;\n}'''
rep(oldpoll,newpoll,'PS2 raw-byte decoder hookup')

oldmouse='''    } else {\n        if protocol!=2 || actual<3 { return 0; } input_push(input_state,4,0,volatile_read8(buffer)); input_push(input_state,5,0,volatile_read8(buffer+1)); input_push(input_state,6,0,volatile_read8(buffer+2));\n    }'''
newmouse='''    } else {\n        if protocol!=2 || actual<3 { return 0; } unsafe { volatile_write64(input_state+3064,1); } input_push(input_state,4,0,volatile_read8(buffer)); input_push(input_state,5,0,volatile_read8(buffer+1)); input_push(input_state,6,0,volatile_read8(buffer+2)); if volatile_read64(input_state+3088)==0 { unsafe { volatile_write64(input_state+3088,1); } serial_marker_frames_live_usb_hid_report_ok(); }\n    }'''
rep(oldmouse,newmouse,'USB live report provenance')

oldruntime='''fn desktop_input_runtime(process:u64,input_state:u64,phys_state:u64,hardware_state:u64) -> u64 {\n    if process==0 || input_state==0 || phys_state==0 || hardware_state==0 { return 0; } let state=volatile_read64(process+1080); let wm=volatile_read64(process+1072); let surface=volatile_read64(process+616); let cursor=volatile_read64(process+640); let dirty=volatile_read64(process+624); let xhci=volatile_read64(input_state+3008); if state==0 || wm==0 || surface==0 || cursor==0 { return 0; }\n    if xhci!=0 && volatile_read64(xhci+416)==1 { if xhci_hid_arm_continuous(xhci,phys_state)==0 { return 0; } }\n    while true { if xhci!=0 && volatile_read64(xhci+808)!=0 { if xhci_hid_poll_continuous(xhci,input_state)==0 { return 0; } } ps2_poll_fallback(input_state); let event=input_pop(input_state); if event!=0 { if gui_input_dispatch(state,wm,event,surface)!=0 { if volatile_read64(event)==4 { desktop_shell_click(process,state,volatile_read64(event+16)); appearance_handle_click(process,state,volatile_read64(event+16)); } cursor_move(cursor,surface,(volatile_read64(state+8)*65536)+volatile_read64(state+16)); if volatile_read64(process+1160)!=0 { appearance_render(process); } else { wm_render_all(wm,surface,dirty); let shell=volatile_read64(process+1088); if shell!=0 { desktop_shell_draw(shell,surface,wm,0); desktop_shell_launcher_draw(shell,surface); } desktop_draw_cursor(surface,volatile_read64(state+8),volatile_read64(state+16)); } } } cpu_pause(); }\n    return 1;\n}'''
newruntime='''fn desktop_input_runtime(process:u64,input_state:u64,phys_state:u64,hardware_state:u64) -> u64 {\n    if process==0 || input_state==0 || phys_state==0 || hardware_state==0 { return 0; } let state=volatile_read64(process+1080); let wm=volatile_read64(process+1072); let surface=volatile_read64(process+616); let cursor=volatile_read64(process+640); let dirty=volatile_read64(process+624); let xhci=volatile_read64(input_state+3008); if state==0 || wm==0 || surface==0 || cursor==0 { return 0; }\n    ps2_mouse_enable_live(input_state);\n    if xhci!=0 && volatile_read64(xhci+416)==1 { if xhci_hid_arm_continuous(xhci,phys_state)==0 { return 0; } }\n    while true {\n        if xhci!=0 && volatile_read64(xhci+808)!=0 { if xhci_hid_poll_continuous(xhci,input_state)==0 { return 0; } }\n        ps2_poll_fallback(input_state); let event=input_pop(input_state);\n        if event!=0 {\n            let oldx=volatile_read64(state+8); let oldy=volatile_read64(state+16); let kind=volatile_read64(event);\n            if gui_input_dispatch(state,wm,event,surface)!=0 {\n                if kind==4 { desktop_shell_click(process,state,volatile_read64(event+16)); appearance_handle_click(process,state,volatile_read64(event+16)); }\n                let newx=volatile_read64(state+8); let newy=volatile_read64(state+16);\n                if (kind==5 || kind==6) && (newx!=oldx || newy!=oldy) {\n                    let source=volatile_read64(input_state+3064);\n                    if source==1 && volatile_read64(input_state+3096)==0 { unsafe { volatile_write64(input_state+3096,1); } serial_marker_frames_live_usb_gui_cursor_ok(); }\n                    if source==2 && volatile_read64(input_state+3104)==0 { unsafe { volatile_write64(input_state+3104,1); } serial_marker_frames_live_ps2_gui_cursor_ok(); }\n                }\n                cursor_move(cursor,surface,(newx*65536)+newy);\n                if volatile_read64(process+1160)!=0 { appearance_render(process); } else { wm_render_all(wm,surface,dirty); let shell=volatile_read64(process+1088); if shell!=0 { desktop_shell_draw(shell,surface,wm,0); desktop_shell_launcher_draw(shell,surface); } desktop_draw_cursor(surface,newx,newy); }\n            }\n        }\n        cpu_pause();\n    }\n    return 1;\n}'''
rep(oldruntime,newruntime,'desktop live input runtime instrumentation')

oldphys='if gui_physical_test_mode!=0 { if full_interactive_desktop_compose(appearance_state,display_state,process_state,window_manager_state)==0 { serial_marker_desktop_cert_fail(); return; } serial_marker_frames_integrated_gui_ok(); serial_marker_gui_physical_test_ready(); return; }'
newphys='if gui_physical_test_mode!=0 { if full_interactive_desktop_compose(appearance_state,display_state,process_state,window_manager_state)==0 { serial_marker_desktop_cert_fail(); return; } serial_marker_frames_integrated_gui_ok(); serial_marker_gui_physical_test_ready(); unsafe { volatile_write64(process_state+1160,0); } if desktop_input_runtime(process_state,input_state,phys_state,hardware_state)==0 { serial_marker_desktop_cert_fail(); return; } return; }'
rep(oldphys,newphys,'physical GUI must enter live runtime')

p.write_text(s)
print('patched',p,'sha256',hashlib.sha256(p.read_bytes()).hexdigest())
