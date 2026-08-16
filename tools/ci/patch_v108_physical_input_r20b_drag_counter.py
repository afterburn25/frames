from pathlib import Path
import hashlib,sys
p=Path(sys.argv[1]); raw=p.read_bytes(); actual=hashlib.sha256(raw).hexdigest(); expected='d5a300fd1d56562570ef3e2cb7de53ff8089b1399be914756a9751d289dead74'
if actual!=expected: raise SystemExit(f'unexpected r20 source hash {actual}')
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

repl_fn('fn gui_input_pointer_move', '''fn gui_input_pointer_move(state:u64,wm:u64,raw:u64,axis:u64) -> u64 {
    if state==0 || wm==0 || volatile_read64(state)!=1 { return 0; }
    var x=volatile_read64(state+8); var y=volatile_read64(state+16); var amount=raw%256;
    if axis==1 { if amount>127 { let d=256-amount; if d>x { x=0; } else { x=x-d; } } else { x=x+amount; if x>=volatile_read64(state+64) { x=volatile_read64(state+64)-1; } } }
    if axis==2 { if amount>127 { let d=256-amount; if d>y { y=0; } else { y=y-d; } } else { y=y+amount; if y>=volatile_read64(state+72) { y=volatile_read64(state+72)-1; } } }
    if y+1>=volatile_read64(state+72) && volatile_read64(state+224)==0 { unsafe { volatile_write64(state+224,1); } serial_marker_v108_pointer_bottom_ok(); }
    if volatile_read64(state+392)!=0 {
        if volatile_read64(state+96)%2==0 { unsafe { volatile_write64(state+392,0); volatile_write64(state+464,0); } }
        else { let px=volatile_read64(state+400); let py=volatile_read64(state+408); var dx:u64=0; var dy:u64=0; if x>px { dx=x-px; } else { dx=px-x; } if y>py { dy=y-py; } else { dy=py-y; } let confirms=volatile_read64(state+464)+1; unsafe { volatile_write64(state+464,confirms); } if confirms>=3 && dx+dy>=6 { unsafe { volatile_write64(state+176,1); volatile_write64(state+184,volatile_read64(state+424)); volatile_write64(state+192,volatile_read64(state+432)); volatile_write64(state+392,0); volatile_write64(state+464,0); volatile_write64(state+448,volatile_read64(state+448)+1); } serial_marker_v108_drag_arm_ok_v120(); } }
    }
    if volatile_read64(state+176)!=0 {
        let ox=volatile_read64(state+184); let oy=volatile_read64(state+192); var wx:u64=0; var wy:u64=0; if x>ox { wx=x-ox; } if y>oy { wy=y-oy; }
        let sw=volatile_read64(state+64); let panel_y=volatile_read64(state+208); if wx+270>sw { wx=sw-270; } if wy+150>panel_y { wy=panel_y-150; }
        unsafe { volatile_write64(state+160,wx); volatile_write64(state+168,wy); volatile_write64(state+200,volatile_read64(state+200)+1); }
        if volatile_read64(state+216)==0 { unsafe { volatile_write64(state+216,1); } serial_marker_v108_window_drag_ok(); }
    }
    let capture=volatile_read64(state+24); let mode=volatile_read64(state+32);
    if capture!=0 { let rec=wm_record(wm,capture); if rec==0 { return 0; } if mode==1 { let rw=volatile_read64(rec+24); let rh=volatile_read64(rec+32); var nx=x; var ny=y; if nx+rw>volatile_read64(wm+56) { nx=volatile_read64(wm+56)-rw; } if ny+rh>volatile_read64(wm+72) { ny=volatile_read64(wm+72)-rh; } if wm_move(wm,capture,(nx*65536)+ny)==0 { return 0; } unsafe { volatile_write64(state+56,volatile_read64(state+56)+1); } }
        if mode==2 { let rx=volatile_read64(rec+8); let ry=volatile_read64(rec+16); var nw:u64=160; var nh:u64=100; if x>rx+160 { nw=x-rx; } if y>ry+100 { nh=y-ry; } if rx+nw>volatile_read64(wm+56) { nw=volatile_read64(wm+56)-rx; } if ry+nh>volatile_read64(wm+72) { nh=volatile_read64(wm+72)-ry; } if wm_resize(wm,capture,(nw*65536)+nh)==0 { return 0; } unsafe { volatile_write64(state+88,volatile_read64(state+88)+1); } }
    }
    if volatile_read64(state+296)!=0 { let px=volatile_read64(state+304); let py=volatile_read64(state+312); var dx:u64=0; var dy:u64=0; if x>px { dx=x-px; } else { dx=px-x; } if y>py { dy=y-py; } else { dy=py-y; } if dx>6 || dy>6 { unsafe { volatile_write64(state+296,0); volatile_write64(state+320,volatile_read64(state+320)+1); } } }
    if volatile_read64(state+128)!=0 { let before=volatile_read64(state+240); let now=v108_context_hit_v118(state,x,y); if now!=before { unsafe { volatile_write64(state+240,now); } if now!=0 && volatile_read64(state+288)==0 { unsafe { volatile_write64(state+288,1); } serial_marker_v108_context_hover_ok(); } } }
    unsafe { volatile_write64(state+8,x); volatile_write64(state+16,y); } return 1;
}''')

a,b=fn_span(s,'fn gui_input_buttons'); f=s[a:b]
f=f.replace('volatile_write64(state+432,y-wy); volatile_write64(state+24,0);','volatile_write64(state+432,y-wy); volatile_write64(state+464,0); volatile_write64(state+24,0);',1)
f=f.replace('volatile_write64(state+176,0); volatile_write64(state+392,0); }','volatile_write64(state+176,0); volatile_write64(state+392,0); volatile_write64(state+464,0); }',1)
s=s[:a]+f+s[b:]

a,b=fn_span(s,'fn gui_input_init'); f=s[a:b]
f=f.replace('volatile_write64(state+456,0); }','volatile_write64(state+456,0); volatile_write64(state+464,0); }',1)
s=s[:a]+f+s[b:]

p.write_text(s)
h=hashlib.sha256(p.read_bytes()).hexdigest(); print(h)
