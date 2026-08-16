#!/usr/bin/env python3
from pathlib import Path
import hashlib,sys

p=Path(sys.argv[1])
raw=p.read_bytes()
expected='b2dee4fc2c1ca3ad68d4428febf564a2143948ee797ea74ee532ac87b2c14ab6'
actual=hashlib.sha256(raw).hexdigest()
if actual!=expected:
    raise SystemExit(f'unexpected r10 hash {actual}')
s=raw.decode()

for off in range(3560,3608,8):
    if f'input_state+{off}' in s:
        raise SystemExit(f'r11 input telemetry offset already used: {off}')
for off in range(840,904,8):
    if f'xhci_state+{off}' in s:
        raise SystemExit(f'r11 xhci telemetry offset already used: {off}')

def fn_span(text,name):
    st=text.index(name); op=text.index('{',st); d=0
    for j in range(op,len(text)):
        if text[j]=='{': d+=1
        elif text[j]=='}':
            d-=1
            if d==0: return st,j+1
    raise RuntimeError(name)

def repl_fn(name,new):
    global s
    st,en=fn_span(s,name); s=s[:st]+new+s[en:]

def text_fn(name,text):
    ops=[]
    for i,c in enumerate(text):
        ops.append(f'if gui_draw_char_scaled(surface,((x+{i*6})*65536)+y,({ord(c)}*65536)+1,color)==0 {{ return 0; }}')
    return f"fn {name}(surface:u64,x:u64,y:u64,color:u64) -> u64 {{ {' '.join(ops)} return 1; }}\n"

def marker_fn(name,text):
    body=' '.join(f'serial_putc({ord(c)});' for c in text+'\n')
    return f'fn {name}() -> void {{ {body} return; }}\n'

old='let hcs1=volatile_read32(base+4); var maxslots=hcs1%256; if maxslots>8 { maxslots=8; } if maxslots==0 { return 0; } unsafe { volatile_write32(op+56,maxslots); }'
new='let hcs1=volatile_read32(base+4); var maxslots=hcs1%256; if maxslots>32 { maxslots=32; } if maxslots==0 { return 0; } unsafe { volatile_write32(op+56,maxslots); }'
if s.count(old)!=1: raise SystemExit('xhci maxslots anchor')
s=s.replace(old,new,1)

old='''while usb_hid_configured==0 && usb_scan_tries<8 {
                    xhci_port_ready=xhci_reset_connected_port_from(xhci_state,usb_scan_start);
                    if xhci_port_ready==0 { usb_scan_tries=8; unsafe { volatile_write64(input_state+3200,usb_scan_tries); } }'''
new='''while usb_hid_configured==0 && usb_scan_tries<32 {
                    xhci_port_ready=xhci_reset_connected_port_from(xhci_state,usb_scan_start);
                    if xhci_port_ready==0 { usb_scan_tries=32; unsafe { volatile_write64(input_state+3200,usb_scan_tries); } }'''
if s.count(old)!=1: raise SystemExit('usb scan cap anchor')
s=s.replace(old,new,1)

