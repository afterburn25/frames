from pathlib import Path
import hashlib,sys
p=Path(sys.argv[1]); raw=p.read_bytes(); actual=hashlib.sha256(raw).hexdigest(); expected='2401b3a460430da6b008716e65f7be10dfb8e289da48b12045e1e1b920ed6caf'
if actual!=expected: raise SystemExit(f'unexpected r14 source hash {actual}')
s=raw.decode()

def fn_span(text,name):
    st=text.index(name); op=text.index('{',st); d=0
    for j in range(op,len(text)):
        if text[j]=='{': d+=1
        elif text[j]=='}':
            d-=1
            if d==0:return st,j+1
    raise RuntimeError(name)

def repl_fn(name,new):
    global s
    a,b=fn_span(s,name); s=s[:a]+new+s[b:]

def marker_fn(name,text):
    return 'fn '+name+'() -> void { '+' '.join(f'serial_putc({ord(c)});' for c in text+'\n')+' return; }\n'

# r15 text-edit state slots in the unused tail of the one-page input state.
# 3976 caret index, 3984 blink phase, 3992 blink TSC, 4000 I-beam marker guard,
# 4008 caret marker guard, 4016 left count, 4024 right count, 4032 delete count, 4040 blink marker guard.
insert=s.index('fn v108_input_test_draw')
helpers = marker_fn('serial_marker_v108_text_ibeam_ok','FRAMES_V108_TEXT_IBEAM_OK')
helpers += marker_fn('serial_marker_v108_text_caret_ok','FRAMES_V108_TEXT_CARET_OK')
helpers += marker_fn('serial_marker_v108_text_blink_ok','FRAMES_V108_TEXT_CARET_BLINK_OK')
helpers += marker_fn('serial_marker_v108_text_left_ok','FRAMES_V108_TEXT_LEFT_OK')
helpers += marker_fn('serial_marker_v108_text_right_ok','FRAMES_V108_TEXT_RIGHT_OK')
helpers += marker_fn('serial_marker_v108_text_delete_ok','FRAMES_V108_TEXT_DELETE_OK')
helpers += r'''fn v108_input_text_hover_v115(state:u64) -> u64 {
    if state==0 { return 0; } let x=volatile_read64(state+8); let y=volatile_read64(state+16); let py=v108_test_y(state);
    if x>=60 && x<640 && y>=py+62 && y<py+110 { return 1; } return 0;
}
fn v108_draw_ibeam_v115(surface:u64,x:u64,y:u64) -> u64 {
    if surface==0 || volatile_read64(surface)!=1 { return 0; } let white:u64=4294244347; let dark:u64=4279244839;
    if display_fill_rect(surface,((x+3)*65536)+y,(2*65536)+16,dark)==0 { return 0; }
    if display_fill_rect(surface,((x+4)*65536)+(y+1),(1*65536)+14,white)==0 { return 0; }
    if display_fill_rect(surface,(x*65536)+y,(8*65536)+2,dark)==0 { return 0; }
    if display_fill_rect(surface,(x*65536)+(y+14),(8*65536)+2,dark)==0 { return 0; }
    return 1;
}
fn v108_input_pointer_draw_v115(surface:u64,state:u64,input_state:u64) -> u64 {
    if state==0 || input_state==0 { return 0; } let x=volatile_read64(state+8); let y=volatile_read64(state+16);
    if v108_input_text_hover_v115(state)!=0 { if volatile_read64(input_state+4000)==0 { unsafe { volatile_write64(input_state+4000,1); } serial_marker_v108_text_ibeam_ok(); } return v108_draw_ibeam_v115(surface,x,y); }
    return desktop_draw_cursor(surface,x,y);
}
fn v108_input_text_reset_blink_v115(input_state:u64) -> void {
    if input_state==0 { return; } unsafe { volatile_write64(input_state+3984,1); volatile_write64(input_state+3992,read_tsc()); } return;
}
fn v108_input_test_key_v115(input_state:u64,sc:u64) -> u64 {
    if input_state==0 || volatile_read64(input_state+3672)==0 { return 0; }
    let len=volatile_read64(input_state+3680); var caret=volatile_read64(input_state+3976); if caret>len { caret=len; unsafe { volatile_write64(input_state+3976,caret); } }
    if sc==75 { if caret>0 { caret=caret-1; unsafe { volatile_write64(input_state+3976,caret); } } unsafe { volatile_write64(input_state+4016,volatile_read64(input_state+4016)+1); } v108_input_text_reset_blink_v115(input_state); if volatile_read64(input_state+4016)==1 { serial_marker_v108_text_left_ok(); } return 1; }
    if sc==77 { if caret<len { caret=caret+1; unsafe { volatile_write64(input_state+3976,caret); } } unsafe { volatile_write64(input_state+4024,volatile_read64(input_state+4024)+1); } v108_input_text_reset_blink_v115(input_state); if volatile_read64(input_state+4024)==1 { serial_marker_v108_text_right_ok(); } return 1; }
    if sc==71 { unsafe { volatile_write64(input_state+3976,0); } v108_input_text_reset_blink_v115(input_state); return 1; }
    if sc==79 { unsafe { volatile_write64(input_state+3976,len); } v108_input_text_reset_blink_v115(input_state); return 1; }
    if sc==83 {
        if caret<len { var i=caret; while i+1<len { unsafe { volatile_write8(input_state+3776+i,volatile_read8(input_state+3776+i+1)); } i=i+1; } unsafe { volatile_write8(input_state+3776+len-1,0); volatile_write64(input_state+3680,len-1); } }
        unsafe { volatile_write64(input_state+4032,volatile_read64(input_state+4032)+1); } v108_input_text_reset_blink_v115(input_state); if volatile_read64(input_state+4032)==1 { serial_marker_v108_text_delete_ok(); } return 1;
    }
    return 0;
}
'''
s=s[:insert]+helpers+s[insert:]

