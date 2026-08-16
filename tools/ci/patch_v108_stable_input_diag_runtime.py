#!/usr/bin/env python3
from pathlib import Path
import hashlib,sys

p=Path(sys.argv[1]); raw=p.read_bytes()
expected='d0421388cd288a7073ca750915b1b51ceeee62acfe524a6785f855e42f9b1e7f'
actual=hashlib.sha256(raw).hexdigest()
if actual!=expected:
    raise SystemExit(f'unexpected r5 kernel hash: {actual}')
s=raw.decode()
marker='fn serial_marker_v108_stable_input_diag_ok() -> void { serial_putc(70); serial_putc(82); serial_putc(65); serial_putc(77); serial_putc(69); serial_putc(83); serial_putc(95); serial_putc(86); serial_putc(49); serial_putc(48); serial_putc(56); serial_putc(95); serial_putc(83); serial_putc(84); serial_putc(65); serial_putc(66); serial_putc(76); serial_putc(69); serial_putc(95); serial_putc(73); serial_putc(78); serial_putc(80); serial_putc(85); serial_putc(84); serial_putc(95); serial_putc(68); serial_putc(73); serial_putc(65); serial_putc(71); serial_putc(95); serial_putc(79); serial_putc(75); serial_putc(10); return; }\n'
if 'serial_marker_v108_stable_input_diag_ok' in s:
    raise SystemExit('stable input diagnostic marker already present')
start=s.index('fn desktop_input_runtime(process:u64,input_state:u64,phys_state:u64,hardware_state:u64) -> u64 {')
i=start; depth=0; end=None
while i<len(s):
    if s[i]=='{': depth+=1
    elif s[i]=='}':
        depth-=1
        if depth==0:
            end=i+1
            if end<len(s) and s[end]=='\n': end+=1
            break
    i+=1
if end is None:
    raise SystemExit('could not locate desktop_input_runtime end')
new='''fn desktop_input_runtime(process:u64,input_state:u64,phys_state:u64,hardware_state:u64) -> u64 {
    if process==0 || input_state==0 || phys_state==0 || hardware_state==0 { return 0; }
    let state=volatile_read64(process+1080); let wm=volatile_read64(process+1072); let surface=volatile_read64(process+616); let xhci=volatile_read64(input_state+3008);
    if state==0 || wm==0 || surface==0 { return 0; }
    if v108_input_backend_prepare(input_state)==0 { return 0; }
    if xhci!=0 && volatile_read64(xhci+416)==1 { if xhci_hid_arm_continuous(xhci,phys_state)==0 { return 0; } }
    if v108_input_overlay_present(process,state,input_state,xhci)==0 { return 0; }
    serial_marker_v108_input_telemetry_ok();
    serial_marker_v108_stable_input_diag_ok();
    unsafe { volatile_write64(input_state+3320,volatile_read64(input_state+3224)); }
    var last_usb_r=volatile_read64(input_state+3128); var last_ps2_pk=volatile_read64(input_state+3176); var last_src=volatile_read64(input_state+3104);
    while true {
        if xhci!=0 && volatile_read64(xhci+808)!=0 { if xhci_hid_poll_continuous(xhci,input_state)==0 { return 0; } }
        ps2_poll_fallback(input_state);
        var redraw:u64=0;
        let raw_now=volatile_read64(input_state+3224);
        if raw_now!=volatile_read64(input_state+3320) { unsafe { volatile_write64(input_state+3320,raw_now); } redraw=1; }
        let usb_now=volatile_read64(input_state+3128); if usb_now!=last_usb_r { last_usb_r=usb_now; redraw=1; }
        let ps2_now=volatile_read64(input_state+3176); if ps2_now!=last_ps2_pk { last_ps2_pk=ps2_now; redraw=1; }
        let src_now=volatile_read64(input_state+3104); if src_now!=last_src { last_src=src_now; redraw=1; }
        let event=input_pop(input_state);
        if event!=0 {
            let kind=volatile_read64(event);
            if kind==4 || kind==5 || kind==6 {
                let oldx=volatile_read64(state+8); let oldy=volatile_read64(state+16);
                if gui_input_dispatch(state,wm,event,surface)!=0 {
                    let newx=volatile_read64(state+8); let newy=volatile_read64(state+16);
                    if (kind==5 || kind==6) && (newx!=oldx || newy!=oldy) {
                        let source=volatile_read64(input_state+3104);
                        if source==1 && volatile_read64(input_state+3112)==0 { unsafe { volatile_write64(input_state+3112,1); } serial_marker_v108_usb_gui_cursor_ok(); }
                        if source==2 && volatile_read64(input_state+3120)==0 { unsafe { volatile_write64(input_state+3120,1); } serial_marker_v108_ps2_gui_cursor_ok(); }
                    }
                    redraw=1;
                }
            }
        }
        if redraw!=0 { if v108_input_overlay_present(process,state,input_state,xhci)==0 { return 0; } }
        cpu_pause();
    }
    return 1;
}
'''
s=s[:start]+marker+new+s[end:]
p.write_text(s)
out=hashlib.sha256(p.read_bytes()).hexdigest()
print(out)
expected_out='de8cd41f707268bc0d7bb2ff5ef925ba0e8981650703afdb065b1a62a1d6cca1'
if out!=expected_out:
    raise SystemExit(f'unexpected stable diagnostic output hash: {out}')
