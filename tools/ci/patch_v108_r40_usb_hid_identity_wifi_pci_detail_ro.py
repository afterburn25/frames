#!/usr/bin/env python3
from pathlib import Path
import hashlib, subprocess, sys
if len(sys.argv)!=2: raise SystemExit('usage: patch_v108_r40_usb_hid_identity_wifi_pci_detail_ro.py <kernel/main.nx>')
p=Path(sys.argv[1])
base=Path(__file__).with_name('patch_v108_r39b_g750jm_hid_idle_1s_wifi_ro.py')
subprocess.run([sys.executable,str(base),str(p)],check=True,stdout=subprocess.DEVNULL)
s=p.read_text()
BASE='7ca4e51896453e0bcaa131d7f4497e64e95556cb96941c599fa4151eb71bbea5'
if hashlib.sha256(s.encode()).hexdigest()!=BASE: raise SystemExit('r39b base mismatch')

def rep(old,new,label):
    global s
    n=s.count(old)
    if n!=1: raise SystemExit(f'{label} count {n}')
    s=s.replace(old,new,1)

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
    return out+' return 1; }'

# r39b proved that SET_IDLE keeps the selected HID endpoint Running, but the
# physical G750JM still produced no interrupt completion. Do not alter the
# recovered USB/touchpad path again until we know exactly which USB mouse is
# selected. Surface the already-read device descriptor VID/PID and protocol.
#
# The r39b read-only network-class scan found 14e4:43b1. Extend that same
# read-only PCI config-space probe with subsystem/revision/resource telemetry.
# No BAR mapping, PCI command writes, bus mastering changes, firmware upload,
# radio control, association, or packet I/O is permitted in r40.
anchor='fn v139_text_r39_v139(surface:u64,x:u64,y:u64,color:u64) -> u64 {'
insert=r'''fn v140_wifi_pci_detail_ro(xhci:u64) -> u64 {
    if xhci==0 || volatile_read64(xhci+3008)==0 { return 0; }
    if volatile_read64(xhci+3120)!=0 { return 1; }
    let bus=volatile_read64(xhci+3032); let dev=volatile_read64(xhci+3040); let fun=volatile_read64(xhci+3048);
    let id=pci_cfg_read32(bus,dev,fun,0); let vendor=id%65536; let device=(id/65536)%65536;
    if vendor!=volatile_read64(xhci+3016) || device!=volatile_read64(xhci+3024) { return 0; }
    let revclass=pci_cfg_read32(bus,dev,fun,8); let subsys=pci_cfg_read32(bus,dev,fun,44);
    let bar0=pci_cfg_read32(bus,dev,fun,16); let bar1=pci_cfg_read32(bus,dev,fun,20); let cmdstat=pci_cfg_read32(bus,dev,fun,4); let irq=pci_cfg_read32(bus,dev,fun,60);
    unsafe {
        volatile_write64(xhci+3064,revclass%256); volatile_write64(xhci+3072,subsys%65536); volatile_write64(xhci+3080,(subsys/65536)%65536);
        volatile_write64(xhci+3088,bar0); volatile_write64(xhci+3096,bar1); volatile_write64(xhci+3104,cmdstat); volatile_write64(xhci+3112,irq); volatile_write64(xhci+3120,1);
    }
    return 1;
}
'''+label_fn('v140_text_r40_v140','R40 S I H V P E')+'\n'+label_fn('v140_text_wifi_v140','W40 V D SV SD R')+'\n'+anchor
rep(anchor,insert,'r40 read-only detail helpers')

rep('if xhci!=0 { v139_wifi_pci_discover_ro(xhci); }',
    'if xhci!=0 { v139_wifi_pci_discover_ro(xhci); v140_wifi_pci_detail_ro(xhci); }',
    'r40 WiFi detail integration')

old='''    v139_text_r39_v139(surface,px+10,py+730,white); if xhci!=0 { v108_draw_small_u64(surface,((px+112)*65536)+(py+730),volatile_read64(xhci+2696),green); v108_draw_small_u64(surface,((px+160)*65536)+(py+730),volatile_read64(xhci+2824),amber); v108_draw_small_u64(surface,((px+208)*65536)+(py+730),volatile_read64(xhci+2960),green); v108_draw_small_u64(surface,((px+256)*65536)+(py+730),volatile_read64(xhci+2968),white); v108_draw_small_u64(surface,((px+316)*65536)+(py+730),volatile_read64(xhci+2976),green); v108_draw_small_u64(surface,((px+376)*65536)+(py+730),volatile_read64(xhci+2784),red); }
    v139_text_wifi_v139(surface,px+10,py+748,white); if xhci!=0 { v108_draw_small_u64(surface,((px+112)*65536)+(py+748),volatile_read64(xhci+3008),green); v108_draw_small_u64(surface,((px+160)*65536)+(py+748),volatile_read64(xhci+3016),white); v108_draw_small_u64(surface,((px+220)*65536)+(py+748),volatile_read64(xhci+3024),white); v108_draw_small_u64(surface,((px+280)*65536)+(py+748),volatile_read64(xhci+3032),amber); v108_draw_small_u64(surface,((px+322)*65536)+(py+748),volatile_read64(xhci+3040),amber); v108_draw_small_u64(surface,((px+364)*65536)+(py+748),volatile_read64(xhci+3048),amber); }'''
