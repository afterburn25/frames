#!/usr/bin/env python3
from pathlib import Path
import subprocess, sys

p=Path(sys.argv[1])
subprocess.check_call([sys.executable, str(Path(__file__).with_name('make_r57_persistent_xhci_trace.py')), str(p)])
s=p.read_text()

def rep(old,new,label):
    global s
    n=s.count(old)
    if n!=1:
        raise SystemExit(f'{label}: expected 1 site, found {n}')
    s=s.replace(old,new)

rep('pointer_diag_draw_tag4(surface,(78*65536)+18,82+(53*256)+(55*65536)+(32*16777216),green);    // R57',
    'pointer_diag_draw_tag4(surface,(78*65536)+18,82+(53*256)+(56*65536)+(32*16777216),green);    // R58',
    'title')

# Flight-recorder hooks: raw PS/2 bytes, decoded PS/2 packets, Generic Pointer
# relative events, and raw USB HID report snapshots.
rep('let packed=((status%256)*256)+(data%256); unsafe { volatile_write64(input_state+3232+(tail*8),packed); }',
    'let packed=((status%256)*256)+(data%256); ptrtrace_emit(input_state,1,status,data); unsafe { volatile_write64(input_state+3232+(tail*8),packed); }',
    'raw PS2 hook')
rep('let packed=buttons+(x_mag*256)+(x_neg*131072)+(y_mag*262144)+(y_neg*134217728);',
    'let packed=buttons+(x_mag*256)+(x_neg*131072)+(y_mag*262144)+(y_neg*134217728); ptrtrace_emit(input_state,2,header,(dx%256)+((dy%256)*256));',
    'decoded PS2 hook')
rep('if generic_pointer_claim(state,source)==0 { return 1; }\n    let buttons=packed%256;',
    'if generic_pointer_claim(state,source)==0 { return 1; }\n    ptrtrace_emit(state,3,source,packed);\n    let buttons=packed%256;',
    'generic pointer hook')
rep('let buffer=volatile_read64(xhci_state+432); let checksum=nvme_read_checksum(buffer,actual); unsafe { volatile_write64(xhci_state+440,actual);',
    'let buffer=volatile_read64(xhci_state+432); ptrtrace_emit(input_state,4,actual,volatile_read64(buffer)); let checksum=nvme_read_checksum(buffer,actual); unsafe { volatile_write64(xhci_state+440,actual);',
    'USB report hook')

