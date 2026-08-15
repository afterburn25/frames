#!/usr/bin/env python3
from pathlib import Path
import subprocess, sys

p=Path(sys.argv[1])
here=Path(__file__).resolve().parent
subprocess.check_call([sys.executable, str(here/'make_r59_windows_log_partition.py'), str(p)])
s=p.read_text()

helpers=r'''
// r63 deterministic physical-port-2 mouse enumeration trace ------------------
// diag+704 PORTSC before reset
// +712 PORTSC after reset
// +720 reset result, +728 slot result, +736 Address Device result
// +744 descriptor8 result, +752 finalize/full-descriptor result
// +760 command completion snapshot, +768 transfer snapshot A
// +776 transfer snapshot B, +784 transfer snapshot C
// +792 VID after full descriptor, +800 deepest stage
fn r63_reset_port2(xhci_state:u64) -> u64 {
    if xhci_state==0 || volatile_read64(xhci_state+56)!=1 { return 0; }
    let op=volatile_read64(xhci_state+8); if op==0 { return 0; }
    let port=op+1024+16; let ps=volatile_read32(port);
    if ps%2==0 { return 0; }
    var write=xhci_port_write_base(ps); write=set_flag(write,16);
    unsafe { volatile_write32(port,write); }
    var spins:u64=0;
    while (volatile_read32(port)/16)%2!=0 && spins<5000000 { cpu_pause(); spins=spins+1; }
    if spins>=5000000 { return 0; }
    let done=volatile_read32(port); if done%2==0 { return 0; }
    unsafe { volatile_write64(xhci_state+112,2); volatile_write64(xhci_state+120,done); volatile_write64(xhci_state+128,1); volatile_write64(xhci_state+384,0); volatile_write64(xhci_state+416,0); }
    return 1;
}
fn r63_port2_mouse_trace(input_state:u64,xhci_state:u64,phys_state:u64) -> u64 {
    if input_state==0 || xhci_state==0 || phys_state==0 { return 0; }
    let diag=volatile_read64(input_state+3976); if diag==0 { return 0; }
    var z:u64=0; while z<13 { unsafe { volatile_write64(diag+704+(z*8),0); } z=z+1; }
    let op=volatile_read64(xhci_state+8); if op==0 { return 0; }
    unsafe { volatile_write64(diag+704,volatile_read32(op+1040)); }
    let rst=r63_reset_port2(xhci_state); unsafe { volatile_write64(diag+720,rst); volatile_write64(diag+712,volatile_read32(op+1040)); }
    if rst==0 { return 0; }
    unsafe { volatile_write64(diag+800,2); }
    let slot=xhci_enable_slot(xhci_state); unsafe { volatile_write64(diag+728,slot); volatile_write64(diag+760,volatile_read64(xhci_state+488)); }
    if slot==0 { return 2; }
    unsafe { volatile_write64(diag+800,3); }
    let addr=xhci_address_default_device(xhci_state,phys_state); unsafe { volatile_write64(diag+736,addr); volatile_write64(diag+760,volatile_read64(xhci_state+488)); }
    if addr==0 { return 3; }
    unsafe { volatile_write64(diag+800,4); }
    let d8=xhci_get_device_descriptor8(xhci_state,phys_state);
    unsafe { volatile_write64(diag+744,d8); volatile_write64(diag+768,volatile_read64(xhci_state+504)); volatile_write64(diag+776,volatile_read64(xhci_state+512)); volatile_write64(diag+784,volatile_read64(xhci_state+520)); }
    if d8==0 { return 4; }
    unsafe { volatile_write64(diag+800,5); }
    let fin=xhci_finalize_address_and_descriptor(xhci_state,phys_state);
    unsafe { volatile_write64(diag+752,fin); volatile_write64(diag+760,volatile_read64(xhci_state+488)); volatile_write64(diag+768,volatile_read64(xhci_state+504)); volatile_write64(diag+776,volatile_read64(xhci_state+512)); volatile_write64(diag+784,volatile_read64(xhci_state+520)); volatile_write64(diag+792,volatile_read64(xhci_state+272)); }
    if fin==0 { return 5; }
    unsafe { volatile_write64(diag+800,6); }
    return 6;
}
'''
needle='fn serial_marker_hwcompat_cpu_ok() -> void {'
if s.count(needle)!=1:
    raise SystemExit(f'r63 helper insertion: expected 1 site, found {s.count(needle)}')
s=s.replace(needle,helpers+'\n'+needle,1)

