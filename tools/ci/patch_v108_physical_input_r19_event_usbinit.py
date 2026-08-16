from pathlib import Path
import hashlib,sys
p=Path(sys.argv[1]); raw=p.read_bytes(); actual=hashlib.sha256(raw).hexdigest(); expected='dd0386720bba6dce4c1fd0576e995dd6a2932638633147914589b342cc3dfe22'
if actual!=expected: raise SystemExit(f'unexpected r18 source hash {actual}')
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

insert=s.index('fn xhci_legacy_handoff_v118')
extra=(marker_fn('serial_marker_v108_drag_proxy_ok_v119','FRAMES_V108_DRAG_PROXY_OK')+
       marker_fn('serial_marker_v108_right_gesture_ok_v119','FRAMES_V108_RIGHT_GESTURE_OK')+
       marker_fn('serial_marker_v108_xhci_window_ok_v119','FRAMES_V108_XHCI_WINDOW_OK')+
       '''fn xhci_map_register_window_v119(phys_state:u64,pml4:u64,base:u64,pages:u64) -> u64 {
    if phys_state==0 || pml4==0 || base==0 || pages==0 { return 0; }
    let start=base-(base%4096); var i:u64=0; while i<pages { if ensure_identity_mmio_page(phys_state,pml4,start+(i*4096))==0 { return 0; } i=i+1; }
    return 1;
}\n'''+
       '''fn xhci_count_connected_ports_v119(xhci_state:u64) -> u64 {
    if xhci_state==0 || volatile_read64(xhci_state+56)!=1 { return 0; }
    let base=volatile_read64(xhci_state); let op=volatile_read64(xhci_state+8); var ports=(volatile_read32(base+4)/16777216)%256; if ports>32 { ports=32; }
    var p:u64=0; var connected:u64=0; while p<ports { if volatile_read32(op+1024+(p*16))%2!=0 { connected=connected+1; } p=p+1; } return connected;
}\n''')
s=s[:insert]+extra+s[insert:]

