from pathlib import Path
import hashlib
import sys
p=Path(sys.argv[1]); raw=p.read_bytes(); actual=hashlib.sha256(raw).hexdigest(); expected='7bc6594c05e71d821a07275a7ded816869681fa2d328e64f18dee0ebd0f02ce9'
if actual!=expected: raise SystemExit(f'unexpected r13 source hash {actual}')
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

def text_fn(name,text):
    ops=[]
    for i,c in enumerate(text):
        ops.append(f'if gui_draw_char_scaled(surface,((x+{i*6})*65536)+y,({ord(c)}*65536)+1,color)==0 {{ return 0; }}')
    return f"fn {name}(surface:u64,x:u64,y:u64,color:u64) -> u64 {{ {' '.join(ops)} return 1; }}\n"

def marker_fn(name,text):
    return 'fn '+name+'() -> void { '+' '.join(f'serial_putc({ord(c)});' for c in text+'\\n')+' return; }\n'

# 1) r13 physical result shows r12 typ-3 relative synthesis causes discontinuities on the real Elantech stream.
old='if typ==3 { return ps2_elan4_motion_v112(input_state,a,b); }'
new='if typ==3 { unsafe { volatile_write64(input_state+3608,volatile_read64(input_state+3608)+1); } return 1; }'
assert s.count(old)==1
s=s.replace(old,new,1)

# 2) First-tier hub traversal: preserve parent control context, skip boot-keyboard children, continue siblings, prefer mouse.
hubmark=s.index('fn xhci_hub_find_boot_hid_v113')
s=s[:hubmark]+marker_fn('serial_marker_usb_hub_keyboard_skipped_v114','FRAMES_USB_HUB_KEYBOARD_SKIPPED')+s[hubmark:]
new_hub=r'''fn xhci_hub_find_boot_hid_v113(xhci_state:u64,phys_state:u64) -> u64 {
    let ports=xhci_hub_prepare_parent_v113(xhci_state,phys_state); if ports==0 { return 0; }
    unsafe { volatile_write64(xhci_state+968,0); volatile_write64(xhci_state+976,0); volatile_write64(xhci_state+984,0); volatile_write64(xhci_state+992,0); volatile_write64(xhci_state+1000,0); }
    var p:u64=1;
    while p<=ports {
        xhci_hub_set_feature_v113(xhci_state,8,p); pit_wait(23864);
        var status=xhci_hub_port_status_v113(xhci_state,phys_state,p);
        if status%2!=0 {
            xhci_hub_set_feature_v113(xhci_state,4,p); pit_wait(59660); status=xhci_hub_port_status_v113(xhci_state,phys_state,p);
            if status%2!=0 {
                let speed=xhci_hub_child_speed_v113(status); unsafe { volatile_write64(xhci_state+960,status); volatile_write64(xhci_state+968,volatile_read64(xhci_state+968)+1); }
                // Snapshot the parent hub EP0/control context after this port's hub-class requests.
                let ps136=volatile_read64(xhci_state+136); let ps152=volatile_read64(xhci_state+152); let ps160=volatile_read64(xhci_state+160); let ps168=volatile_read64(xhci_state+168);
                let ps176=volatile_read64(xhci_state+176); let ps184=volatile_read64(xhci_state+184); let ps192=volatile_read64(xhci_state+192); let ps200=volatile_read64(xhci_state+200);
                let ps208=volatile_read64(xhci_state+208); let ps216=volatile_read64(xhci_state+216); let ps224=volatile_read64(xhci_state+224); let ps232=volatile_read64(xhci_state+232);
                let ps240=volatile_read64(xhci_state+240); let ps248=volatile_read64(xhci_state+248); let ps256=volatile_read64(xhci_state+256); let ps264=volatile_read64(xhci_state+264);
                let ps272=volatile_read64(xhci_state+272); let ps280=volatile_read64(xhci_state+280); let ps288=volatile_read64(xhci_state+288); let ps296=volatile_read64(xhci_state+296);
                let ps384=volatile_read64(xhci_state+384); let ps416=volatile_read64(xhci_state+416);
                if xhci_address_hub_child_v113(xhci_state,phys_state,p,speed)!=0 {
                    if xhci_get_device_descriptor8(xhci_state,phys_state)!=0 && xhci_finalize_address_and_descriptor(xhci_state,phys_state)!=0 {
                        if xhci_discover_boot_hid(xhci_state,phys_state)!=0 {
                            let proto=volatile_read64(xhci_state+336);
                            if proto==2 {
                                unsafe { volatile_write64(xhci_state+992,volatile_read64(xhci_state+992)+1); }
                                if xhci_configure_boot_hid(xhci_state,phys_state)!=0 { unsafe { volatile_write64(xhci_state+1000,volatile_read64(xhci_state+1000)+1); } serial_marker_usb_hub_child_hid_ok_v113(); return 1; }
                            } else { if proto==1 { unsafe { volatile_write64(xhci_state+976,volatile_read64(xhci_state+976)+1); } if volatile_read64(xhci_state+976)==1 { serial_marker_usb_hub_keyboard_skipped_v114(); } } }
                        } else { unsafe { volatile_write64(xhci_state+984,volatile_read64(xhci_state+984)+1); } }
                    } else { unsafe { volatile_write64(xhci_state+984,volatile_read64(xhci_state+984)+1); } }
                } else { unsafe { volatile_write64(xhci_state+984,volatile_read64(xhci_state+984)+1); } }
                // Child was not the pointer we need. Restore the hub parent and keep scanning siblings.
                unsafe {
                    volatile_write64(xhci_state+136,ps136); volatile_write64(xhci_state+152,ps152); volatile_write64(xhci_state+160,ps160); volatile_write64(xhci_state+168,ps168);
                    volatile_write64(xhci_state+176,ps176); volatile_write64(xhci_state+184,ps184); volatile_write64(xhci_state+192,ps192); volatile_write64(xhci_state+200,ps200);
                    volatile_write64(xhci_state+208,ps208); volatile_write64(xhci_state+216,ps216); volatile_write64(xhci_state+224,ps224); volatile_write64(xhci_state+232,ps232);
                    volatile_write64(xhci_state+240,ps240); volatile_write64(xhci_state+248,ps248); volatile_write64(xhci_state+256,ps256); volatile_write64(xhci_state+264,ps264);
                    volatile_write64(xhci_state+272,ps272); volatile_write64(xhci_state+280,ps280); volatile_write64(xhci_state+288,ps288); volatile_write64(xhci_state+296,ps296);
                    volatile_write64(xhci_state+384,ps384); volatile_write64(xhci_state+416,ps416);
                }
            }
        }
        p=p+1;
    }
    return 0;
}'''
repl_fn('fn xhci_hub_find_boot_hid_v113',new_hub)

