from pathlib import Path
import hashlib,sys
p=Path(sys.argv[1]); raw=p.read_bytes(); actual=hashlib.sha256(raw).hexdigest(); expected='17cf352e42806cbe2246cca92fc09993060f4f159c72e3785fbf4177b98ba453'
if actual!=expected: raise SystemExit(f'unexpected r20b source hash {actual}')
s=raw.decode()

def fn_span(text,name):
 st=text.index(name); op=text.index('{',st); d=0
 for j in range(op,len(text)):
  if text[j]=='{': d+=1
  elif text[j]=='}':
   d-=1
   if d==0:return st,j+1
 raise RuntimeError(name)

def marker(name,text):
 return 'fn '+name+'() -> void { '+' '.join(f'serial_putc({ord(c)});' for c in text+'\n')+' return; }\n'
anchor=s.index('fn serial_marker_v108_drag_proxy_ok_v119')
extra=(marker('serial_marker_v108_left_edge_trace_v120','FRAMES_V108_LEFT_EDGE_TRACE')+
       marker('serial_marker_v108_drag_pending_trace_v120','FRAMES_V108_DRAG_PENDING_TRACE')+
       marker('serial_marker_v108_left_outside_trace_v120','FRAMES_V108_LEFT_OUTSIDE_TRACE')+
       marker('serial_marker_v108_drag_pending_move_trace_v120','FRAMES_V108_DRAG_PENDING_MOVE_TRACE'))
s=s[:anchor]+extra+s[anchor:]

a,b=fn_span(s,'fn gui_input_buttons'); f=s[a:b]
f=f.replace('if buttons%2!=0 && old%2==0 {\n        unsafe { volatile_write64(state+296,0); }','if buttons%2!=0 && old%2==0 {\n        serial_marker_v108_left_edge_trace_v120(); unsafe { volatile_write64(state+296,0); }',1)
f=f.replace('let wx=volatile_read64(state+160); let wy=volatile_read64(state+168); if x>=wx && x<wx+270 && y>=wy && y<wy+36 { unsafe {','let wx=volatile_read64(state+160); let wy=volatile_read64(state+168); if x>=wx && x<wx+270 && y>=wy && y<wy+36 { serial_marker_v108_drag_pending_trace_v120(); unsafe {',1)
f=f.replace('        let id=gui_input_hit_test(state,wm,x,y);','        serial_marker_v108_left_outside_trace_v120(); let id=gui_input_hit_test(state,wm,x,y);',1)
s=s[:a]+f+s[b:]

a,b=fn_span(s,'fn gui_input_pointer_move'); f=s[a:b]
f=f.replace('if volatile_read64(state+392)!=0 {\n        if volatile_read64(state+96)%2==0','if volatile_read64(state+392)!=0 {\n        serial_marker_v108_drag_pending_move_trace_v120(); if volatile_read64(state+96)%2==0',1)
s=s[:a]+f+s[b:]
p.write_text(s); print(hashlib.sha256(p.read_bytes()).hexdigest())
# workflow registration trigger