new_xhci=r'''fn xhci_controller_init(hardware_state:u64, phys_state:u64, xhci_state:u64, pml4:u64) -> u64 {
    if hardware_state==0 || phys_state==0 || xhci_state==0 || volatile_read64(hardware_state+24)==0 { return 0; }
    let bdf=volatile_read64(hardware_state+80); unsafe { volatile_write64(xhci_state+1264,1); volatile_write64(xhci_state+1272,0); volatile_write64(xhci_state+1280,bdf); volatile_write64(xhci_state+1288,volatile_read64(hardware_state+144)); }
    let bus=bdf/65536; let dev=(bdf/256)%256; let fun=bdf%256; unsafe { volatile_write64(xhci_state+1344,pci_cfg_read32(bus,dev,fun,208)); volatile_write64(xhci_state+1352,pci_cfg_read32(bus,dev,fun,212)); volatile_write64(xhci_state+1360,pci_cfg_read32(bus,dev,fun,216)); volatile_write64(xhci_state+1368,pci_cfg_read32(bus,dev,fun,220)); }
    if pci_enable_mmio_busmaster(bdf)==0 { unsafe { volatile_write64(xhci_state+1272,1); } return 0; }
    unsafe { volatile_write64(xhci_state+1264,2); }
    let base=volatile_read64(hardware_state+192); if base==0 { unsafe { volatile_write64(xhci_state+1272,2); } return 0; }
    if xhci_map_register_window_v119(phys_state,pml4,base,8)==0 { unsafe { volatile_write64(xhci_state+1272,3); } return 0; } serial_marker_v108_xhci_window_ok_v119();
    let caplen=volatile_read8(base); if caplen<32 || caplen>255 { unsafe { volatile_write64(xhci_state+1272,4); } return 0; } let op=base+caplen; unsafe { volatile_write64(xhci_state+1264,3); }
    let legacy=xhci_legacy_handoff_v118(base,phys_state,pml4); unsafe { volatile_write64(xhci_state+1296,legacy); } if legacy==0 || legacy==3 { unsafe { volatile_write64(xhci_state+1272,5); } return 0; }
    unsafe { volatile_write64(xhci_state+1264,4); }
    var cmd=volatile_read32(op+0); cmd=clear_flag(cmd,1); unsafe { volatile_write32(op+0,cmd); } if xhci_wait_halted(op,1)==0 { unsafe { volatile_write64(xhci_state+1272,6); } return 0; }
    unsafe { volatile_write64(xhci_state+1264,5); }
    cmd=volatile_read32(op+0); cmd=set_flag(cmd,2); unsafe { volatile_write32(op+0,cmd); }
    var spins:u64=0; while (volatile_read32(op+0)/2)%2 != 0 && spins<4000000 { cpu_pause(); spins=spins+1; } if spins>=4000000 { unsafe { volatile_write64(xhci_state+1272,7); } return 0; }
    spins=0; while (volatile_read32(op+4)/2048)%2 != 0 && spins<4000000 { cpu_pause(); spins=spins+1; } if spins>=4000000 { unsafe { volatile_write64(xhci_state+1272,8); } return 0; }
    unsafe { volatile_write64(xhci_state+1264,6); }
    let pages=volatile_read32(op+8); if pages%2==0 { unsafe { volatile_write64(xhci_state+1272,9); } return 0; }
    let command_ring=alloc_dma_page(phys_state,3); let event_ring=alloc_dma_page(phys_state,3); let erst=alloc_dma_page(phys_state,3); let dcbaa=alloc_dma_page(phys_state,3); if command_ring==0 || event_ring==0 || erst==0 || dcbaa==0 { unsafe { volatile_write64(xhci_state+1272,10); } return 0; }
    zero_page(command_ring); zero_page(event_ring); zero_page(erst); zero_page(dcbaa);
    let hcs2=volatile_read32(base+8); let scratch_lo=(hcs2/134217728)%32; let scratch_hi=(hcs2/2097152)%32; let scratch_count=scratch_lo+(scratch_hi*32); var scratch_array:u64=0; var scratch_ready:u64=0; unsafe { volatile_write64(xhci_state+1304,scratch_count); }
    if scratch_count>0 {
        if scratch_count>48 { unsafe { volatile_write64(xhci_state+1272,11); } return 0; }
        scratch_array=alloc_dma_page(phys_state,3); if scratch_array==0 { unsafe { volatile_write64(xhci_state+1272,12); } return 0; } zero_page(scratch_array);
        var si:u64=0; while si<scratch_count { let sp=alloc_dma_page(phys_state,3); if sp==0 { unsafe { volatile_write64(xhci_state+1272,13); } return 0; } zero_page(sp); unsafe { volatile_write64(scratch_array+(si*8),sp); } si=si+1; }
        unsafe { volatile_write64(dcbaa,scratch_array); } scratch_ready=1;
    }
    unsafe { volatile_write64(xhci_state+1312,scratch_ready); volatile_write64(xhci_state+1264,7); }
    unsafe { volatile_write64(command_ring+4080,command_ring); volatile_write64(command_ring+4088,6147); }
    unsafe { volatile_write64(erst+0,event_ring); volatile_write32(erst+8,256); volatile_write32(erst+12,0); }
    unsafe { volatile_write32(op+24,(command_ring%4294967296)+1); volatile_write32(op+28,command_ring/4294967296); volatile_write32(op+48,dcbaa%4294967296); volatile_write32(op+52,dcbaa/4294967296); }
    let hcs1=volatile_read32(base+4); var maxslots=hcs1%256; if maxslots>32 { maxslots=32; } if maxslots==0 { unsafe { volatile_write64(xhci_state+1272,14); } return 0; } unsafe { volatile_write32(op+56,maxslots); }
    cmd=volatile_read32(op+0); cmd=set_flag(cmd,1); unsafe { volatile_write32(op+0,cmd); } if xhci_wait_halted(op,0)==0 { unsafe { volatile_write64(xhci_state+1272,15); } return 0; }
    unsafe { volatile_write64(xhci_state+1264,8); }
    let rtsoff_raw=volatile_read32(base+24); let dboff_raw=volatile_read32(base+20); let runtime=base+(rtsoff_raw-(rtsoff_raw%32)); let doorbells=base+(dboff_raw-(dboff_raw%4));
    if pml4==0 || ensure_identity_mmio_page(phys_state,pml4,runtime)==0 || ensure_identity_mmio_page(phys_state,pml4,doorbells)==0 { unsafe { volatile_write64(xhci_state+1272,16); } return 0; }
    let intr=runtime+32; unsafe { volatile_write32(intr+8,1); volatile_write32(intr+16,erst%4294967296); volatile_write32(intr+20,erst/4294967296); volatile_write32(intr+24,event_ring%4294967296); volatile_write32(intr+28,event_ring/4294967296); }
    unsafe { volatile_write64(xhci_state+0,base); volatile_write64(xhci_state+8,op); volatile_write64(xhci_state+16,command_ring); volatile_write64(xhci_state+24,event_ring); volatile_write64(xhci_state+32,erst); volatile_write64(xhci_state+40,dcbaa); volatile_write64(xhci_state+48,maxslots); volatile_write64(xhci_state+56,1); volatile_write64(xhci_state+64,0); volatile_write64(xhci_state+72,1); volatile_write64(xhci_state+80,runtime); volatile_write64(xhci_state+88,doorbells); volatile_write64(xhci_state+96,0); volatile_write64(xhci_state+104,1); volatile_write64(xhci_state+1264,9); volatile_write64(xhci_state+1272,0); }
    let connected=xhci_count_connected_ports_v119(xhci_state); unsafe { volatile_write64(xhci_state+1320,connected); }
    serial_marker_xhci_ring_ready(); return 1;
}'''
repl_fn('fn xhci_controller_init',new_xhci)