# 3) Right-click test marker + small in-panel context menu. Reuse old clear-count slot 3696 for right-click count.
insert=s.index('fn v108_input_test_draw')
s=s[:insert]+marker_fn('serial_marker_v108_right_click_ok','FRAMES_V108_RIGHT_CLICK_OK')+text_fn('v108_text_rightok','RIGHT CLICK OK')+s[insert:]

# Add fixed context popover when a right-click has been seen.
old_draw='''    v108_text_focus(surface,x+372,y+140,white); v108_draw_small_u64(surface,((x+430)*65536)+(y+140),volatile_read64(input_state+3672),green);\n    v108_text_clicks(surface,x+372,y+160,white); v108_draw_small_u64(surface,((x+436)*65536)+(y+160),volatile_read64(input_state+3688),amber); return 1;'''
new_draw='''    v108_text_focus(surface,x+372,y+140,white); v108_draw_small_u64(surface,((x+430)*65536)+(y+140),volatile_read64(input_state+3672),green);\n    v108_text_clicks(surface,x+372,y+160,white); v108_draw_small_u64(surface,((x+436)*65536)+(y+160),volatile_read64(input_state+3688),amber);\n    if volatile_read64(input_state+3696)!=0 { display_fill_rect(surface,((x+360)*65536)+(y+118),(210*65536)+62,inner); display_fill_rect(surface,((x+360)*65536)+(y+118),(210*65536)+2,edge); v108_text_rightok(surface,x+382,y+134,white); v108_draw_small_u64(surface,((x+470)*65536)+(y+154),volatile_read64(input_state+3696),green); } return 1;'''
assert s.count(old_draw)==1
s=s.replace(old_draw,new_draw,1)