old='''    let len=volatile_read64(input_state+3680); var i:u64=0; while i<len && i<64 { let c=volatile_read8(input_state+3776+i); if c>=32 && c<=126 { gui_draw_char_scaled(surface,((x+30+(i*8))*65536)+(y+78),(c*65536)+1,white); } i=i+1; }'''
new='''    let len=volatile_read64(input_state+3680); var i:u64=0; while i<len && i<64 { let c=volatile_read8(input_state+3776+i); if c>=32 && c<=126 { gui_draw_char_scaled(surface,((x+30+(i*8))*65536)+(y+78),(c*65536)+1,white); } i=i+1; }
    if volatile_read64(input_state+3672)!=0 { var caret=volatile_read64(input_state+3976); if caret>len { caret=len; unsafe { volatile_write64(input_state+3976,caret); } } if volatile_read64(input_state+3984)!=0 { let caret_x=x+30+(caret*8); display_fill_rect(surface,(caret_x*65536)+(y+75),(2*65536)+20,white); if volatile_read64(input_state+4008)==0 { unsafe { volatile_write64(input_state+4008,1); } serial_marker_v108_text_caret_ok(); } } }'''
assert s.count(old)==1
s=s.replace(old,new,1)

s=s.replace('if v108_cursor_capture(cursor,surface,cx,cy)==0 { return 0; } if desktop_draw_cursor(surface,cx,cy)==0 { return 0; }','if v108_cursor_capture(cursor,surface,cx,cy)==0 { return 0; } if v108_input_pointer_draw_v115(surface,state,input_state)==0 { return 0; }',1)

old='''    if x>=60 && x<640 && y>=py+62 && y<py+110 { unsafe { volatile_write64(input_state+3672,1); } return 1; }'''
new='''    if x>=60 && x<640 && y>=py+62 && y<py+110 { let len=volatile_read64(input_state+3680); var caret:u64=0; if x>70 { caret=(x-70)/8; } if caret>len { caret=len; } unsafe { volatile_write64(input_state+3672,1); volatile_write64(input_state+3976,caret); } v108_input_text_reset_blink_v115(input_state); return 1; }'''
assert s.count(old)==1
s=s.replace(old,new,1)

old='''if x>=250 && x<380 && y>=py+132 && y<py+180 { var i:u64=0; while i<64 { unsafe { volatile_write8(input_state+3776+i,0); } i=i+1; } unsafe { volatile_write64(input_state+3680,0); volatile_write64(input_state+3672,1); } return 1; }'''
new='''if x>=250 && x<380 && y>=py+132 && y<py+180 { var i:u64=0; while i<64 { unsafe { volatile_write8(input_state+3776+i,0); } i=i+1; } unsafe { volatile_write64(input_state+3680,0); volatile_write64(input_state+3672,1); volatile_write64(input_state+3976,0); } v108_input_text_reset_blink_v115(input_state); return 1; }'''
assert s.count(old)==1
s=s.replace(old,new,1)

