#!/usr/bin/env python3
from pathlib import Path
import hashlib,subprocess,sys
if len(sys.argv)!=2: raise SystemExit('usage: patch_v108_r29_root_port_recovery.py <kernel/main.nx>')
p=Path(sys.argv[1]); base=Path(__file__).with_name('patch_v108_r28c_hub_ep0_state_isolation.py')
subprocess.run([sys.executable,str(base),str(p)],check=True,stdout=subprocess.DEVNULL)
s=p.read_text()
BASE='8e1401d483bcff3a5e67caf3c6183fdafe370a3de742675ca0adc255c67d13b5'
if hashlib.sha256(s.encode()).hexdigest()!=BASE: raise SystemExit('r28c base mismatch')

def span(name):
 st=s.index('fn '+name);op=s.index('{',st);d=0
 for i in range(op,len(s)):
  if s[i]=='{':d+=1
  elif s[i]=='}':
   d-=1
   if d==0:return st,i+1
 raise RuntimeError(name)
def repl(name,new):
 global s
 a,b=span(name);s=s[:a]+new+s[b:]
def rep(old,new,label):
 global s
 n=s.count(old)
 if n!=1: raise SystemExit(f'{label} count {n}')
 s=s.replace(old,new,1)

# Physical clue from r28c: Intel 8C31 routing is applied and two root-port
# connections are visible, but EP0 telemetry remains untouched.  The old
# scanner aborted the entire controller when reset of the first connected
# root port failed.  On real hardware that first port can be the Rufus boot
# medium, preventing a later HID receiver from ever being attempted.
#
# r29 does two things before changing any HID code:
# 1. Honor xHCI Port Power Control when the controller advertises PPC.
# 2. Treat a failed root-port reset as a per-port failure and continue scanning
#    later connected ports rather than returning the same value used for
#    "no more ports".
helper='''fn xhci_power_root_ports_v129(xhci_state:u64) -> u64 {\n    if xhci_state==0 || volatile_read64(xhci_state+56)!=1 { return 0; }\n    let base=volatile_read64(xhci_state); let op=volatile_read64(xhci_state+8); if base==0 || op==0 { return 0; }\n    var ports=(volatile_read32(base+4)/16777216)%256; if ports>32 { ports=32; } if ports==0 { return 0; }\n    let hcc=volatile_read32(base+16); let ppc=(hcc/8)%2;\n    var before:u64=0; var writes:u64=0; var p:u64=0;\n    while p<ports {\n        let reg=op+1024+(p*16); let ps=volatile_read32(reg);\n        if (ps/512)%2!=0 { before=before+1; }\n        else { if ppc!=0 { var w=xhci_port_write_base(ps); w=set_flag(w,512); unsafe { volatile_write32(reg,w); } writes=writes+1; } }\n        p=p+1;\n    }\n    if writes!=0 { pit_wait(119320); }\n    var after:u64=0; var connected:u64=0; var sample:u64=0; p=0;\n    while p<ports {\n        let ps=volatile_read32(op+1024+(p*16));\n        if (ps/512)%2!=0 { after=after+1; }\n        if ps%2!=0 { connected=connected+1; if sample==0 { sample=ps; } }\n        p=p+1;\n    }\n    unsafe { volatile_write64(xhci_state+1992,ppc); volatile_write64(xhci_state+2000,ports); volatile_write64(xhci_state+2008,before); volatile_write64(xhci_state+2016,writes); volatile_write64(xhci_state+2024,after); volatile_write64(xhci_state+2032,connected); volatile_write64(xhci_state+2040,sample); }\n    return 1;\n}\n'''
rep('fn xhci_controller_init(hardware_state:u64, phys_state:u64, xhci_state:u64, pml4:u64) -> u64 {',helper+'fn xhci_controller_init(hardware_state:u64, phys_state:u64, xhci_state:u64, pml4:u64) -> u64 {','power helper')
rep('    let connected=xhci_count_connected_ports_v119(xhci_state); unsafe { volatile_write64(xhci_state+1320,connected); }','    xhci_power_root_ports_v129(xhci_state); let connected=xhci_count_connected_ports_v119(xhci_state); unsafe { volatile_write64(xhci_state+1320,connected); }','power call')

