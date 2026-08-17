#!/usr/bin/env python3
from pathlib import Path
import hashlib, subprocess, sys
if len(sys.argv)!=2: raise SystemExit('usage: patch_v108_r39_g750jm_hid_idle_disabled_wifi_ro.py <kernel/main.nx>')
p=Path(sys.argv[1])
base=Path(__file__).with_name('patch_v108_r37b_stable_diag.py')
subprocess.run([sys.executable,str(base),str(p)],check=True,stdout=subprocess.DEVNULL)
s=p.read_text()
BASE='2cb422d2c7d00cdbb1da3eee4ee696c9ae0723b3f28669bf80efe256d14de650'
if hashlib.sha256(s.encode()).hexdigest()!=BASE: raise SystemExit('r37b base mismatch')

def rep(old,new,label,count=1):
    global s
    n=s.count(old)
    if n!=count: raise SystemExit(f'{label} count {n}, expected {count}')
    s=s.replace(old,new,count)

def fn_text(name):
    st=s.index('fn '+name); op=s.index('{',st); d=0
    for i in range(op,len(s)):
        if s[i]=='{': d+=1
        elif s[i]=='}':
            d-=1
            if d==0: return s[st:i+1]
    raise SystemExit('unterminated '+name)

def fnrep(name,new):
    rep(fn_text(name),new,name)

def label_fn(name,text):
    out=f'fn {name}(surface:u64,x:u64,y:u64,color:u64) -> u64 {{'
    for i,ch in enumerate(text):
        out+=f' if gui_draw_char_scaled(surface,((x+{i*6})*65536)+y,({ord(ch)}*65536)+1,color)==0 {{ return 0; }}'
    return out+' return 1; }\n'

rep('''    serial_usb_config_diag(22,interface_num);
    unsafe { volatile_write64(xhci_state+392,tring);''','''    serial_usb_config_diag(22,interface_num);
    let idle_setup=2593+(2048*65536)+(interface_num*4294967296); var idle_ok:u64=0; if xhci_control_no_data_out(xhci_state,idle_setup)!=0 { idle_ok=1; } unsafe { volatile_write64(xhci_state+2960,idle_ok); }
    unsafe { volatile_write64(xhci_state+392,tring);''','bounded HID SET_IDLE')

anchor='fn v136_hid_interrupt_recovery_tick(xhci_state:u64) -> u64 {'
helper=r'''fn v139_xhci_hid_reconfigure_disabled(xhci_state:u64) -> u64 {
    if xhci_state==0 || volatile_read64(xhci_state+416)!=1 { return 0; }
    if v136_xhci_endpoint_snapshot(xhci_state)!=0 { return 0; }
    if volatile_read64(xhci_state+2968)>=2 { return 0; }
    let input=volatile_read64(xhci_state+400); let ring=volatile_read64(xhci_state+392); let slot=volatile_read64(xhci_state+136); let ctxsize=volatile_read64(xhci_state+176); let dci=volatile_read64(xhci_state+352);
    if input==0 || ring==0 || slot==0 || ctxsize==0 || dci<2 || dci>31 { return 0; }
    let first=v137_xhci_hid_rebase_ring(xhci_state); if first==0 { return 0; }
    let ep=input+((dci+1)*ctxsize); unsafe { volatile_write64(ep+8,first); volatile_write64(xhci_state+2968,volatile_read64(xhci_state+2968)+1); }
    let done=xhci_command_submit_configure(xhci_state,input,slot); unsafe { volatile_write64(xhci_state+2976,done); volatile_write64(xhci_state+2984,volatile_read64(xhci_state+488)); }
    if done!=slot { return 0; }
    unsafe { volatile_write64(xhci_state+808,0); volatile_write64(xhci_state+2728,0); }
    return xhci_hid_arm_continuous(xhci_state,0);
}
'''+anchor
rep(anchor,helper,'disabled endpoint helper')