new='''    v140_text_r40_v140(surface,px+10,py+730,white); if xhci!=0 { v108_draw_small_u64(surface,((px+112)*65536)+(py+730),volatile_read64(xhci+2696),green); v108_draw_small_u64(surface,((px+150)*65536)+(py+730),volatile_read64(xhci+2960),green); v108_draw_small_u64(surface,((px+188)*65536)+(py+730),volatile_read64(xhci+336),white); v108_draw_small_u64(surface,((px+226)*65536)+(py+730),volatile_read64(xhci+272),white); v108_draw_small_u64(surface,((px+290)*65536)+(py+730),volatile_read64(xhci+280),white); v108_draw_small_u64(surface,((px+370)*65536)+(py+730),volatile_read64(xhci+2784),red); }
    v140_text_wifi_v140(surface,px+10,py+748,white); if xhci!=0 { v108_draw_small_u64(surface,((px+112)*65536)+(py+748),volatile_read64(xhci+3016),white); v108_draw_small_u64(surface,((px+170)*65536)+(py+748),volatile_read64(xhci+3024),white); v108_draw_small_u64(surface,((px+232)*65536)+(py+748),volatile_read64(xhci+3072),white); v108_draw_small_u64(surface,((px+300)*65536)+(py+748),volatile_read64(xhci+3080),white); v108_draw_small_u64(surface,((px+376)*65536)+(py+748),volatile_read64(xhci+3064),amber); }'''
rep(old,new,'r40 full physical rows')

old=fn_text('v108_input_overlay_r37_draw_v137')
new=old.replace('''    v139_text_r39_v139(surface,px+10,py+730,white);
    if xhci!=0 {
        v108_draw_small_u64(surface,((px+112)*65536)+(py+730),volatile_read64(xhci+2696),green);
        v108_draw_small_u64(surface,((px+160)*65536)+(py+730),volatile_read64(xhci+2824),amber);
        v108_draw_small_u64(surface,((px+208)*65536)+(py+730),volatile_read64(xhci+2960),green);
        v108_draw_small_u64(surface,((px+256)*65536)+(py+730),volatile_read64(xhci+2968),white);
        v108_draw_small_u64(surface,((px+316)*65536)+(py+730),volatile_read64(xhci+2976),green);
        v108_draw_small_u64(surface,((px+376)*65536)+(py+730),volatile_read64(xhci+2784),red);
    }''','''    v140_text_r40_v140(surface,px+10,py+730,white);
    if xhci!=0 {
        v108_draw_small_u64(surface,((px+112)*65536)+(py+730),volatile_read64(xhci+2696),green);
        v108_draw_small_u64(surface,((px+150)*65536)+(py+730),volatile_read64(xhci+2960),green);
        v108_draw_small_u64(surface,((px+188)*65536)+(py+730),volatile_read64(xhci+336),white);
        v108_draw_small_u64(surface,((px+226)*65536)+(py+730),volatile_read64(xhci+272),white);
        v108_draw_small_u64(surface,((px+290)*65536)+(py+730),volatile_read64(xhci+280),white);
        v108_draw_small_u64(surface,((px+370)*65536)+(py+730),volatile_read64(xhci+2784),red);
    }''')
if new==old: raise SystemExit('r40 isolated HID identity row anchor missing')
fnrep('v108_input_overlay_r37_draw_v137',new)

wifi=fn_text('v140_wifi_pci_detail_ro')
if 'pci_cfg_write32' in wifi: raise SystemExit('r40 WiFi detail probe is not read-only')
if 'volatile_write32' in wifi: raise SystemExit('r40 WiFi detail probe unexpectedly writes MMIO/config')
if s.count('{')!=s.count('}'): raise SystemExit('brace mismatch')
out=hashlib.sha256(s.encode()).hexdigest()
EXPECTED='ae9598872e6806907e8bb623050f4314dbdda140ecd6b9c620f36e1c669b4c6c'
if out!=EXPECTED: raise SystemExit(f'r40 output sha mismatch {out}')
p.write_text(s)
print(out)