old='ptrtrace_init(input_state,phys_state);\n    pointer_diag_panel(surface,input_state,gui_state);'
new='ptrtrace_init(input_state,phys_state);\n    let r63_mouse_depth=r63_port2_mouse_trace(input_state,xhci,phys_state);\n    pointer_diag_panel(surface,input_state,gui_state);'
if s.count(old)!=1:
    raise SystemExit(f'r63 trace call: expected 1 site, found {s.count(old)}')
s=s.replace(old,new,1)

old='if flight_saved==0 && read_tsc()>=flight_save_at { flight_saved=1; ptrtrace_save_usb(input_state,xhci,phys_state); pointer_diag_panel(surface,input_state,gui_state); display_shadow_present_rect(surface,(8*65536)+8,(960*65536)+258); }'
new='if flight_saved==0 && read_tsc()>=flight_save_at { flight_saved=1; let r63_diag=volatile_read64(input_state+3976); if r63_diag!=0 { unsafe { volatile_write64(r63_diag+632,2); } } pointer_diag_panel(surface,input_state,gui_state); display_shadow_present_rect(surface,(8*65536)+8,(960*65536)+258); }'
if s.count(old)!=1:
    raise SystemExit(f'r63 autosave disable: expected 1 site, found {s.count(old)}')
s=s.replace(old,new,1)

old='pointer_diag_row(surface,(330*65536)+230,82+(69*256)+(67*65536)+(83*16777216),r58_recs);                                  // RECS\n'
new='''pointer_diag_row(surface,(330*65536)+230,82+(69*256)+(67*65536)+(83*16777216),r58_recs);                                  // RECS
    var r63a:u64=0; var r63b:u64=0; var r63c:u64=0; var r63d:u64=0; var r63e:u64=0; var r63f:u64=0; var r63g:u64=0; var r63h:u64=0; var r63i:u64=0; var r63j:u64=0; var r63k:u64=0; var r63l:u64=0; var r63m:u64=0;
    if diag!=0 { r63a=volatile_read64(diag+704); r63b=volatile_read64(diag+712); r63c=volatile_read64(diag+720); r63d=volatile_read64(diag+728); r63e=volatile_read64(diag+736); r63f=volatile_read64(diag+744); r63g=volatile_read64(diag+752); r63h=volatile_read64(diag+760); r63i=volatile_read64(diag+768); r63j=volatile_read64(diag+776); r63k=volatile_read64(diag+784); r63l=volatile_read64(diag+792); r63m=volatile_read64(diag+800); }
    pointer_diag_row(surface,(330*65536)+242,80+(66*256)+(69*65536)+(70*16777216),r63a); // PBEF
    pointer_diag_row(surface,(330*65536)+254,80+(65*256)+(70*65536)+(84*16777216),r63b); // PAFT
    pointer_diag_row(surface,(330*65536)+266,82+(83*256)+(84*65536)+(32*16777216),r63c); // RST
    pointer_diag_row(surface,(330*65536)+278,83+(76*256)+(79*65536)+(84*16777216),r63d); // SLOT
    pointer_diag_row(surface,(330*65536)+290,65+(68*256)+(68*65536)+(82*16777216),r63e); // ADDR
    pointer_diag_row(surface,(330*65536)+302,68+(56*256)+(32*65536)+(32*16777216),r63f); // D8
    pointer_diag_row(surface,(330*65536)+314,70+(73*256)+(78*65536)+(32*16777216),r63g); // FIN
    pointer_diag_row(surface,(330*65536)+326,67+(67*256)+(32*65536)+(32*16777216),r63h); // CC
    pointer_diag_row(surface,(330*65536)+338,84+(82*256)+(65*65536)+(32*16777216),r63i); // TRA
    pointer_diag_row(surface,(330*65536)+350,84+(82*256)+(66*65536)+(32*16777216),r63j); // TRB
    pointer_diag_row(surface,(330*65536)+362,84+(82*256)+(67*65536)+(32*16777216),r63k); // TRC
    pointer_diag_row(surface,(330*65536)+374,86+(73*256)+(68*65536)+(32*16777216),r63l); // VID
    pointer_diag_row(surface,(330*65536)+386,68+(69*256)+(80*65536)+(84*16777216),r63m); // DEPT
'''
if s.count(old)!=1:
    raise SystemExit(f'r63 rows: expected 1 site, found {s.count(old)}')
s=s.replace(old,new,1)

old_title='pointer_diag_draw_tag4(surface,(78*65536)+18,82+(53*256)+(57*65536)+(32*16777216),green);    // R59'
new_title='pointer_diag_draw_tag4(surface,(78*65536)+18,82+(54*256)+(51*65536)+(32*16777216),green);    // R63'
if s.count(old_title)!=1:
    raise SystemExit(f'r63 title: expected 1 R59 title site, found {s.count(old_title)}')
s=s.replace(old_title,new_title,1)

p.write_text(s)
