#!/usr/bin/env python3
from pathlib import Path
import hashlib,subprocess,sys
if len(sys.argv)!=2: raise SystemExit('usage: patch_v108_r30_hid_first_right_click.py <kernel/main.nx>')
p=Path(sys.argv[1]); base=Path(__file__).with_name('patch_v108_r29_root_port_recovery.py')
subprocess.run([sys.executable,str(base),str(p)],check=True,stdout=subprocess.DEVNULL)
s=p.read_text(); BASE='21c34b8d03e581a60c55056e9bf363c298128ea3a3e5e94ad2cb1e15120b1b33'
# Accept the exact r29 identity, including the historical source hash typo guard below.
actual_base=hashlib.sha256(s.encode()).hexdigest()
if actual_base!='21c34b8d03e581a60c55056e9bf363c298128ea3a3a5e94ad2cb1e15120b1b33': raise SystemExit('r29 base mismatch '+actual_base)

def span(name):
 st=s.index('fn '+name); op=s.index('{',st); d=0
 for i in range(op,len(s)):
  if s[i]=='{': d+=1
  elif s[i]=='}':
   d-=1
   if d==0:return st,i+1
 raise RuntimeError(name)
def rep(old,new,label,src=None):
 global s
 target=s if src is None else src
 n=target.count(old)
 if n!=1: raise SystemExit(f'{label} count {n}')
 out=target.replace(old,new,1)
 if src is None: s=out
 return out

def label_fn(name,text):
 out=f'fn {name}(surface:u64,x:u64,y:u64,color:u64) -> u64 {{'
 i=0
 while i<len(text):
  out+=f' if gui_draw_char_scaled(surface,((x+{i*6})*65536)+y,({ord(text[i])}*65536)+1,color)==0 {{ return 0; }}'
  i+=1
 return out+' return 1; }\n'

