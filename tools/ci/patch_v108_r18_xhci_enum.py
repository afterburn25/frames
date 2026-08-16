#!/usr/bin/env python3
from pathlib import Path
import sys
p=Path(sys.argv[1])
s=p.read_text()
def rep(old,new,count=1):
    global s
    n=s.count(old)
    if n!=count:
        raise SystemExit(f"replacement count {n} != {count} for {old[:120]!r}")
    s=s.replace(old,new,count)
# Give physical devices a reset-recovery interval before issuing Enable Slot/Address Device.
old='''                serial_marker_xhci_port_ready(); return p+1;
'''
new='''                pit_wait(11932); serial_marker_xhci_port_ready(); return p+1;
'''
rep(old,new)

# Stage root enumeration so physical telemetry identifies the exact failed operation.
old='''                                if xhci_enable_slot(xhci_state)!=0 && xhci_address_default_device(xhci_state,phys_state)!=0 && xhci_get_device_descriptor8(xhci_state,phys_state)!=0 && xhci_finalize_address_and_descriptor(xhci_state,phys_state)!=0 {
                                    let desc=volatile_read64(xhci_state+264); var root_class:u64=0; if desc!=0 { root_class=volatile_read8(desc+4); } unsafe { volatile_write64(xhci_state+1056,6); volatile_write64(xhci_state+1080,root_class); }
                                    if xhci_discover_boot_hid(xhci_state,phys_state)!=0 {
                                        if v108_xhci_select_boot_hid_v117(xhci_state,wanted)!=0 { unsafe { volatile_write64(xhci_state+1056,7); } if xhci_configure_boot_hid(xhci_state,phys_state)!=0 { unsafe { volatile_write64(xhci_state+1056,8); volatile_write64(xhci_state+1048,1); } if ci!=0 { serial_marker_v108_usb_controller_fallback_ok(); } if wanted==1 { serial_marker_v108_usb_keyboard_selected_ok(); return 3; } return 2; } }
                                    } else { if root_class==9 { unsafe { volatile_write64(xhci_state+1056,9); } if xhci_hub_find_boot_hid_v117(xhci_state,phys_state,wanted)!=0 { unsafe { volatile_write64(xhci_state+1056,10); volatile_write64(xhci_state+1048,1); } if ci!=0 { serial_marker_v108_usb_controller_fallback_ok(); } if wanted==1 { serial_marker_v108_usb_keyboard_selected_ok(); return 3; } return 2; } } }
                                }
'''
new='''                                let slot_ok=xhci_enable_slot(xhci_state); if slot_ok==0 { unsafe { volatile_write64(xhci_state+1240,3); } }
                                else { unsafe { volatile_write64(xhci_state+1056,3); }
                                    let address_ok=xhci_address_default_device(xhci_state,phys_state); if address_ok==0 { unsafe { volatile_write64(xhci_state+1240,4); } }
                                    else { unsafe { volatile_write64(xhci_state+1056,4); }
                                        let d8_ok=xhci_get_device_descriptor8(xhci_state,phys_state); if d8_ok==0 { unsafe { volatile_write64(xhci_state+1240,5); } }
                                        else { unsafe { volatile_write64(xhci_state+1056,5); }
                                            let final_ok=xhci_finalize_address_and_descriptor(xhci_state,phys_state); if final_ok==0 { unsafe { volatile_write64(xhci_state+1240,6); } }
                                            else {
                                                let desc=volatile_read64(xhci_state+264); var root_class:u64=0; if desc!=0 { root_class=volatile_read8(desc+4); } unsafe { volatile_write64(xhci_state+1056,6); volatile_write64(xhci_state+1080,root_class); volatile_write64(xhci_state+1240,0); }
                                                if xhci_discover_boot_hid(xhci_state,phys_state)!=0 {
                                                    if v108_xhci_select_boot_hid_v117(xhci_state,wanted)!=0 { unsafe { volatile_write64(xhci_state+1056,7); } if xhci_configure_boot_hid(xhci_state,phys_state)!=0 { unsafe { volatile_write64(xhci_state+1056,8); volatile_write64(xhci_state+1048,1); } if ci!=0 { serial_marker_v108_usb_controller_fallback_ok(); } if wanted==1 { serial_marker_v108_usb_keyboard_selected_ok(); return 3; } return 2; } }
                                                } else { if root_class==9 { unsafe { volatile_write64(xhci_state+1056,9); } if xhci_hub_find_boot_hid_v117(xhci_state,phys_state,wanted)!=0 { unsafe { volatile_write64(xhci_state+1056,10); volatile_write64(xhci_state+1048,1); } if ci!=0 { serial_marker_v108_usb_controller_fallback_ok(); } if wanted==1 { serial_marker_v108_usb_keyboard_selected_ok(); return 3; } return 2; } } }
                                            }
                                        }
                                    }
                                }
'''
rep(old,new)

p.write_text(s)
