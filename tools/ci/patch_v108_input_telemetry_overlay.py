#!/usr/bin/env python3
from pathlib import Path
import hashlib,sys

p=Path(sys.argv[1]); raw=p.read_bytes()
expected='270c76a79ab56fe275acf87ec0e5cabdf4b1bca5bff15bb0e6ef89a7bafad7e8'
actual=hashlib.sha256(raw).hexdigest()
if actual!=expected:
    raise SystemExit(f'unexpected combined v108 input kernel hash: {actual}')
s=raw.decode()
if 'v108_input_overlay_present' in s:
    raise SystemExit('telemetry overlay already applied')

def text_fn(name,text):
    ops=[]
    for i,c in enumerate(text):
        ops.append(f'if gui_draw_char_scaled(surface,((x+{i*6})*65536)+y,({ord(c)}*65536)+1,color)==0 {{ return 0; }}')
    return f"fn {name}(surface:u64,x:u64,y:u64,color:u64) -> u64 {{ {' '.join(ops)} return 1; }}\n"

helpers='''fn serial_marker_v108_input_telemetry_ok() -> void { serial_putc(70); serial_putc(82); serial_putc(65); serial_putc(77); serial_putc(69); serial_putc(83); serial_putc(95); serial_putc(86); serial_putc(49); serial_putc(48); serial_putc(56); serial_putc(95); serial_putc(73); serial_putc(78); serial_putc(80); serial_putc(85); serial_putc(84); serial_putc(95); serial_putc(84); serial_putc(69); serial_putc(76); serial_putc(69); serial_putc(77); serial_putc(69); serial_putc(84); serial_putc(82); serial_putc(89); serial_putc(95); serial_putc(79); serial_putc(75); serial_putc(10); return; }\n'''
helpers += text_fn('v108_text_input','INPUT V108 LIVE')
helpers += text_fn('v108_text_usb','USB H R P')
helpers += text_fn('v108_text_ps2','PS2 E PK')
helpers += text_fn('v108_text_src','SRC X Y')
helpers += '''fn v108_draw_small_u64(surface:u64,xy:u64,value:u64,color:u64) -> u64 {
    let x=xy/65536; let y=xy%65536; var divisor:u64=1000000000; var started:u64=0; var pos:u64=0;
    while divisor>0 {
        let digit=(value/divisor)%10;
        if digit!=0 || started!=0 || divisor==1 {
            started=1;
            if gui_draw_char_scaled(surface,((x+(pos*6))*65536)+y,((48+digit)*65536)+1,color)==0 { return 0; }
            pos=pos+1;
        }
        divisor=divisor/10;
    }
    return 1;
}
fn v108_input_overlay_draw(surface:u64,state:u64,input_state:u64,xhci:u64) -> u64 {
    if surface==0 || state==0 || input_state==0 { return 0; }
    let w=volatile_read64(surface+16); var px:u64=8; if w>430 { px=w-420; }
    let py:u64=8; let bg:u64=4279308561; let edge:u64=4283268350; let white:u64=4294244347; let green:u64=4286644030; let amber:u64=4294934528;
    if display_fill_rect(surface,(px*65536)+py,(410*65536)+94,bg)==0 { return 0; }
    display_fill_rect(surface,(px*65536)+py,(410*65536)+2,edge); display_fill_rect(surface,(px*65536)+(py+92),(410*65536)+2,edge);
    v108_text_input(surface,px+10,py+8,white);
    v108_text_usb(surface,px+10,py+28,white);
    var usb_h:u64=0; var usb_p:u64=0; if xhci!=0 { usb_h=volatile_read64(xhci+416); usb_p=volatile_read64(xhci+112); }
    let usb_r=volatile_read64(input_state+3128); v108_draw_small_u64(surface,((px+82)*65536)+(py+28),usb_h,green); v108_draw_small_u64(surface,((px+130)*65536)+(py+28),usb_r,green); v108_draw_small_u64(surface,((px+178)*65536)+(py+28),usb_p,amber);
    v108_text_ps2(surface,px+10,py+46,white); v108_draw_small_u64(surface,((px+82)*65536)+(py+46),volatile_read64(input_state+3136),green); v108_draw_small_u64(surface,((px+142)*65536)+(py+46),volatile_read64(input_state+3176),green);
    v108_text_src(surface,px+10,py+64,white); v108_draw_small_u64(surface,((px+58)*65536)+(py+64),volatile_read64(input_state+3104),amber); v108_draw_small_u64(surface,((px+112)*65536)+(py+64),volatile_read64(state+8),white); v108_draw_small_u64(surface,((px+220)*65536)+(py+64),volatile_read64(state+16),white);
    return 1;
}
fn v108_input_overlay_present(process:u64,state:u64,input_state:u64,xhci:u64) -> u64 {
    let surface=volatile_read64(process+616); if surface==0 { return 0; }
    if v108_input_overlay_draw(surface,state,input_state,xhci)==0 { return 0; }
    let dirty=volatile_read64(process+624); let timing=volatile_read64(process+664); let present=volatile_read64(process+672); let w=volatile_read64(surface+16); var px:u64=8; if w>430 { px=w-420; }
    if dirty==0 || timing==0 || present==0 { return 0; }
    if dirty_add(dirty,(px*65536)+8,(410*65536)+94,16)==0 { return 0; }
    if present_enqueue(present,(px*65536)+8,(410*65536)+94,16)==0 { return 0; }
    if present_flush(present,surface,timing)==0 { return 0; }
    return 1;
}
'''
anchor='fn desktop_input_runtime(process:u64,input_state:u64,phys_state:u64,hardware_state:u64) -> u64 {'
if s.count(anchor)!=1: raise SystemExit(f'runtime anchor mismatch: {s.count(anchor)}')
s=s.replace(anchor,helpers+anchor,1)

arm='if xhci!=0 && volatile_read64(xhci+416)==1 { if xhci_hid_arm_continuous(xhci,phys_state)==0 { return 0; } }\n    while true {'
arm_new='if xhci!=0 && volatile_read64(xhci+416)==1 { if xhci_hid_arm_continuous(xhci,phys_state)==0 { return 0; } }\n    if v108_input_overlay_present(process,state,input_state,xhci)==0 { return 0; } serial_marker_v108_input_telemetry_ok();\n    while true {'
if s.count(arm)!=1: raise SystemExit(f'initial overlay anchor mismatch: {s.count(arm)}')
s=s.replace(arm,arm_new,1)

render='if volatile_read64(process+1160)!=0 { appearance_render(process); } else { wm_render_all(wm,surface,dirty); let shell=volatile_read64(process+1088); if shell!=0 { desktop_shell_draw(shell,surface,wm,0); desktop_shell_launcher_draw(shell,surface); } desktop_draw_cursor(surface,newx,newy); }'
render_new=render+' if v108_input_overlay_present(process,state,input_state,xhci)==0 { return 0; }'
if s.count(render)!=1: raise SystemExit(f'event overlay anchor mismatch: {s.count(render)}')
s=s.replace(render,render_new,1)

p.write_text(s)
print(hashlib.sha256(p.read_bytes()).hexdigest())
