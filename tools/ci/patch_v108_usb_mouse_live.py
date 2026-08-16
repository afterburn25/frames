#!/usr/bin/env python3
from pathlib import Path
import hashlib,sys
p=Path(sys.argv[1]); s=p.read_text()
if 'serial_marker_v108_usb_gui_cursor_ok' not in s or 'fn v108_input_backend_prepare' not in s:
    raise SystemExit('apply patch_v108_live_input_common.py first')
if 'input_state+3128' in s:
    raise SystemExit('USB report proof offset already in use')

def rep(old,new,label):
    global s
    n=s.count(old)
    if n!=1: raise SystemExit(f'{label}: expected 1 site, found {n}')
    s=s.replace(old,new,1)

old_fn='''fn xhci_reset_first_port(xhci_state:u64) -> u64 {
    if xhci_state==0 || volatile_read64(xhci_state+56)!=1 { return 0; } let base=volatile_read64(xhci_state); let op=volatile_read64(xhci_state+8); let hcs1=volatile_read32(base+4); var ports=(hcs1/16777216)%256; if ports>32 { ports=32; }
    var p:u64=0; while p<ports { let port=op+1024+(p*16); let ps=volatile_read32(port); if ps%2!=0 { var write=xhci_port_write_base(ps); write=set_flag(write,16); unsafe { volatile_write32(port,write); } var spins:u64=0; while (volatile_read32(port)/16)%2!=0 && spins<5000000 { cpu_pause(); spins=spins+1; } if spins<5000000 { let done=volatile_read32(port); if done%2!=0 { unsafe { volatile_write64(xhci_state+112,p+1); volatile_write64(xhci_state+120,done); volatile_write64(xhci_state+128,1); } serial_marker_xhci_port_ready(); return p+1; } } } p=p+1; }
    return 0;
}'''
new_fn='''fn xhci_reset_connected_port_from(xhci_state:u64,start:u64) -> u64 {
    if xhci_state==0 || volatile_read64(xhci_state+56)!=1 { return 0; }
    let base=volatile_read64(xhci_state); let op=volatile_read64(xhci_state+8); let hcs1=volatile_read32(base+4); var ports=(hcs1/16777216)%256; if ports>32 { ports=32; }
    var p=start;
    while p<ports {
        let port=op+1024+(p*16); let ps=volatile_read32(port);
        if ps%2!=0 {
            var write=xhci_port_write_base(ps); write=set_flag(write,16); unsafe { volatile_write32(port,write); }
            var spins:u64=0; while (volatile_read32(port)/16)%2!=0 && spins<5000000 { cpu_pause(); spins=spins+1; }
            if spins<5000000 { let done=volatile_read32(port); if done%2!=0 {
                unsafe { volatile_write64(xhci_state+112,p+1); volatile_write64(xhci_state+120,done); volatile_write64(xhci_state+128,1); volatile_write64(xhci_state+384,0); volatile_write64(xhci_state+416,0); }
                serial_marker_xhci_port_ready(); return p+1;
            } }
        }
        p=p+1;
    }
    return 0;
}
fn xhci_reset_first_port(xhci_state:u64) -> u64 { return xhci_reset_connected_port_from(xhci_state,0); }'''
rep(old_fn,new_fn,'xHCI multi-port helper')

old_boot='''if controller_probe_ready != 0 && xhci_state != 0 && phys_state != 0 && volatile_read64(hardware_state+24) != 0 { xhci_ready = xhci_controller_init(hardware_state,phys_state,xhci_state,kernel_pml4); if xhci_ready != 0 { xhci_port_ready = xhci_reset_first_port(xhci_state); if xhci_port_ready != 0 { xhci_slot_ready = xhci_enable_slot(xhci_state); if xhci_slot_ready != 0 { xhci_default_ready = xhci_address_default_device(xhci_state,phys_state); if xhci_default_ready != 0 { xhci_descriptor8_ready = xhci_get_device_descriptor8(xhci_state,phys_state); if xhci_descriptor8_ready != 0 { xhci_addressed_ready = xhci_finalize_address_and_descriptor(xhci_state,phys_state); if xhci_addressed_ready != 0 { usb_hid_found = xhci_discover_boot_hid(xhci_state,phys_state); if usb_hid_found != 0 { usb_hid_configured = xhci_configure_boot_hid(xhci_state,phys_state); if usb_hid_configured != 0 { usb_hid_report_ready = xhci_read_first_hid_report(xhci_state,phys_state); } } } } } } } } }'''
new_boot='''if controller_probe_ready != 0 && xhci_state != 0 && phys_state != 0 && volatile_read64(hardware_state+24) != 0 {
            xhci_ready=xhci_controller_init(hardware_state,phys_state,xhci_state,kernel_pml4);
            if xhci_ready!=0 {
                var usb_scan_start:u64=0; var usb_scan_tries:u64=0;
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
                }
            }
        }'''
rep(old_boot,new_boot,'r46+r54 startup handoff')

rep('if input_queue_ready != 0 { if usb_hid_report_ready != 0 { input_decode_ready = input_decode_boot_hid(xhci_state,input_state); } else { ps2_poll_fallback(input_state); } }',
    'if input_queue_ready != 0 { if usb_hid_report_ready != 0 { input_decode_ready = 1; } else { ps2_poll_fallback(input_state); } }',
    'r46 one-shot decode removal')

old_mouse='if protocol!=2 || actual<3 { return 0; } input_push(input_state,4,0,volatile_read8(buffer)); input_push(input_state,5,0,volatile_read8(buffer+1)); input_push(input_state,6,0,volatile_read8(buffer+2));'
new_mouse='if protocol!=2 || actual<3 { return 0; } unsafe { volatile_write64(input_state+3104,1); } if volatile_read64(input_state+3128)==0 { unsafe { volatile_write64(input_state+3128,1); } serial_marker_v108_usb_live_report_ok(); } input_push(input_state,4,0,volatile_read8(buffer)); input_push(input_state,5,0,volatile_read8(buffer+1)); input_push(input_state,6,0,volatile_read8(buffer+2));'
rep(old_mouse,new_mouse,'USB live report provenance')

p.write_text(s)
print(hashlib.sha256(p.read_bytes()).hexdigest())
