from pathlib import Path
import hashlib,sys
p=Path(sys.argv[1]); raw=p.read_bytes(); expected='2401b3a460430da6b008716e65f7be10dfb8e289da48b12045e1e1b920ed6caf'
actual=hashlib.sha256(raw).hexdigest()
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

def text_fn(name,text):
    ops=[]
    for i,c in enumerate(text):
        ops.append(f'if gui_draw_char_scaled(surface,((x+{i*6})*65536)+y,({ord(c)}*65536)+1,color)==0 {{ return 0; }}')
    return f"fn {name}(surface:u64,x:u64,y:u64,color:u64) -> u64 {{ {' '.join(ops)} return 1; }}\n"

def marker_fn(name,text):
    return 'fn '+name+'() -> void { '+' '.join(f'serial_putc({ord(c)});' for c in text+'\n')+' return; }\n'

old='''    input_push(input_state,7,sc,1);\n    let shift=volatile_read64(input_state+3728)+volatile_read64(input_state+3744); let ascii=ps2_set1_ascii_v112(sc,shift,volatile_read64(input_state+3752));'''
new='''    input_push(input_state,7,sc,1);\n    if ext==1 && (sc==75 || sc==77 || sc==83) { input_push(input_state,9,sc,1); }\n    let shift=volatile_read64(input_state+3728)+volatile_read64(input_state+3744); let ascii=ps2_set1_ascii_v112(sc,shift,volatile_read64(input_state+3752));'''
if s.count(old)!=1: raise SystemExit('extended navigation anchor')
s=s.replace(old,new,1)

