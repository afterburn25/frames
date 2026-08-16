#!/usr/bin/env python3
from pathlib import Path
import hashlib,sys

p=Path(sys.argv[1]); s=p.read_text()
if 'fn desktop_input_runtime(' not in s or 'serial_marker_v108_usb_gui_cursor_ok' not in s:
    raise SystemExit('apply v108 live-input common layer before input-test runtime')
if 'FRAMES_V108_INPUT_TEST_RUNTIME_READY' in s:
    raise SystemExit('v108 input-test runtime already applied')

def marker(fn,text):
    body=' '.join(f'serial_putc({ord(c)});' for c in text+'\n')
    return f'fn {fn}() -> void {{ {body} return; }}\n'

anchor='fn desktop_input_runtime(process:u64,input_state:u64,phys_state:u64,hardware_state:u64) -> u64 {'
if s.count(anchor)!=1: raise SystemExit(f'desktop_input_runtime definition anchor mismatch: {s.count(anchor)}')
s=s.replace(anchor,marker('serial_marker_v108_input_test_runtime_ready','FRAMES_V108_INPUT_TEST_RUNTIME_READY')+anchor,1)

old='appearance_ready=appearance_system_phase1_compose(appearance_state,display_state,process_state,window_manager_state); if appearance_ready==0 { serial_marker_desktop_cert_fail(); return; }'
new='appearance_ready=appearance_system_phase1_compose(appearance_state,display_state,process_state,window_manager_state); if appearance_ready==0 { serial_marker_desktop_cert_fail(); return; } serial_marker_v108_input_test_runtime_ready(); if timer_ready != 0 && scheduler_ready != 0 && lifecycle_mode==0 { interrupts_enable(); } if desktop_input_runtime(process_state,input_state,phys_state,hardware_state)==0 { serial_marker_desktop_cert_fail(); return; } return;'
if s.count(old)!=1: raise SystemExit(f'appearance handoff anchor mismatch: {s.count(old)}')
s=s.replace(old,new,1)
p.write_text(s)
print(hashlib.sha256(p.read_bytes()).hexdigest())