repl_fn('fn xhci_discover_boot_hid',r'''fn xhci_discover_boot_hid(xhci_state:u64, phys_state:u64) -> u64 {
    if volatile_read64(xhci_state+296)!=1 { return 0; }
    unsafe {
        volatile_write64(xhci_state+840,0); volatile_write64(xhci_state+848,0); volatile_write64(xhci_state+856,0);
        volatile_write64(xhci_state+864,0); volatile_write64(xhci_state+872,0); volatile_write64(xhci_state+880,0);
        volatile_write64(xhci_state+888,0); volatile_write64(xhci_state+896,0);
    }
    var head:u64=0; var head_ok:u64=0; var htries:u64=0; var total:u64=0; var config_value:u64=0;
    while htries<3 && head_ok==0 {
        head=xhci_control_get(xhci_state,phys_state,2533274823952000,9); htries=htries+1;
        unsafe { volatile_write64(xhci_state+840,htries); }
        if head!=0 && volatile_read8(head)>=9 && volatile_read8(head+1)==2 {
            total=volatile_read8(head+2)+(volatile_read8(head+3)*256); config_value=volatile_read8(head+5);
            unsafe { volatile_write64(xhci_state+848,total); volatile_write64(xhci_state+856,config_value); }
            if total>=9 && total<=4096 && config_value!=0 { head_ok=1; }
        }
        if head_ok==0 { pit_wait(11932); }
    }
    if head_ok==0 { return 0; }
    var full:u64=0; var full_ok:u64=0; var ftries:u64=0;
    while ftries<3 && full_ok==0 {
        let setup=33556096+(total*281474976710656); full=xhci_control_get(xhci_state,phys_state,setup,total); ftries=ftries+1;
        unsafe { volatile_write64(xhci_state+896,ftries); }
        if full!=0 && volatile_read8(full)>=9 && volatile_read8(full+1)==2 { full_ok=1; }
        if full_ok==0 { pit_wait(11932); }
    }
    if full_ok==0 { return 0; }
    var off:u64=0; var active:u64=0; var interface_num:u64=0; var protocol:u64=0; var endpoint:u64=0; var packet:u64=0; var interval:u64=0; var burst:u64=0;
    while off+2<=total {
        let len=volatile_read8(full+off); let typ=volatile_read8(full+off+1); if len<2 || off+len>total { return 0; }
        if typ==4 && len>=9 {
            active=0; let cls=volatile_read8(full+off+5); let sub=volatile_read8(full+off+6); let pro=volatile_read8(full+off+7);
            unsafe { volatile_write64(xhci_state+864,cls); volatile_write64(xhci_state+872,sub); volatile_write64(xhci_state+880,pro); }
            if cls==3 && sub==1 && (pro==1 || pro==2) { active=1; interface_num=volatile_read8(full+off+2); protocol=pro; }
        }
        if typ==5 && len>=7 && active==1 && endpoint==0 {
            let addr=volatile_read8(full+off+2); let attrs=volatile_read8(full+off+3); if addr>=128 && attrs%4==3 {
                let raw=volatile_read8(full+off+4)+(volatile_read8(full+off+5)*256); let epnum=addr%16; let maxpacket=raw%2048; if epnum>0 && maxpacket>0 && maxpacket<=1024 { endpoint=addr; packet=maxpacket; interval=volatile_read8(full+off+6); burst=(raw/2048)%4; unsafe { volatile_write64(xhci_state+888,endpoint); } }
            }
        }
        off=off+len;
    }
    if endpoint==0 || interval==0 { return 0; } let dci=((endpoint%16)*2)+1;
    unsafe { volatile_write64(xhci_state+304,full); volatile_write64(xhci_state+312,total); volatile_write64(xhci_state+320,config_value); volatile_write64(xhci_state+328,interface_num); volatile_write64(xhci_state+336,protocol); volatile_write64(xhci_state+344,endpoint); volatile_write64(xhci_state+352,dci); volatile_write64(xhci_state+360,packet); volatile_write64(xhci_state+368,interval); volatile_write64(xhci_state+376,burst); volatile_write64(xhci_state+384,1); }
    serial_marker_usb_hid_found(); return 1;
}''')

repl_fn('fn ps2_elan4_rel_v110',r'''fn ps2_elan4_rel_v110(oldxy:u64,newxy:u64) -> u64 {
    let ox=oldxy/65536; let oy=oldxy%65536; let x=newxy/65536; let y=newxy%65536; var ax:u64=0; var ay:u64=0; var xr:u64=0; var yr:u64=0;
    if x>=ox { ax=x-ox; } else { ax=ox-x; } if y>=oy { ay=y-oy; } else { ay=oy-y; } if ax>512 || ay>512 { return 0; }
    if ax!=0 { var sx=(ax+3)/4; if sx==0 { sx=1; } if sx>64 { sx=64; } if x>=ox { xr=sx; } else { xr=256-sx; } }
    if ay!=0 { var sy=(ay+3)/4; if sy==0 { sy=1; } if sy>64 { sy=64; } if y>=oy { yr=256-sy; } else { yr=sy; } } return (xr*256)+yr;
}''')

