#!/usr/bin/env python3
from pathlib import Path
import subprocess, sys

p=Path(sys.argv[1])
here=Path(__file__).resolve().parent
subprocess.check_call([sys.executable, str(here/'make_r59_windows_log_partition.py'), str(p)])
s=p.read_text()

helpers=r'''
// r62 physical xHCI root-port enumeration trace -------------------------------
// Replays enumeration port-by-port without touching persistent storage.
// Eight packed records live at diag+704..+760. Each record packs:
// bits 0..7 port, 8..11 speed, 12..15 deepest stage, 16..23 completion snapshot.
// diag+768 deepest port, +776 raw PORTSC, +784 VID, +792 descriptor marker.
fn r62_xhci_root_port_trace(input_state:u64,xhci_state:u64,phys_state:u64) -> u64 {
    if input_state==0 || xhci_state==0 || phys_state==0 { return 0; }
    let diag=volatile_read64(input_state+3976); if diag==0 { return 0; }
    var z:u64=0; while z<12 { unsafe { volatile_write64(diag+704+(z*8),0); } z=z+1; }
    let base=volatile_read64(xhci_state); let op=volatile_read64(xhci_state+8);
    if base==0 || op==0 || volatile_read64(xhci_state+56)!=1 { return 0; }
    let hcs1=volatile_read32(base+4); var ports=(hcs1/16777216)%256; if ports>32 { ports=32; }
    var scan:u64=0; var tries:u64=0; var deepest:u64=0; var deep_port:u64=0;
    while tries<8 {
        let port=xhci_reset_connected_port_from(xhci_state,scan);
        if port==0 { tries=8; }
        else {
            scan=port; tries=tries+1;
            let ps=volatile_read32(op+1024+((port-1)*16));
            let speed=(ps/1024)%16;
            var stage:u64=2; var cc:u64=0; var vid:u64=0;
            let slot=xhci_enable_slot(xhci_state);
            if slot==0 { cc=volatile_read64(xhci_state+488)%256; }
            else {
                stage=3;
                if xhci_address_default_device(xhci_state,phys_state)==0 { cc=volatile_read64(xhci_state+488)%256; }
                else {
                    stage=4;
                    if xhci_get_device_descriptor8(xhci_state,phys_state)==0 { cc=volatile_read64(xhci_state+504)%256; }
                    else {
                        stage=5;
                        if xhci_finalize_address_and_descriptor(xhci_state,phys_state)==0 { cc=volatile_read64(xhci_state+488)%256; }
                        else { stage=6; vid=volatile_read64(xhci_state+272)%65536; }
                    }
                }
            }
            let packed=(port%256)+((speed%16)*256)+((stage%16)*4096)+((cc%256)*65536);
            if tries<=8 { unsafe { volatile_write64(diag+696+(tries*8),packed); } }
            if stage>deepest {
                deepest=stage; deep_port=port;
                unsafe {
                    volatile_write64(diag+768,port); volatile_write64(diag+776,ps);
                    volatile_write64(diag+784,vid); volatile_write64(diag+792,(stage%256)+((cc%256)*256));
                }
            }
        }
    }
    unsafe { volatile_write64(diag+800,tries); volatile_write64(diag+808,deepest); }
    return deepest;
}
'''
needle='fn serial_marker_hwcompat_cpu_ok() -> void {'
if s.count(needle)!=1:
    raise SystemExit(f'r62 helper insertion: expected 1 site, found {s.count(needle)}')
s=s.replace(needle,helpers+'\n'+needle,1)

old='ptrtrace_init(input_state,phys_state);\n    pointer_diag_panel(surface,input_state,gui_state);'
new='ptrtrace_init(input_state,phys_state);\n    let r62_usb_depth=r62_xhci_root_port_trace(input_state,xhci,phys_state);\n    pointer_diag_panel(surface,input_state,gui_state);'
if s.count(old)!=1:
    raise SystemExit(f'r62 trace call: expected 1 site, found {s.count(old)}')
s=s.replace(old,new,1)

old='if flight_saved==0 && read_tsc()>=flight_save_at { flight_saved=1; ptrtrace_save_usb(input_state,xhci,phys_state); pointer_diag_panel(surface,input_state,gui_state); display_shadow_present_rect(surface,(8*65536)+8,(960*65536)+258); }'
new='if flight_saved==0 && read_tsc()>=flight_save_at { flight_saved=1; let r62_diag=volatile_read64(input_state+3976); if r62_diag!=0 { unsafe { volatile_write64(r62_diag+632,2); } } pointer_diag_panel(surface,input_state,gui_state); display_shadow_present_rect(surface,(8*65536)+8,(960*65536)+258); }'
if s.count(old)!=1:
    raise SystemExit(f'r62 autosave disable: expected 1 site, found {s.count(old)}')
s=s.replace(old,new,1)

old='pointer_diag_row(surface,(330*65536)+230,82+(69*256)+(67*65536)+(83*16777216),r58_recs);                                  // RECS\n'
new='pointer_diag_row(surface,(330*65536)+230,82+(69*256)+(67*65536)+(83*16777216),r58_recs);                                  // RECS\n    var r62i:u64=0; while r62i<8 { var rv:u64=0; if diag!=0 { rv=volatile_read64(diag+704+(r62i*8)); } let lab=80+((49+r62i)*256)+(32*65536)+(32*16777216); pointer_diag_row(surface,(330*65536)+242+(r62i*12),lab,rv); r62i=r62i+1; }\n    var dp:u64=0; var dps:u64=0; var dv:u64=0; var ds:u64=0; var dt:u64=0; if diag!=0 { dp=volatile_read64(diag+768); dps=volatile_read64(diag+776); dv=volatile_read64(diag+784); ds=volatile_read64(diag+792); dt=volatile_read64(diag+800); }\n    pointer_diag_row(surface,(330*65536)+338,68+(80*256)+(82*65536)+(84*16777216),dp); // DPRT\n    pointer_diag_row(surface,(330*65536)+350,80+(83*256)+(67*65536)+(32*16777216),dps); // PSC \n    pointer_diag_row(surface,(330*65536)+362,68+(86*256)+(73*65536)+(68*16777216),dv); // DVID\n    pointer_diag_row(surface,(330*65536)+374,68+(83*256)+(67*65536)+(67*16777216),ds); // DSCC\n    pointer_diag_row(surface,(330*65536)+386,80+(67*256)+(78*65536)+(84*16777216),dt); // PCNT\n'
if s.count(old)!=1:
    raise SystemExit(f'r62 rows: expected 1 site, found {s.count(old)}')
s=s.replace(old,new,1)

old_title='pointer_diag_draw_tag4(surface,(78*65536)+18,82+(53*256)+(57*65536)+(32*16777216),green);    // R59'
new_title='pointer_diag_draw_tag4(surface,(78*65536)+18,82+(54*256)+(50*65536)+(32*16777216),green);    // R62'
if s.count(old_title)!=1:
    raise SystemExit(f'r62 title: expected 1 R59 title site, found {s.count(old_title)}')
s=s.replace(old_title,new_title,1)

p.write_text(s)
