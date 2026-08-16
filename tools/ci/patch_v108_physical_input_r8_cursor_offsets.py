#!/usr/bin/env python3
from pathlib import Path
import hashlib, sys

p=Path(sys.argv[1])
raw=p.read_bytes()
expected='d458aa61d92ff33bcf7e529354deec7cd345d5d96188c95b08842853fa3e3e2b'
actual=hashlib.sha256(raw).hexdigest()
if actual!=expected:
    raise SystemExit(f'unexpected r7 final kernel hash: {actual}')
s=raw.decode()

old='let cx=volatile_read64(cursor+16); let cy=volatile_read64(cursor+24);'
if s.count(old)!=2:
    raise SystemExit(f'cursor declaration offset sites: expected 2, got {s.count(old)}')
s=s.replace(old,'let cx=volatile_read64(cursor+8); let cy=volatile_read64(cursor+16);')

old='desktop_draw_cursor(surface,volatile_read64(cursor+16),volatile_read64(cursor+24))'
if s.count(old)!=6:
    raise SystemExit(f'cursor direct-draw offset sites: expected 6, got {s.count(old)}')
s=s.replace(old,'desktop_draw_cursor(surface,volatile_read64(cursor+8),volatile_read64(cursor+16))')

old='''    if v108_input_backend_prepare(input_state)==0 { return 0; }
    if xhci!=0 && volatile_read64(xhci+416)==1 { if xhci_hid_arm_continuous(xhci,phys_state)==0 { return 0; } }
    if v108_input_overlay_present(process,state,input_state,xhci)==0 { return 0; }
    serial_marker_v108_input_telemetry_ok(); serial_marker_v108_stable_input_diag_ok();
    unsafe { volatile_write64(input_state+3320,volatile_read64(input_state+3224)); volatile_write64(input_state+3336,0); }
    v108_cursor_capture(cursor,surface,volatile_read64(state+8),volatile_read64(state+16));
'''
new='''    if v108_input_backend_prepare(input_state)==0 { return 0; }
    if xhci!=0 && volatile_read64(xhci+416)==1 { if xhci_hid_arm_continuous(xhci,phys_state)==0 { return 0; } }
    // r8: remove any cursor painted by pre-runtime compose stages exactly once.
    // The cursor pointer is hidden only for this clean home redraw, then restored.
    unsafe { volatile_write64(process+640,0); }
    let clean_frame=appearance_render(process);
    unsafe { volatile_write64(process+640,cursor); }
    if clean_frame==0 { return 0; }
    let startx=volatile_read64(state+8); let starty=volatile_read64(state+16);
    cursor_move(cursor,surface,(startx*65536)+starty);
    if v108_cursor_capture(cursor,surface,startx,starty)==0 { return 0; }
    if desktop_draw_cursor(surface,startx,starty)==0 { return 0; }
    if v108_cursor_present(process,(startx*65536)+starty,(startx*65536)+starty)==0 { return 0; }
    if v108_input_overlay_present(process,state,input_state,xhci)==0 { return 0; }
    serial_marker_v108_input_telemetry_ok(); serial_marker_v108_stable_input_diag_ok();
    unsafe { volatile_write64(input_state+3320,volatile_read64(input_state+3224)); volatile_write64(input_state+3336,0); }
'''
if s.count(old)!=1:
    raise SystemExit(f'input-runtime startup anchor: expected 1, got {s.count(old)}')
s=s.replace(old,new,1)

if 'cursor+24' in s:
    raise SystemExit('r8 cursor offset repair incomplete: cursor+24 remains')

p.write_text(s)
out=hashlib.sha256(p.read_bytes()).hexdigest()
print(out)
expected_out='b0e7893dea8306b44ea044b5e712fb4568223b5bdd599b9d369f19e523bad037'
if out!=expected_out:
    raise SystemExit(f'unexpected r8 output hash: {out}')
