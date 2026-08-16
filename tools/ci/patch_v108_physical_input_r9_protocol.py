from pathlib import Path
import hashlib
import sys
src=Path(sys.argv[1])
s=src.read_text()
assert hashlib.sha256(src.read_bytes()).hexdigest()=='b0e7893dea8306b44ea044b5e712fb4568223b5bdd599b9d369f19e523bad037'

def fn_span(text,name):
    st=text.index(name)
    op=text.index('{',st); d=0; j=op
    while j<len(text):
        if text[j]=='{': d+=1
        elif text[j]=='}':
            d-=1
            if d==0: return st,j+1
        j+=1
    raise RuntimeError(name)

def repl_fn(name,new):
    global s
    st,en=fn_span(s,name)
    s=s[:st]+new+s[en:]

anchor='fn ps2_mouse_enable_v108(input_state:u64) -> u64 {'
assert s.count(anchor)==1
helpers=r'''fn ps2_mouse_param_v109(cmd:u64,param:u64) -> u64 {
    if ps2_mouse_command_v108(cmd)==0 { return 0; }
    if ps2_wait_input_clear_v108()==0 { return 0; } io_write8(100,212);
    if ps2_wait_input_clear_v108()==0 { return 0; } io_write8(96,param%256);
    return ps2_wait_aux_ack_v108();
}
fn ps2_mouse_read_aux_v109() -> u64 {
    var spins:u64=0;
    while spins<2000000 {
        let status=io_read8(100);
        if status%2!=0 { let data=io_read8(96); if (status/32)%2!=0 { return 256+(data%256); } }
        cpu_pause(); spins=spins+1;
    }
    return 0;
}
fn ps2_mouse_status_v109(input_state:u64) -> u64 {
    if ps2_mouse_command_v108(233)==0 { return 0; }
    let a=ps2_mouse_read_aux_v109(); let b=ps2_mouse_read_aux_v109(); let c=ps2_mouse_read_aux_v109();
    if a<256 || b<256 || c<256 { return 0; }
    unsafe { volatile_write64(input_state+3352,a-256); volatile_write64(input_state+3360,b-256); volatile_write64(input_state+3368,c-256); }
    return 1;
}
fn ps2_synaptics_slice_v109(value:u64) -> u64 {
    var div:u64=64;
    while div>0 { let chunk=(value/div)%4; if ps2_mouse_param_v109(232,chunk)==0 { return 0; } div=div/4; }
    return 1;
}
fn ps2_probe_protocol_v109(input_state:u64) -> u64 {
    unsafe { volatile_write64(input_state+3344,0); volatile_write64(input_state+3352,0); volatile_write64(input_state+3360,0); volatile_write64(input_state+3368,0); }
    var i:u64=0; while i<4 { if ps2_mouse_param_v109(232,0)==0 { return 0; } i=i+1; }
    if ps2_mouse_status_v109(input_state)==0 { return 0; }
    if volatile_read64(input_state+3360)==71 { unsafe { volatile_write64(input_state+3344,1); } }
    return 1;
}
fn ps2_synaptics_relative_v109() -> u64 {
    if ps2_synaptics_slice_v109(0)==0 { return 0; }
    return ps2_mouse_param_v109(243,20);
}
'''
s=s.replace(anchor,helpers+anchor,1)

repl_fn('fn ps2_mouse_enable_v108',r'''fn ps2_mouse_enable_v108(input_state:u64) -> u64 {
    if input_state==0 { return 0; }
    if volatile_read64(input_state+3136)==1 { return 1; }
    if ps2_wait_input_clear_v108()==0 { return 0; } io_write8(100,168);
    if ps2_mouse_command_v108(245)==0 { return 0; }
    let probe=ps2_probe_protocol_v109(input_state);
    if ps2_mouse_command_v108(246)==0 { return 0; }
    if probe!=0 && volatile_read64(input_state+3344)==1 { if ps2_synaptics_relative_v109()==0 { return 0; } }
    if ps2_mouse_command_v108(244)==0 { return 0; }
    unsafe {
        volatile_write64(input_state+3136,1); volatile_write64(input_state+3144,0);
        volatile_write64(input_state+3376,0); volatile_write64(input_state+3384,0); volatile_write64(input_state+3392,0); volatile_write64(input_state+3400,0);
        volatile_write64(input_state+3408,0); volatile_write64(input_state+3416,0);
    }
    serial_marker_v108_ps2_enable_ok(); return 1;
}''')

