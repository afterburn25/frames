#!/usr/bin/env python3
from pathlib import Path
import hashlib, subprocess, sys
if len(sys.argv)!=2: raise SystemExit('usage: patch_v108_r68_ehci_bios_handoff.py <kernel/main.nx>')
p=Path(sys.argv[1]); here=Path(__file__).parent
base=here/'patch_v108_r67_persistent_newsched_cmask.py'
subprocess.run([sys.executable,str(base),str(p)],check=True,stdout=subprocess.DEVNULL)
s=p.read_text()
BASE='fb92da0f8bd6f5fa66912b6ad6b63c700a47bdb353fe3bb349d3fdc7e2e92570'
actual=hashlib.sha256(s.encode()).hexdigest()
if actual!=BASE: raise SystemExit('r68 exact r67 base mismatch '+actual)

def fn_text(src,name):
    st=src.index('fn '+name); op=src.index('{',st); d=0
    for i in range(op,len(src)):
        if src[i]=='{': d+=1
        elif src[i]=='}':
            d-=1
            if d==0: return src[st:i+1]
    raise RuntimeError(name)

def label_fn(name,text):
    out=f'fn {name}(surface:u64,x:u64,y:u64,color:u64) -> u64 {{'
    for i,ch in enumerate(text):
        out+=f' if gui_draw_char_scaled(surface,((x+{i*6})*65536)+y,({ord(ch)}*65536)+1,color)==0 {{ return 0; }}'
    return out+' return 1; }'

# r66/r67 proved both Linux reference split geometries with the persistent,
# hardware-owned QH lifecycle, yet the first qTD remains A=1/R=8/E=0.
# Before changing the scheduler again, perform the standard EHCI extended-cap
# BIOS/OS ownership handoff and disable legacy EHCI SMIs. Legacy USB firmware
# can otherwise retain ownership/interpose on keyboard/mouse traffic even when
# ordinary control transfers appear functional. This does not touch storage or
# xHCI port-routing registers.
arm=fn_text(s,'v159_ehci_mouse_periodic_arm')
anchor='    let ep0mps:u64=8; unsafe { volatile_write64(xhci_state+3936,ep0mps); }\n'
handoff='''    let h_ebdf=v108_pci_nth_ehci_v121(1); if h_ebdf==0 { unsafe { volatile_write64(xhci_state+4056,60); } return 60; }\n    let h_base=pci_bar_base(h_ebdf,0); if h_base==0 { unsafe { volatile_write64(xhci_state+4056,60); } return 60; }\n    let h_caplen=volatile_read8(h_base); if h_caplen<16 || h_caplen>128 { unsafe { volatile_write64(xhci_state+4056,60); } return 60; }\n    let h_hcc=volatile_read32(h_base+8); let h_bus=h_ebdf/65536; let h_dev=(h_ebdf/256)%256; let h_fun=h_ebdf%256;\n    var leg_off=(h_hcc/256)%256; var leg_found:u64=0; var leg_cap:u64=0; var leg_walk:u64=0;\n    while leg_off!=0 && leg_found==0 && leg_walk<16 { leg_cap=pci_cfg_read32(h_bus,h_dev,h_fun,leg_off); if leg_cap%256==1 { leg_found=1; } else { leg_off=(leg_cap/256)%256; } leg_walk=leg_walk+1; }\n    var handoff_code:u64=4; var bios_before:u64=0; var os_before:u64=0;\n    if leg_found!=0 {\n        bios_before=(leg_cap/65536)%2; os_before=(leg_cap/16777216)%2;\n        if bios_before!=0 {\n            if os_before==0 { pci_cfg_write32(h_ebdf,leg_off,leg_cap+16777216); }\n            var handwait:u64=0; var leg_now=pci_cfg_read32(h_bus,h_dev,h_fun,leg_off);\n            while (leg_now/65536)%2!=0 && handwait<100 { pit_wait(23864); leg_now=pci_cfg_read32(h_bus,h_dev,h_fun,leg_off); handwait=handwait+1; }\n            if (leg_now/65536)%2!=0 { unsafe { volatile_write64(xhci_state+3984,3); volatile_write64(xhci_state+3992,bios_before); volatile_write64(xhci_state+4000,os_before); volatile_write64(xhci_state+4056,61); } return 61; }\n            handoff_code=1;\n        } else { handoff_code=2; }\n        pci_cfg_write32(h_ebdf,leg_off+4,0);\n    }\n    unsafe { volatile_write64(xhci_state+3984,handoff_code); volatile_write64(xhci_state+3992,bios_before); volatile_write64(xhci_state+4000,os_before); }\n'''
if arm.count(anchor)!=1: raise SystemExit('r68 pre-control handoff anchor mismatch '+str(arm.count(anchor)))
arm=arm.replace(anchor,handoff+anchor,1)
oldwrite='    unsafe { volatile_write64(xhci_state+3984,profile); volatile_write64(xhci_state+3992,28); volatile_write64(xhci_state+4000,ttrc); }\n'
newwrite='    unsafe { volatile_write64(xhci_state+3984,profile); volatile_write64(xhci_state+3992,28); volatile_write64(xhci_state+4000,ttrc); volatile_write64(xhci_state+3984,handoff_code); volatile_write64(xhci_state+3992,bios_before); volatile_write64(xhci_state+4000,os_before); }\n'
if arm.count(oldwrite)!=1: raise SystemExit('r68 handoff telemetry restore anchor mismatch '+str(arm.count(oldwrite)))
arm=arm.replace(oldwrite,newwrite,1)
s=s.replace(fn_text(s,'v159_ehci_mouse_periodic_arm'),arm,1)

