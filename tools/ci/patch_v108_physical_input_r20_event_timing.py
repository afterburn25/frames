from pathlib import Path
import hashlib,sys
p=Path(sys.argv[1]); raw=p.read_bytes(); actual=hashlib.sha256(raw).hexdigest(); expected='c78deb76e51b1e2aae2412eb020a82cf2aeca1206254e1b1a7041a60eadec557'
if actual!=expected: raise SystemExit(f'unexpected r19 source hash {actual}')
s=raw.decode()

def fn_span(text,name):
    st=text.index(name); op=text.index('{',st); d=0
    for j in range(op,len(text)):
        if text[j]=='{': d+=1
        elif text[j]=='}':
            d-=1
            if d==0:return st,j+1
    raise RuntimeError(name)

def repl_fn(name,new):
    global s
    a,b=fn_span(s,name); s=s[:a]+new+s[b:]

def marker_fn(name,text):
    return 'fn '+name+'() -> void { '+' '.join(f'serial_putc({ord(c)});' for c in text+'\n')+' return; }\n'

def text_fn(name,text):
    ops=[]
    for i,c in enumerate(text):
        ops.append(f'if gui_draw_char_scaled(surface,((x+{i*6})*65536)+y,({ord(c)}*65536)+1,color)==0 {{ return 0; }}')
    return f"fn {name}(surface:u64,x:u64,y:u64,color:u64) -> u64 {{ {' '.join(ops)} return 1; }}\n"

# Add r20 markers/text before the existing r19 xHCI helper block.
anchor=s.index('fn xhci_map_register_window_v119')
extra=(marker_fn('serial_marker_v108_drag_arm_ok_v120','FRAMES_V108_DRAG_ARM_OK')+
       marker_fn('serial_marker_v108_right_click_restored_v120','FRAMES_V108_RIGHT_CLICK_RESTORED_OK')+
       marker_fn('serial_marker_v108_xhci_timing_ok_v120','FRAMES_V108_XHCI_TIMING_OK')+
       marker_fn('serial_marker_v108_xhci_route_ok_v120','FRAMES_V108_XHCI_ROUTE_OK')+
       marker_fn('serial_marker_v108_full_repaint_v120','FRAMES_V108_FULL_REPAINT_V120')+
       text_fn('v108_text_xrt_v120','XRT U2 M2 U3 M3')+
       '''fn v108_apply_route_mask_v120(route:u64,mask:u64,bits:u64) -> u64 { var out=route; var bit:u64=1; var i:u64=0; while i<bits { if (mask/bit)%2!=0 { out=set_flag(out,bit); } bit=bit*2; i=i+1; } return out; }\n'''+
       '''fn v108_xhci_route_ports_v120(bdf:u64,xhci_state:u64) -> u64 { if bdf==0 || xhci_state==0 { return 0; } let bus=bdf/65536; let dev=(bdf/256)%256; let fun=bdf%256; let id=pci_cfg_read32(bus,dev,fun,0); let vendor=id%65536; let device=(id/65536)%65536; let u2r=pci_cfg_read32(bus,dev,fun,208); let u2m=pci_cfg_read32(bus,dev,fun,212); let u3r=pci_cfg_read32(bus,dev,fun,216); let u3m=pci_cfg_read32(bus,dev,fun,220); unsafe { volatile_write64(xhci_state+1376,u2r); volatile_write64(xhci_state+1384,u2m); volatile_write64(xhci_state+1392,u3r); volatile_write64(xhci_state+1400,u3m); } if vendor==32902 && device==35889 { let n2=v108_apply_route_mask_v120(u2r,u2m,15); let n3=v108_apply_route_mask_v120(u3r,u3m,6); pci_cfg_write32(bdf,208,n2); pci_cfg_write32(bdf,216,n3); let r2=pci_cfg_read32(bus,dev,fun,208); let r3=pci_cfg_read32(bus,dev,fun,216); unsafe { volatile_write64(xhci_state+1408,r2); volatile_write64(xhci_state+1416,r3); volatile_write64(xhci_state+1424,1); } serial_marker_v108_xhci_route_ok_v120(); return 2; } unsafe { volatile_write64(xhci_state+1408,u2r); volatile_write64(xhci_state+1416,u3r); volatile_write64(xhci_state+1424,0); } return 1; }\n'''+
       '''fn v108_pci_enable_xhci_v120(bdf:u64,xhci_state:u64) -> u64 { if bdf==0 { return 0; } let bus=bdf/65536; let dev=(bdf/256)%256; let fun=bdf%256; let old=pci_cfg_read32(bus,dev,fun,4); var command=old%65536; if (command/2)%2==0 { command=command+2; } if (command/4)%2==0 { command=command+4; } unsafe { if xhci_state!=0 { volatile_write64(xhci_state+1432,old%65536); } } var tries:u64=0; while tries<3 { let address=2147483648+(bus*65536)+(dev*2048)+(fun*256)+4; io_write32(3320,address); io_write16(3324,command); pit_wait(1193); let check=pci_cfg_read32(bus,dev,fun,4)%65536; unsafe { if xhci_state!=0 { volatile_write64(xhci_state+1440,check); } } if (check/2)%2!=0 && (check/4)%2!=0 { return 1; } tries=tries+1; } return 0; }\n'''+
       '''fn xhci_wait_bit_v120(addr:u64,divisor:u64,wanted:u64,rounds:u64) -> u64 { if addr==0 || divisor==0 || rounds==0 { return 0; } var i:u64=0; while i<rounds { let bit=(volatile_read32(addr)/divisor)%2; if bit==wanted { return 1; } pit_wait(1193); i=i+1; } return 0; }\n''')
