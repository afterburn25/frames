#!/usr/bin/env python3
from pathlib import Path
import hashlib,subprocess,sys
if len(sys.argv)!=2: raise SystemExit('usage: patch_v108_r31_hid_runtime_rearm.py <kernel/main.nx>')
p=Path(sys.argv[1]); base=Path(__file__).with_name('patch_v108_r30b_hid_first_device_state.py')
subprocess.run([sys.executable,str(base),str(p)],check=True,stdout=subprocess.DEVNULL)
s=p.read_text()
BASE='d947d603112369340749e6be8397bfed08bf1de49651a0a0602571afcb754c3b'
if hashlib.sha256(s.encode()).hexdigest()!=BASE: raise SystemExit('r30b base mismatch')

def rep(old,new,label):
 global s
 n=s.count(old)
 if n!=1: raise SystemExit(f'{label}: {n}')
 s=s.replace(old,new,1)

def label_fn(name,text):
 out=f'fn {name}(surface:u64,x:u64,y:u64,color:u64) -> u64 {{'
 for i,ch in enumerate(text):
  out+=f' if gui_draw_char_scaled(surface,((x+{i*6})*65536)+y,({ord(ch)}*65536)+1,color)==0 {{ return 0; }}'
 return out+' return 1; }\n'

# Seed runtime-HID diagnostics with the selected device identity when configuration succeeds.
old='''unsafe { volatile_write64(xhci_state+392,tring); volatile_write64(xhci_state+400,input); volatile_write64(xhci_state+408,0); volatile_write64(xhci_state+416,1); volatile_write64(xhci_state+424,interval); volatile_write64(xhci_state+480,1); volatile_write64(xhci_state+800,1); volatile_write64(xhci_state+808,0); volatile_write64(xhci_state+816,0); volatile_write64(xhci_state+824,0); volatile_write64(xhci_state+832,0); volatile_write64(xhci_state+1216,0); volatile_write64(xhci_state+1224,0); volatile_write64(xhci_state+1232,0); volatile_write64(xhci_state+1328,0); volatile_write64(xhci_state+1248,0); volatile_write64(xhci_state+1256,0); }'''
new='''unsafe { volatile_write64(xhci_state+392,tring); volatile_write64(xhci_state+400,input); volatile_write64(xhci_state+408,0); volatile_write64(xhci_state+416,1); volatile_write64(xhci_state+424,interval); volatile_write64(xhci_state+480,1); volatile_write64(xhci_state+800,1); volatile_write64(xhci_state+808,0); volatile_write64(xhci_state+816,0); volatile_write64(xhci_state+824,0); volatile_write64(xhci_state+832,0); volatile_write64(xhci_state+1216,0); volatile_write64(xhci_state+1224,0); volatile_write64(xhci_state+1232,0); volatile_write64(xhci_state+1328,0); volatile_write64(xhci_state+1248,0); volatile_write64(xhci_state+1256,0); volatile_write64(xhci_state+2176,0); volatile_write64(xhci_state+2184,0); volatile_write64(xhci_state+2192,0); volatile_write64(xhci_state+2200,0); volatile_write64(xhci_state+2208,0); volatile_write64(xhci_state+2216,0); volatile_write64(xhci_state+2224,0); volatile_write64(xhci_state+2232,0); volatile_write64(xhci_state+2240,volatile_read64(xhci_state+272)); volatile_write64(xhci_state+2248,volatile_read64(xhci_state+280)); volatile_write64(xhci_state+2256,slot); volatile_write64(xhci_state+2264,dci); volatile_write64(xhci_state+2272,mps); volatile_write64(xhci_state+2280,interval); volatile_write64(xhci_state+2288,volatile_read64(xhci_state+112)); volatile_write64(xhci_state+2296,0); volatile_write64(xhci_state+2304,0); }'''
rep(old,new,'hid runtime diag init')

# Arm as soon as HID configuration completes instead of waiting for the desktop/PS2 setup path.
old='''let usbsel=v108_xhci_scan_pointer_v116(hardware_state,phys_state,xhci_state,kernel_pml4);\n            if usbsel!=0 { xhci_ready=1; }'''
new='''let usbsel=v108_xhci_scan_pointer_v116(hardware_state,phys_state,xhci_state,kernel_pml4);\n            if usbsel>=2 && volatile_read64(xhci_state+416)==1 && volatile_read64(xhci_state+808)==0 { xhci_hid_arm_continuous(xhci_state,phys_state); }\n            if usbsel!=0 { xhci_ready=1; }'''
rep(old,new,'early HID arm')

