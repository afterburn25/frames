#!/usr/bin/env python3
from pathlib import Path
import subprocess, sys

p=Path(sys.argv[1])
subprocess.check_call([sys.executable, str(Path(__file__).with_name('make_r53b_input_protocol_id.py')), str(p)])
s=p.read_text()

def rep(old,new,label):
    global s
    n=s.count(old)
    if n!=1:
        raise SystemExit(f'{label}: expected 1 site, found {n}')
    s=s.replace(old,new)

rep('pointer_diag_draw_tag4(surface,(78*65536)+18,82+(53*256)+(51*65536)+(66*16777216),green);    // R53B',
    'pointer_diag_draw_tag4(surface,(78*65536)+18,82+(53*256)+(52*65536)+(32*16777216),green);    // R54',
    'title')

old_fn='''fn xhci_reset_first_port(xhci_state:u64) -> u64 {\n    if xhci_state==0 || volatile_read64(xhci_state+56)!=1 { return 0; } let base=volatile_read64(xhci_state); let op=volatile_read64(xhci_state+8); let hcs1=volatile_read32(base+4); var ports=(hcs1/16777216)%256; if ports>32 { ports=32; }\n    var p:u64=0; while p<ports { let port=op+1024+(p*16); let ps=volatile_read32(port); if ps%2!=0 { var write=xhci_port_write_base(ps); write=set_flag(write,16); unsafe { volatile_write32(port,write); } var spins:u64=0; while (volatile_read32(port)/16)%2!=0 && spins<5000000 { cpu_pause(); spins=spins+1; } if spins<5000000 { let done=volatile_read32(port); if done%2!=0 { unsafe { volatile_write64(xhci_state+112,p+1); volatile_write64(xhci_state+120,done); volatile_write64(xhci_state+128,1); } serial_marker_xhci_port_ready(); return p+1; } } } p=p+1; }\n    return 0;\n}'''
new_fn='''fn xhci_reset_connected_port_from(xhci_state:u64,start:u64) -> u64 {\n    if xhci_state==0 || volatile_read64(xhci_state+56)!=1 { return 0; }\n    let base=volatile_read64(xhci_state); let op=volatile_read64(xhci_state+8); let hcs1=volatile_read32(base+4); var ports=(hcs1/16777216)%256; if ports>32 { ports=32; }\n    var p=start;\n    while p<ports {\n        let port=op+1024+(p*16); let ps=volatile_read32(port);\n        if ps%2!=0 {\n            var write=xhci_port_write_base(ps); write=set_flag(write,16); unsafe { volatile_write32(port,write); }\n            var spins:u64=0; while (volatile_read32(port)/16)%2!=0 && spins<5000000 { cpu_pause(); spins=spins+1; }\n            if spins<5000000 { let done=volatile_read32(port); if done%2!=0 {\n                unsafe { volatile_write64(xhci_state+112,p+1); volatile_write64(xhci_state+120,done); volatile_write64(xhci_state+128,1); volatile_write64(xhci_state+384,0); volatile_write64(xhci_state+416,0); }\n                serial_marker_xhci_port_ready(); return p+1;\n            } }\n        }\n        p=p+1;\n    }\n    return 0;\n}\nfn xhci_reset_first_port(xhci_state:u64) -> u64 { return xhci_reset_connected_port_from(xhci_state,0); }'''
rep(old_fn,new_fn,'multi-port reset helper')

old_boot='''if controller_probe_ready != 0 && xhci_state != 0 && phys_state != 0 && volatile_read64(hardware_state+24) != 0 { xhci_ready = xhci_controller_init(hardware_state,phys_state,xhci_state,kernel_pml4); if xhci_ready != 0 { xhci_port_ready = xhci_reset_first_port(xhci_state); if xhci_port_ready != 0 { xhci_slot_ready = xhci_enable_slot(xhci_state); if xhci_slot_ready != 0 { xhci_default_ready = xhci_address_default_device(xhci_state,phys_state); if xhci_default_ready != 0 { xhci_descriptor8_ready = xhci_get_device_descriptor8(xhci_state,phys_state); if xhci_descriptor8_ready != 0 { xhci_addressed_ready = xhci_finalize_address_and_descriptor(xhci_state,phys_state); if xhci_addressed_ready != 0 { usb_hid_found = xhci_discover_boot_hid(xhci_state,phys_state); if usb_hid_found != 0 { usb_hid_configured = xhci_configure_boot_hid(xhci_state,phys_state); if usb_hid_configured != 0 { usb_hid_report_ready = 1; } } } } } } } } }'''
new_boot='''if controller_probe_ready != 0 && xhci_state != 0 && phys_state != 0 && volatile_read64(hardware_state+24) != 0 {\n            xhci_ready = xhci_controller_init(hardware_state,phys_state,xhci_state,kernel_pml4);\n            if xhci_ready != 0 {\n                // r54 physical repair: do not assume the first connected xHCI port is HID.\n                // On USB-booted hardware it is frequently the Frames flash drive. Walk\n                // connected root ports until a boot-HID interface is discovered/configured.\n                var usb_scan_start:u64=0; var usb_scan_tries:u64=0;\n                while usb_hid_configured==0 && usb_scan_tries<8 {\n                    xhci_port_ready=xhci_reset_connected_port_from(xhci_state,usb_scan_start);\n                    if xhci_port_ready==0 { usb_scan_tries=8; }\n                    else {\n                        usb_scan_start=xhci_port_ready; usb_scan_tries=usb_scan_tries+1;\n                        xhci_slot_ready=xhci_enable_slot(xhci_state);\n                        if xhci_slot_ready!=0 {\n                            xhci_default_ready=xhci_address_default_device(xhci_state,phys_state);\n                            if xhci_default_ready!=0 {\n                                xhci_descriptor8_ready=xhci_get_device_descriptor8(xhci_state,phys_state);\n                                if xhci_descriptor8_ready!=0 {\n                                    xhci_addressed_ready=xhci_finalize_address_and_descriptor(xhci_state,phys_state);\n                                    if xhci_addressed_ready!=0 {\n                                        usb_hid_found=xhci_discover_boot_hid(xhci_state,phys_state);\n                                        if usb_hid_found!=0 {\n                                            usb_hid_configured=xhci_configure_boot_hid(xhci_state,phys_state);\n                                            if usb_hid_configured!=0 { usb_hid_report_ready=1; }\n                                        }\n                                    }\n                                }\n                            }\n                        }\n                    }\n                }\n            }\n        }'''
rep(old_boot,new_boot,'boot HID multi-port scan')

# Re-purpose the two report-byte rows while configuration is the focus.
rep('pointer_diag_row(surface,(330*65536)+194,540156501,u0b);                                                                    // U0B ',
    'pointer_diag_row(surface,(330*65536)+194,1380929621,volatile_read64(r53b_xhci+112));                                      // UPOR',
    'USB port row')
rep('pointer_diag_row(surface,(330*65536)+206,540222037,u1b);                                                                    // U1B ',
    'pointer_diag_row(surface,(330*65536)+206,1145656661,volatile_read64(r53b_xhci+272));                                      // UVID',
    'USB VID row')

p.write_text(s)
