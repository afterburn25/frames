#!/usr/bin/env python3
from pathlib import Path
import hashlib, subprocess, sys

if len(sys.argv)!=2:
    raise SystemExit('usage: patch_v108_r61_altsetting_reset_tt_boot_mouse.py <kernel/main.nx>')
p=Path(sys.argv[1]); here=Path(__file__).parent
base=here/'patch_v108_r60_reference_ehci_boot_mouse.py'
subprocess.run([sys.executable,str(base),str(p)],check=True,stdout=subprocess.DEVNULL)
s=p.read_text()
BASE='dc1d8d0590965f6d499eba0fe2d010287d6052d2c7ceab73dff41120fadcc04d'
actual=hashlib.sha256(s.encode()).hexdigest()
if actual!=BASE:
    raise SystemExit('r61 exact r60 base mismatch '+actual)

def fn_text(src,name):
    st=src.index('fn '+name); op=src.index('{',st); d=0
    for i in range(op,len(src)):
        if src[i]=='{': d+=1
        elif src[i]=='}':
            d-=1
            if d==0: return src[st:i+1]
    raise SystemExit('unterminated '+name)

def label_fn(name,text):
    out=f'fn {name}(surface:u64,x:u64,y:u64,color:u64) -> u64 {{'
    for i,ch in enumerate(text):
        out+=f' if gui_draw_char_scaled(surface,((x+{i*6})*65536)+y,({ord(ch)}*65536)+1,color)==0 {{ return 0; }}'
    return out+' return 1; }'

# r59t2 proved that moving the interrupt-IN qTD onto the async list does not
# change the physical failure: both qTD and QH overlay remain Active with all
# eight bytes outstanding. Return to the standards-correct periodic model from
# r60, but prove two device/TT preconditions before arming it:
#   1. discover the alternate setting that actually owns endpoint 0x82 and
#      issue SET_INTERFACE if it is non-zero;
#   2. issue USB 2.0 HUB_RESET_TT after the child control setup, immediately
#      before installing the periodic QH.
arm=fn_text(s,'v159_ehci_mouse_periodic_arm')
old="let kep=volatile_read64(xhci_state+3936); let mep=volatile_read64(xhci_state+3944); let mif=volatile_read64(xhci_state+3952); let mmps=volatile_read64(xhci_state+3960); let hids=volatile_read64(xhci_state+3968); let mint=volatile_read64(xhci_state+3976); let cfg=volatile_read64(xhci_state+4008); let speed=volatile_read64(xhci_state+4024); let dma=volatile_read64(xhci_state+4040);"
new="let kep=volatile_read64(xhci_state+3936); let mep=volatile_read64(xhci_state+3944); let mif=volatile_read64(xhci_state+3952); let mmps=volatile_read64(xhci_state+3960); let hids=volatile_read64(xhci_state+3968); let mint=volatile_read64(xhci_state+3976); let cfg=volatile_read64(xhci_state+4008); let total=volatile_read64(xhci_state+4016); let speed=volatile_read64(xhci_state+4024); let dma=volatile_read64(xhci_state+4040); let port=volatile_read64(xhci_state+3928);"
if arm.count(old)!=1: raise SystemExit('r61 arm declaration anchor mismatch '+str(arm.count(old)))
arm=arm.replace(old,new,1)
old="if kep==0 || mep<128 || (mep%128)==0 || mif>31 || mmps==0 || mmps>64 || hids<2 || mint==0 || mint>255 || cfg==0 || speed>1 || dma==0 { unsafe { volatile_write64(xhci_state+4056,11); } return 11; }\n    let ep0mps:u64=8; unsafe { volatile_write64(xhci_state+3936,ep0mps); }\n"
new="""if kep==0 || mep<128 || (mep%128)==0 || mif>31 || mmps==0 || mmps>64 || hids<2 || mint==0 || mint>255 || cfg==0 || total<9 || total>256 || speed>1 || dma==0 || port==0 || port>15 { unsafe { volatile_write64(xhci_state+4056,11); } return 11; }
    let ep0mps:u64=8; unsafe { volatile_write64(xhci_state+3936,ep0mps); }
    let full_setup=usb_setup_length_v113(usb_setup_value_v113(128,6,512,0),total); var rc=v157_ehci_tt_control(xhci_state,2,full_setup,total); if rc!=1 { unsafe { volatile_write64(xhci_state+3936,kep); volatile_write64(xhci_state+4056,31); volatile_write64(xhci_state+4000,rc); } return 31; }
    let data0=dma+576; var off0:u64=0; var alt_active:u64=0; var malt:u64=0; var epfound:u64=0;
    while off0+2<=total { let dl0=volatile_read8(data0+off0); let dt0=volatile_read8(data0+off0+1); if dl0<2 || off0+dl0>total { off0=total; } else { if dt0==4 && dl0>=9 { let if0=volatile_read8(data0+off0+2); let al0=volatile_read8(data0+off0+3); let ic0=volatile_read8(data0+off0+5); let sub0=volatile_read8(data0+off0+6); let pr0=volatile_read8(data0+off0+7); alt_active=0; if if0==mif && ic0==3 && sub0==1 && pr0==2 { alt_active=1; malt=al0; } } if dt0==5 && dl0>=7 && alt_active!=0 { let ea0=volatile_read8(data0+off0+2); let at0=volatile_read8(data0+off0+3); if ea0==mep && at0%4==3 { epfound=1; } } off0=off0+dl0; } }
    if epfound==0 { unsafe { volatile_write64(xhci_state+3936,kep); volatile_write64(xhci_state+4056,32); volatile_write64(xhci_state+3984,malt); } return 32; }
"""
if arm.count(old)!=1: raise SystemExit('r61 alternate-setting scan anchor mismatch '+str(arm.count(old)))
arm=arm.replace(old,new,1)
old="let setcfg=2304+(cfg*65536); var rc=v157_ehci_tt_control(xhci_state,2,setcfg,0); if rc!=1 { unsafe { volatile_write64(xhci_state+3936,kep); volatile_write64(xhci_state+4056,12); volatile_write64(xhci_state+4000,rc); } return 12; }\n    pit_wait(23864);\n    let setproto="
new="""let setcfg=2304+(cfg*65536); rc=v157_ehci_tt_control(xhci_state,2,setcfg,0); if rc!=1 { unsafe { volatile_write64(xhci_state+3936,kep); volatile_write64(xhci_state+4056,12); volatile_write64(xhci_state+4000,rc); } return 12; }
    pit_wait(23864);
    var ifrc:u64=0; if malt!=0 { let setif=1+(11*256)+(malt*65536)+(mif*4294967296); ifrc=v157_ehci_tt_control(xhci_state,2,setif,0); if ifrc!=1 { unsafe { volatile_write64(xhci_state+3936,kep); volatile_write64(xhci_state+4056,33); volatile_write64(xhci_state+3984,malt); volatile_write64(xhci_state+3992,ifrc); } return 33; } pit_wait(23864); }
    let setproto="""