s=s[:anchor]+extra+s[anchor:]

repl_fn('fn xhci_wait_halted', '''fn xhci_wait_halted(op:u64, wanted:u64) -> u64 { if op==0 { return 0; } return xhci_wait_bit_v120(op+4,1,wanted,250); }''')

# Make PCI command writes and controller/reset waits tolerant of older real hardware.
a,b=fn_span(s,'fn xhci_controller_init')
old=s[a:b]
old=old.replace('''    if pci_enable_mmio_busmaster(bdf)==0 { unsafe { volatile_write64(xhci_state+1272,1); } return 0; }\n    unsafe { volatile_write64(xhci_state+1264,2); }''','''    if v108_pci_enable_xhci_v120(bdf,xhci_state)==0 { unsafe { volatile_write64(xhci_state+1272,1); } return 0; }\n    unsafe { volatile_write64(xhci_state+1264,2); }\n    v108_xhci_route_ports_v120(bdf,xhci_state);''')
old=old.replace('''    cmd=volatile_read32(op+0); cmd=set_flag(cmd,2); unsafe { volatile_write32(op+0,cmd); }\n    var spins:u64=0; while (volatile_read32(op+0)/2)%2 != 0 && spins<4000000 { cpu_pause(); spins=spins+1; } if spins>=4000000 { unsafe { volatile_write64(xhci_state+1272,7); } return 0; }\n    spins=0; while (volatile_read32(op+4)/2048)%2 != 0 && spins<4000000 { cpu_pause(); spins=spins+1; } if spins>=4000000 { unsafe { volatile_write64(xhci_state+1272,8); } return 0; }\n    unsafe { volatile_write64(xhci_state+1264,6); }''','''    cmd=volatile_read32(op+0); cmd=set_flag(cmd,2); unsafe { volatile_write32(op+0,cmd); }\n    if xhci_wait_bit_v120(op+0,2,0,1000)==0 { unsafe { volatile_write64(xhci_state+1272,7); } return 0; }\n    if xhci_wait_bit_v120(op+4,2048,0,1000)==0 { unsafe { volatile_write64(xhci_state+1272,8); } return 0; }\n    unsafe { volatile_write64(xhci_state+1264,6); } serial_marker_v108_xhci_timing_ok_v120();''')
if old==s[a:b]: raise SystemExit('xhci_controller_init replacements did not apply')
s=s[:a]+old+s[b:]

repl_fn('fn xhci_reset_connected_port_from', '''fn xhci_reset_connected_port_from(xhci_state:u64,start:u64) -> u64 {
    if xhci_state==0 || volatile_read64(xhci_state+56)!=1 { return 0; }
    let base=volatile_read64(xhci_state); let op=volatile_read64(xhci_state+8); let hcs1=volatile_read32(base+4); var ports=(hcs1/16777216)%256; if ports>32 { ports=32; }
    var p=start;
    while p<ports {
        let port=op+1024+(p*16); let ps=volatile_read32(port);
        if ps%2!=0 {
            unsafe { volatile_write64(xhci_state+1456,p+1); volatile_write64(xhci_state+1464,ps); }
            var write=xhci_port_write_base(ps); write=set_flag(write,16); unsafe { volatile_write32(port,write); }
            if xhci_wait_bit_v120(port,16,0,200)!=0 { let done=volatile_read32(port); unsafe { volatile_write64(xhci_state+1472,done); } if done%2!=0 {
                unsafe { volatile_write64(xhci_state+112,p+1); volatile_write64(xhci_state+120,done); volatile_write64(xhci_state+128,1); volatile_write64(xhci_state+384,0); volatile_write64(xhci_state+416,0); }
                pit_wait(11932); serial_marker_xhci_port_ready(); return p+1;
            } }
        }
        p=p+1;
    }
    return 0;
}''')