old=fn_text('v136_hid_interrupt_recovery_tick')
new=old.replace('''    let slot=volatile_read64(xhci_state+136); let dci=volatile_read64(xhci_state+352); let doorbells=volatile_read64(xhci_state+88); if slot==0 || dci<2 || dci>31 || doorbells==0 { return 1; }
    if state==1 {''','''    let slot=volatile_read64(xhci_state+136); let dci=volatile_read64(xhci_state+352); let doorbells=volatile_read64(xhci_state+88); if slot==0 || dci<2 || dci>31 || doorbells==0 { return 1; }
    if state==0 { v139_xhci_hid_reconfigure_disabled(xhci_state); return 1; }
    if state==1 {''',1)
if new==old: raise SystemExit('disabled endpoint invocation anchor missing')
fnrep('v136_hid_interrupt_recovery_tick',new)

overlay='fn v108_input_overlay_draw(surface:u64,state:u64,input_state:u64,xhci:u64) -> u64 {'
wifi=r'''fn v139_wifi_pci_discover_ro(xhci:u64) -> u64 {
    if xhci==0 { return 0; }
    if volatile_read64(xhci+3000)!=0 { return volatile_read64(xhci+3008); }
    unsafe { volatile_write64(xhci+3000,1); volatile_write64(xhci+3008,0); }
    var bus:u64=0;
    while bus<32 {
        var dev:u64=0;
        while dev<32 {
            var fun:u64=0;
            while fun<8 {
                let id=pci_cfg_read32(bus,dev,fun,0); let vendor=id%65536;
                if vendor!=65535 && vendor!=0 {
                    let cls=pci_cfg_read32(bus,dev,fun,8); let base=(cls/16777216)%256; let sub=(cls/65536)%256;
                    if base==2 && sub==128 {
                        unsafe { volatile_write64(xhci+3008,1); volatile_write64(xhci+3016,vendor); volatile_write64(xhci+3024,(id/65536)%65536); volatile_write64(xhci+3032,bus); volatile_write64(xhci+3040,dev); volatile_write64(xhci+3048,fun); volatile_write64(xhci+3056,sub); }
                        return 1;
                    }
                }
                fun=fun+1;
            }
            dev=dev+1;
        }
        bus=bus+1;
    }
    return 0;
}
'''+label_fn('v139_text_r39_v139','R39 S Q I R C E')+label_fn('v139_text_wifi_v139','WIFI P V D B N F')+overlay
rep(overlay,wifi,'Wi-Fi discovery helpers')

rep('''    let py:u64=8; let bg:u64=4279308561; let edge:u64=4283268350; let white:u64=4294244347; let green:u64=4286644030; let amber:u64=4294934528; let red:u64=4294907956;
    if display_fill_rect(surface,(px*65536)+py,(410*65536)+760,bg)==0 { return 0; }''','''    let py:u64=8; let bg:u64=4279308561; let edge:u64=4283268350; let white:u64=4294244347; let green:u64=4286644030; let amber:u64=4294934528; let red:u64=4294907956;
    if xhci!=0 { v139_wifi_pci_discover_ro(xhci); }
    if display_fill_rect(surface,(px*65536)+py,(410*65536)+780,bg)==0 { return 0; }''','Wi-Fi scan and overlay height')

