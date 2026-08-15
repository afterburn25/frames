#!/usr/bin/env python3
from pathlib import Path
import subprocess, sys

p=Path(sys.argv[1])
here=Path(__file__).resolve().parent
subprocess.check_call([sys.executable, str(here/'make_r63_port2_mouse_enumeration_trace.py'), str(p)])
s=p.read_text()

helpers=r'''
// r64 xHCI EP0/control-transfer transition trace -----------------------------
// diag+808 pre-finalize CC, +816/+824/+832 pre transfer snapshots
// +840 finalize result, +848 post-finalize CC, +856/+864/+872 post snapshots
// +880 VID, +888 HID discover, +896 HID configure, +904 deepest stage
fn r64_ep0_control_trace(input_state:u64,xhci_state:u64,phys_state:u64) -> u64 {
    if input_state==0 || xhci_state==0 || phys_state==0 { return 0; }
    let diag=volatile_read64(input_state+3976); if diag==0 { return 0; }
    var z:u64=0; while z<13 { unsafe { volatile_write64(diag+808+(z*8),0); } z=z+1; }
    let rst=r63_reset_port2(xhci_state); if rst==0 { return 0; }
    unsafe { volatile_write64(diag+904,2); }
    let slot=xhci_enable_slot(xhci_state); if slot==0 { return 2; }
    unsafe { volatile_write64(diag+904,3); }
    let addr=xhci_address_default_device(xhci_state,phys_state); if addr==0 { return 3; }
    unsafe { volatile_write64(diag+904,4); }
    let d8=xhci_get_device_descriptor8(xhci_state,phys_state); if d8==0 { return 4; }
    unsafe {
        volatile_write64(diag+904,5);
        volatile_write64(diag+808,volatile_read64(xhci_state+488));
        volatile_write64(diag+816,volatile_read64(xhci_state+504));
        volatile_write64(diag+824,volatile_read64(xhci_state+512));
        volatile_write64(diag+832,volatile_read64(xhci_state+520));
    }
    let fin=xhci_finalize_address_and_descriptor(xhci_state,phys_state);
    unsafe {
        volatile_write64(diag+840,fin);
        volatile_write64(diag+848,volatile_read64(xhci_state+488));
        volatile_write64(diag+856,volatile_read64(xhci_state+504));
        volatile_write64(diag+864,volatile_read64(xhci_state+512));
        volatile_write64(diag+872,volatile_read64(xhci_state+520));
        volatile_write64(diag+880,volatile_read64(xhci_state+272));
    }
    if fin==0 { return 5; }
    unsafe { volatile_write64(diag+904,6); }
    let hid=xhci_discover_boot_hid(xhci_state,phys_state); unsafe { volatile_write64(diag+888,hid); }
    if hid==0 { return 6; }
    unsafe { volatile_write64(diag+904,7); }
    let cfg=xhci_configure_boot_hid(xhci_state,phys_state); unsafe { volatile_write64(diag+896,cfg); }
    if cfg==0 { return 7; }
    unsafe { volatile_write64(diag+904,8); }
    return 8;
}
'''
needle='fn serial_marker_hwcompat_cpu_ok() -> void {'
if s.count(needle)!=1:
    raise SystemExit(f'r64 helper insertion: expected 1 site, found {s.count(needle)}')
s=s.replace(needle,helpers+'\n'+needle,1)

old='let r63_mouse_depth=r63_port2_mouse_trace(input_state,xhci,phys_state);'
new='let r64_ep0_depth=r64_ep0_control_trace(input_state,xhci,phys_state);'
if s.count(old)!=1:
    raise SystemExit(f'r64 trace call: expected 1 site, found {s.count(old)}')
s=s.replace(old,new,1)

# Replace r63 row block with r64 pre/post-finalize transition rows.
start='    var r63a:u64=0; var r63b:u64=0; var r63c:u64=0; var r63d:u64=0; var r63e:u64=0; var r63f:u64=0; var r63g:u64=0; var r63h:u64=0; var r63i:u64=0; var r63j:u64=0; var r63k:u64=0; var r63l:u64=0; var r63m:u64=0;\n'
end='    pointer_diag_row(surface,(330*65536)+386,68+(69*256)+(80*65536)+(84*16777216),r63m); // DEPT\n'
a=s.find(start)
b=s.find(end,a)
if a<0 or b<0:
    raise SystemExit('r64 rows: r63 block not found')
b += len(end)
rows='''    var q0:u64=0; var q1:u64=0; var q2:u64=0; var q3:u64=0; var q4:u64=0; var q5:u64=0; var q6:u64=0; var q7:u64=0; var q8:u64=0; var q9:u64=0; var q10:u64=0; var q11:u64=0; var q12:u64=0;
    if diag!=0 { q0=volatile_read64(diag+808); q1=volatile_read64(diag+816); q2=volatile_read64(diag+824); q3=volatile_read64(diag+832); q4=volatile_read64(diag+840); q5=volatile_read64(diag+848); q6=volatile_read64(diag+856); q7=volatile_read64(diag+864); q8=volatile_read64(diag+872); q9=volatile_read64(diag+880); q10=volatile_read64(diag+888); q11=volatile_read64(diag+896); q12=volatile_read64(diag+904); }
    pointer_diag_row(surface,(330*65536)+242,80+(67*256)+(67*65536)+(32*16777216),q0);  // PCC
    pointer_diag_row(surface,(330*65536)+254,80+(84*256)+(65*65536)+(32*16777216),q1);  // PTA
    pointer_diag_row(surface,(330*65536)+266,80+(84*256)+(66*65536)+(32*16777216),q2);  // PTB
    pointer_diag_row(surface,(330*65536)+278,80+(84*256)+(67*65536)+(32*16777216),q3);  // PTC
    pointer_diag_row(surface,(330*65536)+290,70+(73*256)+(78*65536)+(32*16777216),q4);  // FIN
    pointer_diag_row(surface,(330*65536)+302,70+(67*256)+(67*65536)+(32*16777216),q5);  // FCC
    pointer_diag_row(surface,(330*65536)+314,70+(84*256)+(65*65536)+(32*16777216),q6);  // FTA
    pointer_diag_row(surface,(330*65536)+326,70+(84*256)+(66*65536)+(32*16777216),q7);  // FTB
    pointer_diag_row(surface,(330*65536)+338,70+(84*256)+(67*65536)+(32*16777216),q8);  // FTC
    pointer_diag_row(surface,(330*65536)+350,86+(73*256)+(68*65536)+(32*16777216),q9);  // VID
    pointer_diag_row(surface,(330*65536)+362,72+(73*256)+(68*65536)+(70*16777216),q10); // HIDF
    pointer_diag_row(surface,(330*65536)+374,72+(73*256)+(68*65536)+(67*16777216),q11); // HIDC
    pointer_diag_row(surface,(330*65536)+386,68+(69*256)+(80*65536)+(84*16777216),q12); // DEPT
'''
s=s[:a]+rows+s[b:]

old_title='pointer_diag_draw_tag4(surface,(78*65536)+18,82+(54*256)+(51*65536)+(32*16777216),green);    // R63'
new_title='pointer_diag_draw_tag4(surface,(78*65536)+18,82+(54*256)+(52*65536)+(32*16777216),green);    // R64'
if s.count(old_title)!=1:
    raise SystemExit(f'r64 title: expected 1 R63 title site, found {s.count(old_title)}')
s=s.replace(old_title,new_title,1)

p.write_text(s)