# Restore raw right-button edges; filter them at the GUI gesture layer instead of discarding them in PS/2 decode.
repl_fn('fn ps2_elan4_buttons_v111', '''fn ps2_elan4_buttons_v111(input_state:u64,a:u64) -> u64 {
    if input_state==0 { return 0; }
    let raw=(a/65536)%4; let left=raw%2; let raw_right=(raw/2)%2; let buttons=left+(raw_right*2); let old=volatile_read64(input_state+3560);
    unsafe { volatile_write64(input_state+3760,raw_right); volatile_write64(input_state+3768,1); }
    if buttons!=old {
        unsafe { if buttons!=0 { volatile_write64(input_state+4088,1); } volatile_write64(input_state+3560,buttons); volatile_write64(input_state+3568,volatile_read64(input_state+3568)+1); if buttons%2!=0 && old%2==0 { volatile_write64(input_state+3576,volatile_read64(input_state+3576)+1); } }
        input_push(input_state,4,0,buttons);
    }
    return buttons;
}''')

# Drag becomes a hold+move gesture. Merely entering the title bar cannot activate it.
repl_fn('fn gui_input_pointer_move', '''fn gui_input_pointer_move(state:u64,wm:u64,raw:u64,axis:u64) -> u64 {
    if state==0 || wm==0 || volatile_read64(state)!=1 { return 0; }
    var x=volatile_read64(state+8); var y=volatile_read64(state+16); var amount=raw%256;
    if axis==1 { if amount>127 { let d=256-amount; if d>x { x=0; } else { x=x-d; } } else { x=x+amount; if x>=volatile_read64(state+64) { x=volatile_read64(state+64)-1; } } }
    if axis==2 { if amount>127 { let d=256-amount; if d>y { y=0; } else { y=y-d; } } else { y=y+amount; if y>=volatile_read64(state+72) { y=volatile_read64(state+72)-1; } } }
    if y+1>=volatile_read64(state+72) && volatile_read64(state+224)==0 { unsafe { volatile_write64(state+224,1); } serial_marker_v108_pointer_bottom_ok(); }
    if volatile_read64(state+392)!=0 {
        if volatile_read64(state+96)%2==0 { unsafe { volatile_write64(state+392,0); } }
        else { let started=volatile_read64(state+416); let now=read_tsc(); let px=volatile_read64(state+400); let py=volatile_read64(state+408); var dx:u64=0; var dy:u64=0; if x>px { dx=x-px; } else { dx=px-x; } if y>py { dy=y-py; } else { dy=py-y; } if started!=0 && now>started && now-started>20000000 && dx+dy>=3 { unsafe { volatile_write64(state+176,1); volatile_write64(state+184,volatile_read64(state+424)); volatile_write64(state+192,volatile_read64(state+432)); volatile_write64(state+392,0); volatile_write64(state+448,volatile_read64(state+448)+1); } serial_marker_v108_drag_arm_ok_v120(); } }
    }
    if volatile_read64(state+176)!=0 {
        let ox=volatile_read64(state+184); let oy=volatile_read64(state+192); var wx:u64=0; var wy:u64=0; if x>ox { wx=x-ox; } if y>oy { wy=y-oy; }
        let sw=volatile_read64(state+64); let panel_y=volatile_read64(state+208); if wx+270>sw { wx=sw-270; } if wy+150>panel_y { wy=panel_y-150; }
        unsafe { volatile_write64(state+160,wx); volatile_write64(state+168,wy); volatile_write64(state+200,volatile_read64(state+200)+1); }
        if volatile_read64(state+216)==0 { unsafe { volatile_write64(state+216,1); } serial_marker_v108_window_drag_ok(); }
    }
    let capture=volatile_read64(state+24); let mode=volatile_read64(state+32);
    if capture!=0 { let rec=wm_record(wm,capture); if rec==0 { return 0; } if mode==1 { let rw=volatile_read64(rec+24); let rh=volatile_read64(rec+32); var nx=x; var ny=y; if nx+rw>volatile_read64(wm+56) { nx=volatile_read64(wm+56)-rw; } if ny+rh>volatile_read64(wm+72) { ny=volatile_read64(wm+72)-rh; } if wm_move(wm,capture,(nx*65536)+ny)==0 { return 0; } unsafe { volatile_write64(state+56,volatile_read64(state+56)+1); } }
        if mode==2 { let rx=volatile_read64(rec+8); let ry=volatile_read64(rec+16); var nw:u64=160; var nh:u64=100; if x>rx+160 { nw=x-rx; } if y>ry+100 { nh=y-ry; } if rx+nw>volatile_read64(wm+56) { nw=volatile_read64(wm+56)-rx; } if ry+nh>volatile_read64(wm+72) { nh=volatile_read64(wm+72)-ry; } if wm_resize(wm,capture,(nw*65536)+nh)==0 { return 0; } unsafe { volatile_write64(state+88,volatile_read64(state+88)+1); } }
    }
    if volatile_read64(state+296)!=0 { let px=volatile_read64(state+304); let py=volatile_read64(state+312); var dx:u64=0; var dy:u64=0; if x>px { dx=x-px; } else { dx=px-x; } if y>py { dy=y-py; } else { dy=py-y; } if dx>6 || dy>6 { unsafe { volatile_write64(state+296,0); volatile_write64(state+320,volatile_read64(state+320)+1); } } }
    if volatile_read64(state+128)!=0 { let before=volatile_read64(state+240); let now=v108_context_hit_v118(state,x,y); if now!=before { unsafe { volatile_write64(state+240,now); } if now!=0 && volatile_read64(state+288)==0 { unsafe { volatile_write64(state+288,1); } serial_marker_v108_context_hover_ok(); } } }
    unsafe { volatile_write64(state+8,x); volatile_write64(state+16,y); } return 1;
}''')

