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
# --- telemetry: add xHCI handoff/scratch/failure row and expand overlay by 18px ---
def text_fn(name,text):
    body=' '.join([f'if gui_draw_char_scaled(surface,((x+{i*6})*65536)+y,({ord(c)}*65536)+1,color)==0 {{ return 0; }}' for i,c in enumerate(text)])
    return f'fn {name}(surface:u64,x:u64,y:u64,color:u64) -> u64 {{ {body} return 1; }}\n'

input_anchor='fn v108_input_test_draw(surface:u64,state:u64,input_state:u64) -> u64 {'
input_idx=s.find(input_anchor)
if input_idx<0: raise SystemExit('input test draw anchor missing')
s=s[:input_idx]+text_fn('v108_text_menuitem_v118','MENU ITEM')+s[input_idx:]
old='''    if volatile_read64(input_state+3696)!=0 { display_fill_rect(surface,((x+360)*65536)+(y+118),(210*65536)+62,inner); display_fill_rect(surface,((x+360)*65536)+(y+118),(210*65536)+2,edge); v108_text_rightok(surface,x+382,y+134,white); v108_draw_small_u64(surface,((x+470)*65536)+(y+154),volatile_read64(input_state+3696),green); } return 1;
'''
new='''    if volatile_read64(input_state+3696)!=0 { display_fill_rect(surface,((x+360)*65536)+(y+118),(210*65536)+62,inner); display_fill_rect(surface,((x+360)*65536)+(y+118),(210*65536)+2,edge); v108_text_rightok(surface,x+382,y+134,white); v108_draw_small_u64(surface,((x+470)*65536)+(y+154),volatile_read64(input_state+3696),green); }
    if volatile_read64(state+256)!=0 { v108_text_menuitem_v118(surface,x+372,y+186,white); v108_draw_small_u64(surface,((x+436)*65536)+(y+186),volatile_read64(state+256),green); } return 1;
'''
rep(old,new)
anchor='fn v108_text_udev(surface:u64,x:u64,y:u64,color:u64) -> u64 {'
idx=s.find(anchor)
if idx<0: raise SystemExit('udev text anchor missing')
s=s[:idx]+text_fn('v108_text_xhc','XHC L S R F C T')+s[idx:]
s=s.replace('(410*65536)+364,bg','(410*65536)+382,bg',1)
s=s.replace('(410*65536)+382,16','(410*65536)+400,16',2)
old='''    v108_text_udev(surface,px+10,py+352,white); if xhci!=0 { v108_draw_small_u64(surface,((px+112)*65536)+(py+352),volatile_read64(xhci+1056),amber); v108_draw_small_u64(surface,((px+154)*65536)+(py+352),volatile_read64(xhci+1072),white); v108_draw_small_u64(surface,((px+196)*65536)+(py+352),volatile_read64(xhci+1080),white); v108_draw_small_u64(surface,((px+238)*65536)+(py+352),volatile_read64(xhci+1208),green); v108_draw_small_u64(surface,((px+280)*65536)+(py+352),volatile_read64(xhci+816),green); v108_draw_small_u64(surface,((px+322)*65536)+(py+352),volatile_read64(xhci+1192),green); v108_draw_small_u64(surface,((px+364)*65536)+(py+352),volatile_read64(xhci+1200),green); }
    return 1;
'''
new='''    v108_text_udev(surface,px+10,py+352,white); if xhci!=0 { v108_draw_small_u64(surface,((px+112)*65536)+(py+352),volatile_read64(xhci+1056),amber); v108_draw_small_u64(surface,((px+154)*65536)+(py+352),volatile_read64(xhci+1072),white); v108_draw_small_u64(surface,((px+196)*65536)+(py+352),volatile_read64(xhci+1080),white); v108_draw_small_u64(surface,((px+238)*65536)+(py+352),volatile_read64(xhci+1208),green); v108_draw_small_u64(surface,((px+280)*65536)+(py+352),volatile_read64(xhci+816),green); v108_draw_small_u64(surface,((px+322)*65536)+(py+352),volatile_read64(xhci+1192),green); v108_draw_small_u64(surface,((px+364)*65536)+(py+352),volatile_read64(xhci+1200),green); }
    v108_text_xhc(surface,px+10,py+370,white); if xhci!=0 { v108_draw_small_u64(surface,((px+100)*65536)+(py+370),volatile_read64(xhci+1232),amber); v108_draw_small_u64(surface,((px+148)*65536)+(py+370),volatile_read64(xhci+1216),white); v108_draw_small_u64(surface,((px+196)*65536)+(py+370),volatile_read64(xhci+1224),green); v108_draw_small_u64(surface,((px+244)*65536)+(py+370),volatile_read64(xhci+1240),red); v108_draw_small_u64(surface,((px+292)*65536)+(py+370),volatile_read64(xhci+488),amber); v108_draw_small_u64(surface,((px+340)*65536)+(py+370),volatile_read64(xhci+504),amber); }
    return 1;
'''
rep(old,new)
s=s.replace('fn v108_desktop_interaction_repaint_v116(','fn v108_desktop_interaction_repaint_v118(',1)
s=s.replace('v108_desktop_interaction_repaint_v116(process,state,input_state,xhci)','v108_desktop_interaction_repaint_v118(process,state,input_state,xhci)')
p.write_text(s)