repl('xhci_reset_connected_port_from','''fn xhci_reset_connected_port_from(xhci_state:u64,start:u64) -> u64 {\n    if xhci_state==0 || volatile_read64(xhci_state+56)!=1 { return 0; }\n    let base=volatile_read64(xhci_state); let op=volatile_read64(xhci_state+8); let hcs1=volatile_read32(base+4); var ports=(hcs1/16777216)%256; if ports>32 { ports=32; }\n    unsafe { volatile_write64(xhci_state+1640,0); volatile_write64(xhci_state+1648,0); volatile_write64(xhci_state+1656,0); volatile_write64(xhci_state+1664,0); volatile_write64(xhci_state+1672,0); volatile_write64(xhci_state+2048,0); volatile_write64(xhci_state+2056,0); volatile_write64(xhci_state+2064,0); }\n    var p=start; var failed:u64=0; var first_failed:u64=0; var first_reason:u64=0;\n    while p<ports {\n        let port=op+1024+(p*16); let ps=volatile_read32(port);\n        if ps%2!=0 {\n            var reason:u64=0; var done:u64=ps; var good:u64=0;\n            var write=xhci_port_write_base(ps); if (ps/512)%2==0 { let hcc=volatile_read32(base+16); if (hcc/8)%2!=0 { write=set_flag(write,512); } } write=set_flag(write,16); unsafe { volatile_write32(port,write); }\n            var spins:u64=0; while (volatile_read32(port)/16)%2!=0 && spins<5000000 { cpu_pause(); spins=spins+1; }\n            if spins>=5000000 { done=volatile_read32(port); reason=1; }\n            else {\n                pit_wait(11932); done=volatile_read32(port);\n                if done%2==0 { reason=2; }\n                else {\n                    spins=0; while (done/2)%2==0 && spins<2000000 { cpu_pause(); done=volatile_read32(port); spins=spins+1; }\n                    if (done/2)%2==0 { reason=3; } else { good=1; }\n                }\n            }\n            if good!=0 {\n                unsafe { volatile_write64(xhci_state+1640,p+1); volatile_write64(xhci_state+1648,ps); volatile_write64(xhci_state+1656,done); volatile_write64(xhci_state+1664,1); volatile_write64(xhci_state+1672,0); volatile_write64(xhci_state+112,p+1); volatile_write64(xhci_state+120,done); volatile_write64(xhci_state+128,1); volatile_write64(xhci_state+384,0); volatile_write64(xhci_state+416,0); volatile_write64(xhci_state+2048,failed); volatile_write64(xhci_state+2056,first_failed); volatile_write64(xhci_state+2064,first_reason); }\n                serial_marker_xhci_port_ready(); return p+1;\n            }\n            failed=failed+1; if first_failed==0 { first_failed=p+1; first_reason=reason; }\n        }\n        p=p+1;\n    }\n    unsafe { volatile_write64(xhci_state+1672,4); volatile_write64(xhci_state+2048,failed); volatile_write64(xhci_state+2056,first_failed); volatile_write64(xhci_state+2064,first_reason); }\n    return 0;\n}''')

# Freeze the first root-port attempt regardless of speed.  r28c only froze
# LS/FS attempts, which made a failed HS boot-media port indistinguishable from
# "scanner never ran" on physical hardware.
rep('if pspeed<=2 && volatile_read64(hardware_state+736)==0','if volatile_read64(hardware_state+736)==0','root attempt telemetry')

