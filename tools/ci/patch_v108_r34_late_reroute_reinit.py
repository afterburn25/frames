#!/usr/bin/env python3
from pathlib import Path
import hashlib, subprocess, sys
if len(sys.argv)!=2: raise SystemExit('usage: patch_v108_r34_late_reroute_reinit.py <kernel/main.nx>')
p=Path(sys.argv[1])
# Chain from the exact certified r33c source.
base=Path(__file__).with_name('patch_v108_r33c_motion_telemetry_isolation.py')
subprocess.run([sys.executable,str(base),str(p)],check=True,stdout=subprocess.DEVNULL)
s=p.read_text()
BASE='53a6e654154d2d622650c16aefac12bc9cbee9c4a3cfc772948dd60feeb62c3e'
if hashlib.sha256(s.encode()).hexdigest()!=BASE: raise SystemExit('r33c base mismatch')

def rep(old,new,label,count=1):
    global s
    n=s.count(old)
    if n!=count: raise SystemExit(f'{label} count {n}')
    s=s.replace(old,new,count)

def label_fn(name,text):
    out=f'fn {name}(surface:u64,x:u64,y:u64,color:u64) -> u64 {{'
    for i,ch in enumerate(text):
        out+=f' if gui_draw_char_scaled(surface,((x+{i*6})*65536)+y,({ord(ch)}*65536)+1,color)==0 {{ return 0; }}'
    return out+' return 1; }\n'

old='''                    let init_ok_v120=xhci_controller_init(hardware_state,phys_state,xhci_state,pml4); if init_ok_v120!=0 { let route_post_v133=v108_intel_xhci_route_ports_v120(bdf,xhci_state,hardware_state); pit_wait(119320); let post_v133=xhci_root_port_settle_v132(xhci_state); unsafe { volatile_write64(xhci_state+2360,route_post_v133); volatile_write64(xhci_state+2368,post_v133); volatile_write64(xhci_state+1320,post_v133); } }'''
new='''                    var init_ok_v120=xhci_controller_init(hardware_state,phys_state,xhci_state,pml4); if init_ok_v120!=0 {
                        let before_v134=volatile_read64(xhci_state+2032); let route_post_v133=v108_intel_xhci_route_ports_v120(bdf,xhci_state,hardware_state); pit_wait(119320); let post_v133=xhci_root_port_settle_v132(xhci_state); unsafe { volatile_write64(xhci_state+2360,route_post_v133); volatile_write64(xhci_state+2368,post_v133); volatile_write64(xhci_state+1320,post_v133); volatile_write64(xhci_state+2496,before_v134); volatile_write64(xhci_state+2504,post_v133); volatile_write64(xhci_state+2512,0); volatile_write64(xhci_state+2520,1); volatile_write64(xhci_state+2528,post_v133); volatile_write64(xhci_state+2536,0); volatile_write64(xhci_state+2544,route_post_v133); }
                        if post_v133>before_v134 {
                            unsafe { volatile_write64(xhci_state+2512,1); }
                            let route_reinit_pre_v134=v108_intel_xhci_route_ports_v120(bdf,xhci_state,hardware_state); let reinit_ok_v134=xhci_controller_init(hardware_state,phys_state,xhci_state,pml4); var reinit_after_v134:u64=0; var route_reinit_post_v134:u64=route_reinit_pre_v134;
                            if reinit_ok_v134!=0 { route_reinit_post_v134=v108_intel_xhci_route_ports_v120(bdf,xhci_state,hardware_state); pit_wait(119320); xhci_power_root_ports_v129(xhci_state); reinit_after_v134=xhci_root_port_settle_v132(xhci_state); unsafe { volatile_write64(xhci_state+1320,reinit_after_v134); } }
                            let reinit_err_v134=volatile_read64(xhci_state+1272); unsafe { volatile_write64(xhci_state+2496,before_v134); volatile_write64(xhci_state+2504,post_v133); volatile_write64(xhci_state+2512,1); volatile_write64(xhci_state+2520,reinit_ok_v134); volatile_write64(xhci_state+2528,reinit_after_v134); volatile_write64(xhci_state+2536,reinit_err_v134); volatile_write64(xhci_state+2544,route_reinit_post_v134); volatile_write64(xhci_state+2360,route_post_v133); volatile_write64(xhci_state+2368,post_v133); }
                            if reinit_ok_v134==0 { init_ok_v120=0; }
                        }
                    }'''
