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

# Right click only anchors when closed; left click on open menu selects/dismisses and consumes click.
old='''    let right=(buttons/2)%2; let old_right=(old/2)%2; if right!=0 && old_right==0 { unsafe { volatile_write64(state+128,1); volatile_write64(state+136,x); volatile_write64(state+144,y); volatile_write64(state+152,volatile_read64(state+152)+1); } serial_marker_v108_desktop_context_ok(); return 1; }
    if buttons%2!=0 && old%2==0 {
        if volatile_read64(state+128)!=0 { unsafe { volatile_write64(state+128,0); } }
'''
new='''    let right=(buttons/2)%2; let old_right=(old/2)%2; if right!=0 && old_right==0 { if volatile_read64(state+128)==0 { let opens=volatile_read64(state+152)+1; unsafe { volatile_write64(state+128,1); volatile_write64(state+136,x); volatile_write64(state+144,y); volatile_write64(state+152,opens); volatile_write64(state+240,0); volatile_write64(state+288,0); } serial_marker_v108_desktop_context_ok(); if opens>=2 { serial_marker_v108_context_repeat_ok(); } } return 1; }
    if buttons%2!=0 && old%2==0 {
        if volatile_read64(state+128)!=0 { let hit=v108_context_hit_v118(surface,state,x,y); unsafe { volatile_write64(state+248,volatile_read64(state+248)+1); volatile_write64(state+256,hit); volatile_write64(state+128,0); volatile_write64(state+240,0); volatile_write64(state+264,volatile_read64(state+264)+1); } if hit!=0 { serial_marker_v108_context_select_ok(); } else { serial_marker_v108_context_outside_ok(); } serial_marker_v108_context_dismiss_ok(); return 1; }
'''
rep(old,new)

old='''volatile_write64(state+208,panel_y); volatile_write64(state+216,0); volatile_write64(state+224,0); volatile_write64(state+232,0); }
'''
new='''volatile_write64(state+208,panel_y); volatile_write64(state+216,0); volatile_write64(state+224,0); volatile_write64(state+232,0); volatile_write64(state+240,0); volatile_write64(state+248,0); volatile_write64(state+256,0); volatile_write64(state+264,0); volatile_write64(state+272,0); volatile_write64(state+280,0); volatile_write64(state+288,0); }
'''
rep(old,new)

anchor='fn v108_desktop_interaction_repaint_v116(process:u64,state:u64,input_state:u64,xhci:u64) -> u64 {'
menu_present='''fn v108_context_present_v118(process:u64,state:u64,cursor:u64) -> u64 {
    let surface=volatile_read64(process+616); let dirty=volatile_read64(process+624); let timing=volatile_read64(process+664); let present=volatile_read64(process+672); if surface==0 || dirty==0 || timing==0 || present==0 || cursor==0 || volatile_read64(state+128)==0 { return 0; }
    let cx=volatile_read64(state+8); let cy=volatile_read64(state+16); v108_cursor_restore(cursor,surface); if v108_desktop_context_draw_v118(surface,state)==0 { return 0; } if v108_cursor_capture(cursor,surface,cx,cy)==0 { return 0; } if v108_input_pointer_draw_v115(surface,state,0)==0 { return 0; }
    let x=volatile_read64(state+272); let y=volatile_read64(state+280); dirty_add(dirty,(x*65536)+y,(182*65536)+132,16); present_enqueue(present,(x*65536)+y,(182*65536)+132,16); dirty_add(dirty,(cx*65536)+cy,(8*65536)+16,16); present_enqueue(present,(cx*65536)+cy,(8*65536)+16,16); if present_flush(present,surface,timing)==0 { return 0; } return 1;
}
'''
rep(anchor,menu_present+anchor)
s=s.replace('if v108_input_pointer_draw_v115(surface,state,0)==0 { return 0; }','if desktop_draw_cursor(surface,cx,cy)==0 { return 0; }',1)

old='''        var telemetry_redraw:u64=0; var test_redraw:u64=0; var pointer_changed:u64=0; var desktop_redraw:u64=0;
        let raw_now=volatile_read64(input_state+3224); if raw_now!=last_raw { if raw_now>last_raw { raw_budget=raw_budget+(raw_now-last_raw); } last_raw=raw_now; if raw_budget>=24 { raw_budget=0; telemetry_redraw=1; } }
'''
new='''        var telemetry_redraw:u64=0; var test_redraw:u64=0; var pointer_changed:u64=0; var desktop_redraw:u64=0; var menu_redraw:u64=0;
        let raw_now=volatile_read64(input_state+3224); if raw_now!=last_raw { last_raw=raw_now; unsafe { volatile_write64(input_state+4056,read_tsc()); volatile_write64(input_state+4064,1); } }
'''
rep(old,new)
old='''                        if kind==5 || kind==6 { pointer_changed=1; if volatile_read64(state+176)!=0 { desktop_redraw=1; } }
'''
new='''                        if kind==5 || kind==6 { let menu_before=volatile_read64(state+240); pointer_changed=1; if volatile_read64(state+176)!=0 { desktop_redraw=1; } if volatile_read64(state+128)!=0 && volatile_read64(state+240)!=menu_before { menu_redraw=1; } }
'''
rep(old,new)
old='''                if kind==4 || kind==5 || kind==6 {
                    if gui_input_dispatch(state,wm,event,surface)!=0 {
'''
new='''                if kind==4 || kind==5 || kind==6 {
                    let menu_before=volatile_read64(state+240); let context_before=volatile_read64(state+128); if gui_input_dispatch(state,wm,event,surface)!=0 {
'''
rep(old,new)
s=s.replace('if kind==5 || kind==6 { let menu_before=volatile_read64(state+240); pointer_changed=1;','if kind==5 || kind==6 { pointer_changed=1;',1)
old='''        let newx=volatile_read64(state+8); let newy=volatile_read64(state+16);
        if desktop_redraw!=0 { if v108_desktop_interaction_repaint_v116(process,state,input_state,xhci)==0 { return 0; } pointer_changed=0; test_redraw=0; telemetry_redraw=0; }
'''
new='''        let newx=volatile_read64(state+8); let newy=volatile_read64(state+16);
        if volatile_read64(input_state+4064)!=0 { let moved=volatile_read64(input_state+4056); let now_idle=read_tsc(); if moved!=0 && now_idle>moved && now_idle-moved>180000000 { unsafe { volatile_write64(input_state+4064,0); } telemetry_redraw=1; } }
        if desktop_redraw!=0 { if v108_desktop_interaction_repaint_v116(process,state,input_state,xhci)==0 { return 0; } pointer_changed=0; test_redraw=0; telemetry_redraw=0; menu_redraw=0; }
'''
rep(old,new)
old='''        if pointer_changed!=0 && (newx!=oldx || newy!=oldy) {
'''
new='''        if menu_redraw!=0 && desktop_redraw==0 { if v108_context_present_v118(process,state,cursor)==0 { return 0; } pointer_changed=0; }
        if pointer_changed!=0 && (newx!=oldx || newy!=oldy) {
'''
rep(old,new)
p.write_text(s)