repl_fn('fn ps2_mouse_decode_v108',r'''fn ps2_mouse_decode_v108(input_state:u64,data:u64) -> u64 {
    if input_state==0 || volatile_read64(input_state+32)!=1 { return 0; }
    let byte=data%256; unsafe { volatile_write64(input_state+3184,volatile_read64(input_state+3184)+1); }
    if byte==250 || byte==170 { return 1; }
    var count=volatile_read64(input_state+3376);
    if count==0 { unsafe { volatile_write64(input_state+3384,byte); volatile_write64(input_state+3376,1); } return 1; }
    if count==1 { unsafe { volatile_write64(input_state+3392,byte); volatile_write64(input_state+3376,2); } return 1; }
    let h=volatile_read64(input_state+3384)%256; let dx=volatile_read64(input_state+3392)%256; let dy=byte;
    unsafe { volatile_write64(input_state+3400,dy); volatile_write64(input_state+3296,h); volatile_write64(input_state+3304,dx); volatile_write64(input_state+3312,dy); }
    let xsign=(h/16)%2; let ysign=(h/32)%2; var valid:u64=1;
    if (h/8)%2==0 || (h/64)%2!=0 || (h/128)%2!=0 { valid=0; unsafe { volatile_write64(input_state+3280,volatile_read64(input_state+3280)+1); } }
    if valid!=0 && (xsign!=(dx/128)%2 || ysign!=(dy/128)%2) { valid=0; unsafe { volatile_write64(input_state+3288,volatile_read64(input_state+3288)+1); } }
    var ax=dx; if xsign!=0 { ax=256-dx; } var ay=dy; if ysign!=0 { ay=256-dy; }
    if valid!=0 && (ax>80 || ay>80) { valid=0; unsafe { volatile_write64(input_state+3416,volatile_read64(input_state+3416)+1); } }
    if valid==0 {
        unsafe { volatile_write64(input_state+3384,dx); volatile_write64(input_state+3392,dy); volatile_write64(input_state+3376,2); volatile_write64(input_state+3408,0); volatile_write64(input_state+3272,volatile_read64(input_state+3272)+1); }
        return 1;
    }
    unsafe { volatile_write64(input_state+3376,0); }
    var run=volatile_read64(input_state+3408)+1; if run>3 { run=3; } unsafe { volatile_write64(input_state+3408,run); }
    if run<2 { return 1; }
    let buttons=h%8; let yscreen=(256-dy)%256;
    unsafe { volatile_write64(input_state+3104,2); volatile_write64(input_state+3176,volatile_read64(input_state+3176)+1); }
    if volatile_read64(input_state+3168)==0 { unsafe { volatile_write64(input_state+3168,1); } serial_marker_v108_ps2_packet_ok(); }
    input_push(input_state,4,0,buttons); input_push(input_state,5,0,dx); input_push(input_state,6,0,yscreen);
    return 1;
}''')

st,en=fn_span(s,'fn xhci_finalize_address_and_descriptor')
old=s[st:en]
needle='''    let full=xhci_control_get(xhci_state,phys_state,5066549597570688,18); if full==0 { return 0; }\n    if volatile_read8(full)<18 || volatile_read8(full+1)!=1 { return 0; }\n    let vid=volatile_read8(full+8)+(volatile_read8(full+9)*256); let pid=volatile_read8(full+10)+(volatile_read8(full+11)*256); let configs=volatile_read8(full+17); if configs==0 { return 0; }'''
assert old.count(needle)==1
replacement='''    var full:u64=0; var full_ok:u64=0; var tries:u64=0;\n    while tries<3 && full_ok==0 {\n        full=xhci_control_get(xhci_state,phys_state,5066549597570688,18); tries=tries+1;\n        if full!=0 { let dl=volatile_read8(full); let dt=volatile_read8(full+1); unsafe { volatile_write64(xhci_state+552,dl); volatile_write64(xhci_state+560,dt); } if dl>=18 && dt==1 { full_ok=1; } }\n    }\n    unsafe { volatile_write64(xhci_state+544,tries); } if full_ok==0 { return 0; }\n    let vid=volatile_read8(full+8)+(volatile_read8(full+9)*256); let pid=volatile_read8(full+10)+(volatile_read8(full+11)*256); let configs=volatile_read8(full+17); unsafe { volatile_write64(xhci_state+568,configs); } if configs==0 { return 0; }'''
old=old.replace(needle,replacement,1)
s=s[:st]+old+s[en:]

st,en=fn_span(s,'fn v108_text_us2')
block=s[st:en]
oldchar='((x+48)*65536)+y,(67*65536)+1'
assert block.count(oldchar)==1
block=block.replace(oldchar,'((x+48)*65536)+y,(88*65536)+1',1)
s=s[:st]+block+s[en:]

st,en=fn_span(s,'fn v108_input_overlay_draw')
block=s[st:en]
oldline='''    let usb_r=volatile_read64(input_state+3128); var usb_cc:u64=0; if xhci!=0 { usb_cc=volatile_read64(xhci+488); }'''
newline='''    let usb_r=volatile_read64(input_state+3128); var usb_cc:u64=0; var usb_xfer:u64=0; if xhci!=0 { usb_cc=volatile_read64(xhci+488); usb_xfer=volatile_read64(xhci+504); }'''
assert block.count(oldline)==1
block=block.replace(oldline,newline,1)
old='''v108_draw_small_u64(surface,((px+178)*65536)+(py+46),volatile_read64(input_state+3216),white); v108_draw_small_u64(surface,((px+232)*65536)+(py+46),usb_cc,red);'''
new='''v108_draw_small_u64(surface,((px+178)*65536)+(py+46),usb_xfer,red); v108_draw_small_u64(surface,((px+232)*65536)+(py+46),usb_cc,red);'''
assert block.count(old)==1
block=block.replace(old,new,1)
s=s[:st]+block+s[en:]

src.write_text(s)
out=hashlib.sha256(src.read_bytes()).hexdigest()
expected_out='6612834b5e4735a97c7c90f48cce61d332310cb419c34158de664e10d3738488'
if out!=expected_out: raise SystemExit(f'unexpected r9 output hash: {out}')
print(out)