s=s.replace('volatile_write64(xhci_state+1240,3)','volatile_write64(xhci_state+1328,3)')
s=s.replace('volatile_write64(xhci_state+1240,4)','volatile_write64(xhci_state+1328,4)')
s=s.replace('volatile_write64(xhci_state+1240,5)','volatile_write64(xhci_state+1328,5)')
s=s.replace('volatile_write64(xhci_state+1240,6)','volatile_write64(xhci_state+1328,6)')
s=s.replace('volatile_write64(xhci_state+1240,0)','volatile_write64(xhci_state+1328,0)')

new_buttons=r'''fn ps2_elan4_buttons_v111(input_state:u64,a:u64) -> u64 {
    if input_state==0 { return 0; }
    let raw=(a/65536)%4; let left=raw%2; let raw_right=(raw/2)%2; var candidate=volatile_read64(input_state+3760); var seen=volatile_read64(input_state+3768);
    if raw_right==candidate { if seen<3 { seen=seen+1; } } else { candidate=raw_right; seen=1; }
    unsafe { volatile_write64(input_state+3760,candidate); volatile_write64(input_state+3768,seen); }
    let old=volatile_read64(input_state+3560); var stable_right=(old/2)%2; if seen>=2 { stable_right=raw_right; } let buttons=left+(stable_right*2);
    if buttons!=old {
        unsafe {
            if buttons!=0 { volatile_write64(input_state+4088,1); }
            volatile_write64(input_state+3560,buttons);
            volatile_write64(input_state+3568,volatile_read64(input_state+3568)+1);
            if buttons%2!=0 && old%2==0 { volatile_write64(input_state+3576,volatile_read64(input_state+3576)+1); }
        }
        input_push(input_state,4,0,buttons);
    }
    return buttons;
}'''
repl_fn('fn ps2_elan4_buttons_v111',new_buttons)

old='''    if volatile_read64(state+128)!=0 { let before=volatile_read64(state+240); let now=v108_context_hit_v118(state,x,y); if now!=before { unsafe { volatile_write64(state+240,now); } if now!=0 && volatile_read64(state+288)==0 { unsafe { volatile_write64(state+288,1); } serial_marker_v108_context_hover_ok(); } } }\n    unsafe { volatile_write64(state+8,x); volatile_write64(state+16,y); } return 1;'''
new='''    if volatile_read64(state+296)!=0 { let px=volatile_read64(state+304); let py=volatile_read64(state+312); var dx:u64=0; var dy:u64=0; if x>px { dx=x-px; } else { dx=px-x; } if y>py { dy=y-py; } else { dy=py-y; } if dx>6 || dy>6 { unsafe { volatile_write64(state+296,0); volatile_write64(state+320,volatile_read64(state+320)+1); } } }\n    if volatile_read64(state+128)!=0 { let before=volatile_read64(state+240); let now=v108_context_hit_v118(state,x,y); if now!=before { unsafe { volatile_write64(state+240,now); } if now!=0 && volatile_read64(state+288)==0 { unsafe { volatile_write64(state+288,1); } serial_marker_v108_context_hover_ok(); } } }\n    unsafe { volatile_write64(state+8,x); volatile_write64(state+16,y); } return 1;'''
assert s.count(old)==1
s=s.replace(old,new,1)

