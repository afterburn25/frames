#!/usr/bin/env python3
from pathlib import Path
import subprocess, sys

p=Path(sys.argv[1])
here=Path(__file__).resolve().parent
subprocess.check_call([sys.executable, str(here/'make_r59_windows_log_partition.py'), str(p)])
s=p.read_text()

helpers=r'''
// r61 isolated storage write bring-up -------------------------------------------
// One-sector proof only: read original PTRLOG first sector, write signature,
// flush, read-back verify, restore original, flush, verify restoration.
// diag+640 = stage, diag+648 = error, diag+656 = target LBA,
// diag+664 = write result, diag+672 = flush result, diag+680 = readback result,
// diag+688 = restore result, diag+696 = final verify result.
fn r61_storage_write_bringup(input_state:u64,xhci_state:u64,phys_state:u64) -> u64 {
    if input_state==0 || xhci_state==0 || phys_state==0 { return 0; }
    let diag=volatile_read64(input_state+3976); if diag==0 { return 0; }
    unsafe {
        volatile_write64(diag+640,1); volatile_write64(diag+648,0); volatile_write64(diag+656,0);
        volatile_write64(diag+664,0); volatile_write64(diag+672,0); volatile_write64(diag+680,0);
        volatile_write64(diag+688,0); volatile_write64(diag+696,0);
    }
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
    unsafe { volatile_write64(diag+640,3); volatile_write64(diag+656,log_lba); }

    let orig=usb_msc_bot_read10(xhci_state,16384,log_lba,1);
    if orig==0 { unsafe { volatile_write64(diag+648,3); } return 0; }
    let backup=alloc_phys_page(phys_state); if backup==0 { unsafe { volatile_write64(diag+648,4); } return 0; }
    zero_page(backup); var i:u64=0; while i<512 { unsafe { volatile_write8(backup+i,volatile_read8(orig+i)); } i=i+1; }
    unsafe { volatile_write64(diag+640,4); }

    let proof=alloc_phys_page(phys_state); if proof==0 { unsafe { volatile_write64(diag+648,5); } return 0; }
    zero_page(proof);
    unsafe {
        volatile_write64(proof+0,5787213827064189522); // R61PROOF-like marker
        volatile_write64(proof+8,4702394920421080402);
        volatile_write64(proof+16,log_lba);
        volatile_write64(proof+24,61);
    }
    let wr=usb_msc_bot_write10(xhci_state,log_lba,1,proof); unsafe { volatile_write64(diag+664,wr); }
    if wr==0 { unsafe { volatile_write64(diag+648,6); } return 0; }
    unsafe { volatile_write64(diag+640,5); }

    let fl=usb_msc_bot_nodata(xhci_state,16385,53); unsafe { volatile_write64(diag+672,fl); }
    if fl==0 { unsafe { volatile_write64(diag+648,7); } return 0; }
    unsafe { volatile_write64(diag+640,6); }

    let back=usb_msc_bot_read10(xhci_state,16386,log_lba,1); if back==0 { unsafe { volatile_write64(diag+648,8); } return 0; }
    unsafe { volatile_write64(diag+680,1); }
    if volatile_read64(back)!=5787213827064189522 || volatile_read64(back+8)!=4702394920421080402 || volatile_read64(back+16)!=log_lba {
        unsafe { volatile_write64(diag+648,9); }
        return 0;
    }
    unsafe { volatile_write64(diag+640,7); }

    let rr=usb_msc_bot_write10(xhci_state,log_lba,1,backup); unsafe { volatile_write64(diag+688,rr); }
    if rr==0 { unsafe { volatile_write64(diag+648,10); } return 0; }
    if usb_msc_bot_nodata(xhci_state,16387,53)==0 { unsafe { volatile_write64(diag+648,11); } return 0; }
    let restored=usb_msc_bot_read10(xhci_state,16388,log_lba,1); if restored==0 { unsafe { volatile_write64(diag+648,12); } return 0; }
    var same:u64=1; i=0; while i<512 { if volatile_read8(restored+i)!=volatile_read8(backup+i) { same=0; i=512; } else { i=i+1; } }
    unsafe { volatile_write64(diag+696,same); }
    if same==0 { unsafe { volatile_write64(diag+648,13); } return 0; }
    unsafe { volatile_write64(diag+640,8); volatile_write64(diag+648,0); }
    return 1;
}
'''
needle='fn serial_marker_hwcompat_cpu_ok() -> void {'
if s.count(needle)!=1:
    raise SystemExit(f'r61 helper insertion site: expected 1, found {s.count(needle)}')