if arm.count(old)!=1: raise SystemExit('r61 SET_INTERFACE anchor mismatch '+str(arm.count(old)))
arm=arm.replace(old,new,1)
old="""if volatile_read8(dma+576)!=0 { unsafe { volatile_write64(xhci_state+3936,kep); volatile_write64(xhci_state+4056,29); volatile_write64(xhci_state+4000,volatile_read8(dma+576)); } return 29; }
    unsafe { volatile_write64(xhci_state+3984,0); volatile_write64(xhci_state+3992,0); }
    unsafe { volatile_write64(xhci_state+3936,kep); }
"""
new="""if volatile_read8(dma+576)!=0 { unsafe { volatile_write64(xhci_state+3936,kep); volatile_write64(xhci_state+4056,29); volatile_write64(xhci_state+4000,volatile_read8(dma+576)); } return 29; }
    unsafe { volatile_write64(xhci_state+3984,0); volatile_write64(xhci_state+3992,0); }
    unsafe { volatile_write64(xhci_state+3936,kep); }
    var hubproto:u64=0; var hrc=v155_ehci_control(xhci_state,1,5066549597570688,18); if hrc==1 { if volatile_read8(dma+577)==1 { hubproto=volatile_read8(dma+582); } }
    var ttidx:u64=1; if hubproto==2 { ttidx=port; } let resettt=35+(9*256)+(ttidx*4294967296); var ttrc=v155_ehci_control(xhci_state,1,resettt,0); pit_wait(23864);
    unsafe { volatile_write64(xhci_state+3984,malt); volatile_write64(xhci_state+3992,ifrc); volatile_write64(xhci_state+4000,ttrc); }
"""
if arm.count(old)!=1: raise SystemExit('r61 RESET_TT anchor mismatch '+str(arm.count(old)))
arm=arm.replace(old,new,1)
s=s.replace(fn_text(s,'v159_ehci_mouse_periodic_arm'),arm,1)