# Count arms/doorbells and freeze the selected runtime endpoint identity.
old='''tail=tail+1; unsafe { volatile_write64(xhci_state+408,tail); volatile_write64(xhci_state+800,cycle); volatile_write64(xhci_state+808,1); volatile_write32(doorbells+(slot*4),dci); }\n    if volatile_read64(xhci_state+832)==0'''
new='''tail=tail+1; unsafe { volatile_write64(xhci_state+408,tail); volatile_write64(xhci_state+800,cycle); volatile_write64(xhci_state+808,1); volatile_write64(xhci_state+2176,volatile_read64(xhci_state+2176)+1); volatile_write64(xhci_state+2184,volatile_read64(xhci_state+2184)+1); volatile_write64(xhci_state+2192,1); volatile_write64(xhci_state+2256,slot); volatile_write64(xhci_state+2264,dci); volatile_write64(xhci_state+2272,packet); volatile_write64(xhci_state+2280,volatile_read64(xhci_state+424)); volatile_write64(xhci_state+2288,volatile_read64(xhci_state+112)); volatile_write64(xhci_state+2296,0); volatile_write32(doorbells+(slot*4),dci); }\n    if volatile_read64(xhci_state+832)==0'''
rep(old,new,'arm telemetry')

# Make the continuous poll fail-soft and re-ring a pending transfer periodically.
old='''let slot=volatile_read64(xhci_state+136); let dci=volatile_read64(xhci_state+352); let packet=volatile_read64(xhci_state+360); var code:u64=0; var residue:u64=0; var matched:u64=0;'''
new='''let slot=volatile_read64(xhci_state+136); let dci=volatile_read64(xhci_state+352); let packet=volatile_read64(xhci_state+360); let doorbells=volatile_read64(xhci_state+88); unsafe { volatile_write64(xhci_state+2200,volatile_read64(xhci_state+2200)+1); } var code:u64=0; var residue:u64=0; var matched:u64=0;'''
rep(old,new,'poll telemetry header')
old='''let trb=event_ring+(index*16); let control=volatile_read32(trb+12); if control%2!=cycle { return 1; }'''
new='''let trb=event_ring+(index*16); let control=volatile_read32(trb+12); if control%2!=cycle { var idle=volatile_read64(xhci_state+2296)+1; if idle>=500000 { unsafe { volatile_write32(doorbells+(slot*4),dci); volatile_write64(xhci_state+2184,volatile_read64(xhci_state+2184)+1); volatile_write64(xhci_state+2296,0); } } else { unsafe { volatile_write64(xhci_state+2296,idle); } } return 1; }'''
rep(old,new,'pending doorbell recovery')
old='''unsafe { volatile_write64(xhci_state+808,0); }\n    if (code!=1 && code!=13) || residue>packet { return 0; }\n    let actual=packet-residue; let protocol=volatile_read64(xhci_state+336); if actual==0 || (protocol==1 && actual<8) || (protocol==2 && actual<3) { return 0; }'''
new='''unsafe { volatile_write64(xhci_state+808,0); volatile_write64(xhci_state+2192,0); volatile_write64(xhci_state+2208,volatile_read64(xhci_state+2208)+1); volatile_write64(xhci_state+2216,code); volatile_write64(xhci_state+2224,residue); volatile_write64(xhci_state+2296,0); }\n    if (code!=1 && code!=13) || residue>packet { unsafe { volatile_write64(xhci_state+2304,volatile_read64(xhci_state+2304)+1); } return xhci_hid_arm_continuous(xhci_state,0); }\n    let actual=packet-residue; unsafe { volatile_write64(xhci_state+2232,actual); } let protocol=volatile_read64(xhci_state+336); if actual==0 || (protocol==1 && actual<8) || (protocol==2 && actual<3) { unsafe { volatile_write64(xhci_state+2304,volatile_read64(xhci_state+2304)+1); } return xhci_hid_arm_continuous(xhci_state,0); }'''
rep(old,new,'fail-soft completion')
old='''if input_decode_boot_hid(xhci_state,input_state)==0 { return 0; }'''
new='''if input_decode_boot_hid(xhci_state,input_state)==0 { unsafe { volatile_write64(xhci_state+2304,volatile_read64(xhci_state+2304)+1); } return xhci_hid_arm_continuous(xhci_state,0); }'''
rep(old,new,'fail-soft decode')

