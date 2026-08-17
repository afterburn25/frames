#!/usr/bin/env python3
from pathlib import Path
import sys, hashlib, subprocess

if len(sys.argv)!=2:
    raise SystemExit('usage: patch_v108_physical_input_r23_dragright_xhci_ro.py <kernel/main.nx>')
p=Path(sys.argv[1])
# r23 is a corrective delta over the exact r22 transform.  Applying r22 first
# preserves the certified no-full-repaint/live-drag/focus architecture while
# keeping r22 itself immutable as a failed physical diagnostic revision.
r22=Path(__file__).with_name('patch_v108_physical_input_r22_livefocus_ehci.py')
subprocess.run([sys.executable,str(r22),str(p)],check=True,stdout=subprocess.DEVNULL)
s=p.read_text()

def replace_once(old,new,label):
    global s
    n=s.count(old)
    if n!=1:
        raise SystemExit(f'{label}: expected 1 anchor, got {n}')
    s=s.replace(old,new,1)

def fn_text(name):
    start=s.index('fn '+name)
    i=s.index('{',start); depth=0
    for j in range(i,len(s)):
        if s[j]=='{': depth+=1
        elif s[j]=='}':
            depth-=1
            if depth==0: return s[start:j+1]
    raise SystemExit('unterminated '+name)

def text_fn(name,text):
    parts=[]
    for i,ch in enumerate(text):
        parts.append(f'if gui_draw_char_scaled(surface,((x+{i*6})*65536)+y,({ord(ch)}*65536)+1,color)==0 {{ return 0; }}')
    return f"fn {name}(surface:u64,x:u64,y:u64,color:u64) -> u64 {{ "+' '.join(parts)+" return 1; }\n"

# Physical r22 evidence: ordinary Elantech motion produced many transient right
# edges.  Do not let those edges steal a real left drag, and do not permit a
# second context menu while the first one is still active/backed.
old=fn_text('gui_input_buttons')
new=r'''fn gui_input_buttons(state:u64,wm:u64,buttons:u64,surface:u64) -> u64 {
    if state==0 || wm==0 || surface==0 || volatile_read64(state)!=1 { return 0; }
    let old=volatile_read64(state+96); let x=volatile_read64(state+8); let y=volatile_read64(state+16);
    let left=buttons%2; let old_left=old%2; let right=(buttons/2)%2; let old_right=(old/2)%2;

    // Left ownership always wins.  A transient right bit may not cancel, arm,
    // or replace a left-button window drag.  Canonicalize the stored button
    // state to left-only for the duration of a left gesture.
    if left!=0 || old_left!=0 || volatile_read64(state+176)!=0 {
        unsafe { volatile_write64(state+96,left); volatile_write64(state+296,0); volatile_write64(state+392,0); }
        if left!=0 && old_left==0 {
            if volatile_read64(state+128)!=0 { let hit=v108_context_hit_v118(state,x,y); unsafe { volatile_write64(state+248,volatile_read64(state+248)+1); volatile_write64(state+256,hit); volatile_write64(state+128,0); volatile_write64(state+240,0); volatile_write64(state+264,volatile_read64(state+264)+1); } if hit!=0 { serial_marker_v108_context_select_ok(); } else { serial_marker_v108_context_outside_ok(); } serial_marker_v108_context_dismiss_ok(); return 1; }
            let wx=volatile_read64(state+160); let wy=volatile_read64(state+168); if x>=wx && x<wx+270 && y>=wy && y<wy+36 { unsafe { volatile_write64(state+176,1); volatile_write64(state+184,x-wx); volatile_write64(state+192,y-wy); volatile_write64(state+24,0); volatile_write64(state+32,0); } return 1; }
            let id=gui_input_hit_test(state,wm,x,y); if id!=0 { if gui_input_focus(state,wm,id)==0 { return 0; } let rec=wm_record(wm,id); let rx=volatile_read64(rec+8); let ry=volatile_read64(rec+16); let rw=volatile_read64(rec+24); let rh=volatile_read64(rec+32); var mode:u64=0; if y>=ry && y<ry+36 { mode=1; } if x+18>=rx+rw && y+18>=ry+rh { mode=2; } unsafe { volatile_write64(state+24,id); volatile_write64(state+32,mode); } }
        }
        if left==0 && old_left!=0 { unsafe { volatile_write64(state+24,0); volatile_write64(state+32,0); volatile_write64(state+176,0); } }
        return 1;
    }

    unsafe { volatile_write64(state+96,buttons); }

    // Context menu is a singleton.  Until the active menu is explicitly
    // dismissed by a left click, further right edges cannot move its geometry
    // or invalidate the one backing buffer used for local restoration.
    if volatile_read64(state+128)!=0 {
        unsafe { volatile_write64(state+296,0); volatile_write64(state+392,0); }
        return 1;
    }

    if right!=0 && old_right==0 { unsafe { volatile_write64(state+296,1); volatile_write64(state+304,x); volatile_write64(state+312,y); volatile_write64(state+392,read_tsc()); } return 1; }
    if right==0 && old_right!=0 {
        if volatile_read64(state+296)!=0 {
            let start=volatile_read64(state+392); let now=read_tsc(); let ax=volatile_read64(state+304); let ay=volatile_read64(state+312); var dx:u64=0; var dy:u64=0; if x>ax { dx=x-ax; } else { dx=ax-x; } if y>ay { dy=y-ay; } else { dy=ay-y; }
            if start!=0 && now>start && now-start<3000000000 && dx<=4 && dy<=4 {
                let opens=volatile_read64(state+152)+1;
                unsafe { volatile_write64(state+296,0); volatile_write64(state+128,1); volatile_write64(state+136,ax); volatile_write64(state+144,ay); volatile_write64(state+152,opens); volatile_write64(state+240,0); volatile_write64(state+288,0); volatile_write64(state+328,volatile_read64(state+328)+1); volatile_write64(state+336,x); volatile_write64(state+344,y); volatile_write64(state+392,0); }
                if v108_context_geometry_v118(surface,state)==0 { return 0; } serial_marker_v108_right_gesture_v120(); serial_marker_v108_desktop_context_ok(); if opens>=2 { serial_marker_v108_context_repeat_ok(); } return 1;
            }
            unsafe { volatile_write64(state+320,volatile_read64(state+320)+1); }
        }
        unsafe { volatile_write64(state+296,0); volatile_write64(state+392,0); } return 1;
    }
    return 1;
}'''
replace_once(old,new,'exclusive left/right ownership and singleton context')