repl_fn('fn gui_input_buttons', '''fn gui_input_buttons(state:u64,wm:u64,buttons:u64,surface:u64) -> u64 {
    if state==0 || wm==0 || surface==0 || volatile_read64(state)!=1 { return 0; }
    let old=volatile_read64(state+96); unsafe { volatile_write64(state+96,buttons); } let x=volatile_read64(state+8); let y=volatile_read64(state+16);
    let right=(buttons/2)%2; let old_right=(old/2)%2;
    if right!=0 && old_right==0 { unsafe { volatile_write64(state+296,1); volatile_write64(state+304,x); volatile_write64(state+312,y); volatile_write64(state+440,read_tsc()); } return 1; }
    if right==0 && old_right!=0 {
        if volatile_read64(state+296)!=0 { let started=volatile_read64(state+440); let now=read_tsc(); if started!=0 && now>started && now-started>20000000 && now-started<2000000000 {
            let ax=volatile_read64(state+304); let ay=volatile_read64(state+312); let opens=volatile_read64(state+152)+1;
            unsafe { volatile_write64(state+296,0); volatile_write64(state+128,1); volatile_write64(state+136,ax); volatile_write64(state+144,ay); volatile_write64(state+152,opens); volatile_write64(state+240,0); volatile_write64(state+288,0); volatile_write64(state+328,volatile_read64(state+328)+1); volatile_write64(state+336,x); volatile_write64(state+344,y); volatile_write64(state+456,volatile_read64(state+456)+1); }
            if v108_context_geometry_v118(surface,state)==0 { return 0; } serial_marker_v108_right_click_restored_v120(); serial_marker_v108_right_gesture_ok_v119(); serial_marker_v108_desktop_context_ok(); if opens>=2 { serial_marker_v108_context_repeat_ok(); } return 1;
        } unsafe { volatile_write64(state+296,0); } }
        return 1;
    }
    if buttons%2!=0 && old%2==0 {
        unsafe { volatile_write64(state+296,0); }
        if volatile_read64(state+128)!=0 { let hit=v108_context_hit_v118(state,x,y); unsafe { volatile_write64(state+248,volatile_read64(state+248)+1); volatile_write64(state+256,hit); volatile_write64(state+128,0); volatile_write64(state+240,0); volatile_write64(state+264,volatile_read64(state+264)+1); } if hit!=0 { serial_marker_v108_context_select_ok(); } else { serial_marker_v108_context_outside_ok(); } serial_marker_v108_context_dismiss_ok(); return 1; }
        let wx=volatile_read64(state+160); let wy=volatile_read64(state+168); if x>=wx && x<wx+270 && y>=wy && y<wy+36 { unsafe { volatile_write64(state+392,1); volatile_write64(state+400,x); volatile_write64(state+408,y); volatile_write64(state+416,read_tsc()); volatile_write64(state+424,x-wx); volatile_write64(state+432,y-wy); volatile_write64(state+24,0); volatile_write64(state+32,0); } return 1; }
        let id=gui_input_hit_test(state,wm,x,y); if id!=0 { if gui_input_focus(state,wm,id)==0 { return 0; } let rec=wm_record(wm,id); let rx=volatile_read64(rec+8); let ry=volatile_read64(rec+16); let rw=volatile_read64(rec+24); let rh=volatile_read64(rec+32); var mode:u64=0; if y>=ry && y<ry+36 { mode=1; } if x+18>=rx+rw && y+18>=ry+rh { mode=2; } unsafe { volatile_write64(state+24,id); volatile_write64(state+32,mode); } }
    }
    if buttons%2==0 && old%2!=0 { unsafe { volatile_write64(state+24,0); volatile_write64(state+32,0); volatile_write64(state+176,0); volatile_write64(state+392,0); } }
    return 1;
}''')