# Add explicit power/retry evidence to the physical overlay.
labels='''fn v108_text_xpwr_v129(surface:u64,x:u64,y:u64,color:u64) -> u64 { if gui_draw_char_scaled(surface,((x+0)*65536)+y,(88*65536)+1,color)==0 { return 0; } if gui_draw_char_scaled(surface,((x+6)*65536)+y,(80*65536)+1,color)==0 { return 0; } if gui_draw_char_scaled(surface,((x+12)*65536)+y,(87*65536)+1,color)==0 { return 0; } if gui_draw_char_scaled(surface,((x+18)*65536)+y,(82*65536)+1,color)==0 { return 0; } if gui_draw_char_scaled(surface,((x+24)*65536)+y,(32*65536)+1,color)==0 { return 0; } if gui_draw_char_scaled(surface,((x+30)*65536)+y,(80*65536)+1,color)==0 { return 0; } if gui_draw_char_scaled(surface,((x+36)*65536)+y,(80*65536)+1,color)==0 { return 0; } if gui_draw_char_scaled(surface,((x+42)*65536)+y,(67*65536)+1,color)==0 { return 0; } if gui_draw_char_scaled(surface,((x+48)*65536)+y,(32*65536)+1,color)==0 { return 0; } if gui_draw_char_scaled(surface,((x+54)*65536)+y,(78*65536)+1,color)==0 { return 0; } if gui_draw_char_scaled(surface,((x+60)*65536)+y,(32*65536)+1,color)==0 { return 0; } if gui_draw_char_scaled(surface,((x+66)*65536)+y,(66*65536)+1,color)==0 { return 0; } if gui_draw_char_scaled(surface,((x+72)*65536)+y,(32*65536)+1,color)==0 { return 0; } if gui_draw_char_scaled(surface,((x+78)*65536)+y,(87*65536)+1,color)==0 { return 0; } if gui_draw_char_scaled(surface,((x+84)*65536)+y,(32*65536)+1,color)==0 { return 0; } if gui_draw_char_scaled(surface,((x+90)*65536)+y,(65*65536)+1,color)==0 { return 0; } if gui_draw_char_scaled(surface,((x+96)*65536)+y,(32*65536)+1,color)==0 { return 0; } if gui_draw_char_scaled(surface,((x+102)*65536)+y,(67*65536)+1,color)==0 { return 0; } return 1; }\nfn v108_text_xrty_v129(surface:u64,x:u64,y:u64,color:u64) -> u64 { if gui_draw_char_scaled(surface,((x+0)*65536)+y,(88*65536)+1,color)==0 { return 0; } if gui_draw_char_scaled(surface,((x+6)*65536)+y,(82*65536)+1,color)==0 { return 0; } if gui_draw_char_scaled(surface,((x+12)*65536)+y,(84*65536)+1,color)==0 { return 0; } if gui_draw_char_scaled(surface,((x+18)*65536)+y,(89*65536)+1,color)==0 { return 0; } if gui_draw_char_scaled(surface,((x+24)*65536)+y,(32*65536)+1,color)==0 { return 0; } if gui_draw_char_scaled(surface,((x+30)*65536)+y,(78*65536)+1,color)==0 { return 0; } if gui_draw_char_scaled(surface,((x+36)*65536)+y,(32*65536)+1,color)==0 { return 0; } if gui_draw_char_scaled(surface,((x+42)*65536)+y,(70*65536)+1,color)==0 { return 0; } if gui_draw_char_scaled(surface,((x+48)*65536)+y,(80*65536)+1,color)==0 { return 0; } if gui_draw_char_scaled(surface,((x+54)*65536)+y,(32*65536)+1,color)==0 { return 0; } if gui_draw_char_scaled(surface,((x+60)*65536)+y,(70*65536)+1,color)==0 { return 0; } if gui_draw_char_scaled(surface,((x+66)*65536)+y,(67*65536)+1,color)==0 { return 0; } return 1; }\n'''
rep('fn v108_input_overlay_draw(surface:u64,state:u64,input_state:u64,xhci:u64) -> u64 {',labels+'fn v108_input_overlay_draw(surface:u64,state:u64,input_state:u64,xhci:u64) -> u64 {','telemetry labels')
rep('if display_fill_rect(surface,(px*65536)+py,(410*65536)+598,bg)==0 { return 0; }','if display_fill_rect(surface,(px*65536)+py,(410*65536)+634,bg)==0 { return 0; }','overlay height')
rep('    let fr=volatile_read64(input_state+3792); v108_text_frec_v125(surface,px+10,py+568,white); if fr!=0 { v108_draw_small_u64(surface,((px+130)*65536)+(py+568),volatile_read64(fr+32),white); v108_draw_small_u64(surface,((px+184)*65536)+(py+568),volatile_read64(fr+56),amber); v108_draw_small_u64(surface,((px+238)*65536)+(py+568),volatile_read64(fr+64),green); v108_draw_small_u64(surface,((px+292)*65536)+(py+568),volatile_read64(fr+96),green); v108_draw_small_u64(surface,((px+346)*65536)+(py+568),volatile_read64(fr+104),red); }\n    return 1;','    let fr=volatile_read64(input_state+3792); v108_text_frec_v125(surface,px+10,py+568,white); if fr!=0 { v108_draw_small_u64(surface,((px+130)*65536)+(py+568),volatile_read64(fr+32),white); v108_draw_small_u64(surface,((px+184)*65536)+(py+568),volatile_read64(fr+56),amber); v108_draw_small_u64(surface,((px+238)*65536)+(py+568),volatile_read64(fr+64),green); v108_draw_small_u64(surface,((px+292)*65536)+(py+568),volatile_read64(fr+96),green); v108_draw_small_u64(surface,((px+346)*65536)+(py+568),volatile_read64(fr+104),red); }\n    v108_text_xpwr_v129(surface,px+10,py+586,white); if xhci!=0 { v108_draw_small_u64(surface,((px+130)*65536)+(py+586),volatile_read64(xhci+1992),amber); v108_draw_small_u64(surface,((px+178)*65536)+(py+586),volatile_read64(xhci+2000),white); v108_draw_small_u64(surface,((px+226)*65536)+(py+586),volatile_read64(xhci+2008),amber); v108_draw_small_u64(surface,((px+274)*65536)+(py+586),volatile_read64(xhci+2016),red); v108_draw_small_u64(surface,((px+322)*65536)+(py+586),volatile_read64(xhci+2024),green); v108_draw_small_u64(surface,((px+370)*65536)+(py+586),volatile_read64(xhci+2032),green); }\n    v108_text_xrty_v129(surface,px+10,py+604,white); if xhci!=0 { v108_draw_small_u64(surface,((px+112)*65536)+(py+604),volatile_read64(xhci+2048),amber); v108_draw_small_u64(surface,((px+178)*65536)+(py+604),volatile_read64(xhci+2056),white); v108_draw_small_u64(surface,((px+244)*65536)+(py+604),volatile_read64(xhci+2064),red); }\n    return 1;','overlay telemetry')