new_char=r'''fn v108_input_test_char_v112(input_state:u64,ascii:u64) -> u64 {
    if input_state==0 || volatile_read64(input_state+3672)==0 { return 0; } var len=volatile_read64(input_state+3680); var caret=volatile_read64(input_state+3976); if caret>len { caret=len; }
    if ascii==8 {
        if caret>0 && len>0 { var i=caret-1; while i+1<len { unsafe { volatile_write8(input_state+3776+i,volatile_read8(input_state+3776+i+1)); } i=i+1; } unsafe { volatile_write8(input_state+3776+len-1,0); volatile_write64(input_state+3680,len-1); volatile_write64(input_state+3976,caret-1); } }
        v108_input_text_reset_blink_v115(input_state); return 1;
    }
    if ascii==13 { return 1; } if ascii<32 || ascii>126 || len>=64 { return 0; }
    var i=len; while i>caret { unsafe { volatile_write8(input_state+3776+i,volatile_read8(input_state+3776+i-1)); } i=i-1; }
    unsafe { volatile_write8(input_state+3776+caret,ascii); volatile_write64(input_state+3680,len+1); volatile_write64(input_state+3976,caret+1); }
    v108_input_text_reset_blink_v115(input_state); if len==0 { serial_marker_v108_keyboard_text_ok(); } return 1;
}'''
repl_fn('fn v108_input_test_char_v112',new_char)

old='''                if kind==7 { if value!=0 { gui_input_dispatch(state,wm,event,surface); } telemetry_redraw=1; }'''
new='''                if kind==7 { if value!=0 { gui_input_dispatch(state,wm,event,surface); if v108_input_test_key_v115(input_state,code)!=0 { test_redraw=1; } } telemetry_redraw=1; }'''
assert s.count(old)==1
s=s.replace(old,new,1)

old='''            v108_cursor_restore(cursor,surface); cursor_move(cursor,surface,(newx*65536)+newy); v108_cursor_capture(cursor,surface,newx,newy); desktop_draw_cursor(surface,newx,newy); v108_cursor_present(process,(oldx*65536)+oldy,(newx*65536)+newy); if volatile_read64(input_state+3336)==0 { unsafe { volatile_write64(input_state+3336,1); } serial_marker_v108_physical_cursor_visible_ok(); }'''
new='''            v108_cursor_restore(cursor,surface); cursor_move(cursor,surface,(newx*65536)+newy); v108_cursor_capture(cursor,surface,newx,newy); v108_input_pointer_draw_v115(surface,state,input_state); v108_cursor_present(process,(oldx*65536)+oldy,(newx*65536)+newy); if volatile_read64(input_state+3336)==0 { unsafe { volatile_write64(input_state+3336,1); } serial_marker_v108_physical_cursor_visible_ok(); }'''
assert s.count(old)==1
s=s.replace(old,new,1)

old='''        if test_redraw!=0 { if v108_input_test_present(process,state,input_state,cursor)==0 { return 0; } }
        if telemetry_redraw!=0 { if v108_input_overlay_present(process,state,input_state,xhci)==0 { return 0; } }
        cpu_pause();'''
new='''        if volatile_read64(input_state+3672)!=0 { let now=read_tsc(); let then=volatile_read64(input_state+3992); if then==0 { unsafe { volatile_write64(input_state+3992,now); volatile_write64(input_state+3984,1); } } else { if now>then && now-then>600000000 { let phase=volatile_read64(input_state+3984); var next:u64=1; if phase!=0 { next=0; } unsafe { volatile_write64(input_state+3984,next); volatile_write64(input_state+3992,now); } if volatile_read64(input_state+4040)==0 { unsafe { volatile_write64(input_state+4040,1); } serial_marker_v108_text_blink_ok(); } test_redraw=1; } } }
        if test_redraw!=0 { if v108_input_test_present(process,state,input_state,cursor)==0 { return 0; } }
        if telemetry_redraw!=0 { if v108_input_overlay_present(process,state,input_state,xhci)==0 { return 0; } }
        cpu_pause();'''
assert s.count(old)==1
s=s.replace(old,new,1)

p.write_text(s)
out=hashlib.sha256(p.read_bytes()).hexdigest(); print(out)
if out!='fa0f42f558f0004f7663f79b49c3049c57c896203cf18646b1ec6f999824f941': raise SystemExit(f'unexpected r15 source hash {out}')