new_gui_buttons=r'''fn gui_input_buttons(state:u64,wm:u64,buttons:u64,surface:u64) -> u64 {
    if state==0 || wm==0 || surface==0 || volatile_read64(state)!=1 { return 0; }
    let old=volatile_read64(state+96); unsafe { volatile_write64(state+96,buttons); } let x=volatile_read64(state+8); let y=volatile_read64(state+16);
    let right=(buttons/2)%2; let old_right=(old/2)%2;
    if right!=0 && old_right==0 { unsafe { volatile_write64(state+296,1); volatile_write64(state+304,x); volatile_write64(state+312,y); } return 1; }
    if right==0 && old_right!=0 {
        if volatile_read64(state+296)!=0 {
            let ax=volatile_read64(state+304); let ay=volatile_read64(state+312); let opens=volatile_read64(state+152)+1;
            unsafe { volatile_write64(state+296,0); volatile_write64(state+128,1); volatile_write64(state+136,ax); volatile_write64(state+144,ay); volatile_write64(state+152,opens); volatile_write64(state+240,0); volatile_write64(state+288,0); volatile_write64(state+328,volatile_read64(state+328)+1); volatile_write64(state+336,x); volatile_write64(state+344,y); }
            if v108_context_geometry_v118(surface,state)==0 { return 0; } serial_marker_v108_right_gesture_ok_v119(); serial_marker_v108_desktop_context_ok(); if opens>=2 { serial_marker_v108_context_repeat_ok(); } return 1;
        }
        return 1;
    }
    if buttons%2!=0 && old%2==0 {
        unsafe { volatile_write64(state+296,0); }
        if volatile_read64(state+128)!=0 { let hit=v108_context_hit_v118(state,x,y); unsafe { volatile_write64(state+248,volatile_read64(state+248)+1); volatile_write64(state+256,hit); volatile_write64(state+128,0); volatile_write64(state+240,0); volatile_write64(state+264,volatile_read64(state+264)+1); } if hit!=0 { serial_marker_v108_context_select_ok(); } else { serial_marker_v108_context_outside_ok(); } serial_marker_v108_context_dismiss_ok(); return 1; }
        let wx=volatile_read64(state+160); let wy=volatile_read64(state+168); if x>=wx && x<wx+270 && y>=wy && y<wy+36 { unsafe { volatile_write64(state+176,1); volatile_write64(state+184,x-wx); volatile_write64(state+192,y-wy); volatile_write64(state+24,0); volatile_write64(state+32,0); } return 1; }
        let id=gui_input_hit_test(state,wm,x,y); if id!=0 { if gui_input_focus(state,wm,id)==0 { return 0; } let rec=wm_record(wm,id); let rx=volatile_read64(rec+8); let ry=volatile_read64(rec+16); let rw=volatile_read64(rec+24); let rh=volatile_read64(rec+32); var mode:u64=0; if y>=ry && y<ry+36 { mode=1; } if x+18>=rx+rw && y+18>=ry+rh { mode=2; } unsafe { volatile_write64(state+24,id); volatile_write64(state+32,mode); } }
    }
    if buttons%2==0 && old%2!=0 { unsafe { volatile_write64(state+24,0); volatile_write64(state+32,0); volatile_write64(state+176,0); } }
    return 1;
}'''
repl_fn('fn gui_input_buttons',new_gui_buttons)