# H/B/O report ownership outcome and initial BIOS/OS semaphore state. X/A/R/E
# remain the live split/QH state, so the physical test directly shows whether
# legacy handoff changes the previously frozen first transaction.
s=s.replace(fn_text(s,'v140_text_wifi_v140'),label_fn('v140_text_wifi_v140','R68 HBOXARE'),1)
rs=s.index('v140_text_wifi_v140(surface,px+10,py+748,white);')
re=s.index('\n    return 1;\n}',rs)
newrow="v140_text_wifi_v140(surface,px+10,py+748,white); if xhci!=0 { let dm=volatile_read64(xhci+4040); let rr=volatile_read64(xhci+4080); let old_mint=volatile_read64(xhci+3976); var sm:u64=0; var cm:u64=0; var x:u64=0; var a:u64=0; var t:u64=0; var r:u64=0; var e:u64=0; if dm!=0 { let qi=volatile_read32(dm+8); sm=qi%256; cm=(qi/256)%256; let ot=volatile_read32(dm+24); x=(ot/2)%2; a=(ot/128)%2; t=(ot/2147483648)%2; r=(ot/65536)%32768; e=(ot/4)%32; } let compat=old_mint+sm+cm+((rr/2)%2)+t; v108_draw_small_u64(surface,((px+100)*65536)+(py+748),volatile_read64(xhci+3984)+(compat*0),green); v108_draw_small_u64(surface,((px+140)*65536)+(py+748),volatile_read64(xhci+3992),amber); v108_draw_small_u64(surface,((px+180)*65536)+(py+748),volatile_read64(xhci+4000),white); v108_draw_small_u64(surface,((px+220)*65536)+(py+748),x,green); v108_draw_small_u64(surface,((px+260)*65536)+(py+748),a,amber); v108_draw_small_u64(surface,((px+300)*65536)+(py+748),r,white); v108_draw_small_u64(surface,((px+340)*65536)+(py+748),e,green); }"
s=s[:rs]+newrow+s[re:]

arm2=fn_text(s,'v159_ehci_mouse_periodic_arm'); tick=fn_text(s,'v159_ehci_mouse_periodic_tick')
for q in (
    'let h_hcc=volatile_read32(h_base+8)','var leg_off=(h_hcc/256)%256','leg_cap%256==1',
    'bios_before=(leg_cap/65536)%2','os_before=(leg_cap/16777216)%2',
    'pci_cfg_write32(h_ebdf,leg_off,leg_cap+16777216)','pci_cfg_write32(h_ebdf,leg_off+4,0)',
    'handoff_code=1','handoff_code=2','volatile_write64(xhci_state+3984,handoff_code)',
    'hubvid==32903','hubpid==32768 || hubpid==32776','let info2=1090591745','let qcount:u64=24'):
    if q not in arm2: raise SystemExit('r68 handoff/persistent witness missing '+q)
for q in ('let idx=volatile_read64(xhci_state+4080)','let tok=volatile_read32(td+8)','let otok=volatile_read32(qh+24)','input_push(input_state,4,0,buttons)'):
    if q not in tick: raise SystemExit('r68 completion witness missing '+q)
if 'pci_cfg_write32(h_ebdf,208' in s or 'pci_cfg_write32(h_ebdf,212' in s:
    raise SystemExit('r68 must not write Intel xHCI routing registers')
for bad in ('write(10)','nvme_submit_write','ahci_write','fat_write','block_write'):
    if bad in (arm2+tick).lower(): raise SystemExit('r68 exceeds input-controller scope '+bad)
out=hashlib.sha256(s.encode()).hexdigest()
EXPECTED='b20e7b5414dd0059c451e64ecf2ec8a918d05b8e099dec712ee0e745dd7d2fbf'
if out!=EXPECTED: raise SystemExit('r68 output sha mismatch '+out)
p.write_text(s)
print(out)