# Preserve the r60 completion-to-pointer path, but make this test maximally
# diagnostic if the transfer is still blocked. G uses the same execution-state
# encoding as r59t2 so the periodic and async experiments can be compared:
# bit contributions: qTD Active 2, overlay Active 4, SplitX 8, errors*16,
# qTD remaining*1024, overlay remaining*32768.
s=s.replace(fn_text(s,'v140_text_wifi_v140'),label_fn('v140_text_wifi_v140','R61 A I T G N B X'),1)
rs=s.index('v140_text_wifi_v140(surface,px+10,py+748,white);')
re=s.index('\n    return 1;\n}',rs)
newrow="v140_text_wifi_v140(surface,px+10,py+748,white); if xhci!=0 { let rr=volatile_read64(xhci+4080); let dm=volatile_read64(xhci+4040); var sm:u64=0; var cm:u64=0; var gate:u64=0; if dm!=0 { let qi=volatile_read32(dm+8); sm=qi%256; cm=(qi/256)%256; let qtdtok=volatile_read32(dm+136); let qtok=volatile_read32(dm+24); let ta=(qtdtok/128)%2; let qa=(qtok/128)%2; let sx=(qtok/2)%2; let er=((qtdtok/4)%32)+((qtok/4)%32); let rem=(qtdtok/65536)%32768; let orem=(qtok/65536)%32768; gate=1+(ta*2)+(qa*4)+(sx*8)+(er*16)+(rem*1024)+(orem*32768); } let compat_i=volatile_read64(xhci+3976); let compat_x=(rr/2)%2; let compat_e=(rr/4)%32; let actual=volatile_read64(xhci+4088); let delivered=volatile_read64(xhci+4072); v108_draw_small_u64(surface,((px+112)*65536)+(py+748),volatile_read64(xhci+3984)+(compat_i*0)+(compat_x*0)+(compat_e*0)+(sm*0)+(cm*0)+(actual*0)+(delivered*0),green); v108_draw_small_u64(surface,((px+150)*65536)+(py+748),volatile_read64(xhci+3992),amber); v108_draw_small_u64(surface,((px+188)*65536)+(py+748),volatile_read64(xhci+4000),white); v108_draw_small_u64(surface,((px+226)*65536)+(py+748),gate,green); v108_draw_small_u64(surface,((px+286)*65536)+(py+748),volatile_read64(xhci+4064),amber); v108_draw_small_u64(surface,((px+326)*65536)+(py+748),rr%256,white); v108_draw_small_u64(surface,((px+366)*65536)+(py+748),(rr/256)%256,green); }"
s=s[:rs]+newrow+s[re:]

scope=s[s.index('fn v159_ehci_mouse_periodic_arm'):s.index('fn v135_hid_control_fallback_prepare')]
for q in (
    'let full_setup=usb_setup_length_v113(usb_setup_value_v113(128,6,512,0),total)',
    'let al0=volatile_read8(data0+off0+3)',
    'if ea0==mep && at0%4==3 { epfound=1; }',
    'let setif=1+(11*256)+(malt*65536)+(mif*4294967296)',
    'let resettt=35+(9*256)+(ttidx*4294967296)',
    'v155_ehci_control(xhci_state,1,resettt,0)',
    'let info2=1090591745',
    'let token=560512',
    'input_push(input_state,4,0,buttons)',
):
    if q not in scope: raise SystemExit('r61 witness missing '+q)
for bad in ('write(10)','nvme_submit_write','ahci_write','fat_write','block_write'):
    if bad in scope.lower(): raise SystemExit('r61 exceeds read-only input scope '+bad)
if s.count('{')!=s.count('}'):
    raise SystemExit('r61 brace mismatch')
out=hashlib.sha256(s.encode()).hexdigest()
EXPECTED='5903008c46c2d6e4be84a5eab7fa44a322ba7a594ff8cb810fcbe277e716d9ee'
if out!=EXPECTED:
    raise SystemExit('r61 output sha mismatch '+out)
p.write_text(s)
print(out)