insert=s.index('fn v108_desktop_interaction_repaint_v118')
proxy=r'''fn v108_drag_outline_toggle_v119(surface:u64,x:u64,y:u64) -> u64 {
    if surface==0 || volatile_read64(surface)!=1 { return 0; } let sw=volatile_read64(surface+16); let sh=volatile_read64(surface+24); let stride=volatile_read64(surface+32); let base=volatile_read64(surface+8); if base==0 || x>=sw || y>=sh { return 0; }
    var w:u64=270; var h:u64=150; if x+w>sw { w=sw-x; } if y+h>sh { h=sh-y; } if w<2 || h<2 { return 0; }
    var i:u64=0; while i<w { let p1=base+(((y*stride)+(x+i))*4); let p2=base+((((y+h-1)*stride)+(x+i))*4); unsafe { volatile_write32(p1,4294967295-volatile_read32(p1)); volatile_write32(p2,4294967295-volatile_read32(p2)); } i=i+1; }
    i=1; while i+1<h { let p1=base+((((y+i)*stride)+x)*4); let p2=base+((((y+i)*stride)+(x+w-1))*4); unsafe { volatile_write32(p1,4294967295-volatile_read32(p1)); volatile_write32(p2,4294967295-volatile_read32(p2)); } i=i+1; }
    return 1;
}
fn v108_drag_proxy_present_v119(process:u64,state:u64) -> u64 {
    if process==0 || state==0 { return 0; } let surface=volatile_read64(process+616); let dirty=volatile_read64(process+624); let timing=volatile_read64(process+664); let present=volatile_read64(process+672); let cursor=volatile_read64(process+640); if surface==0 || dirty==0 || timing==0 || present==0 || cursor==0 { return 0; }
    let active=volatile_read64(state+368); let ox=volatile_read64(state+352); let oy=volatile_read64(state+360); let nx=volatile_read64(state+160); let ny=volatile_read64(state+168); let cx=volatile_read64(state+8); let cy=volatile_read64(state+16);
    v108_cursor_restore(cursor,surface); if active!=0 { v108_drag_outline_toggle_v119(surface,ox,oy); } if v108_drag_outline_toggle_v119(surface,nx,ny)==0 { return 0; }
    unsafe { volatile_write64(state+352,nx); volatile_write64(state+360,ny); volatile_write64(state+368,1); }
    v108_cursor_capture(cursor,surface,cx,cy); desktop_draw_cursor(surface,cx,cy); if active!=0 { dirty_add(dirty,(ox*65536)+oy,(270*65536)+150,16); present_enqueue(present,(ox*65536)+oy,(270*65536)+150,16); } dirty_add(dirty,(nx*65536)+ny,(270*65536)+150,16); present_enqueue(present,(nx*65536)+ny,(270*65536)+150,16); dirty_add(dirty,(cx*65536)+cy,(8*65536)+16,16); present_enqueue(present,(cx*65536)+cy,(8*65536)+16,16); if present_flush(present,surface,timing)==0 { return 0; }
    if volatile_read64(state+376)==0 { unsafe { volatile_write64(state+376,1); } serial_marker_v108_drag_proxy_ok_v119(); } return 1;
}
'''
s=s[:insert]+proxy+s[insert:]

old='''    if process==0 || state==0 || input_state==0 { return 0; } let cursor=volatile_read64(process+640); if cursor==0 { return 0; } let surface=volatile_read64(process+616); let dirty=volatile_read64(process+624); let timing=volatile_read64(process+664); let present=volatile_read64(process+672); if surface==0 || dirty==0 || timing==0 || present==0 { return 0; }\n    unsafe { volatile_write64(process+640,0); } if appearance_render(process)==0 { unsafe { volatile_write64(process+640,cursor); } return 0; } unsafe { volatile_write64(process+640,cursor); }'''
new='''    if process==0 || state==0 || input_state==0 { return 0; } let cursor=volatile_read64(process+640); if cursor==0 { return 0; } let surface=volatile_read64(process+616); let dirty=volatile_read64(process+624); let timing=volatile_read64(process+664); let present=volatile_read64(process+672); if surface==0 || dirty==0 || timing==0 || present==0 { return 0; }\n    unsafe { volatile_write64(state+368,0); volatile_write64(state+384,volatile_read64(state+384)+1); volatile_write64(process+640,0); } if appearance_render(process)==0 { unsafe { volatile_write64(process+640,cursor); } return 0; } unsafe { volatile_write64(process+640,cursor); }'''
assert s.count(old)==1
s=s.replace(old,new,1)

