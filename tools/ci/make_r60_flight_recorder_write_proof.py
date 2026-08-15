#!/usr/bin/env python3
from pathlib import Path
import subprocess, sys

p=Path(sys.argv[1])
here=Path(__file__).resolve().parent
subprocess.check_call([sys.executable, str(here/'make_r59_windows_log_partition.py'), str(p)])
s=p.read_text()

helpers=r'''
// r60 storage-path proof ---------------------------------------------------------
// Runs before the pointer capture loop. It proves that FRAMESLOG/PTRLOG.BIN can
// be found, written through USB MSC WRITE(10), flushed, read back, and verified.
// diag+640 = proof stage, diag+648 = error code.
fn ptrtrace_storage_proof(input_state:u64,xhci_state:u64,phys_state:u64) -> u64 {
    if input_state==0 || xhci_state==0 || phys_state==0 { return 0; }
    let diag=volatile_read64(input_state+3976); if diag==0 { return 0; }
    unsafe { volatile_write64(diag+640,1); volatile_write64(diag+648,0); }

    var scan:u64=0; var tries:u64=0; var msc:u64=0;
    while msc==0 && tries<8 {
        let port=xhci_reset_connected_port_from(xhci_state,scan);
        if port==0 { tries=8; }
        else {
            scan=port; tries=tries+1;
            let slot=xhci_enable_slot(xhci_state);
            if slot!=0 && xhci_address_default_device(xhci_state,phys_state)!=0 && xhci_get_device_descriptor8(xhci_state,phys_state)!=0 && xhci_finalize_address_and_descriptor(xhci_state,phys_state)!=0 {
                if usb_msc_discover(xhci_state,phys_state)!=0 && usb_msc_configure(xhci_state,phys_state)!=0 { msc=1; }
            }
        }
    }
    if msc==0 { unsafe { volatile_write64(diag+648,1); } return 0; }
    unsafe { volatile_write64(diag+640,2); }

    let log_lba=ptrlog_find_contiguous_file(xhci_state);
    if log_lba==0 { unsafe { volatile_write64(diag+648,2); } return 0; }
    unsafe { volatile_write64(diag+640,3); }

    let proof=alloc_phys_page(phys_state);
    if proof==0 { unsafe { volatile_write64(diag+648,3); } return 0; }
    zero_page(proof);
    unsafe {
        volatile_write64(proof+0,5787213827047412306);  // "R60PROOF"
        volatile_write64(proof+8,5063528412317797458);  // recognizable marker
        volatile_write64(proof+16,log_lba);
        volatile_write64(proof+24,read_tsc());
        volatile_write64(proof+32,60);
    }
    if usb_msc_bot_write10(xhci_state,log_lba,1,proof)==0 { unsafe { volatile_write64(diag+648,4); } return 0; }
    unsafe { volatile_write64(diag+640,4); }

    if usb_msc_bot_nodata(xhci_state,12288,53)==0 { unsafe { volatile_write64(diag+648,5); } return 0; }
    unsafe { volatile_write64(diag+640,5); }

    let back=usb_msc_bot_read10(xhci_state,12289,log_lba,1);
    if back==0 { unsafe { volatile_write64(diag+648,6); } return 0; }
    unsafe { volatile_write64(diag+640,6); }
    if volatile_read64(back)!=5787213827047412306 || volatile_read64(back+8)!=5063528412317797458 || volatile_read64(back+16)!=log_lba {
        unsafe { volatile_write64(diag+648,7); }
        return 0;
    }
    unsafe { volatile_write64(diag+640,7); volatile_write64(diag+648,0); }
    return 1;
}
'''
needle='fn serial_marker_hwcompat_cpu_ok() -> void {'
if s.count(needle)!=1:
    raise SystemExit(f'r60 helper insertion site: expected 1, found {s.count(needle)}')
s=s.replace(needle,helpers+'\n'+needle,1)

# Run proof after the recorder exists but before the pointer capture loop begins.
old='ptrtrace_init(input_state,phys_state);\n    pointer_diag_panel(surface,input_state,gui_state);'
new='ptrtrace_init(input_state,phys_state);\n    let r60_storage_ok=ptrtrace_storage_proof(input_state,xhci,phys_state);\n    pointer_diag_panel(surface,input_state,gui_state);'
if s.count(old)!=1:
    raise SystemExit(f'r60 proof call: expected 1 site, found {s.count(old)}')
s=s.replace(old,new,1)

# If the pre-capture proof failed, do not attempt the later full persistence pass.
old='if flight_saved==0 && read_tsc()>=flight_save_at { flight_saved=1; ptrtrace_save_usb(input_state,xhci,phys_state); pointer_diag_panel(surface,input_state,gui_state); display_shadow_present_rect(surface,(8*65536)+8,(960*65536)+258); }'
new='if flight_saved==0 && read_tsc()>=flight_save_at { flight_saved=1; if r60_storage_ok!=0 { ptrtrace_save_usb(input_state,xhci,phys_state); } else { let r60_diag=volatile_read64(input_state+3976); if r60_diag!=0 { unsafe { volatile_write64(r60_diag+632,3); } } } pointer_diag_panel(surface,input_state,gui_state); display_shadow_present_rect(surface,(8*65536)+8,(960*65536)+258); }'
if s.count(old)!=1:
    raise SystemExit(f'r60 autosave guard: expected 1 site, found {s.count(old)}')
s=s.replace(old,new,1)

# Add proof stage/error rows to the diagnostic panel.
old='pointer_diag_row(surface,(330*65536)+230,82+(69*256)+(67*65536)+(83*16777216),r58_recs);                                  // RECS\n'
new='pointer_diag_row(surface,(330*65536)+230,82+(69*256)+(67*65536)+(83*16777216),r58_recs);                                  // RECS\n    var r60_wstg:u64=0; var r60_werr:u64=0; if diag!=0 { r60_wstg=volatile_read64(diag+640); r60_werr=volatile_read64(diag+648); }\n    pointer_diag_row(surface,(330*65536)+242,87+(83*256)+(84*65536)+(71*16777216),r60_wstg);                                  // WSTG\n    pointer_diag_row(surface,(330*65536)+254,87+(69*256)+(82*65536)+(82*16777216),r60_werr);                                  // WERR\n'
if s.count(old)!=1:
    raise SystemExit(f'r60 proof rows: expected 1 site, found {s.count(old)}')
s=s.replace(old,new,1)

# Visible revision R59 -> R60.
old_title='pointer_diag_draw_tag4(surface,(78*65536)+18,82+(53*256)+(57*65536)+(32*16777216),green);    // R59'
new_title='pointer_diag_draw_tag4(surface,(78*65536)+18,82+(54*256)+(48*65536)+(32*16777216),green);    // R60'
if s.count(old_title)!=1:
    raise SystemExit(f'r60 title: expected 1 R59 title site, found {s.count(old_title)}')
s=s.replace(old_title,new_title,1)

p.write_text(s)
