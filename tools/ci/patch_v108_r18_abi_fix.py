#!/usr/bin/env python3
from pathlib import Path
import sys
p=Path(sys.argv[1]); s=p.read_text()
def rep(old,new,count=1):
    global s
    n=s.count(old)
    if n!=count: raise SystemExit(f'replacement count {n} != {count} for {old[:120]!r}')
    s=s.replace(old,new,count)
rep('fn v108_context_hit_v118(surface:u64,state:u64,x:u64,y:u64) -> u64 {\n    if surface==0 || state==0 || volatile_read64(state+128)==0 { return 0; } if v108_context_geometry_v118(surface,state)==0 { return 0; }',
    'fn v108_context_hit_v118(state:u64,x:u64,y:u64) -> u64 {\n    if state==0 || volatile_read64(state+128)==0 { return 0; }')
s=s.replace('v108_context_hit_v118(surface,state,x,y)','v108_context_hit_v118(state,x,y)')
rep('fn gui_input_pointer_move(state:u64,wm:u64,surface:u64,raw:u64,axis:u64) -> u64 {','fn gui_input_pointer_move(state:u64,wm:u64,raw:u64,axis:u64) -> u64 {')
s=s.replace('gui_input_pointer_move(state,wm,surface,value,1)','gui_input_pointer_move(state,wm,value,1)')
s=s.replace('gui_input_pointer_move(state,wm,surface,value,2)','gui_input_pointer_move(state,wm,value,2)')
s=s.replace('gui_input_pointer_move(state,wm,surface,12,1)','gui_input_pointer_move(state,wm,12,1)')
s=s.replace('gui_input_pointer_move(state,wm,surface,8,2)','gui_input_pointer_move(state,wm,8,2)')
s=s.replace('gui_input_pointer_move(state,wm,surface,10,1)','gui_input_pointer_move(state,wm,10,1)')
s=s.replace('gui_input_pointer_move(state,wm,surface,10,2)','gui_input_pointer_move(state,wm,10,2)')
old='''unsafe { volatile_write64(state+128,1); volatile_write64(state+136,x); volatile_write64(state+144,y); volatile_write64(state+152,opens); volatile_write64(state+240,0); volatile_write64(state+288,0); } serial_marker_v108_desktop_context_ok();'''
new='''unsafe { volatile_write64(state+128,1); volatile_write64(state+136,x); volatile_write64(state+144,y); volatile_write64(state+152,opens); volatile_write64(state+240,0); volatile_write64(state+288,0); } if v108_context_geometry_v118(surface,state)==0 { return 0; } serial_marker_v108_desktop_context_ok();'''
rep(old,new)
p.write_text(s)