s=s.replace(needle,helpers+'\n'+needle,1)

old='ptrtrace_init(input_state,phys_state);\n    pointer_diag_panel(surface,input_state,gui_state);'
new='ptrtrace_init(input_state,phys_state);\n    let r61_storage_ok=r61_storage_write_bringup(input_state,xhci,phys_state);\n    pointer_diag_panel(surface,input_state,gui_state);'
if s.count(old)!=1:
    raise SystemExit(f'r61 proof call: expected 1 site, found {s.count(old)}')
s=s.replace(old,new,1)

# Disable full flight-recorder persistence in r61; this revision is storage-only.
old='if flight_saved==0 && read_tsc()>=flight_save_at { flight_saved=1; ptrtrace_save_usb(input_state,xhci,phys_state); pointer_diag_panel(surface,input_state,gui_state); display_shadow_present_rect(surface,(8*65536)+8,(960*65536)+258); }'
new='if flight_saved==0 && read_tsc()>=flight_save_at { flight_saved=1; let r61_diag=volatile_read64(input_state+3976); if r61_diag!=0 { unsafe { volatile_write64(r61_diag+632,2+r61_storage_ok); } } pointer_diag_panel(surface,input_state,gui_state); display_shadow_present_rect(surface,(8*65536)+8,(960*65536)+258); }'
if s.count(old)!=1:
    raise SystemExit(f'r61 autosave replacement: expected 1 site, found {s.count(old)}')
s=s.replace(old,new,1)

old='pointer_diag_row(surface,(330*65536)+230,82+(69*256)+(67*65536)+(83*16777216),r58_recs);                                  // RECS\n'
new='pointer_diag_row(surface,(330*65536)+230,82+(69*256)+(67*65536)+(83*16777216),r58_recs);                                  // RECS\n    var r61_st:u64=0; var r61_er:u64=0; var r61_lba:u64=0; var r61_wr:u64=0; var r61_fl:u64=0; var r61_rb:u64=0; var r61_rs:u64=0; var r61_vf:u64=0;\n    if diag!=0 { r61_st=volatile_read64(diag+640); r61_er=volatile_read64(diag+648); r61_lba=volatile_read64(diag+656); r61_wr=volatile_read64(diag+664); r61_fl=volatile_read64(diag+672); r61_rb=volatile_read64(diag+680); r61_rs=volatile_read64(diag+688); r61_vf=volatile_read64(diag+696); }\n    pointer_diag_row(surface,(330*65536)+242,83+(84*256)+(71*65536)+(69*16777216),r61_st); // STGE\n    pointer_diag_row(surface,(330*65536)+254,69+(82*256)+(82*65536)+(32*16777216),r61_er); // ERR \n    pointer_diag_row(surface,(330*65536)+266,76+(66*256)+(65*65536)+(32*16777216),r61_lba); // LBA \n    pointer_diag_row(surface,(330*65536)+278,87+(82*256)+(32*65536)+(32*16777216),r61_wr); // WR  \n    pointer_diag_row(surface,(330*65536)+290,70+(76*256)+(83*65536)+(72*16777216),r61_fl); // FLSH\n    pointer_diag_row(surface,(330*65536)+302,82+(68*256)+(66*65536)+(75*16777216),r61_rb); // RDBK\n    pointer_diag_row(surface,(330*65536)+314,82+(83*256)+(84*65536)+(82*16777216),r61_rs); // RSTR\n    pointer_diag_row(surface,(330*65536)+326,86+(69*256)+(82*65536)+(73*16777216),r61_vf); // VERI\n'
if s.count(old)!=1:
    raise SystemExit(f'r61 rows: expected 1 site, found {s.count(old)}')
s=s.replace(old,new,1)

old_title='pointer_diag_draw_tag4(surface,(78*65536)+18,82+(53*256)+(57*65536)+(32*16777216),green);    // R59'
new_title='pointer_diag_draw_tag4(surface,(78*65536)+18,82+(54*256)+(49*65536)+(32*16777216),green);    // R61'
if s.count(old_title)!=1:
    raise SystemExit(f'r61 title: expected 1 R59 title site, found {s.count(old_title)}')
s=s.replace(old_title,new_title,1)

p.write_text(s)