# Fail-closed structural contracts.
for q in ('fn xhci_power_root_ports_v129','pit_wait(119320)','volatile_write64(xhci_state+2032,connected)','fn v108_text_xpwr_v129','fn v108_text_xrty_v129'):
 if q not in s: raise SystemExit('r29 missing '+q)
a,b=span('xhci_reset_connected_port_from');rst=s[a:b]
for q in ('failed=failed+1','p=p+1','first_reason=reason','return p+1'):
 if q not in rst: raise SystemExit('r29 reset recovery missing '+q)
if 'if spins>=5000000' in rst and 'return 0;' in rst[rst.index('if spins>=5000000'):rst.index('if spins>=5000000')+220]: raise SystemExit('r29 still aborts on first reset timeout')
if 'if pspeed<=2 && volatile_read64(hardware_state+736)==0' in s: raise SystemExit('r29 root telemetry still LSFS-only')
if s.count('{')!=s.count('}'): raise SystemExit('brace imbalance')
expected='21c34b8d03e581a60c55056e9bf363c298128ea3a3a5e94ad2cb1e15120b1b33'
actual=hashlib.sha256(s.encode()).hexdigest()
if actual!=expected: raise SystemExit(f'r29 identity mismatch {actual}')
p.write_text(s); print(actual)