insert=s.index('fn v108_input_test_draw')
helpers=(
    marker_fn('serial_marker_v108_text_left_ok','FRAMES_V108_TEXT_LEFT_OK')+
    marker_fn('serial_marker_v108_text_right_ok','FRAMES_V108_TEXT_RIGHT_OK')+
    marker_fn('serial_marker_v108_text_delete_ok','FRAMES_V108_TEXT_DELETE_OK')+
    marker_fn('serial_marker_v108_text_backspace_ok','FRAMES_V108_TEXT_BACKSPACE_OK')+
    marker_fn('serial_marker_v108_ibeam_ok','FRAMES_V108_IBEAM_OK')+
    marker_fn('serial_marker_v108_caret_blink_ok','FRAMES_V108_CARET_BLINK_OK')+
    marker_fn('serial_marker_v108_text_edit_sequence_ok','FRAMES_V108_TEXT_EDIT_SEQUENCE_OK')+
    text_fn('v108_text_edit','EDIT P L R D B')+
'''fn v108_input_pointer_draw(surface:u64,state:u64,input_state:u64,x:u64,y:u64) -> u64 {
    if surface==0 || state==0 || input_state==0 { return 0; } let py=v108_test_y(state);
    if x>=60 && x<640 && y>=py+62 && y<py+110 {
        let white:u64=4294244347; let dark:u64=4279244839;
        if display_fill_rect(surface,((x+1)*65536)+y,(6*65536)+2,dark)==0 { return 0; }
        if display_fill_rect(surface,((x+3)*65536)+(y+1),(2*65536)+14,dark)==0 { return 0; }
        if display_fill_rect(surface,((x+1)*65536)+(y+14),(6*65536)+2,dark)==0 { return 0; }
        display_fill_rect(surface,((x+4)*65536)+(y+2),(1*65536)+12,white);
        if volatile_read64(input_state+4032)==0 { unsafe { volatile_write64(input_state+4032,1); } serial_marker_v108_ibeam_ok(); }
        return 1;
    }
    return desktop_draw_cursor(surface,x,y);
}
fn v108_text_blink_reset_v114(input_state:u64) -> u64 {
    if input_state==0 { return 0; } unsafe { volatile_write64(input_state+3984,read_tsc()); volatile_write64(input_state+3992,1); } return 1;
}
fn v108_input_test_nav_v114(input_state:u64,sc:u64) -> u64 {
    if input_state==0 || volatile_read64(input_state+3672)==0 { return 0; } let len=volatile_read64(input_state+3680); var pos=volatile_read64(input_state+3976); if pos>len { pos=len; }
    if sc==75 { if pos>0 { pos=pos-1; } unsafe { volatile_write64(input_state+3976,pos); volatile_write64(input_state+4000,volatile_read64(input_state+4000)+1); } if volatile_read64(input_state+4000)==1 { serial_marker_v108_text_left_ok(); } v108_text_blink_reset_v114(input_state); return 1; }
    if sc==77 { if pos<len { pos=pos+1; } unsafe { volatile_write64(input_state+3976,pos); volatile_write64(input_state+4008,volatile_read64(input_state+4008)+1); } if volatile_read64(input_state+4008)==1 { serial_marker_v108_text_right_ok(); } v108_text_blink_reset_v114(input_state); return 1; }
    if sc==83 { if pos<len { var i=pos; while i+1<len { unsafe { volatile_write8(input_state+3776+i,volatile_read8(input_state+3776+i+1)); } i=i+1; } unsafe { volatile_write8(input_state+3776+len-1,0); volatile_write64(input_state+3680,len-1); } } unsafe { volatile_write64(input_state+4016,volatile_read64(input_state+4016)+1); } if volatile_read64(input_state+4016)==1 { serial_marker_v108_text_delete_ok(); } v108_text_blink_reset_v114(input_state); return 1; }
    return 0;
}
fn v108_input_test_caret_present_v114(process:u64,state:u64,input_state:u64,cursor:u64) -> u64 {
    let surface=volatile_read64(process+616); let dirty=volatile_read64(process+624); let timing=volatile_read64(process+664); let present=volatile_read64(process+672); if surface==0 || dirty==0 || timing==0 || present==0 || cursor==0 { return 0; }
    if volatile_read64(input_state+3672)==0 { return 1; } let len=volatile_read64(input_state+3680); var pos=volatile_read64(input_state+3976); if pos>len { pos=len; unsafe { volatile_write64(input_state+3976,pos); } }
    let py=v108_test_y(state); let caret_x=68+(pos*8); let caret_y=py+74; let inner:u64=4280624420; let amber:u64=4294934528; let c=volatile_read64(input_state+3992); let cx=volatile_read64(state+8); let cy=volatile_read64(state+16);
    v108_cursor_restore(cursor,surface); if c!=0 { display_fill_rect(surface,(caret_x*65536)+caret_y,(2*65536)+22,amber); } else { display_fill_rect(surface,(caret_x*65536)+caret_y,(2*65536)+22,inner); }
    v108_cursor_capture(cursor,surface,cx,cy); v108_input_pointer_draw(surface,state,input_state,cx,cy);
    dirty_add(dirty,(caret_x*65536)+caret_y,(2*65536)+22,16); present_enqueue(present,(caret_x*65536)+caret_y,(2*65536)+22,16); dirty_add(dirty,(cx*65536)+cy,(8*65536)+16,16); present_enqueue(present,(cx*65536)+cy,(8*65536)+16,16); return present_flush(present,surface,timing);
}
''')
s=s[:insert]+helpers+s[insert:]

old='''    let len=volatile_read64(input_state+3680); var i:u64=0; while i<len && i<64 { let c=volatile_read8(input_state+3776+i); if c>=32 && c<=126 { gui_draw_char_scaled(surface,((x+30+(i*8))*65536)+(y+78),(c*65536)+1,white); } i=i+1; }'''
new='''    let len=volatile_read64(input_state+3680); var i:u64=0; while i<len && i<64 { let c=volatile_read8(input_state+3776+i); if c>=32 && c<=126 { gui_draw_char_scaled(surface,((x+30+(i*8))*65536)+(y+78),(c*65536)+1,white); } i=i+1; }
    var caret=volatile_read64(input_state+3976); if caret>len { caret=len; unsafe { volatile_write64(input_state+3976,caret); } } if volatile_read64(input_state+3672)!=0 && volatile_read64(input_state+3992)!=0 { display_fill_rect(surface,((x+28+(caret*8))*65536)+(y+74),(2*65536)+22,amber); }'''
if s.count(old)!=1: raise SystemExit('text draw anchor')
s=s.replace(old,new,1)