old='''        var telemetry_redraw:u64=0; var test_redraw:u64=0; var pointer_changed:u64=0; var desktop_redraw:u64=0; var menu_redraw:u64=0;'''
new='''        var telemetry_redraw:u64=0; var test_redraw:u64=0; var pointer_changed:u64=0; var desktop_redraw:u64=0; var menu_redraw:u64=0; var drag_proxy_redraw:u64=0;'''
assert s.count(old)==1; s=s.replace(old,new,1)
old='''                    let menu_before=volatile_read64(state+240); let context_before=volatile_read64(state+128); if gui_input_dispatch(state,wm,event,surface)!=0 {\n                        if kind==4 {\n                            let buttons=value; let old_buttons=volatile_read64(input_state+3584); let ctx_before=volatile_read64(state+128); let drag_before=volatile_read64(state+176); if buttons!=old_buttons { unsafe { volatile_write64(input_state+3584,buttons); volatile_write64(input_state+3592,volatile_read64(input_state+3592)+1); if buttons%2!=0 && old_buttons%2==0 { volatile_write64(input_state+3600,volatile_read64(input_state+3600)+1); } } if buttons%2!=0 && old_buttons%2==0 && volatile_read64(input_state+3600)==1 { serial_marker_v108_gui_click_ok(); } }\n                            if v108_input_test_click_v112(state,input_state,buttons,old_buttons)!=0 { test_redraw=1; }\n                            desktop_shell_click(process,state,buttons); appearance_handle_click(process,state,buttons); telemetry_redraw=1; if ctx_before!=volatile_read64(state+128) || drag_before!=volatile_read64(state+176) || ((buttons/2)%2!=0 && (old_buttons/2)%2==0) { desktop_redraw=1; }\n                        }\n                        if kind==5 || kind==6 { pointer_changed=1; if volatile_read64(state+176)!=0 { desktop_redraw=1; } if volatile_read64(state+128)!=0 && volatile_read64(state+240)!=menu_before { menu_redraw=1; } }\n                    }'''
new='''                    let menu_before=volatile_read64(state+240); let context_before=volatile_read64(state+128); let drag_before=volatile_read64(state+176); if gui_input_dispatch(state,wm,event,surface)!=0 {\n                        if kind==4 {\n                            let buttons=value; let old_buttons=volatile_read64(input_state+3584); if buttons!=old_buttons { unsafe { volatile_write64(input_state+3584,buttons); volatile_write64(input_state+3592,volatile_read64(input_state+3592)+1); if buttons%2!=0 && old_buttons%2==0 { volatile_write64(input_state+3600,volatile_read64(input_state+3600)+1); } } if buttons%2!=0 && old_buttons%2==0 && volatile_read64(input_state+3600)==1 { serial_marker_v108_gui_click_ok(); } }\n                            if v108_input_test_click_v112(state,input_state,buttons,old_buttons)!=0 { test_redraw=1; }\n                            desktop_shell_click(process,state,buttons); appearance_handle_click(process,state,buttons); telemetry_redraw=1; let context_after=volatile_read64(state+128); let drag_after=volatile_read64(state+176); if context_before!=context_after || (drag_before!=0 && drag_after==0) { desktop_redraw=1; }\n                        }\n                        if kind==5 || kind==6 { pointer_changed=1; if volatile_read64(state+176)!=0 { drag_proxy_redraw=1; } if volatile_read64(state+128)!=0 && volatile_read64(state+240)!=menu_before { menu_redraw=1; } }\n                    }'''
assert s.count(old)==1
s=s.replace(old,new,1)
old='''        if desktop_redraw!=0 { if v108_desktop_interaction_repaint_v118(process,state,input_state,xhci)==0 { return 0; } pointer_changed=0; test_redraw=0; telemetry_redraw=0; menu_redraw=0; }\n        if menu_redraw!=0 && desktop_redraw==0 { if v108_context_present_v118(process,state,cursor)==0 { return 0; } pointer_changed=0; }'''
new='''        if desktop_redraw!=0 { if v108_desktop_interaction_repaint_v118(process,state,input_state,xhci)==0 { return 0; } pointer_changed=0; test_redraw=0; telemetry_redraw=0; menu_redraw=0; drag_proxy_redraw=0; }\n        if drag_proxy_redraw!=0 && desktop_redraw==0 { if v108_drag_proxy_present_v119(process,state)==0 { return 0; } pointer_changed=0; }\n        if menu_redraw!=0 && desktop_redraw==0 && drag_proxy_redraw==0 { if v108_context_present_v118(process,state,cursor)==0 { return 0; } pointer_changed=0; }'''
assert s.count(old)==1
s=s.replace(old,new,1)