# Read-only xHCI root-port census.  This does not set PORT_POWER, issue a port
# reset, or change controller routing.  It records the physical PORTSC state
# after Intel routing + xHC initialization so the next write decision is based
# on real hardware evidence.
anchor='fn serial_marker_v108_drag_live_v122() -> void {'
helpers=r'''fn serial_marker_v108_xhci_port_census_v123() -> void { serial_putc(70); serial_putc(82); serial_putc(65); serial_putc(77); serial_putc(69); serial_putc(83); serial_putc(95); serial_putc(86); serial_putc(49); serial_putc(48); serial_putc(56); serial_putc(95); serial_putc(88); serial_putc(72); serial_putc(67); serial_putc(73); serial_putc(95); serial_putc(80); serial_putc(79); serial_putc(82); serial_putc(84); serial_putc(95); serial_putc(67); serial_putc(69); serial_putc(78); serial_putc(83); serial_putc(85); serial_putc(83); serial_putc(95); serial_putc(86); serial_putc(49); serial_putc(50); serial_putc(51); serial_putc(95); serial_putc(79); serial_putc(75); serial_putc(10); return; }
fn v108_xhci_port_census_ro_v123(xhci_state:u64,hardware_state:u64) -> u64 {
    if xhci_state==0 || hardware_state==0 || volatile_read64(xhci_state+56)!=1 { return 0; }
    let base=volatile_read64(xhci_state); let op=volatile_read64(xhci_state+8); if base==0 || op==0 { return 0; }
    var ports=(volatile_read32(base+4)/16777216)%256; if ports>32 { ports=32; } if ports==0 { return 0; }
    var connected:u64=0; var enabled:u64=0; var powered:u64=0; var sample:u64=0; var p:u64=0;
    while p<ports {
        let ps=volatile_read32(op+1024+(p*16));
        if ps%2!=0 { connected=connected+1; if sample==0 { sample=ps; } }
        if (ps/2)%2!=0 { enabled=enabled+1; }
        if (ps/512)%2!=0 { powered=powered+1; }
        if sample==0 && ps!=0 { sample=ps; }
        p=p+1;
    }
    unsafe { volatile_write64(hardware_state+560,ports); volatile_write64(hardware_state+568,connected); volatile_write64(hardware_state+576,enabled); volatile_write64(hardware_state+584,powered); volatile_write64(hardware_state+592,sample); }
    serial_marker_v108_xhci_port_census_v123(); return 1;
}
'''
replace_once(anchor,helpers+anchor,'xHCI census helpers')