# Keep the HID-discovery pass controller-clean. r29 proved the first physical
# root device is the Rufus MSC device; configuring that MSC before trying the
# next port perturbs the same shared xHCI scratch state and adds boot latency.
a,b=span('v108_xhci_scan_pointer_v116'); scan=s[a:b]
scan=rep('if volatile_read64(hardware_state+712)==0 { v108_msc_snapshot_v125(xhci_state,hardware_state,phys_state,fr); }','if volatile_read64(hardware_state+712)==0 { unsafe { volatile_write64(hardware_state+912,volatile_read64(hardware_state+912)+1); } }','defer MSC during HID scan',scan)
scan=rep('volatile_write64(hardware_state+800,0); volatile_write64(hardware_state+808,0); volatile_write64(hardware_state+816,0); }','volatile_write64(hardware_state+800,0); volatile_write64(hardware_state+808,0); volatile_write64(hardware_state+816,0); volatile_write64(hardware_state+824,0); volatile_write64(hardware_state+832,0); volatile_write64(hardware_state+840,0); volatile_write64(hardware_state+848,0); volatile_write64(hardware_state+856,0); volatile_write64(hardware_state+864,0); volatile_write64(hardware_state+872,0); volatile_write64(hardware_state+880,0); volatile_write64(hardware_state+888,0); volatile_write64(hardware_state+896,0); volatile_write64(hardware_state+904,0); volatile_write64(hardware_state+912,0); }','r30 telemetry init',scan)
scan=rep('let pspeed=(volatile_read64(xhci_state+120)/1024)%16; if volatile_read64(hardware_state+736)==0 { unsafe { volatile_write64(hardware_state+736,1); volatile_write64(hardware_state+744,pspeed); volatile_write64(hardware_state+752,port); } } unsafe { volatile_write64(hardware_state+680,2); }','let pspeed=(volatile_read64(xhci_state+120)/1024)%16; if volatile_read64(hardware_state+736)==0 { unsafe { volatile_write64(hardware_state+736,1); volatile_write64(hardware_state+744,pspeed); volatile_write64(hardware_state+752,port); } } else { if volatile_read64(hardware_state+824)==0 && port!=volatile_read64(hardware_state+752) { unsafe { volatile_write64(hardware_state+824,1); volatile_write64(hardware_state+832,pspeed); volatile_write64(hardware_state+840,port); volatile_write64(hardware_state+848,2); } } } unsafe { volatile_write64(hardware_state+680,2); }','capture second port',scan)
scan=rep('let slot_ok=xhci_enable_slot(xhci_state); if slot_ok==0 {','let slot_ok=xhci_enable_slot(xhci_state); if volatile_read64(hardware_state+824)!=0 && volatile_read64(hardware_state+840)==port { unsafe { volatile_write64(hardware_state+848,3); volatile_write64(hardware_state+856,volatile_read64(xhci_state+488)); if slot_ok!=0 { volatile_write64(hardware_state+864,slot_ok); } } } if slot_ok==0 {','capture second slot',scan)
scan=rep('unsafe { volatile_write64(hardware_state+680,3); } let address_ok=xhci_address_default_device(xhci_state,phys_state);','unsafe { volatile_write64(hardware_state+680,3); } let address_ok=xhci_address_default_device(xhci_state,phys_state); if volatile_read64(hardware_state+824)!=0 && volatile_read64(hardware_state+840)==port { unsafe { volatile_write64(hardware_state+848,4); volatile_write64(hardware_state+856,volatile_read64(xhci_state+488)); } }','capture second address',scan)
scan=rep('unsafe { volatile_write64(hardware_state+680,4); } let d8_ok=xhci_get_device_descriptor8(xhci_state,phys_state);','unsafe { volatile_write64(hardware_state+680,4); } let d8_ok=xhci_get_device_descriptor8(xhci_state,phys_state); if volatile_read64(hardware_state+824)!=0 && volatile_read64(hardware_state+840)==port { unsafe { volatile_write64(hardware_state+848,5); volatile_write64(hardware_state+864,volatile_read64(xhci_state+504)); } }','capture second descriptor8',scan)
scan=rep('unsafe { volatile_write64(hardware_state+680,5); } let final_ok=xhci_finalize_address_and_descriptor(xhci_state,phys_state);','unsafe { volatile_write64(hardware_state+680,5); } let final_ok=xhci_finalize_address_and_descriptor(xhci_state,phys_state); if volatile_read64(hardware_state+824)!=0 && volatile_read64(hardware_state+840)==port { unsafe { volatile_write64(hardware_state+848,6); volatile_write64(hardware_state+864,volatile_read64(xhci_state+504)); } }','capture second final',scan)
scan=rep('if xhci_discover_boot_hid(xhci_state,phys_state)!=0 {','if volatile_read64(hardware_state+824)!=0 && volatile_read64(hardware_state+840)==port { unsafe { volatile_write64(hardware_state+872,volatile_read64(xhci_state+272)); volatile_write64(hardware_state+880,volatile_read64(xhci_state+280)); } } let hid_probe_v130=xhci_discover_boot_hid(xhci_state,phys_state); if volatile_read64(hardware_state+824)!=0 && volatile_read64(hardware_state+840)==port { unsafe { volatile_write64(hardware_state+888,hid_probe_v130); volatile_write64(hardware_state+896,volatile_read64(xhci_state+1192)); volatile_write64(hardware_state+904,volatile_read64(xhci_state+1200)); } } if hid_probe_v130!=0 {','capture second HID probe',scan)
scan=rep('volatile_write64(xhci_state+1984,volatile_read64(hardware_state+816)); }','volatile_write64(xhci_state+1984,volatile_read64(hardware_state+816)); volatile_write64(xhci_state+2072,volatile_read64(hardware_state+824)); volatile_write64(xhci_state+2080,volatile_read64(hardware_state+832)); volatile_write64(xhci_state+2088,volatile_read64(hardware_state+840)); volatile_write64(xhci_state+2096,volatile_read64(hardware_state+848)); volatile_write64(xhci_state+2104,volatile_read64(hardware_state+856)); volatile_write64(xhci_state+2112,volatile_read64(hardware_state+864)); volatile_write64(xhci_state+2120,volatile_read64(hardware_state+872)); volatile_write64(xhci_state+2128,volatile_read64(hardware_state+880)); volatile_write64(xhci_state+2136,volatile_read64(hardware_state+888)); volatile_write64(xhci_state+2144,volatile_read64(hardware_state+896)); volatile_write64(xhci_state+2152,volatile_read64(hardware_state+904)); volatile_write64(xhci_state+2160,volatile_read64(hardware_state+912)); }','freeze second device telemetry',scan)
s=s[:a]+scan+s[b:]

# Physical ELAN button reports are edge/event driven. Requiring three repeated
# right-button packets can suppress a stationary right click completely.
rep('var need:u64=3; if typ==1 || typ==2 { need=1; }','var need:u64=1;','ELAN right edge acceptance')

# Make the context menu visible on the right-button down edge. This avoids
# depending on a second release packet and gives immediate physical proof.
a,b=span('gui_input_buttons'); gui=s[a:b]
gui=rep('if right!=0 && old_right==0 { unsafe { volatile_write64(state+296,1); volatile_write64(state+304,x); volatile_write64(state+312,y); volatile_write64(state+392,read_tsc()); } return 1; }','if right!=0 && old_right==0 { let opens=volatile_read64(state+152)+1; unsafe { volatile_write64(state+296,0); volatile_write64(state+128,1); volatile_write64(state+136,x); volatile_write64(state+144,y); volatile_write64(state+152,opens); volatile_write64(state+240,0); volatile_write64(state+288,0); volatile_write64(state+328,volatile_read64(state+328)+1); volatile_write64(state+336,x); volatile_write64(state+344,y); volatile_write64(state+392,0); } if v108_context_geometry_v118(surface,state)==0 { return 0; } serial_marker_v108_right_gesture_v120(); serial_marker_v108_desktop_context_ok(); if opens>=2 { serial_marker_v108_context_repeat_ok(); } return 1; }','context on press',gui)
tag='if right==0 && old_right!=0 {'; i=gui.index(tag); op=gui.index('{',i); d=0; end=0
for k in range(op,len(gui)):
 if gui[k]=='{': d+=1
 elif gui[k]=='}':
  d-=1
  if d==0: end=k+1; break