helpers=r'''
// r58 persistent physical-input flight recorder ---------------------------------
// Trace format: 32-byte records {tsc,kind,a,b}. The recorder is RAM-resident
// during the test. A bounded auto-save later re-enumerates the boot USB as MSC,
// finds preallocated root file PTRLOG.BIN, overwrites only its reserved sectors,
// then issues SCSI SYNCHRONIZE CACHE. No FAT metadata is changed at runtime.
fn ptrtrace_init(input_state:u64,phys_state:u64) -> u64 {
    if input_state==0 || phys_state==0 { return 0; }
    let diag=volatile_read64(input_state+3976); if diag==0 { return 0; }
    let meta=alloc_phys_page(phys_state); if meta==0 { return 0; } zero_page(meta);
    var i:u64=0;
    while i<96 {
        let page=alloc_phys_page(phys_state); if page==0 { return 0; }
        zero_page(page); unsafe { volatile_write64(meta+64+(i*8),page); }
        i=i+1;
    }
    unsafe {
        volatile_write64(meta+0,15821226413937222); // "FRPTR58\0"
        volatile_write64(meta+8,0);                 // record count
        volatile_write64(meta+16,0);                // dropped records
        volatile_write64(meta+24,12288);            // max records
        volatile_write64(meta+32,96);               // data pages
        volatile_write64(meta+40,0);                // save state: 0 pending,1 saving,2 saved,3 failed
        volatile_write64(meta+48,0);                // save error
        volatile_write64(meta+56,read_tsc());       // session start
        volatile_write64(diag+616,meta);
        volatile_write64(diag+624,phys_state);
        volatile_write64(diag+632,0);
    }
    return 1;
}
fn ptrtrace_emit(input_state:u64,kind:u64,a:u64,b:u64) -> u64 {
    if input_state==0 { return 0; }
    let diag=volatile_read64(input_state+3976); if diag==0 { return 0; }
    let meta=volatile_read64(diag+616); if meta==0 || volatile_read64(meta)!=15821226413937222 { return 0; }
    let count=volatile_read64(meta+8); let limit=volatile_read64(meta+24);
    if count>=limit { unsafe { volatile_write64(meta+16,volatile_read64(meta+16)+1); } return 0; }
    let page_index=count/128; let rec_index=count%128; let page=volatile_read64(meta+64+(page_index*8)); if page==0 { return 0; }
    let rec=page+(rec_index*32);
    unsafe { volatile_write64(rec,read_tsc()); volatile_write64(rec+8,kind); volatile_write64(rec+16,a); volatile_write64(rec+24,b); volatile_write64(meta+8,count+1); }
    return 1;
}
fn ptrlog_short_name(entry:u64) -> u64 {
    if volatile_read8(entry)!=80 || volatile_read8(entry+1)!=84 || volatile_read8(entry+2)!=82 || volatile_read8(entry+3)!=76 || volatile_read8(entry+4)!=79 || volatile_read8(entry+5)!=71 { return 0; }
    if volatile_read8(entry+6)!=32 || volatile_read8(entry+7)!=32 || volatile_read8(entry+8)!=66 || volatile_read8(entry+9)!=73 || volatile_read8(entry+10)!=78 { return 0; }
    return 1;
}
fn usb_msc_prepare_write10_cbw(xhci_state:u64,tag:u64,lba:u64,blocks:u64) -> u64 {
    let cbw=volatile_read64(xhci_state+752); if cbw==0 || blocks==0 || blocks>8 { return 0; }
    zero_page(cbw); let transfer=blocks*512;
    unsafe {
        volatile_write32(cbw,1128420181); volatile_write32(cbw+4,tag); volatile_write32(cbw+8,transfer);
        volatile_write8(cbw+12,0); volatile_write8(cbw+13,0); volatile_write8(cbw+14,10); volatile_write8(cbw+15,42);
        volatile_write8(cbw+17,(lba/16777216)%256); volatile_write8(cbw+18,(lba/65536)%256); volatile_write8(cbw+19,(lba/256)%256); volatile_write8(cbw+20,lba%256);
        volatile_write8(cbw+22,(blocks/256)%256); volatile_write8(cbw+23,blocks%256);
    }
    return cbw;
}
fn usb_msc_bot_write10(xhci_state:u64,tag:u64,lba:u64,blocks:u64,source:u64) -> u64 {
    if source==0 { return 0; }
    let cbw=usb_msc_prepare_write10_cbw(xhci_state,tag,lba,blocks); let data=volatile_read64(xhci_state+768); let csw=volatile_read64(xhci_state+760);
    if cbw==0 || data==0 || csw==0 { return 0; }
    let length=blocks*512; zero_page(data); zero_page(csw); var i:u64=0;
    while i<length { unsafe { volatile_write8(data+i,volatile_read8(source+i)); } i=i+1; }
    if usb_msc_bulk_td(xhci_state,0,cbw,31)!=31 { return 0; }
    if usb_msc_bulk_td(xhci_state,0,data,length)!=length { return 0; }
    if usb_msc_bulk_td(xhci_state,1,csw,13)!=13 { return 0; }
    return usb_msc_check_csw(xhci_state,tag);
}
fn usb_msc_bot_nodata(xhci_state:u64,tag:u64,opcode:u64) -> u64 {
    let cbw=usb_msc_prepare_cbw(xhci_state,tag,opcode,0); let csw=volatile_read64(xhci_state+760); if cbw==0 || csw==0 { return 0; }
    zero_page(csw); if usb_msc_bulk_td(xhci_state,0,cbw,31)!=31 { return 0; } if usb_msc_bulk_td(xhci_state,1,csw,13)!=13 { return 0; }
    return usb_msc_check_csw(xhci_state,tag);
}
fn ptrlog_find_contiguous_file(xhci_state:u64) -> u64 {
    var tag:u64=4096;
    let pe=usb_msc_bot_read10(xhci_state,tag,2,1); if pe==0 { return 0; } tag=tag+1;
    let part_lba=volatile_read64(pe+32); if part_lba<34 { return 0; }
    let boot=usb_msc_bot_read10(xhci_state,tag,part_lba,1); if boot==0 { return 0; } tag=tag+1;
    let bps=read_u16_le(boot+11); let spc=volatile_read8(boot+13); let reserved=read_u16_le(boot+14); let fats=volatile_read8(boot+16); let fatsecs=volatile_read32(boot+36); let root=volatile_read32(boot+44)%268435456;
    if bps!=512 || spc!=1 || reserved==0 || fats==0 || fatsecs==0 || root<2 { return 0; }
    let fat_start=part_lba+reserved; let data_start=fat_start+(fats*fatsecs); var cluster=root; var guard:u64=0;
    while cluster>=2 && cluster<268435448 && guard<128 {
        let dir=usb_msc_bot_read10(xhci_state,tag,data_start+(cluster-2),1); if dir==0 { return 0; } tag=tag+1;
        var off:u64=0;
        while off+32<=512 {
            let first=volatile_read8(dir+off); if first==0 { off=512; }
            else {
                let attr=volatile_read8(dir+off+11);
                if first!=229 && attr!=15 && ptrlog_short_name(dir+off)!=0 {
                    let fcluster=(read_u16_le(dir+off+20)*65536)+read_u16_le(dir+off+26); let fsize=volatile_read32(dir+off+28);
                    if fcluster<2 || fsize<1048576 { return 0; }
                    unsafe { volatile_write64(xhci_state+880,data_start+(fcluster-2)); volatile_write64(xhci_state+888,fsize); }
                    return data_start+(fcluster-2);
                }
                off=off+32;
            }
        }
        let byteoff=cluster*4; let fat=usb_msc_bot_read10(xhci_state,tag,fat_start+(byteoff/512),1); if fat==0 { return 0; } tag=tag+1;
        cluster=volatile_read32(fat+(byteoff%512))%268435456; guard=guard+1;
    }
    return 0;
}
fn ptrtrace_save_usb(input_state:u64,xhci_state:u64,phys_state:u64) -> u64 {
    if input_state==0 || xhci_state==0 || phys_state==0 { return 0; }
    let diag=volatile_read64(input_state+3976); if diag==0 { return 0; } let meta=volatile_read64(diag+616); if meta==0 { return 0; }
    if volatile_read64(meta+40)==2 { return 2; } unsafe { volatile_write64(meta+40,1); volatile_write64(meta+48,0); volatile_write64(diag+632,1); }
    ptrtrace_emit(input_state,5,volatile_read64(xhci_state+840),(volatile_read64(xhci_state+856)*256)+volatile_read64(xhci_state+864));
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
    if msc==0 { unsafe { volatile_write64(meta+40,3); volatile_write64(meta+48,1); volatile_write64(diag+632,3); } return 0; }
    let log_lba=ptrlog_find_contiguous_file(xhci_state); if log_lba==0 { unsafe { volatile_write64(meta+40,3); volatile_write64(meta+48,2); volatile_write64(diag+632,3); } return 0; }
    let header=alloc_phys_page(phys_state); if header==0 { unsafe { volatile_write64(meta+40,3); volatile_write64(meta+48,3); volatile_write64(diag+632,3); } return 0; } zero_page(header);
    unsafe {
        volatile_write64(header+0,15821226413937222); volatile_write64(header+8,58); volatile_write64(header+16,volatile_read64(meta+8)); volatile_write64(header+24,volatile_read64(meta+16));
        volatile_write64(header+32,32); volatile_write64(header+40,volatile_read64(meta+32)); volatile_write64(header+48,volatile_read64(xhci_state+840)); volatile_write64(header+56,volatile_read64(xhci_state+856));
        volatile_write64(header+64,volatile_read64(xhci_state+864)); volatile_write64(header+72,volatile_read64(xhci_state+112)); volatile_write64(header+80,volatile_read64(xhci_state+272));
        volatile_write64(header+88,volatile_read64(input_state+3824)); volatile_write64(header+96,volatile_read64(input_state+3144)); volatile_write64(header+104,volatile_read64(input_state+3840)); volatile_write64(header+112,volatile_read64(diag+16)); volatile_write64(header+120,read_tsc());
    }
    var tag:u64=8192; if usb_msc_bot_write10(xhci_state,tag,log_lba,1,header)==0 { unsafe { volatile_write64(meta+40,3); volatile_write64(meta+48,4); volatile_write64(diag+632,3); } return 0; } tag=tag+1;
    let count=volatile_read64(meta+8); var pages=(count+127)/128; if pages>96 { pages=96; }
    var pidx:u64=0; var lba=log_lba+1;
    while pidx<pages {
        let page=volatile_read64(meta+64+(pidx*8)); if page==0 { unsafe { volatile_write64(meta+40,3); volatile_write64(meta+48,5); volatile_write64(diag+632,3); } return 0; }
        if usb_msc_bot_write10(xhci_state,tag,lba,8,page)==0 { unsafe { volatile_write64(meta+40,3); volatile_write64(meta+48,6); volatile_write64(diag+632,3); } return 0; }
        tag=tag+1; lba=lba+8; pidx=pidx+1;
    }
    if usb_msc_bot_nodata(xhci_state,tag,53)==0 { unsafe { volatile_write64(meta+48,7); } }
    unsafe { volatile_write64(meta+40,2); volatile_write64(diag+632,2); }
    return 2;
}
'''
needle='fn serial_marker_hwcompat_cpu_ok() -> void {'
if needle not in s:
    raise SystemExit('helper insertion site missing')