old_click='''fn v108_input_test_click_v112(state:u64,input_state:u64,buttons:u64,old_buttons:u64) -> u64 {\n    if state==0 || input_state==0 { return 0; } if buttons%2==0 || old_buttons%2!=0 { return 0; } let x=volatile_read64(state+8); let y=volatile_read64(state+16); let py=v108_test_y(state);'''
new_click='''fn v108_input_test_click_v112(state:u64,input_state:u64,buttons:u64,old_buttons:u64) -> u64 {\n    if state==0 || input_state==0 { return 0; }\n    let right=(buttons/2)%2; let old_right=(old_buttons/2)%2; if right!=0 && old_right==0 { unsafe { volatile_write64(input_state+3696,volatile_read64(input_state+3696)+1); volatile_write64(input_state+3672,0); } if volatile_read64(input_state+3696)==1 { serial_marker_v108_right_click_ok(); } return 1; }\n    if buttons%2==0 || old_buttons%2!=0 { return 0; } let x=volatile_read64(state+8); let y=volatile_read64(state+16); let py=v108_test_y(state);'''
assert s.count(old_click)==1
s=s.replace(old_click,new_click,1)
# Clear no longer increments 3696; it only clears text/focus.
s=s.replace('volatile_write64(input_state+3680,0); volatile_write64(input_state+3696,volatile_read64(input_state+3696)+1); volatile_write64(input_state+3672,1);','volatile_write64(input_state+3680,0); volatile_write64(input_state+3672,1);',1)

# 4) Persistent hub telemetry row so physical photos show whether hub traversal happened and how far it got.
telemetry_insert=s.index('fn v108_input_overlay_draw')
s=s[:telemetry_insert]+text_fn('v108_text_hub','HUB F N A K M O')+s[telemetry_insert:]
s=s.replace('(410*65536)+328,bg','(410*65536)+346,bg',1)
s=s.replace('(px+326),(410*65536)+2,edge','(px+344),(410*65536)+2,edge',1)
old_tail='''    v108_text_test(surface,px+10,py+298,white); v108_draw_small_u64(surface,((px+82)*65536)+(py+298),volatile_read64(input_state+3672),green); v108_draw_small_u64(surface,((px+142)*65536)+(py+298),volatile_read64(input_state+3688),green); v108_draw_small_u64(surface,((px+202)*65536)+(py+298),volatile_read64(input_state+3680),white);\n    return 1;'''
new_tail='''    v108_text_test(surface,px+10,py+298,white); v108_draw_small_u64(surface,((px+82)*65536)+(py+298),volatile_read64(input_state+3672),green); v108_draw_small_u64(surface,((px+142)*65536)+(py+298),volatile_read64(input_state+3688),green); v108_draw_small_u64(surface,((px+202)*65536)+(py+298),volatile_read64(input_state+3680),white);\n    v108_text_hub(surface,px+10,py+316,white); if xhci!=0 { v108_draw_small_u64(surface,((px+82)*65536)+(py+316),volatile_read64(xhci+904),green); v108_draw_small_u64(surface,((px+130)*65536)+(py+316),volatile_read64(xhci+912),white); v108_draw_small_u64(surface,((px+178)*65536)+(py+316),volatile_read64(xhci+968),amber); v108_draw_small_u64(surface,((px+226)*65536)+(py+316),volatile_read64(xhci+976),amber); v108_draw_small_u64(surface,((px+274)*65536)+(py+316),volatile_read64(xhci+992),green); v108_draw_small_u64(surface,((px+322)*65536)+(py+316),volatile_read64(xhci+1000),green); }\n    return 1;'''
assert s.count(old_tail)==1
s=s.replace(old_tail,new_tail,1)

p.write_text(s)
out=hashlib.sha256(p.read_bytes()).hexdigest(); print(out)
if out!='2401b3a460430da6b008716e65f7be10dfb8e289da48b12045e1e1b920ed6caf': raise SystemExit(f'unexpected r14 source hash {out}')
