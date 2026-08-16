#!/usr/bin/env python3
from pathlib import Path
import sys

if len(sys.argv) != 2:
    raise SystemExit('usage: instrument_v72_file_manager.py PATH_TO_kernel_main.nx')

p=Path(sys.argv[1])
s=p.read_text()
start_marker='fn file_manager_phase1_compose(state:u64,surface:u64,process:u64,wm:u64) -> u64 {'
end_marker='\nfn serial_marker_settings_window_ok() -> void {'
start=s.find(start_marker)
if start < 0:
    raise SystemExit('file_manager_phase1_compose not found')
end=s.find(end_marker,start)
if end < 0:
    raise SystemExit('settings marker boundary not found after file manager')
new='''fn file_manager_phase1_compose(state:u64,surface:u64,process:u64,wm:u64) -> u64 {
    serial_desktop_diag(85,state); serial_desktop_diag(86,surface); serial_desktop_diag(87,process); serial_desktop_diag(88,wm);
    if state==0 || surface==0 || process==0 || wm==0 { return 0; }
    let vfs=volatile_read64(process+464); let path=volatile_read64(process+520); let sec=volatile_read64(process+528); let helix=volatile_read64(process+1008);
    serial_desktop_diag(89,vfs); serial_desktop_diag(90,path); serial_desktop_diag(91,sec); serial_desktop_diag(92,helix);
    if vfs==0 || path==0 || sec==0 || helix==0 { return 0; }
    let mounts=volatile_read64(vfs+8); serial_desktop_diag(93,mounts); if mounts<5 { return 0; }
    serial_marker_fileman_vfs_ok();
    let value=helixfs_path_read_u64(helix,path,sec,401); let checksum=helixfs_path_traverse_checksum(helix,path,sec);
    serial_desktop_diag(94,value); serial_desktop_diag(95,checksum);
    if value!=6434604069960107346 || checksum!=8256 { return 0; }
    serial_marker_fileman_helix_ok();
    let desktop=volatile_read64(process+1064); serial_desktop_diag(96,desktop); if desktop==0 { return 0; }
    let sw=volatile_read64(desktop+8); let id=wm_create(wm,(42*65536)+146,(470*65536)+330,5); serial_desktop_diag(97,id);
    let focus_ok=wm_focus(wm,id); serial_desktop_diag(98,focus_ok); if id!=4 || focus_ok==0 { return 0; }
    let rec=wm_record(wm,id); serial_desktop_diag(99,rec); if rec==0 || wm_render_window(surface,rec,1,4285661183)==0 { return 0; }
    let x=volatile_read64(rec+8); let y=volatile_read64(rec+16); let rail:u64=4280034105; let row:u64=4280953426; let accent:u64=4285661183;
    if display_fill_rect(surface,((x+14)*65536)+(y+48),(110*65536)+264,rail)==0 { return 0; }
    var i:u64=0; while i<4 { if display_fill_rect(surface,((x+142)*65536)+(y+56+(i*48)),(292*65536)+34,row)==0 { return 0; } i=i+1; }
    if display_fill_rect(surface,((x+142)*65536)+(y+104),(292*65536)+34,accent)==0 { return 0; }
    serial_marker_fileman_window_ok();
    zero_page(state); unsafe { volatile_write64(state,1); volatile_write64(state+8,id); volatile_write64(state+16,mounts); volatile_write64(state+24,4); volatile_write64(state+32,2); volatile_write64(state+40,value); volatile_write64(state+48,checksum); volatile_write64(state+56,1); }
    let dirty=volatile_read64(process+624); let timing=volatile_read64(process+664); let present=volatile_read64(process+672); let cursor=volatile_read64(process+640); let sh=volatile_read64(desktop+16);
    if dirty==0 || timing==0 || present==0 || cursor==0 { return 0; }
    if desktop_draw_cursor(surface,volatile_read64(cursor+16),volatile_read64(cursor+24))==0 { return 0; }
    if dirty_add(dirty,0,(sw*65536)+sh,16)==0 || present_enqueue(present,0,(sw*65536)+sh,16)==0 || present_flush(present,surface,timing)==0 { return 0; }
    serial_desktop_diag(50,mounts); serial_desktop_diag(51,4); serial_desktop_diag(52,2); serial_desktop_diag(53,value); serial_desktop_diag(54,checksum); serial_desktop_diag(55,id); serial_marker_fileman_phase1_ok(); serial_marker_desktop_phase8_ok(); return 1;
}
'''
ns=s[:start]+new+s[end:]
# Structural guard: the next phase must remain defined after the replacement.
if 'fn settings_phase1_compose(state:u64,surface:u64,process:u64,wm:u64) -> u64 {' not in ns:
    raise SystemExit('settings_phase1_compose lost during instrumentation')
p.write_text(ns)
print('instrumented file_manager_phase1_compose stages 85-99 with bounded replacement')