tele=s.index('fn v108_input_overlay_draw')
s=s[:tele]+text_fn('v108_text_editdiag','EDIT P L R D B')+s[tele:]
s=s.replace('(410*65536)+346,bg','(410*65536)+364,bg',1)
s=s.replace('(px+344),(410*65536)+2,edge','(px+362),(410*65536)+2,edge',1)
old_hub='''    v108_text_hub(surface,px+10,py+316,white); if xhci!=0 { v108_draw_small_u64(surface,((px+82)*65536)+(py+316),volatile_read64(xhci+904),green); v108_draw_small_u64(surface,((px+130)*65536)+(py+316),volatile_read64(xhci+912),white); v108_draw_small_u64(surface,((px+178)*65536)+(py+316),volatile_read64(xhci+968),amber); v108_draw_small_u64(surface,((px+226)*65536)+(py+316),volatile_read64(xhci+976),amber); v108_draw_small_u64(surface,((px+274)*65536)+(py+316),volatile_read64(xhci+992),green); v108_draw_small_u64(surface,((px+322)*65536)+(py+316),volatile_read64(xhci+1000),green); }
    return 1;'''
new_hub='''    v108_text_hub(surface,px+10,py+316,white); if xhci!=0 { v108_draw_small_u64(surface,((px+82)*65536)+(py+316),volatile_read64(xhci+904),green); v108_draw_small_u64(surface,((px+130)*65536)+(py+316),volatile_read64(xhci+912),white); v108_draw_small_u64(surface,((px+178)*65536)+(py+316),volatile_read64(xhci+968),amber); v108_draw_small_u64(surface,((px+226)*65536)+(py+316),volatile_read64(xhci+976),amber); v108_draw_small_u64(surface,((px+274)*65536)+(py+316),volatile_read64(xhci+992),green); v108_draw_small_u64(surface,((px+322)*65536)+(py+316),volatile_read64(xhci+1000),green); }
    v108_text_editdiag(surface,px+10,py+334,white); v108_draw_small_u64(surface,((px+82)*65536)+(py+334),volatile_read64(input_state+3976),white); v108_draw_small_u64(surface,((px+130)*65536)+(py+334),volatile_read64(input_state+4000),green); v108_draw_small_u64(surface,((px+178)*65536)+(py+334),volatile_read64(input_state+4008),green); v108_draw_small_u64(surface,((px+226)*65536)+(py+334),volatile_read64(input_state+4016),amber); v108_draw_small_u64(surface,((px+274)*65536)+(py+334),volatile_read64(input_state+4024),amber);
    return 1;'''
if s.count(old_hub)!=1: raise SystemExit('hub tail anchor')
s=s.replace(old_hub,new_hub,1)
s=s.replace('(410*65536)+328,16','(410*65536)+364,16',2)

s=s.replace('if v108_cursor_capture(cursor,surface,cx,cy)==0 { return 0; } if desktop_draw_cursor(surface,cx,cy)==0 { return 0; }','if v108_cursor_capture(cursor,surface,cx,cy)==0 { return 0; } if v108_input_pointer_draw(surface,state,input_state,cx,cy)==0 { return 0; }',1)

old='''    if x>=60 && x<640 && y>=py+62 && y<py+110 { unsafe { volatile_write64(input_state+3672,1); } return 1; }'''
new='''    if x>=60 && x<640 && y>=py+62 && y<py+110 { let len=volatile_read64(input_state+3680); var pos:u64=0; if x>70 { pos=(x-70+4)/8; } if pos>len { pos=len; } unsafe { volatile_write64(input_state+3672,1); volatile_write64(input_state+3976,pos); } v108_text_blink_reset_v114(input_state); return 1; }'''
if s.count(old)!=1: raise SystemExit('textbox click anchor')
s=s.replace(old,new,1)
s=s.replace('volatile_write64(input_state+3680,0); volatile_write64(input_state+3672,1);','volatile_write64(input_state+3680,0); volatile_write64(input_state+3976,0); volatile_write64(input_state+3672,1);',1)

