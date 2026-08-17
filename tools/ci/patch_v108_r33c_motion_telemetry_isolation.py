#!/usr/bin/env python3
from pathlib import Path
import hashlib,subprocess,sys
if len(sys.argv)!=2: raise SystemExit('usage: patch_v108_r33c_motion_telemetry_isolation.py <kernel/main.nx>')
p=Path(sys.argv[1]); base=Path(__file__).with_name('patch_v108_r33b_overlay_render_recovery.py')
subprocess.run([sys.executable,str(base),str(p)],check=True,stdout=subprocess.DEVNULL)
s=p.read_text(); BASE='78081f168b3612b0f36d81b7dacca130a0f1ef0808385db81ae7a8178c130bb4'
if hashlib.sha256(s.encode()).hexdigest()!=BASE: raise SystemExit('r33b base mismatch')

def rep(old,new,label,count=1):
 global s
 n=s.count(old)
 if n!=count: raise SystemExit(f'{label} count {n}')
 s=s.replace(old,new,count)

# Pointer motion changes the high-frequency PS/2 counters, but must not force
# the entire diagnostic panel to be cleared and repainted.  The smoothness gate
# deliberately excludes the top diagnostic strip because those live counters
# are expected to change.  Keep the full USB/ownership rows for true USB,
# button and keyboard state changes, while giving raw motion a compact redraw.
helper=r'''fn v108_input_overlay_motion_draw_v133c(surface:u64,input_state:u64) -> u64 {
    if surface==0 || input_state==0 { return 0; }
    let w=volatile_read64(surface+16); var px:u64=8; if w>430 { px=w-420; }
    let py:u64=8; let bg:u64=4279308561; let white:u64=4294244347; let green:u64=4286644030; let amber:u64=4294934528; let red:u64=4294907956;
    if display_fill_rect(surface,(px*65536)+(py+96),(410*65536)+94,bg)==0 { return 0; }
    v108_text_ps2(surface,px+10,py+100,white); v108_draw_small_u64(surface,((px+82)*65536)+(py+100),volatile_read64(input_state+3136),green); v108_draw_small_u64(surface,((px+142)*65536)+(py+100),volatile_read64(input_state+3176),green);
    v108_text_p2raw(surface,px+10,py+118,white); v108_draw_small_u64(surface,((px+82)*65536)+(py+118),volatile_read64(input_state+3224),white); v108_draw_small_u64(surface,((px+148)*65536)+(py+118),volatile_read64(input_state+3232),green); v108_draw_small_u64(surface,((px+214)*65536)+(py+118),volatile_read64(input_state+3240),red);
    v108_text_p2dec(surface,px+10,py+136,white); v108_draw_small_u64(surface,((px+82)*65536)+(py+136),volatile_read64(input_state+3184),white); v108_draw_small_u64(surface,((px+148)*65536)+(py+136),volatile_read64(input_state+3488),amber); v108_draw_small_u64(surface,((px+214)*65536)+(py+136),volatile_read64(input_state+3176),green);
    v108_text_p2rej(surface,px+10,py+154,white); v108_draw_small_u64(surface,((px+82)*65536)+(py+154),volatile_read64(input_state+3528),white); v108_draw_small_u64(surface,((px+148)*65536)+(py+154),volatile_read64(input_state+3272)+volatile_read64(input_state+3280),red); v108_draw_small_u64(surface,((px+214)*65536)+(py+154),volatile_read64(input_state+3288),red);
    v108_text_p2a(surface,px+10,py+172,white); v108_draw_small_u64(surface,((px+82)*65536)+(py+172),volatile_read64(input_state+3432),white); v108_draw_small_u64(surface,((px+148)*65536)+(py+172),volatile_read64(input_state+3440),white); v108_draw_small_u64(surface,((px+214)*65536)+(py+172),volatile_read64(input_state+3448),white);
    return 1;
}
fn v108_input_overlay_motion_present_v133c(process:u64,input_state:u64) -> u64 {
    if process==0 || input_state==0 { return 0; }
    let surface=volatile_read64(process+616); let dirty=volatile_read64(process+624); let timing=volatile_read64(process+664); let present=volatile_read64(process+672);
    if surface==0 || dirty==0 || timing==0 || present==0 { return 0; }
    let w=volatile_read64(surface+16); var px:u64=8; if w>430 { px=w-420; }
    if v108_input_overlay_motion_draw_v133c(surface,input_state)==0 { return 0; }
    let xy=(px*65536)+104; let wh=(410*65536)+94;
    if dirty_add(dirty,xy,wh,16)==0 || present_enqueue(present,xy,wh,16)==0 || present_flush(present,surface,timing)==0 { return 0; }
    return 1;
}
'''
rep('fn v108_input_overlay_present(process:u64,state:u64,input_state:u64,xhci:u64) -> u64 {',helper+'fn v108_input_overlay_present(process:u64,state:u64,input_state:u64,xhci:u64) -> u64 {','motion telemetry helpers')
rep('var telemetry_redraw:u64=0; var test_redraw:u64=0; var pointer_changed:u64=0;','var telemetry_redraw:u64=0; var motion_telemetry_redraw:u64=0; var test_redraw:u64=0; var pointer_changed:u64=0;','motion telemetry state')
rep('if volatile_read64(input_state+4064)!=0 { let moved=volatile_read64(input_state+4056); let now_idle=read_tsc(); if moved!=0 && now_idle>moved && now_idle-moved>180000000 { unsafe { volatile_write64(input_state+4064,0); } telemetry_redraw=1; } }','if volatile_read64(input_state+4064)!=0 { let moved=volatile_read64(input_state+4056); let now_idle=read_tsc(); if moved!=0 && now_idle>moved && now_idle-moved>180000000 { unsafe { volatile_write64(input_state+4064,0); } motion_telemetry_redraw=1; } }','motion idle redraw isolation')
rep('if telemetry_redraw!=0 { if v108_input_overlay_present(process,state,input_state,xhci)==0 { return 0; } }','if telemetry_redraw!=0 { if v108_input_overlay_present(process,state,input_state,xhci)==0 { return 0; } } else { if motion_telemetry_redraw!=0 { if v108_input_overlay_motion_present_v133c(process,input_state)==0 { return 0; } } }','motion compact present')

for q in ('fn v108_input_overlay_motion_draw_v133c','fn v108_input_overlay_motion_present_v133c','motion_telemetry_redraw=1','v108_input_overlay_motion_present_v133c(process,input_state)'):
 if q not in s: raise SystemExit('r33c contract missing '+q)
if 'volatile_write64(xhci_state+2368,post_v133)' not in s: raise SystemExit('r33c lost ownership reroute evidence')
if s.count('{')!=s.count('}'): raise SystemExit('brace imbalance')
expected='53a6e654154d2d622650c16aefac12bc9cbee9c4a3cfc772948dd60feeb62c3e'
actual=hashlib.sha256(s.encode()).hexdigest()
if actual!=expected: raise SystemExit(f'r33c identity mismatch {actual}')
p.write_text(s); print(actual)