# Capture the Intel Lynx Point controller's root-port state before subsequent
# scan attempts zero/reuse xhci_state.
old='''if (pci_cfg_read32(bdf/65536,(bdf/256)%256,bdf%256,0)%65536)==32902 && ((pci_cfg_read32(bdf/65536,(bdf/256)%256,bdf%256,0)/65536)%65536)==35889 { unsafe { volatile_write64(hardware_state+496,volatile_read64(xhci_state+1264)); volatile_write64(hardware_state+504,volatile_read64(xhci_state+1272)); volatile_write64(hardware_state+512,volatile_read64(xhci_state+1320)); volatile_write64(hardware_state+536,volatile_read64(xhci_state+1296)); volatile_write64(hardware_state+544,volatile_read64(xhci_state+1304)); volatile_write64(hardware_state+552,volatile_read64(xhci_state+1328)); } serial_marker_v108_usb_frozen_v121(); }'''
new='''if (pci_cfg_read32(bdf/65536,(bdf/256)%256,bdf%256,0)%65536)==32902 && ((pci_cfg_read32(bdf/65536,(bdf/256)%256,bdf%256,0)/65536)%65536)==35889 { unsafe { volatile_write64(hardware_state+496,volatile_read64(xhci_state+1264)); volatile_write64(hardware_state+504,volatile_read64(xhci_state+1272)); volatile_write64(hardware_state+512,volatile_read64(xhci_state+1320)); volatile_write64(hardware_state+536,volatile_read64(xhci_state+1296)); volatile_write64(hardware_state+544,volatile_read64(xhci_state+1304)); volatile_write64(hardware_state+552,volatile_read64(xhci_state+1328)); } if init_ok_v120!=0 { v108_xhci_port_census_ro_v123(xhci_state,hardware_state); } serial_marker_v108_usb_frozen_v121(); }'''
replace_once(old,new,'Intel xHCI census hook')

# Preserve census through the final xHCI scratch-state reuse.
old='''volatile_write64(xhci_state+1472,volatile_read64(hardware_state+520)); volatile_write64(xhci_state+1480,volatile_read64(hardware_state+528)); }'''
new='''volatile_write64(xhci_state+1472,volatile_read64(hardware_state+520)); volatile_write64(xhci_state+1480,volatile_read64(hardware_state+528)); volatile_write64(xhci_state+1600,volatile_read64(hardware_state+560)); volatile_write64(xhci_state+1608,volatile_read64(hardware_state+568)); volatile_write64(xhci_state+1616,volatile_read64(hardware_state+576)); volatile_write64(xhci_state+1624,volatile_read64(hardware_state+584)); volatile_write64(xhci_state+1632,volatile_read64(hardware_state+592)); }'''
replace_once(old,new,'preserve xHCI census')

# Replace the now-conclusive EHCI port-count row with the xHCI root-port row;
# the EHCI controller BDF row remains immediately above it for traceability.
label_anchor='fn v108_input_overlay_draw(surface:u64,state:u64,input_state:u64,xhci:u64) -> u64 {'
replace_once(label_anchor,text_fn('v108_text_xprt_v123','XPRT N C E P S')+label_anchor,'XPRT label')
old='''    v108_text_eprt_v122(surface,px+10,py+532,white); if xhci!=0 { v108_draw_small_u64(surface,((px+136)*65536)+(py+532),volatile_read64(xhci+1488),white); v108_draw_small_u64(surface,((px+196)*65536)+(py+532),volatile_read64(xhci+1496),green); v108_draw_small_u64(surface,((px+256)*65536)+(py+532),volatile_read64(xhci+1528),white); v108_draw_small_u64(surface,((px+316)*65536)+(py+532),volatile_read64(xhci+1536),green); v108_draw_small_u64(surface,((px+376)*65536)+(py+532),volatile_read64(xhci+1568),amber); }'''
new='''    v108_text_xprt_v123(surface,px+10,py+532,white); if xhci!=0 { v108_draw_small_u64(surface,((px+112)*65536)+(py+532),volatile_read64(xhci+1600),white); v108_draw_small_u64(surface,((px+166)*65536)+(py+532),volatile_read64(xhci+1608),green); v108_draw_small_u64(surface,((px+220)*65536)+(py+532),volatile_read64(xhci+1616),amber); v108_draw_small_u64(surface,((px+274)*65536)+(py+532),volatile_read64(xhci+1624),green); v108_draw_small_u64(surface,((px+328)*65536)+(py+532),volatile_read64(xhci+1632),white); }'''
replace_once(old,new,'XPRT telemetry row')

# Model-level invariants: no desktop-wide repaint was reintroduced into the
# runtime event path, the full-window drag renderer stays in use, and the new
# xHCI census contains no controller or PORTSC writes.
census=fn_text('v108_xhci_port_census_ro_v123')
for bad in ('volatile_write32','volatile_write16','volatile_write8','pci_cfg_write'):
    if bad in census: raise SystemExit('xHCI census is not read-only: '+bad)
proxy=fn_text('v108_drag_proxy_present_v119')
if 'v108_drag_outline_toggle_v119' in proxy or 'v108_drag_window_draw_v116' not in proxy:
    raise SystemExit('live full-window drag regressed')
buttons=fn_text('gui_input_buttons')
for req in ('left!=0 || old_left!=0 || volatile_read64(state+176)!=0','if volatile_read64(state+128)!=0','dx<=4 && dy<=4'):
    if req not in buttons: raise SystemExit('right/drag guard missing: '+req)

p.write_text(s)
print(hashlib.sha256(s.encode()).hexdigest())
