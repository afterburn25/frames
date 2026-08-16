#!/usr/bin/env python3
from pathlib import Path
import hashlib,sys
p=Path(sys.argv[1]); s=p.read_text()
if 'serial_marker_v108_ps2_gui_cursor_ok' not in s or 'fn v108_input_backend_prepare(input_state:u64) -> u64 { return 1; }' not in s:
    raise SystemExit('apply patch_v108_live_input_common.py first')
for off in ('input_state+3136','input_state+3144','input_state+3152','input_state+3160','input_state+3168','input_state+3176','input_state+3184'):
    if off in s: raise SystemExit(f'PS2 state offset already used: {off}')

def rep(old,new,label):
    global s
    n=s.count(old)
    if n!=1: raise SystemExit(f'{label}: expected 1 site, found {n}')
    s=s.replace(old,new,1)

helper='fn v108_input_backend_prepare(input_state:u64) -> u64 { return 1; }'
ps2=r'''fn ps2_wait_input_clear_v108() -> u64 {
    var spins:u64=0; while spins<2000000 { if (io_read8(100)/2)%2==0 { return 1; } cpu_pause(); spins=spins+1; } return 0;
}
fn ps2_wait_aux_ack_v108() -> u64 {
    var spins:u64=0;
    while spins<2000000 {
        let status=io_read8(100);
        if status%2!=0 { let data=io_read8(96); if (status/32)%2!=0 && data==250 { return 1; } }
        cpu_pause(); spins=spins+1;
    }
    return 0;
}
fn ps2_mouse_command_v108(cmd:u64) -> u64 {
    if ps2_wait_input_clear_v108()==0 { return 0; } io_write8(100,212);
    if ps2_wait_input_clear_v108()==0 { return 0; } io_write8(96,cmd);
    return ps2_wait_aux_ack_v108();
}
fn ps2_mouse_enable_v108(input_state:u64) -> u64 {
    if input_state==0 { return 0; }
    if volatile_read64(input_state+3136)==1 { return 1; }
    if ps2_wait_input_clear_v108()==0 { return 0; } io_write8(100,168);
    if ps2_mouse_command_v108(246)==0 { return 0; }
    if ps2_mouse_command_v108(244)==0 { return 0; }
    unsafe { volatile_write64(input_state+3136,1); volatile_write64(input_state+3144,0); }
    serial_marker_v108_ps2_enable_ok(); return 1;
}
fn ps2_mouse_resync_v108(input_state:u64,data:u64) -> u64 {
    if (data/8)%2!=0 { unsafe { volatile_write64(input_state+3152,data%256); volatile_write64(input_state+3144,1); } }
    else { unsafe { volatile_write64(input_state+3144,0); } }
    return 1;
}
fn ps2_mouse_decode_v108(input_state:u64,data:u64) -> u64 {
    if input_state==0 || volatile_read64(input_state+32)!=1 { return 0; }
    let byte=data%256; unsafe { volatile_write64(input_state+3184,volatile_read64(input_state+3184)+1); }
    if byte==250 || byte==170 { return 1; }
    let phase=volatile_read64(input_state+3144);
    if phase==0 { return ps2_mouse_resync_v108(input_state,byte); }
    if phase==1 { unsafe { volatile_write64(input_state+3160,byte); volatile_write64(input_state+3144,2); } return 1; }
    let header=volatile_read64(input_state+3152)%256; let dx=volatile_read64(input_state+3160)%256; let dy=byte;
    unsafe { volatile_write64(input_state+3144,0); }
    if (header/8)%2==0 || (header/64)%2!=0 || (header/128)%2!=0 { return ps2_mouse_resync_v108(input_state,dy); }
    let xsign=(header/16)%2; let ysign=(header/32)%2;
    if xsign!=(dx/128)%2 || ysign!=(dy/128)%2 { return ps2_mouse_resync_v108(input_state,dy); }
    let buttons=header%8; let yscreen=(256-dy)%256;
    unsafe { volatile_write64(input_state+3104,2); volatile_write64(input_state+3176,volatile_read64(input_state+3176)+1); }
    if volatile_read64(input_state+3168)==0 { unsafe { volatile_write64(input_state+3168,1); } serial_marker_v108_ps2_packet_ok(); }
    input_push(input_state,4,0,buttons); input_push(input_state,5,0,dx); input_push(input_state,6,0,yscreen);
    return 1;
}
fn v108_input_backend_prepare(input_state:u64) -> u64 {
    ps2_mouse_enable_v108(input_state); return 1;
}'''
rep(helper,ps2,'PS2 backend prepare')

old='''fn ps2_poll_fallback(input_state:u64) -> u64 {
    if input_state==0 || volatile_read64(input_state+32)!=1 { return 0; } let status=io_read8(100); if status%2==0 { return 0; } let data=io_read8(96); if (status/32)%2!=0 { input_push(input_state,8,0,data); } else { input_push(input_state,7,data,1); } unsafe { volatile_write64(input_state+56,1); } return 1;
}'''
new='''fn ps2_poll_fallback(input_state:u64) -> u64 {
    if input_state==0 || volatile_read64(input_state+32)!=1 { return 0; }
    let status=io_read8(100); if status%2==0 { return 0; } let data=io_read8(96);
    if (status/32)%2!=0 { ps2_mouse_decode_v108(input_state,data); } else { input_push(input_state,7,data,1); }
    unsafe { volatile_write64(input_state+56,1); } return 1;
}'''
rep(old,new,'PS2 polling decoder hookup')
p.write_text(s)
print(hashlib.sha256(p.read_bytes()).hexdigest())
