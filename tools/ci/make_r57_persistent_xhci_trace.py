#!/usr/bin/env python3
from pathlib import Path
import subprocess, sys

p=Path(sys.argv[1])
subprocess.check_call([sys.executable, str(Path(__file__).with_name('make_r56_linux_input_architecture.py')), str(p)])
s=p.read_text()

def rep(old,new,label):
    global s
    n=s.count(old)
    if n!=1:
        raise SystemExit(f'{label}: expected 1 site, found {n}')
    s=s.replace(old,new)

rep('pointer_diag_draw_tag4(surface,(78*65536)+18,82+(53*256)+(54*65536)+(32*16777216),green);    // R56',
    'pointer_diag_draw_tag4(surface,(78*65536)+18,82+(53*256)+(55*65536)+(32*16777216),green);    // R57',
    'title')

# Persistent xHCI trace fields live in the 4 KiB xHCI state page and therefore
# exist during controller/device enumeration, before pointer diagnostics are attached.
# +840 ESTG deepest successful enumeration stage
# +848 ETRY connected-root-port attempts
# +856 EFLR first/current failing stage (0 when no failure recorded)
# +864 ECC  underlying xHCI command/transfer completion snapshot
rep('unsafe { volatile_write64(xhci_state+0,base); volatile_write64(xhci_state+8,op); volatile_write64(xhci_state+16,command_ring); volatile_write64(xhci_state+24,event_ring); volatile_write64(xhci_state+32,erst); volatile_write64(xhci_state+40,dcbaa); volatile_write64(xhci_state+48,maxslots); volatile_write64(xhci_state+56,1); volatile_write64(xhci_state+64,0); volatile_write64(xhci_state+72,1); volatile_write64(xhci_state+80,runtime); volatile_write64(xhci_state+88,doorbells); volatile_write64(xhci_state+96,0); volatile_write64(xhci_state+104,1); }',
    'unsafe { volatile_write64(xhci_state+0,base); volatile_write64(xhci_state+8,op); volatile_write64(xhci_state+16,command_ring); volatile_write64(xhci_state+24,event_ring); volatile_write64(xhci_state+32,erst); volatile_write64(xhci_state+40,dcbaa); volatile_write64(xhci_state+48,maxslots); volatile_write64(xhci_state+56,1); volatile_write64(xhci_state+64,0); volatile_write64(xhci_state+72,1); volatile_write64(xhci_state+80,runtime); volatile_write64(xhci_state+88,doorbells); volatile_write64(xhci_state+96,0); volatile_write64(xhci_state+104,1); volatile_write64(xhci_state+840,1); volatile_write64(xhci_state+848,0); volatile_write64(xhci_state+856,0); volatile_write64(xhci_state+864,0); }',
    'persistent trace init')

old='''                var usb_scan_start:u64=0; var usb_scan_tries:u64=0;
                let r55_diag=volatile_read64(input_state+3976);
                if r55_diag!=0 { unsafe { volatile_write64(r55_diag+592,1); volatile_write64(r55_diag+600,0); } }
                while usb_hid_configured==0 && usb_scan_tries<8 {
                    xhci_port_ready=xhci_reset_connected_port_from(xhci_state,usb_scan_start);
                    if xhci_port_ready==0 { usb_scan_tries=8; if r55_diag!=0 { unsafe { volatile_write64(r55_diag+600,usb_scan_tries); } } }
                    else {
                        usb_scan_start=xhci_port_ready; usb_scan_tries=usb_scan_tries+1;
                        if r55_diag!=0 { unsafe { volatile_write64(r55_diag+592,2); volatile_write64(r55_diag+600,usb_scan_tries); } }
                        xhci_slot_ready=xhci_enable_slot(xhci_state);
                        if xhci_slot_ready!=0 {
                            if r55_diag!=0 { unsafe { volatile_write64(r55_diag+592,3); } }
                            xhci_default_ready=xhci_address_default_device(xhci_state,phys_state);
                            if xhci_default_ready!=0 {
                                if r55_diag!=0 { unsafe { volatile_write64(r55_diag+592,4); } }
                                xhci_descriptor8_ready=xhci_get_device_descriptor8(xhci_state,phys_state);
                                if xhci_descriptor8_ready!=0 {
                                    if r55_diag!=0 { unsafe { volatile_write64(r55_diag+592,5); } }
                                    xhci_addressed_ready=xhci_finalize_address_and_descriptor(xhci_state,phys_state);
                                    if xhci_addressed_ready!=0 {
                                        if r55_diag!=0 { unsafe { volatile_write64(r55_diag+592,6); } }
                                        usb_hid_found=xhci_discover_boot_hid(xhci_state,phys_state);
                                        if usb_hid_found!=0 {
                                            if r55_diag!=0 { unsafe { volatile_write64(r55_diag+592,7); } }
                                            usb_hid_configured=xhci_configure_boot_hid(xhci_state,phys_state);
                                            if usb_hid_configured!=0 { usb_hid_report_ready=1; if r55_diag!=0 { unsafe { volatile_write64(r55_diag+592,8); } } }
                                        }
                                    }
                                }
                            }
                        }
                    }
                }'''