rep(old,new,'late-reroute reinit block')

# Add a dedicated physical telemetry row. B/P = xHCI connections before/after
# late EHCI release routing; A/O = reinit attempted/succeeded; C/E = post-reinit
# connections/init error. This makes the next physical result decisive.
rep('fn v108_input_overlay_draw(surface:u64,state:u64,input_state:u64,xhci:u64) -> u64 {',label_fn('v108_text_r34_v134','R34 B P A O C E')+'fn v108_input_overlay_draw(surface:u64,state:u64,input_state:u64,xhci:u64) -> u64 {','r34 label insert')
# The r33c panel rectangle is 760px high. Extend it for one more row.
rep('(410*65536)+760','(410*65536)+778','r34 overlay height',count=s.count('(410*65536)+760'))
row='''    v108_text_r32_v132(surface,px+10,py+694,white); if xhci!=0 { v108_draw_small_u64(surface,((px+130)*65536)+(py+694),volatile_read64(xhci+2312),white); v108_draw_small_u64(surface,((px+178)*65536)+(py+694),volatile_read64(xhci+2320),amber); v108_draw_small_u64(surface,((px+226)*65536)+(py+694),volatile_read64(xhci+2328),green); v108_draw_small_u64(surface,((px+274)*65536)+(py+694),volatile_read64(xhci+2344),red); v108_draw_small_u64(surface,((px+322)*65536)+(py+694),volatile_read64(xhci+2352),green); v108_draw_small_u64(surface,((px+370)*65536)+(py+694),volatile_read64(xhci+2368),green); }
    return 1;'''
row2='''    v108_text_r32_v132(surface,px+10,py+694,white); if xhci!=0 { v108_draw_small_u64(surface,((px+130)*65536)+(py+694),volatile_read64(xhci+2312),white); v108_draw_small_u64(surface,((px+178)*65536)+(py+694),volatile_read64(xhci+2320),amber); v108_draw_small_u64(surface,((px+226)*65536)+(py+694),volatile_read64(xhci+2328),green); v108_draw_small_u64(surface,((px+274)*65536)+(py+694),volatile_read64(xhci+2344),red); v108_draw_small_u64(surface,((px+322)*65536)+(py+694),volatile_read64(xhci+2352),green); v108_draw_small_u64(surface,((px+370)*65536)+(py+694),volatile_read64(xhci+2368),green); }
    v108_text_r34_v134(surface,px+10,py+712,white); if xhci!=0 { v108_draw_small_u64(surface,((px+112)*65536)+(py+712),volatile_read64(xhci+2496),white); v108_draw_small_u64(surface,((px+166)*65536)+(py+712),volatile_read64(xhci+2504),amber); v108_draw_small_u64(surface,((px+220)*65536)+(py+712),volatile_read64(xhci+2512),green); v108_draw_small_u64(surface,((px+274)*65536)+(py+712),volatile_read64(xhci+2520),green); v108_draw_small_u64(surface,((px+328)*65536)+(py+712),volatile_read64(xhci+2528),green); v108_draw_small_u64(surface,((px+376)*65536)+(py+712),volatile_read64(xhci+2536),red); }
    return 1;'''
rep(row,row2,'r34 telemetry row')

for q in ('var init_ok_v120=xhci_controller_init','if post_v133>before_v134','route_reinit_pre_v134','reinit_ok_v134=xhci_controller_init','volatile_write64(xhci_state+2528,reinit_after_v134)','fn v108_text_r34_v134','volatile_read64(xhci+2496)','volatile_read64(xhci+2536)'):
    if q not in s: raise SystemExit('r34 contract missing '+q)
if s.count('{')!=s.count('}'): raise SystemExit('brace imbalance')
expected='faed1632f131333e4e2c81c393b1e0df6a7940fde2c8506605e9b8964e7c5621'
actual=hashlib.sha256(s.encode()).hexdigest()
if actual!=expected: raise SystemExit(f'r34 identity mismatch {actual}')
p.write_text(s)
print(actual)
