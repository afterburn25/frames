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

def marker_fn(name,text):
    vals=' '.join(f'serial_putc({ord(c)});' for c in text)
    return f'fn {name}() -> void {{ {vals} return; }}\n'
# --- context menu behavior ---
serial_anchor='fn serial_marker_v108_window_drag_ok() -> void {'
idx=s.find(serial_anchor)
if idx<0: raise SystemExit('serial anchor missing')
extra=(marker_fn('serial_marker_v108_context_hover_ok','FRAMES_V108_CONTEXT_HOVER_OK\\n')+
       marker_fn('serial_marker_v108_context_select_ok','FRAMES_V108_CONTEXT_SELECT_OK\\n')+
       marker_fn('serial_marker_v108_context_dismiss_ok','FRAMES_V108_CONTEXT_DISMISS_OK\\n')+
       marker_fn('serial_marker_v108_context_outside_ok','FRAMES_V108_CONTEXT_OUTSIDE_DISMISS_OK\\n')+
       marker_fn('serial_marker_v108_context_repeat_ok','FRAMES_V108_CONTEXT_REPEAT_OK\\n'))
s=s[:idx]+extra+s[idx:]

anchor='fn v108_desktop_context_draw_v116(surface:u64,state:u64) -> u64 {'
helper='''fn v108_context_geometry_v118(surface:u64,state:u64) -> u64 {
    if surface==0 || state==0 { return 0; } let sw=volatile_read64(surface+16); let sh=volatile_read64(surface+24); var x=volatile_read64(state+136); var y=volatile_read64(state+144); let w:u64=176; let h:u64=126;
    if x+w>=sw { if sw>w+8 { x=sw-w-8; } else { x=0; } } if y+h>=sh { if sh>h+8 { y=sh-h-8; } else { y=0; } }
    unsafe { volatile_write64(state+272,x); volatile_write64(state+280,y); } return 1;
}
fn v108_context_hit_v118(surface:u64,state:u64,x:u64,y:u64) -> u64 {
    if surface==0 || state==0 || volatile_read64(state+128)==0 { return 0; } if v108_context_geometry_v118(surface,state)==0 { return 0; }
    let mx=volatile_read64(state+272); let my=volatile_read64(state+280); if x<mx+8 || x>=mx+168 || y<my+8 || y>=my+116 { return 0; }
    if y>=my+8 && y<my+32 { return 1; } if y>=my+36 && y<my+60 { return 2; } if y>=my+64 && y<my+88 { return 3; } if y>=my+92 && y<my+116 { return 4; } return 0;
}
'''
rep(anchor,helper+'fn v108_desktop_context_draw_v118(surface:u64,state:u64) -> u64 {')
old='''    let sw=volatile_read64(surface+16); let sh=volatile_read64(surface+24); var x=volatile_read64(state+136); var y=volatile_read64(state+144); let w:u64=176; let h:u64=126; if x+w>=sw { if sw>w+8 { x=sw-w-8; } else { x=0; } } if y+h>=sh { if sh>h+8 { y=sh-h-8; } else { y=0; } }
    let shadow:u64=4278717716; let border:u64=4283268350; let bg:u64=4280298820; let item:u64=4280953426; let white:u64=4294244347;
    display_fill_rect(surface,((x+5)*65536)+(y+5),(w*65536)+h,shadow); display_fill_rect(surface,(x*65536)+y,(w*65536)+h,border); display_fill_rect(surface,((x+2)*65536)+(y+2),((w-4)*65536)+(h-4),bg);
    display_fill_rect(surface,((x+8)*65536)+(y+8),((w-16)*65536)+24,item); display_fill_rect(surface,((x+8)*65536)+(y+36),((w-16)*65536)+24,item); display_fill_rect(surface,((x+8)*65536)+(y+64),((w-16)*65536)+24,item); display_fill_rect(surface,((x+8)*65536)+(y+92),((w-16)*65536)+24,item);
'''
new='''    if v108_context_geometry_v118(surface,state)==0 { return 0; } let x=volatile_read64(state+272); let y=volatile_read64(state+280); let w:u64=176; let h:u64=126;
    let shadow:u64=4278717716; let border:u64=4283268350; let bg:u64=4280298820; let item:u64=4280953426; let hover:u64=4283268350; let white:u64=4294244347; let sel=volatile_read64(state+240);
    display_fill_rect(surface,((x+5)*65536)+(y+5),(w*65536)+h,shadow); display_fill_rect(surface,(x*65536)+y,(w*65536)+h,border); display_fill_rect(surface,((x+2)*65536)+(y+2),((w-4)*65536)+(h-4),bg);
    var i1=item; var i2=item; var i3=item; var i4=item; if sel==1 { i1=hover; } if sel==2 { i2=hover; } if sel==3 { i3=hover; } if sel==4 { i4=hover; }
    display_fill_rect(surface,((x+8)*65536)+(y+8),((w-16)*65536)+24,i1); display_fill_rect(surface,((x+8)*65536)+(y+36),((w-16)*65536)+24,i2); display_fill_rect(surface,((x+8)*65536)+(y+64),((w-16)*65536)+24,i3); display_fill_rect(surface,((x+8)*65536)+(y+92),((w-16)*65536)+24,i4);
'''
rep(old,new)
s=s.replace('v108_desktop_context_draw_v116(surface,state)','v108_desktop_context_draw_v118(surface,state)')
old='''    unsafe { volatile_write64(state+8,x); volatile_write64(state+16,y); } return 1;
}
fn gui_input_buttons(state:u64,wm:u64,buttons:u64,surface:u64) -> u64 {
'''
new='''    if volatile_read64(state+128)!=0 { let before=volatile_read64(state+240); let now=v108_context_hit_v118(surface,state,x,y); if now!=before { unsafe { volatile_write64(state+240,now); } if now!=0 && volatile_read64(state+288)==0 { unsafe { volatile_write64(state+288,1); } serial_marker_v108_context_hover_ok(); } } }
    unsafe { volatile_write64(state+8,x); volatile_write64(state+16,y); } return 1;
}
fn gui_input_buttons(state:u64,wm:u64,buttons:u64,surface:u64) -> u64 {
'''
rep(old,new)
s=s.replace('fn gui_input_pointer_move(state:u64,wm:u64,raw:u64,axis:u64) -> u64 {','fn gui_input_pointer_move(state:u64,wm:u64,surface:u64,raw:u64,axis:u64) -> u64 {',1)
s=s.replace('gui_input_pointer_move(state,wm,value,1)','gui_input_pointer_move(state,wm,surface,value,1)')
s=s.replace('gui_input_pointer_move(state,wm,value,2)','gui_input_pointer_move(state,wm,surface,value,2)')
s=s.replace('gui_input_pointer_move(state,wm,12,1)','gui_input_pointer_move(state,wm,surface,12,1)')
s=s.replace('gui_input_pointer_move(state,wm,8,2)','gui_input_pointer_move(state,wm,surface,8,2)')
s=s.replace('gui_input_pointer_move(state,wm,10,1)','gui_input_pointer_move(state,wm,surface,10,1)')
s=s.replace('gui_input_pointer_move(state,wm,10,2)','gui_input_pointer_move(state,wm,surface,10,2)')
p.write_text(s)