# Replace the r30 second-device rows with runtime transfer evidence that survives after HID selection.
labels=label_fn('v108_text_urun_v131','URUN A P E C N')+label_fn('v108_text_uhid_v131','UHID V P S E K I')
rep('fn v108_input_overlay_draw(surface:u64,state:u64,input_state:u64,xhci:u64) -> u64 {',labels+'fn v108_input_overlay_draw(surface:u64,state:u64,input_state:u64,xhci:u64) -> u64 {','r31 labels')
old='''v108_text_x2a_v130(surface,px+10,py+622,white); if xhci!=0 { v108_draw_small_u64(surface,((px+112)*65536)+(py+622),volatile_read64(xhci+2080),amber); v108_draw_small_u64(surface,((px+166)*65536)+(py+622),volatile_read64(xhci+2088),white); v108_draw_small_u64(surface,((px+220)*65536)+(py+622),volatile_read64(xhci+2096),amber); v108_draw_small_u64(surface,((px+280)*65536)+(py+622),volatile_read64(xhci+2104),red); v108_draw_small_u64(surface,((px+340)*65536)+(py+622),volatile_read64(xhci+2112),red); }\n    v108_text_x2f_v130(surface,px+10,py+640,white); if xhci!=0 { v108_draw_small_u64(surface,((px+112)*65536)+(py+640),volatile_read64(xhci+2120),white); v108_draw_small_u64(surface,((px+184)*65536)+(py+640),volatile_read64(xhci+2128),white); v108_draw_small_u64(surface,((px+256)*65536)+(py+640),volatile_read64(xhci+2136),green); v108_draw_small_u64(surface,((px+304)*65536)+(py+640),volatile_read64(xhci+2144),green); v108_draw_small_u64(surface,((px+352)*65536)+(py+640),volatile_read64(xhci+2152),green); }'''
new='''v108_text_urun_v131(surface,px+10,py+622,white); if xhci!=0 { v108_draw_small_u64(surface,((px+112)*65536)+(py+622),volatile_read64(xhci+2176),amber); v108_draw_small_u64(surface,((px+166)*65536)+(py+622),volatile_read64(xhci+2192),white); v108_draw_small_u64(surface,((px+220)*65536)+(py+622),volatile_read64(xhci+2208),green); v108_draw_small_u64(surface,((px+280)*65536)+(py+622),volatile_read64(xhci+2216),red); v108_draw_small_u64(surface,((px+340)*65536)+(py+622),volatile_read64(xhci+2232),green); }\n    v108_text_uhid_v131(surface,px+10,py+640,white); if xhci!=0 { v108_draw_small_u64(surface,((px+112)*65536)+(py+640),volatile_read64(xhci+2240),white); v108_draw_small_u64(surface,((px+184)*65536)+(py+640),volatile_read64(xhci+2248),white); v108_draw_small_u64(surface,((px+256)*65536)+(py+640),volatile_read64(xhci+2256),green); v108_draw_small_u64(surface,((px+304)*65536)+(py+640),volatile_read64(xhci+2264),green); v108_draw_small_u64(surface,((px+352)*65536)+(py+640),volatile_read64(xhci+2272),green); v108_draw_small_u64(surface,((px+388)*65536)+(py+640),volatile_read64(xhci+2280),green); }'''
rep(old,new,'runtime overlay rows')

if s.count('{')!=s.count('}'): raise SystemExit('brace imbalance')
expected='10f1ebafec755666d4432d49c237b78cd7e9bc0a67cc4fe2a08351ebe42d5117'
actual=hashlib.sha256(s.encode()).hexdigest()
if actual!=expected: raise SystemExit(f'r31 identity mismatch {actual}')
p.write_text(s); print(actual)