emit_at=s.index('fn ps2_elan4_emit_v110')
s=s[:emit_at]+r'''fn ps2_elan4_buttons_v111(input_state:u64,a:u64) -> u64 {
    if input_state==0 { return 0; }
    let buttons=(a/65536)%4; let old=volatile_read64(input_state+3560);
    if buttons!=old {
        unsafe {
            volatile_write64(input_state+3560,buttons);
            volatile_write64(input_state+3568,volatile_read64(input_state+3568)+1);
            if buttons%2!=0 && old%2==0 { volatile_write64(input_state+3576,volatile_read64(input_state+3576)+1); }
        }
        input_push(input_state,4,0,buttons);
    }
    return buttons;
}
'''+s[emit_at:]

repl_fn('fn ps2_elan4_emit_v110',r'''fn ps2_elan4_emit_v110(input_state:u64,a:u64,b:u64,typ:u64) -> u64 {
    if input_state==0 { return 0; }
    ps2_elan4_buttons_v111(input_state,a);
    if typ==1 { let fingers=(a/256)%32; if fingers==0 { unsafe { volatile_write64(input_state+3512,0); } } return 1; }
    if typ!=2 { return 1; }
    let xy=ps2_elan4_xy_v110(a,b); let x=xy/65536; let y=xy%65536;
    if volatile_read64(input_state+3512)==0 { unsafe { volatile_write64(input_state+3496,x); volatile_write64(input_state+3504,y); volatile_write64(input_state+3512,1); } return 1; }
    let ox=volatile_read64(input_state+3496); let oy=volatile_read64(input_state+3504); unsafe { volatile_write64(input_state+3496,x); volatile_write64(input_state+3504,y); }
    let rel=ps2_elan4_rel_v110((ox*65536)+oy,xy); let xr=rel/256; let yr=rel%256;
    unsafe { volatile_write64(input_state+3104,2); volatile_write64(input_state+3176,volatile_read64(input_state+3176)+1); volatile_write64(input_state+3520,volatile_read64(input_state+3520)+1); }
    if volatile_read64(input_state+3168)==0 { unsafe { volatile_write64(input_state+3168,1); } serial_marker_v108_ps2_packet_ok(); }
    if xr!=0 { input_push(input_state,5,0,xr); } if yr!=0 { input_push(input_state,6,0,yr); } return 1;
}''')

anchor='volatile_write64(input_state+3536,0); volatile_write64(input_state+3544,0); volatile_write64(input_state+3552,0);'
if s.count(anchor)!=1: raise SystemExit('r11 reset anchor')
s=s.replace(anchor,anchor+'\n        volatile_write64(input_state+3560,0); volatile_write64(input_state+3568,0); volatile_write64(input_state+3576,0); volatile_write64(input_state+3584,0); volatile_write64(input_state+3592,0); volatile_write64(input_state+3600,0);',1)

old='''if ps2_elan4_rel_v110(base,(1080*65536)+1000)!=(10*256) { return 0; } if ps2_elan4_rel_v110(base,(920*65536)+1000)!=(246*256) { return 0; }
    if ps2_elan4_rel_v110(base,(1000*65536)+1080)!=246 { return 0; } if ps2_elan4_rel_v110(base,(1000*65536)+920)!=10 { return 0; }'''
new='''if ps2_elan4_rel_v110(base,(1080*65536)+1000)!=(20*256) { return 0; } if ps2_elan4_rel_v110(base,(920*65536)+1000)!=(236*256) { return 0; }
    if ps2_elan4_rel_v110(base,(1000*65536)+1080)!=236 { return 0; } if ps2_elan4_rel_v110(base,(1000*65536)+920)!=20 { return 0; }'''
if s.count(old)!=1: raise SystemExit('r11 selftest gain anchor')
s=s.replace(old,new,1)

runtime_at=s.index('fn desktop_input_runtime')
s=s[:runtime_at]+marker_fn('serial_marker_v108_gui_click_ok','FRAMES_V108_GUI_CLICK_OK')+s[runtime_at:]
old='''if gui_input_dispatch(state,wm,event,surface)!=0 {
                    let newx=volatile_read64(state+8); let newy=volatile_read64(state+16);'''
