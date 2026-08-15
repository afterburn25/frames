#!/usr/bin/env python3
from pathlib import Path
import subprocess, sys

p=Path(sys.argv[1])
subprocess.check_call([sys.executable, str(Path(__file__).with_name('make_r54_usb_multiport_hid.py')), str(p)])
s=p.read_text()

def rep(old,new,label):
    global s
    n=s.count(old)
    if n!=1:
        raise SystemExit(f'{label}: expected 1 site, found {n}')
    s=s.replace(old,new)

rep('pointer_diag_draw_tag4(surface,(78*65536)+18,82+(53*256)+(52*65536)+(32*16777216),green);    // R54',
    'pointer_diag_draw_tag4(surface,(78*65536)+18,82+(53*256)+(53*65536)+(32*16777216),green);    // R55',
    'title')

# Persist the deepest USB-enumeration stage reached plus scan-attempt count in the
# existing diagnostic state. This is observational only; it does not alter USB flow.
# r55 hands-on goal: identify the first failing xHCI enumeration boundary on real hardware.
old='''                var usb_scan_start:u64=0; var usb_scan_tries:u64=0;\n                while usb_hid_configured==0 && usb_scan_tries<8 {\n                    xhci_port_ready=xhci_reset_connected_port_from(xhci_state,usb_scan_start);\n                    if xhci_port_ready==0 { usb_scan_tries=8; }\n                    else {\n                        usb_scan_start=xhci_port_ready; usb_scan_tries=usb_scan_tries+1;\n                        xhci_slot_ready=xhci_enable_slot(xhci_state);\n                        if xhci_slot_ready!=0 {\n                            xhci_default_ready=xhci_address_default_device(xhci_state,phys_state);\n                            if xhci_default_ready!=0 {\n                                xhci_descriptor8_ready=xhci_get_device_descriptor8(xhci_state,phys_state);\n                                if xhci_descriptor8_ready!=0 {\n                                    xhci_addressed_ready=xhci_finalize_address_and_descriptor(xhci_state,phys_state);\n                                    if xhci_addressed_ready!=0 {\n                                        usb_hid_found=xhci_discover_boot_hid(xhci_state,phys_state);\n                                        if usb_hid_found!=0 {\n                                            usb_hid_configured=xhci_configure_boot_hid(xhci_state,phys_state);\n                                            if usb_hid_configured!=0 { usb_hid_report_ready=1; }\n                                        }\n                                    }\n                                }\n                            }\n                        }\n                    }\n                }'''
new='''                var usb_scan_start:u64=0; var usb_scan_tries:u64=0;\n                let r55_diag=volatile_read64(input_state+3976);\n                if r55_diag!=0 { unsafe { volatile_write64(r55_diag+592,1); volatile_write64(r55_diag+600,0); } }\n                while usb_hid_configured==0 && usb_scan_tries<8 {\n                    xhci_port_ready=xhci_reset_connected_port_from(xhci_state,usb_scan_start);\n                    if xhci_port_ready==0 { usb_scan_tries=8; if r55_diag!=0 { unsafe { volatile_write64(r55_diag+600,usb_scan_tries); } } }\n                    else {\n                        usb_scan_start=xhci_port_ready; usb_scan_tries=usb_scan_tries+1;\n                        if r55_diag!=0 { unsafe { volatile_write64(r55_diag+592,2); volatile_write64(r55_diag+600,usb_scan_tries); } }\n                        xhci_slot_ready=xhci_enable_slot(xhci_state);\n                        if xhci_slot_ready!=0 {\n                            if r55_diag!=0 { unsafe { volatile_write64(r55_diag+592,3); } }\n                            xhci_default_ready=xhci_address_default_device(xhci_state,phys_state);\n                            if xhci_default_ready!=0 {\n                                if r55_diag!=0 { unsafe { volatile_write64(r55_diag+592,4); } }\n                                xhci_descriptor8_ready=xhci_get_device_descriptor8(xhci_state,phys_state);\n                                if xhci_descriptor8_ready!=0 {\n                                    if r55_diag!=0 { unsafe { volatile_write64(r55_diag+592,5); } }\n                                    xhci_addressed_ready=xhci_finalize_address_and_descriptor(xhci_state,phys_state);\n                                    if xhci_addressed_ready!=0 {\n                                        if r55_diag!=0 { unsafe { volatile_write64(r55_diag+592,6); } }\n                                        usb_hid_found=xhci_discover_boot_hid(xhci_state,phys_state);\n                                        if usb_hid_found!=0 {\n                                            if r55_diag!=0 { unsafe { volatile_write64(r55_diag+592,7); } }\n                                            usb_hid_configured=xhci_configure_boot_hid(xhci_state,phys_state);\n                                            if usb_hid_configured!=0 { usb_hid_report_ready=1; if r55_diag!=0 { unsafe { volatile_write64(r55_diag+592,8); } } }\n                                        }\n                                    }\n                                }\n                            }\n                        }\n                    }\n                }'''
rep(old,new,'USB enumeration stage telemetry')

# Show stage/attempts in place of runtime report counters that can never advance until
# configuration succeeds. Keep UCFG/UPRT/ULEN/UPOR/UVID visible.
rep('pointer_diag_row(surface,(330*65536)+158,1297236053,uarm);                                                                  // UARM',
    'pointer_diag_row(surface,(330*65536)+158,1196708693,volatile_read64(diag+592));                                           // USTG',
    'USB stage row')
rep('pointer_diag_row(surface,(330*65536)+170,1414546005,urpt);                                                                  // URPT',
    'pointer_diag_row(surface,(330*65536)+170,1498567765,volatile_read64(diag+600));                                           // UTRY',
    'USB attempts row')

p.write_text(s)