new='''                var usb_scan_start:u64=0; var usb_scan_tries:u64=0;
                unsafe { volatile_write64(xhci_state+840,1); volatile_write64(xhci_state+848,0); volatile_write64(xhci_state+856,0); volatile_write64(xhci_state+864,0); }
                while usb_hid_configured==0 && usb_scan_tries<8 {
                    xhci_port_ready=xhci_reset_connected_port_from(xhci_state,usb_scan_start);
                    if xhci_port_ready==0 {
                        usb_scan_tries=8;
                        unsafe { volatile_write64(xhci_state+848,usb_scan_tries); volatile_write64(xhci_state+856,2); volatile_write64(xhci_state+864,0); }
                    }
                    else {
                        usb_scan_start=xhci_port_ready; usb_scan_tries=usb_scan_tries+1;
                        unsafe { volatile_write64(xhci_state+840,2); volatile_write64(xhci_state+848,usb_scan_tries); volatile_write64(xhci_state+856,0); }
                        xhci_slot_ready=xhci_enable_slot(xhci_state);
                        if xhci_slot_ready==0 {
                            unsafe { volatile_write64(xhci_state+856,3); volatile_write64(xhci_state+864,volatile_read64(xhci_state+488)); }
                        }
                        else {
                            unsafe { volatile_write64(xhci_state+840,3); }
                            xhci_default_ready=xhci_address_default_device(xhci_state,phys_state);
                            if xhci_default_ready==0 {
                                unsafe { volatile_write64(xhci_state+856,4); volatile_write64(xhci_state+864,volatile_read64(xhci_state+488)); }
                            }
                            else {
                                unsafe { volatile_write64(xhci_state+840,4); }
                                xhci_descriptor8_ready=xhci_get_device_descriptor8(xhci_state,phys_state);
                                if xhci_descriptor8_ready==0 {
                                    unsafe { volatile_write64(xhci_state+856,5); volatile_write64(xhci_state+864,volatile_read64(xhci_state+504)+(volatile_read64(xhci_state+512)*256)+(volatile_read64(xhci_state+520)*65536)); }
                                }
                                else {
                                    unsafe { volatile_write64(xhci_state+840,5); }
                                    xhci_addressed_ready=xhci_finalize_address_and_descriptor(xhci_state,phys_state);
                                    if xhci_addressed_ready==0 {
                                        unsafe { volatile_write64(xhci_state+856,6); volatile_write64(xhci_state+864,(volatile_read64(xhci_state+488)*256)+volatile_read64(xhci_state+504)); }
                                    }
                                    else {
                                        unsafe { volatile_write64(xhci_state+840,6); }
                                        usb_hid_found=xhci_discover_boot_hid(xhci_state,phys_state);
                                        if usb_hid_found==0 {
                                            unsafe { volatile_write64(xhci_state+856,7); volatile_write64(xhci_state+864,volatile_read64(xhci_state+504)); }
                                        }
                                        else {
                                            unsafe { volatile_write64(xhci_state+840,7); }
                                            usb_hid_configured=xhci_configure_boot_hid(xhci_state,phys_state);
                                            if usb_hid_configured==0 {
                                                unsafe { volatile_write64(xhci_state+856,8); volatile_write64(xhci_state+864,(volatile_read64(xhci_state+488)*256)+volatile_read64(xhci_state+504)); }
                                            }
                                            else {
                                                usb_hid_report_ready=1;
                                                unsafe { volatile_write64(xhci_state+840,8); volatile_write64(xhci_state+856,0); volatile_write64(xhci_state+864,0); }
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                }'''
rep(old,new,'persistent enumeration trace')

# Diagnostic panel now reads persistent xHCI trace directly.
rep('pointer_diag_row(surface,(330*65536)+146,1396785752,xbas);                                                                 // XBAS',
    'pointer_diag_row(surface,(330*65536)+146,1380730437,volatile_read64(r53b_xhci+856));                                      // EFLR',
    'failure row')
rep('pointer_diag_row(surface,(330*65536)+158,1196708693,volatile_read64(diag+592));                                           // USTG',
    'pointer_diag_row(surface,(330*65536)+158,1196708693,volatile_read64(r53b_xhci+840));                                      // USTG',
    'persistent stage row')
rep('pointer_diag_row(surface,(330*65536)+170,1498567765,volatile_read64(diag+600));                                           // UTRY',
    'pointer_diag_row(surface,(330*65536)+170,1498567765,volatile_read64(r53b_xhci+848));                                      // UTRY',
    'persistent attempts row')
rep('pointer_diag_row(surface,(330*65536)+182,542134360,xopb);                                                                  // XOP ',
    'pointer_diag_row(surface,(330*65536)+182,541280069,volatile_read64(r53b_xhci+864));                                       // ECC ',
    'completion-code row')

p.write_text(s)