new='''if gui_input_dispatch(state,wm,event,surface)!=0 {
                    if kind==4 {
                        let buttons=volatile_read64(event+16); let old_buttons=volatile_read64(input_state+3584);
                        if buttons!=old_buttons {
                            unsafe {
                                volatile_write64(input_state+3584,buttons);
                                volatile_write64(input_state+3592,volatile_read64(input_state+3592)+1);
                                if buttons%2!=0 && old_buttons%2==0 { volatile_write64(input_state+3600,volatile_read64(input_state+3600)+1); }
                            }
                            if buttons%2!=0 && old_buttons%2==0 && volatile_read64(input_state+3600)==1 { serial_marker_v108_gui_click_ok(); }
                        }
                        desktop_shell_click(process,state,buttons); appearance_handle_click(process,state,buttons);
                    }
                    let newx=volatile_read64(state+8); let newy=volatile_read64(state+16);'''
if s.count(old)!=1: raise SystemExit('r11 gui click anchor')
s=s.replace(old,new,1)

overlay_at=s.index('fn v108_input_overlay_draw')
s=s[:overlay_at]+text_fn('v108_text_usbcfg','USB G L I S P E')+text_fn('v108_text_btn','BTN H HP G GP')+s[overlay_at:]

repl_fn('fn v108_input_overlay_draw',r'''fn v108_input_overlay_draw(surface:u64,state:u64,input_state:u64,xhci:u64) -> u64 {
    if surface==0 || state==0 || input_state==0 { return 0; }
    let w=volatile_read64(surface+16); var px:u64=8; if w>430 { px=w-420; }
    let py:u64=8; let bg:u64=4279308561; let edge:u64=4283268350; let white:u64=4294244347; let green:u64=4286644030; let amber:u64=4294934528; let red:u64=4294907956;
    if display_fill_rect(surface,(px*65536)+py,(410*65536)+256,bg)==0 { return 0; }
    display_fill_rect(surface,(px*65536)+py,(410*65536)+2,edge); display_fill_rect(surface,(px*65536)+(py+254),(410*65536)+2,edge);
    v108_text_input(surface,px+10,py+8,white);
    v108_text_usb(surface,px+10,py+28,white);
    var usb_h:u64=0; var usb_p:u64=0; if xhci!=0 { usb_h=volatile_read64(xhci+416); usb_p=volatile_read64(xhci+112); }
    let usb_r=volatile_read64(input_state+3128); var usb_cc:u64=0; var usb_xfer:u64=0; if xhci!=0 { usb_cc=volatile_read64(xhci+488); usb_xfer=volatile_read64(xhci+504); }
    v108_draw_small_u64(surface,((px+82)*65536)+(py+28),usb_h,green); v108_draw_small_u64(surface,((px+130)*65536)+(py+28),usb_r,green); v108_draw_small_u64(surface,((px+178)*65536)+(py+28),usb_p,amber);
    v108_text_us2(surface,px+10,py+46,white);
    v108_draw_small_u64(surface,((px+82)*65536)+(py+46),volatile_read64(input_state+3192),amber); v108_draw_small_u64(surface,((px+130)*65536)+(py+46),volatile_read64(input_state+3200),white); v108_draw_small_u64(surface,((px+178)*65536)+(py+46),usb_xfer,red); v108_draw_small_u64(surface,((px+232)*65536)+(py+46),usb_cc,red);
    v108_text_usbd(surface,px+10,py+64,white); if xhci!=0 { v108_draw_small_u64(surface,((px+82)*65536)+(py+64),volatile_read64(xhci+576),white); v108_draw_small_u64(surface,((px+130)*65536)+(py+64),volatile_read64(xhci+552),amber); v108_draw_small_u64(surface,((px+178)*65536)+(py+64),volatile_read64(xhci+560),amber); v108_draw_small_u64(surface,((px+226)*65536)+(py+64),volatile_read64(xhci+568),green); v108_draw_small_u64(surface,((px+274)*65536)+(py+64),volatile_read64(xhci+544),white); }
    v108_text_usbcfg(surface,px+10,py+82,white); if xhci!=0 { v108_draw_small_u64(surface,((px+82)*65536)+(py+82),volatile_read64(xhci+840),white); v108_draw_small_u64(surface,((px+130)*65536)+(py+82),volatile_read64(xhci+848),white); v108_draw_small_u64(surface,((px+178)*65536)+(py+82),volatile_read64(xhci+864),amber); v108_draw_small_u64(surface,((px+226)*65536)+(py+82),volatile_read64(xhci+872),amber); v108_draw_small_u64(surface,((px+274)*65536)+(py+82),volatile_read64(xhci+880),amber); v108_draw_small_u64(surface,((px+322)*65536)+(py+82),volatile_read64(xhci+888),green); }
    v108_text_ps2(surface,px+10,py+100,white); v108_draw_small_u64(surface,((px+82)*65536)+(py+100),volatile_read64(input_state+3136),green); v108_draw_small_u64(surface,((px+142)*65536)+(py+100),volatile_read64(input_state+3176),green);
    v108_text_p2raw(surface,px+10,py+118,white); v108_draw_small_u64(surface,((px+82)*65536)+(py+118),volatile_read64(input_state+3224),white); v108_draw_small_u64(surface,((px+148)*65536)+(py+118),volatile_read64(input_state+3232),green); v108_draw_small_u64(surface,((px+214)*65536)+(py+118),volatile_read64(input_state+3240),red);
    v108_text_p2dec(surface,px+10,py+136,white); v108_draw_small_u64(surface,((px+82)*65536)+(py+136),volatile_read64(input_state+3184),white); v108_draw_small_u64(surface,((px+148)*65536)+(py+136),volatile_read64(input_state+3488),amber); v108_draw_small_u64(surface,((px+214)*65536)+(py+136),volatile_read64(input_state+3176),green);
    v108_text_p2rej(surface,px+10,py+154,white); v108_draw_small_u64(surface,((px+82)*65536)+(py+154),volatile_read64(input_state+3528),white); v108_draw_small_u64(surface,((px+148)*65536)+(py+154),volatile_read64(input_state+3272)+volatile_read64(input_state+3280),red); v108_draw_small_u64(surface,((px+214)*65536)+(py+154),volatile_read64(input_state+3288),red);
    v108_text_p2a(surface,px+10,py+172,white); v108_draw_small_u64(surface,((px+82)*65536)+(py+172),volatile_read64(input_state+3432),white); v108_draw_small_u64(surface,((px+148)*65536)+(py+172),volatile_read64(input_state+3440),white); v108_draw_small_u64(surface,((px+214)*65536)+(py+172),volatile_read64(input_state+3448),white);
    v108_text_p2lst(surface,px+10,py+190,white); v108_draw_small_u64(surface,((px+82)*65536)+(py+190),volatile_read64(input_state+3456),white); v108_draw_small_u64(surface,((px+148)*65536)+(py+190),volatile_read64(input_state+3464),white); v108_draw_small_u64(surface,((px+214)*65536)+(py+190),volatile_read64(input_state+3472),white);
    v108_text_src(surface,px+10,py+208,white); v108_draw_small_u64(surface,((px+58)*65536)+(py+208),volatile_read64(input_state+3104),amber); v108_draw_small_u64(surface,((px+112)*65536)+(py+208),volatile_read64(state+8),white); v108_draw_small_u64(surface,((px+220)*65536)+(py+208),volatile_read64(state+16),white);
    v108_text_btn(surface,px+10,py+226,white); v108_draw_small_u64(surface,((px+82)*65536)+(py+226),volatile_read64(input_state+3560),amber); v108_draw_small_u64(surface,((px+130)*65536)+(py+226),volatile_read64(input_state+3576),green); v108_draw_small_u64(surface,((px+202)*65536)+(py+226),volatile_read64(input_state+3584),amber); v108_draw_small_u64(surface,((px+250)*65536)+(py+226),volatile_read64(input_state+3600),green);
    return 1;
}''')

if s.count('(410*65536)+220')!=2: raise SystemExit('r11 overlay present height anchor')
s=s.replace('(410*65536)+220','(410*65536)+256')

p.write_text(s)
out=hashlib.sha256(p.read_bytes()).hexdigest()
print(out)
expected_out='4e6b4fd0f4c44020099e2c097615d3b6f03e8e123763fd803c90eb1d40f3b016'
if out!=expected_out:
    raise SystemExit(f'unexpected r11 output hash {out}')
