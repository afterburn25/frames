#!/usr/bin/env python3
from pathlib import Path
import hashlib,sys

p=Path(sys.argv[1])
raw=p.read_bytes()
expected='ffc5721eca68844357dbdca63b0edf266e7e210f9d162eecde8cae0067f210a8'
actual=hashlib.sha256(raw).hexdigest()
if actual!=expected:
    raise SystemExit(f'unexpected certified v108 kernel hash: {actual}')
s=raw.decode()
for off in ('input_state+3104','input_state+3112','input_state+3120'):
    if off in s:
        raise SystemExit(f'reserved live-input state offset already used: {off}')

def marker(fn,text):
    body=' '.join(f'serial_putc({ord(c)});' for c in text+'\n')
    return f'fn {fn}() -> void {{ {body} return; }}\n'

old='''fn desktop_input_runtime(process:u64,input_state:u64,phys_state:u64,hardware_state:u64) -> u64 {
    if process==0 || input_state==0 || phys_state==0 || hardware_state==0 { return 0; } let state=volatile_read64(process+1080); let wm=volatile_read64(process+1072); let surface=volatile_read64(process+616); let cursor=volatile_read64(process+640); let dirty=volatile_read64(process+624); let xhci=volatile_read64(input_state+3008); if state==0 || wm==0 || surface==0 || cursor==0 { return 0; }
    if xhci!=0 && volatile_read64(xhci+416)==1 { if xhci_hid_arm_continuous(xhci,phys_state)==0 { return 0; } }
    while true { if xhci!=0 && volatile_read64(xhci+808)!=0 { if xhci_hid_poll_continuous(xhci,input_state)==0 { return 0; } } ps2_poll_fallback(input_state); let event=input_pop(input_state); if event!=0 { if gui_input_dispatch(state,wm,event,surface)!=0 { if volatile_read64(event)==4 { desktop_shell_click(process,state,volatile_read64(event+16)); appearance_handle_click(process,state,volatile_read64(event+16)); } cursor_move(cursor,surface,(volatile_read64(state+8)*65536)+volatile_read64(state+16)); if volatile_read64(process+1160)!=0 { appearance_render(process); } else { wm_render_all(wm,surface,dirty); let shell=volatile_read64(process+1088); if shell!=0 { desktop_shell_draw(shell,surface,wm,0); desktop_shell_launcher_draw(shell,surface); } desktop_draw_cursor(surface,volatile_read64(state+8),volatile_read64(state+16)); } } } cpu_pause(); }
    return 1;
}'''
if s.count(old)!=1:
    raise SystemExit(f'desktop_input_runtime anchor mismatch: {s.count(old)}')

prefix=(marker('serial_marker_v108_usb_live_report_ok','FRAMES_V108_USB_LIVE_REPORT_OK')+
        marker('serial_marker_v108_usb_gui_cursor_ok','FRAMES_V108_USB_GUI_CURSOR_OK')+
        marker('serial_marker_v108_ps2_enable_ok','FRAMES_V108_PS2_ENABLE_OK')+
        marker('serial_marker_v108_ps2_packet_ok','FRAMES_V108_PS2_PACKET_OK')+
        marker('serial_marker_v108_ps2_gui_cursor_ok','FRAMES_V108_PS2_GUI_CURSOR_OK')+
        marker('serial_marker_v108_input_test_runtime_ready','FRAMES_V108_INPUT_TEST_RUNTIME_READY')+
        'fn v108_input_backend_prepare(input_state:u64) -> u64 { return 1; }\n')
new=prefix+'''fn desktop_input_runtime(process:u64,input_state:u64,phys_state:u64,hardware_state:u64) -> u64 {
    if process==0 || input_state==0 || phys_state==0 || hardware_state==0 { return 0; }
    let state=volatile_read64(process+1080); let wm=volatile_read64(process+1072); let surface=volatile_read64(process+616); let cursor=volatile_read64(process+640); let dirty=volatile_read64(process+624); let xhci=volatile_read64(input_state+3008);
    if state==0 || wm==0 || surface==0 || cursor==0 { return 0; }
    if v108_input_backend_prepare(input_state)==0 { return 0; }
    if xhci!=0 && volatile_read64(xhci+416)==1 { if xhci_hid_arm_continuous(xhci,phys_state)==0 { return 0; } }
    while true {
        if xhci!=0 && volatile_read64(xhci+808)!=0 { if xhci_hid_poll_continuous(xhci,input_state)==0 { return 0; } }
        ps2_poll_fallback(input_state);
        let event=input_pop(input_state);
        if event!=0 {
            let kind=volatile_read64(event); let oldx=volatile_read64(state+8); let oldy=volatile_read64(state+16);
            if gui_input_dispatch(state,wm,event,surface)!=0 {
                if kind==4 { desktop_shell_click(process,state,volatile_read64(event+16)); appearance_handle_click(process,state,volatile_read64(event+16)); }
                let newx=volatile_read64(state+8); let newy=volatile_read64(state+16);
                if (kind==5 || kind==6) && (newx!=oldx || newy!=oldy) {
                    let source=volatile_read64(input_state+3104);
                    if source==1 && volatile_read64(input_state+3112)==0 { unsafe { volatile_write64(input_state+3112,1); } serial_marker_v108_usb_gui_cursor_ok(); }
                    if source==2 && volatile_read64(input_state+3120)==0 { unsafe { volatile_write64(input_state+3120,1); } serial_marker_v108_ps2_gui_cursor_ok(); }
                }
                cursor_move(cursor,surface,(newx*65536)+newy);
                if volatile_read64(process+1160)!=0 { appearance_render(process); } else { wm_render_all(wm,surface,dirty); let shell=volatile_read64(process+1088); if shell!=0 { desktop_shell_draw(shell,surface,wm,0); desktop_shell_launcher_draw(shell,surface); } desktop_draw_cursor(surface,newx,newy); }
            }
        }
        cpu_pause();
    }
    return 1;
}'''
s=s.replace(old,new,1)

appearance='appearance_ready=appearance_system_phase1_compose(appearance_state,display_state,process_state,window_manager_state); if appearance_ready==0 { serial_marker_desktop_cert_fail(); return; }'
input_handoff='appearance_ready=appearance_system_phase1_compose(appearance_state,display_state,process_state,window_manager_state); if appearance_ready==0 { serial_marker_desktop_cert_fail(); return; } serial_marker_v108_input_test_runtime_ready(); if timer_ready != 0 && scheduler_ready != 0 && lifecycle_mode==0 { interrupts_enable(); } if desktop_input_runtime(process_state,input_state,phys_state,hardware_state)==0 { serial_marker_desktop_cert_fail(); return; } return;'
if s.count(appearance)!=1:
    raise SystemExit(f'appearance input-test handoff mismatch: {s.count(appearance)}')
s=s.replace(appearance,input_handoff,1)

p.write_text(s)
print(hashlib.sha256(p.read_bytes()).hexdigest())