tele=s.index('fn v108_input_overlay_draw')
s=s[:tele]+text_fn('v108_text_xini_v119','XINI S F P L C E')+text_fn('v108_text_xpci_v119','XPCI B I R0 R1')+text_fn('v108_text_drep_v119','DREP F P R M')+s[tele:]
old='''    v108_text_xhc(surface,px+10,py+370,white); if xhci!=0 { v108_draw_small_u64(surface,((px+100)*65536)+(py+370),volatile_read64(xhci+1232),amber); v108_draw_small_u64(surface,((px+148)*65536)+(py+370),volatile_read64(xhci+1216),white); v108_draw_small_u64(surface,((px+196)*65536)+(py+370),volatile_read64(xhci+1224),green); v108_draw_small_u64(surface,((px+244)*65536)+(py+370),volatile_read64(xhci+1240),red); v108_draw_small_u64(surface,((px+292)*65536)+(py+370),volatile_read64(xhci+488),amber); v108_draw_small_u64(surface,((px+340)*65536)+(py+370),volatile_read64(xhci+504),amber); }\n    return 1;'''
new='''    v108_text_xhc(surface,px+10,py+370,white); if xhci!=0 { v108_draw_small_u64(surface,((px+100)*65536)+(py+370),volatile_read64(xhci+1232),amber); v108_draw_small_u64(surface,((px+148)*65536)+(py+370),volatile_read64(xhci+1216),white); v108_draw_small_u64(surface,((px+196)*65536)+(py+370),volatile_read64(xhci+1224),green); v108_draw_small_u64(surface,((px+244)*65536)+(py+370),volatile_read64(xhci+1328),red); v108_draw_small_u64(surface,((px+292)*65536)+(py+370),volatile_read64(xhci+488),amber); v108_draw_small_u64(surface,((px+340)*65536)+(py+370),volatile_read64(xhci+504),amber); }\n    v108_text_xini_v119(surface,px+10,py+388,white); if xhci!=0 { v108_draw_small_u64(surface,((px+100)*65536)+(py+388),volatile_read64(xhci+1264),green); v108_draw_small_u64(surface,((px+148)*65536)+(py+388),volatile_read64(xhci+1272),red); v108_draw_small_u64(surface,((px+196)*65536)+(py+388),volatile_read64(xhci+1320),amber); v108_draw_small_u64(surface,((px+244)*65536)+(py+388),volatile_read64(xhci+1296),white); v108_draw_small_u64(surface,((px+292)*65536)+(py+388),volatile_read64(xhci+1304),white); v108_draw_small_u64(surface,((px+340)*65536)+(py+388),volatile_read64(xhci+1328),red); }\n    v108_text_xpci_v119(surface,px+10,py+406,white); if xhci!=0 { v108_draw_small_u64(surface,((px+100)*65536)+(py+406),volatile_read64(xhci+1280),white); v108_draw_small_u64(surface,((px+178)*65536)+(py+406),volatile_read64(xhci+1288),amber); v108_draw_small_u64(surface,((px+256)*65536)+(py+406),volatile_read64(xhci+1344),white); v108_draw_small_u64(surface,((px+334)*65536)+(py+406),volatile_read64(xhci+1352),white); }\n    v108_text_drep_v119(surface,px+10,py+424,white); v108_draw_small_u64(surface,((px+100)*65536)+(py+424),volatile_read64(state+384),amber); v108_draw_small_u64(surface,((px+160)*65536)+(py+424),volatile_read64(state+376),green); v108_draw_small_u64(surface,((px+220)*65536)+(py+424),volatile_read64(state+296),white); v108_draw_small_u64(surface,((px+280)*65536)+(py+424),volatile_read64(state+128),white);\n    return 1;'''
assert s.count(old)==1
s=s.replace(old,new,1)
s=s.replace('(410*65536)+400,bg','(410*65536)+454,bg',1)
s=s.replace('(410*65536)+400,16','(410*65536)+454,16')

p.write_text(s)
out=hashlib.sha256(p.read_bytes()).hexdigest(); print(out)
if out!='c78deb76e51b1e2aae2412eb020a82cf2aeca1206254e1b1a7041a60eadec557': raise SystemExit(f'unexpected r19 source hash {out}')