if end==0: raise SystemExit('right release branch not found')
gui=gui[:i]+'if right==0 && old_right!=0 { unsafe { volatile_write64(state+296,0); volatile_write64(state+392,0); } return 1; }'+gui[end:]
s=s[:a]+gui+s[b:]

labels=label_fn('v108_text_x2a_v130','X2A S P ST CC XC')+label_fn('v108_text_x2f_v130','X2F VID PID H M K')+label_fn('v108_text_rbtn_v130','RBTN R S O T M N')
rep('fn v108_input_overlay_draw(surface:u64,state:u64,input_state:u64,xhci:u64) -> u64 {',labels+'fn v108_input_overlay_draw(surface:u64,state:u64,input_state:u64,xhci:u64) -> u64 {','r30 labels')
rep('if display_fill_rect(surface,(px*65536)+py,(410*65536)+634,bg)==0 { return 0; }','if display_fill_rect(surface,(px*65536)+py,(410*65536)+688,bg)==0 { return 0; }','overlay height')
if s.count('(410*65536)+598')!=12: raise SystemExit('overlay dirty extent mismatch')
s=s.replace('(410*65536)+598','(410*65536)+688')
a,b=span('v108_input_overlay_draw'); ov=s[a:b]
rows='''    v108_text_x2a_v130(surface,px+10,py+622,white); if xhci!=0 { v108_draw_small_u64(surface,((px+112)*65536)+(py+622),volatile_read64(xhci+2080),amber); v108_draw_small_u64(surface,((px+166)*65536)+(py+622),volatile_read64(xhci+2088),white); v108_draw_small_u64(surface,((px+220)*65536)+(py+622),volatile_read64(xhci+2096),amber); v108_draw_small_u64(surface,((px+280)*65536)+(py+622),volatile_read64(xhci+2104),red); v108_draw_small_u64(surface,((px+340)*65536)+(py+622),volatile_read64(xhci+2112),red); }\n    v108_text_x2f_v130(surface,px+10,py+640,white); if xhci!=0 { v108_draw_small_u64(surface,((px+112)*65536)+(py+640),volatile_read64(xhci+2120),white); v108_draw_small_u64(surface,((px+184)*65536)+(py+640),volatile_read64(xhci+2128),white); v108_draw_small_u64(surface,((px+256)*65536)+(py+640),volatile_read64(xhci+2136),green); v108_draw_small_u64(surface,((px+304)*65536)+(py+640),volatile_read64(xhci+2144),green); v108_draw_small_u64(surface,((px+352)*65536)+(py+640),volatile_read64(xhci+2152),green); }\n    v108_text_rbtn_v130(surface,px+10,py+658,white); v108_draw_small_u64(surface,((px+112)*65536)+(py+658),volatile_read64(input_state+3760),amber); v108_draw_small_u64(surface,((px+166)*65536)+(py+658),volatile_read64(input_state+2808),white); v108_draw_small_u64(surface,((px+220)*65536)+(py+658),volatile_read64(input_state+2816),green); v108_draw_small_u64(surface,((px+274)*65536)+(py+658),volatile_read64(input_state+3768),green); v108_draw_small_u64(surface,((px+328)*65536)+(py+658),volatile_read64(state+128),green); v108_draw_small_u64(surface,((px+376)*65536)+(py+658),volatile_read64(state+152),green);\n    return 1;\n}'''
ov=rep('    return 1;\n}',rows,'r30 overlay rows',ov); s=s[:a]+ov+s[b:]

# Structural contracts.
sa,sb=span('v108_xhci_scan_pointer_v116'); scan=s[sa:sb]
if 'v108_msc_snapshot_v125(xhci_state,hardware_state,phys_state,fr)' in scan: raise SystemExit('MSC still mutates HID scan')
for q in ('hid_probe_v130','volatile_write64(xhci_state+2072','v108_text_x2a_v130','v108_text_rbtn_v130','var need:u64=1;'):
 if q not in s: raise SystemExit('r30 contract missing '+q)
ga,gb=span('gui_input_buttons'); g=s[ga:gb]
if 'volatile_write64(state+128,1)' not in g or 'if right!=0 && old_right==0' not in g: raise SystemExit('right context down-edge missing')
if s.count('{')!=s.count('}'): raise SystemExit('brace imbalance')
expected='430399228868e7cef069c5a45bb7c687954cc6e87dc9e461ba8669516e82ea4d'
actual=hashlib.sha256(s.encode()).hexdigest()
if actual!=expected: raise SystemExit(f'r30 identity mismatch {actual}')
p.write_text(s); print(actual)