# Initialize new GUI gesture state explicitly.
a,b=fn_span(s,'fn gui_input_init')
old=s[a:b]
old=old.replace('volatile_write64(state+288,0); }','volatile_write64(state+288,0); volatile_write64(state+392,0); volatile_write64(state+400,0); volatile_write64(state+408,0); volatile_write64(state+416,0); volatile_write64(state+424,0); volatile_write64(state+432,0); volatile_write64(state+440,0); volatile_write64(state+448,0); volatile_write64(state+456,0); }')
if old==s[a:b]: raise SystemExit('gui_input_init anchor not found')
s=s[:a]+old+s[b:]

# Add xHCI routing row and expand overlay dirty region by one line.
a,b=fn_span(s,'fn v108_input_overlay_draw')
old=s[a:b]
needle='''    v108_text_drep_v119(surface,px+10,py+424,white); v108_draw_small_u64(surface,((px+100)*65536)+(py+424),volatile_read64(state+384),amber); v108_draw_small_u64(surface,((px+160)*65536)+(py+424),volatile_read64(state+376),green); v108_draw_small_u64(surface,((px+220)*65536)+(py+424),volatile_read64(state+296),white); v108_draw_small_u64(surface,((px+280)*65536)+(py+424),volatile_read64(state+128),white);\n    return 1;'''
replacement='''    v108_text_drep_v119(surface,px+10,py+424,white); v108_draw_small_u64(surface,((px+100)*65536)+(py+424),volatile_read64(state+384),amber); v108_draw_small_u64(surface,((px+160)*65536)+(py+424),volatile_read64(state+376),green); v108_draw_small_u64(surface,((px+220)*65536)+(py+424),volatile_read64(state+296),white); v108_draw_small_u64(surface,((px+280)*65536)+(py+424),volatile_read64(state+128),white);\n    v108_text_xrt_v120(surface,px+10,py+442,white); if xhci!=0 { v108_draw_small_u64(surface,((px+112)*65536)+(py+442),volatile_read64(xhci+1408),white); v108_draw_small_u64(surface,((px+184)*65536)+(py+442),volatile_read64(xhci+1384),white); v108_draw_small_u64(surface,((px+256)*65536)+(py+442),volatile_read64(xhci+1416),white); v108_draw_small_u64(surface,((px+328)*65536)+(py+442),volatile_read64(xhci+1400),white); }\n    return 1;'''
if needle not in old: raise SystemExit('overlay tail anchor missing')
old=old.replace(needle,replacement,1); s=s[:a]+old+s[b:]

s=s.replace('(410*65536)+454,16)==0 { return 0; }','(410*65536)+472,16)==0 { return 0; }',1)
s=s.replace('(410*65536)+454,16)==0 { return 0; }','(410*65536)+472,16)==0 { return 0; }',1)

# Emit a machine-readable marker on every expensive full desktop repaint.
a,b=fn_span(s,'fn v108_desktop_interaction_repaint_v118')
rf=s[a:b]
rneedle='unsafe { volatile_write64(state+368,0); volatile_write64(state+384,volatile_read64(state+384)+1); volatile_write64(process+640,0); }'
if rneedle not in rf: raise SystemExit('full repaint counter anchor missing')
rf=rf.replace(rneedle,rneedle+' serial_marker_v108_full_repaint_v120();',1)
s=s[:a]+rf+s[b:]

p.write_text(s)
h=hashlib.sha256(p.read_bytes()).hexdigest(); print(h)