s=s.replace(needle,helpers+'\n'+needle,1)

# Allocate recorder after the existing diagnostic page exists.
rep('let ps2diag=alloc_phys_page(phys_state); if ps2diag!=0 { zero_page(ps2diag); unsafe { volatile_write64(input_state+3976,ps2diag); } }\n    pointer_diag_panel(surface,input_state,gui_state);',
    'let ps2diag=alloc_phys_page(phys_state); if ps2diag!=0 { zero_page(ps2diag); unsafe { volatile_write64(input_state+3976,ps2diag); } }\n    ptrtrace_init(input_state,phys_state);\n    pointer_diag_panel(surface,input_state,gui_state);',
    'trace init')

# Autosave after a bounded capture window. ~40e9 invariant-TSC ticks is normally
# 10-25 seconds on contemporary x86 laptops; the exact TSC is also in the log.
rep('var panel_next:u64=read_tsc()+250000000; var panel_refreshes:u64=0;\n    while true {',
    'var panel_next:u64=read_tsc()+250000000; var panel_refreshes:u64=0; var flight_saved:u64=0; let flight_save_at=read_tsc()+40000000000;\n    while true {',
    'autosave timer init')
rep('panel_refreshes=panel_refreshes+1; panel_next=now_panel+250000000;\n        }\n        cpu_pause();',
    'panel_refreshes=panel_refreshes+1; panel_next=now_panel+250000000;\n        }\n        if flight_saved==0 && read_tsc()>=flight_save_at { flight_saved=1; ptrtrace_save_usb(input_state,xhci,phys_state); pointer_diag_panel(surface,input_state,gui_state); display_shadow_present_rect(surface,(8*65536)+8,(960*65536)+258); }\n        cpu_pause();',
    'autosave call')

# Show save state and record count directly on-screen so the user knows when it is
# safe to power down/remove the USB without sending us a photo.
rep('pointer_diag_row(surface,(330*65536)+206,1145656661,volatile_read64(r53b_xhci+272));                                      // UVID\n',
    'pointer_diag_row(surface,(330*65536)+206,1145656661,volatile_read64(r53b_xhci+272));                                      // UVID\n    var r58_save:u64=0; var r58_recs:u64=0; if diag!=0 { r58_save=volatile_read64(diag+632); let r58_meta=volatile_read64(diag+616); if r58_meta!=0 { r58_recs=volatile_read64(r58_meta+8); } }\n    pointer_diag_row(surface,(330*65536)+218,83+(65*256)+(86*65536)+(69*16777216),r58_save);                                  // SAVE\n    pointer_diag_row(surface,(330*65536)+230,82+(69*256)+(67*65536)+(83*16777216),r58_recs);                                  // RECS\n',
    'save status rows')

p.write_text(s)