rep('''    v108_text_r37_v137(surface,px+10,py+730,white); if xhci!=0 { v108_draw_small_u64(surface,((px+112)*65536)+(py+730),volatile_read64(xhci+2696),green); v108_draw_small_u64(surface,((px+160)*65536)+(py+730),volatile_read64(xhci+2824),amber); v108_draw_small_u64(surface,((px+208)*65536)+(py+730),volatile_read64(xhci+2832),white); v108_draw_small_u64(surface,((px+256)*65536)+(py+730),volatile_read64(xhci+2728),white); v108_draw_small_u64(surface,((px+316)*65536)+(py+730),volatile_read64(xhci+2816),green); v108_draw_small_u64(surface,((px+376)*65536)+(py+730),volatile_read64(xhci+2784),red); }
    return 1;''','''    v139_text_r39_v139(surface,px+10,py+730,white); if xhci!=0 { v108_draw_small_u64(surface,((px+112)*65536)+(py+730),volatile_read64(xhci+2696),green); v108_draw_small_u64(surface,((px+160)*65536)+(py+730),volatile_read64(xhci+2824),amber); v108_draw_small_u64(surface,((px+208)*65536)+(py+730),volatile_read64(xhci+2960),green); v108_draw_small_u64(surface,((px+256)*65536)+(py+730),volatile_read64(xhci+2968),white); v108_draw_small_u64(surface,((px+316)*65536)+(py+730),volatile_read64(xhci+2976),green); v108_draw_small_u64(surface,((px+376)*65536)+(py+730),volatile_read64(xhci+2784),red); }
    v139_text_wifi_v139(surface,px+10,py+748,white); if xhci!=0 { v108_draw_small_u64(surface,((px+112)*65536)+(py+748),volatile_read64(xhci+3008),green); v108_draw_small_u64(surface,((px+160)*65536)+(py+748),volatile_read64(xhci+3016),white); v108_draw_small_u64(surface,((px+220)*65536)+(py+748),volatile_read64(xhci+3024),white); v108_draw_small_u64(surface,((px+280)*65536)+(py+748),volatile_read64(xhci+3032),amber); v108_draw_small_u64(surface,((px+322)*65536)+(py+748),volatile_read64(xhci+3040),amber); v108_draw_small_u64(surface,((px+364)*65536)+(py+748),volatile_read64(xhci+3048),amber); }
    return 1;''','r39 and Wi-Fi rows')

rep('(410*65536)+760','(410*65536)+780','full overlay geometry',12)

rep('''    v108_text_r37_v137(surface,px+10,py+730,white);
    if xhci!=0 {
        v108_draw_small_u64(surface,((px+112)*65536)+(py+730),volatile_read64(xhci+2696),green);
        v108_draw_small_u64(surface,((px+160)*65536)+(py+730),volatile_read64(xhci+2824),amber);
        v108_draw_small_u64(surface,((px+208)*65536)+(py+730),volatile_read64(xhci+2832),white);
        v108_draw_small_u64(surface,((px+256)*65536)+(py+730),volatile_read64(xhci+2728),white);
        v108_draw_small_u64(surface,((px+316)*65536)+(py+730),volatile_read64(xhci+2816),green);
        v108_draw_small_u64(surface,((px+376)*65536)+(py+730),volatile_read64(xhci+2784),red);
    }''','''    v139_text_r39_v139(surface,px+10,py+730,white);
    if xhci!=0 {
        v108_draw_small_u64(surface,((px+112)*65536)+(py+730),volatile_read64(xhci+2696),green);
        v108_draw_small_u64(surface,((px+160)*65536)+(py+730),volatile_read64(xhci+2824),amber);
        v108_draw_small_u64(surface,((px+208)*65536)+(py+730),volatile_read64(xhci+2960),green);
        v108_draw_small_u64(surface,((px+256)*65536)+(py+730),volatile_read64(xhci+2968),white);
        v108_draw_small_u64(surface,((px+316)*65536)+(py+730),volatile_read64(xhci+2976),green);
        v108_draw_small_u64(surface,((px+376)*65536)+(py+730),volatile_read64(xhci+2784),red);
    }''','isolated r39 row')

if 'pci_cfg_write32' in fn_text('v139_wifi_pci_discover_ro'): raise SystemExit('Wi-Fi discovery is not read-only')
if s.count('{')!=s.count('}'): raise SystemExit('brace mismatch')
out=hashlib.sha256(s.encode()).hexdigest()
EXPECTED='ba873c5bcfb810faa6210f440832ad359c5e91c012541fc2431c2bd1acb3a8d1'
if out!=EXPECTED: raise SystemExit(f'r39 output sha mismatch {out}')
p.write_text(s)
print(out)