new_char=r'''fn v108_input_test_char_v112(input_state:u64,ascii:u64) -> u64 {
    if input_state==0 || volatile_read64(input_state+3672)==0 { return 0; } var len=volatile_read64(input_state+3680); var pos=volatile_read64(input_state+3976); if pos>len { pos=len; }
    if ascii==8 {
        if pos>0 && len>0 { var i=pos-1; while i+1<len { unsafe { volatile_write8(input_state+3776+i,volatile_read8(input_state+3776+i+1)); } i=i+1; } unsafe { volatile_write8(input_state+3776+len-1,0); volatile_write64(input_state+3680,len-1); volatile_write64(input_state+3976,pos-1); } }
        unsafe { volatile_write64(input_state+4024,volatile_read64(input_state+4024)+1); } if volatile_read64(input_state+4024)==1 { serial_marker_v108_text_backspace_ok(); } if volatile_read64(input_state+3680)==1 && volatile_read8(input_state+3776)==65 && volatile_read64(input_state+4000)>=2 && volatile_read64(input_state+4008)>=1 && volatile_read64(input_state+4016)>=1 && volatile_read64(input_state+4048)==0 { unsafe { volatile_write64(input_state+4048,1); } serial_marker_v108_text_edit_sequence_ok(); } v108_text_blink_reset_v114(input_state); return 1;
    }
    if ascii==13 { return 1; } if ascii<32 || ascii>126 || len>=64 { return 0; }
    var i=len; while i>pos { unsafe { volatile_write8(input_state+3776+i,volatile_read8(input_state+3776+i-1)); } i=i-1; }
    unsafe { volatile_write8(input_state+3776+pos,ascii); volatile_write64(input_state+3680,len+1); volatile_write64(input_state+3976,pos+1); }
    v108_text_blink_reset_v114(input_state); if len==0 { serial_marker_v108_keyboard_text_ok(); } return 1;
}'''
repl_fn('fn v108_input_test_char_v112',new_char)

old='''                if kind==7 { if value!=0 { gui_input_dispatch(state,wm,event,surface); } telemetry_redraw=1; }
                if kind==8 { if v108_input_test_char_v112(input_state,code)!=0 { test_redraw=1; } telemetry_redraw=1; }'''
new='''                if kind==7 { if value!=0 { gui_input_dispatch(state,wm,event,surface); } telemetry_redraw=1; }
                if kind==8 { if v108_input_test_char_v112(input_state,code)!=0 { test_redraw=1; } telemetry_redraw=1; }
                if kind==9 { if value!=0 && v108_input_test_nav_v114(input_state,code)!=0 { test_redraw=1; } telemetry_redraw=1; }'''
if s.count(old)!=1: raise SystemExit('runtime key anchor')
s=s.replace(old,new,1)
s=s.replace('v108_cursor_capture(cursor,surface,newx,newy); desktop_draw_cursor(surface,newx,newy);','v108_cursor_capture(cursor,surface,newx,newy); v108_input_pointer_draw(surface,state,input_state,newx,newy);',1)
old='''        if test_redraw!=0 { if v108_input_test_present(process,state,input_state,cursor)==0 { return 0; } }
        if telemetry_redraw!=0 { if v108_input_overlay_present(process,state,input_state,xhci)==0 { return 0; } }
        cpu_pause();'''
new='''        if test_redraw!=0 { if v108_input_test_present(process,state,input_state,cursor)==0 { return 0; } }
        if telemetry_redraw!=0 { if v108_input_overlay_present(process,state,input_state,xhci)==0 { return 0; } }
        if volatile_read64(input_state+3672)!=0 {
            let now=read_tsc(); let last=volatile_read64(input_state+3984); if last==0 { unsafe { volatile_write64(input_state+3984,now); volatile_write64(input_state+3992,1); } }
            else { if now>last && now-last>=1000000000 { let v=volatile_read64(input_state+3992); if v==0 { unsafe { volatile_write64(input_state+3992,1); } } else { unsafe { volatile_write64(input_state+3992,0); } } unsafe { volatile_write64(input_state+3984,now); } if volatile_read64(input_state+4040)==0 { unsafe { volatile_write64(input_state+4040,1); } serial_marker_v108_caret_blink_ok(); } if v108_input_test_caret_present_v114(process,state,input_state,cursor)==0 { return 0; } } }
        }
        cpu_pause();'''
if s.count(old)!=1: raise SystemExit('blink loop anchor')
s=s.replace(old,new,1)

p.write_text(s)
out=hashlib.sha256(p.read_bytes()).hexdigest(); print(out)
if out!='45f9baa577e2736019fa63a06ba2e5b42d9a5a9d3c19c5745017ca831c5605be': raise SystemExit(f'unexpected r14b source hash {out}')
