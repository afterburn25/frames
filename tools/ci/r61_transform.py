#!/usr/bin/env python3
from pathlib import Path
import hashlib, sys

BASE='10a1a6550abafe7c593d059eeb983d6a576b19ab46c1dcde6ec71888aa6d4a03'
if len(sys.argv)!=2:
    raise SystemExit('usage: r61_transform.py <exact-r59s-kernel.nx>')
p=Path(sys.argv[1])
s=p.read_text()
actual=hashlib.sha256(s.encode()).hexdigest()
if actual!=BASE:
    raise SystemExit('r61 exact r59s base mismatch '+actual)

def fn_text(src,name):
    st=src.index('fn '+name)
    op=src.index('{',st)
    d=0
    for i in range(op,len(src)):
        if src[i]=='{':
            d+=1
        elif src[i]=='}':
            d-=1
            if d==0:
                return src[st:i+1]
    raise SystemExit('unterminated '+name)

def rep_in(text,old,new,label,count=1):
    n=text.count(old)
    if n!=count:
        raise SystemExit(f'r61 {label}: {n} expected {count}')
    return text.replace(old,new,count)

def label_fn(name,text):
    out=f'fn {name}(surface:u64,x:u64,y:u64,color:u64) -> u64 {{'
    for i,ch in enumerate(text):
        out+=f' if gui_draw_char_scaled(surface,((x+{i*6})*65536)+y,({ord(ch)}*65536)+1,color)==0 {{ return 0; }}'
    return out+' return 1; }'

arm=fn_text(s,'v159_ehci_mouse_periodic_arm')
restore='    unsafe { volatile_write64(xhci_state+3936,kep); }'
preflight=r'''    let r61_total=volatile_read64(xhci_state+4016);
    if r61_total<9 || r61_total>256 { unsafe { volatile_write64(xhci_state+4056,30); volatile_write64(xhci_state+4000,0); } return 30; }
    let r61_full=usb_setup_length_v113(usb_setup_value_v113(128,6,512,0),r61_total);
    let r61_frc=v157_ehci_tt_control(xhci_state,2,r61_full,r61_total);
    if r61_frc!=1 { unsafe { volatile_write64(xhci_state+4056,31); volatile_write64(xhci_state+4000,r61_frc); } return 31; }
    let r61_data=dma+576; var r61_off:u64=0; var r61_active:u64=0; var r61_iface:u64=0; var r61_alt:u64=0; var r61_ep:u64=0; var r61_mps:u64=0; var r61_int:u64=0;
    while r61_off+2<=r61_total {
        let r61_dl=volatile_read8(r61_data+r61_off); let r61_dt=volatile_read8(r61_data+r61_off+1);
        if r61_dl<2 || r61_off+r61_dl>r61_total { r61_off=r61_total; } else {
            if r61_dt==4 && r61_dl>=9 {
                let r61_ic=volatile_read8(r61_data+r61_off+5); let r61_sub=volatile_read8(r61_data+r61_off+6); let r61_pr=volatile_read8(r61_data+r61_off+7);
                r61_active=0;
                if r61_ic==3 && r61_sub==1 && r61_pr==2 { r61_active=1; r61_iface=volatile_read8(r61_data+r61_off+2); r61_alt=volatile_read8(r61_data+r61_off+3); }
            }
            if r61_dt==5 && r61_dl>=7 && r61_active!=0 && r61_ep==0 {
                let r61_ea=volatile_read8(r61_data+r61_off+2); let r61_attr=volatile_read8(r61_data+r61_off+3);
                if r61_ea>=128 && r61_attr%4==3 { r61_ep=r61_ea; r61_mps=volatile_read8(r61_data+r61_off+4)+(volatile_read8(r61_data+r61_off+5)*256); r61_int=volatile_read8(r61_data+r61_off+6); }
            }
            r61_off=r61_off+r61_dl;
        }
    }
    if r61_ep==0 || r61_iface!=mif || r61_ep!=mep || r61_mps!=mmps || r61_int!=mint { unsafe { volatile_write64(xhci_state+4056,32); volatile_write64(xhci_state+4000,1); } return 32; }
    var r61_prep:u64=1;
    if r61_alt!=0 {
        let r61_setif=1+(11*256)+(r61_alt*65536)+(r61_iface*4294967296);
        let r61_src=v157_ehci_tt_control(xhci_state,2,r61_setif,0);
        if r61_src!=1 { unsafe { volatile_write64(xhci_state+4056,33); volatile_write64(xhci_state+4000,r61_src); } return 33; }
    }
    let r61_getif=129+(10*256)+(r61_iface*4294967296)+(1*281474976710656);
    let r61_girc=v157_ehci_tt_control(xhci_state,2,r61_getif,1);
    if r61_girc!=1 || volatile_read8(dma+576)!=r61_alt { unsafe { volatile_write64(xhci_state+4056,34); volatile_write64(xhci_state+4000,r61_girc); } return 34; }
    r61_prep=r61_prep+2;
    let r61_boot=33+(11*256)+(r61_iface*4294967296);
    let r61_brc=v157_ehci_tt_control(xhci_state,2,r61_boot,0);
    if r61_brc!=1 { unsafe { volatile_write64(xhci_state+4056,35); volatile_write64(xhci_state+4000,r61_brc); } return 35; }
    let r61_gp=161+(3*256)+(r61_iface*4294967296)+(1*281474976710656);
    let r61_gprc=v157_ehci_tt_control(xhci_state,2,r61_gp,1);
    if r61_gprc!=1 || volatile_read8(dma+576)!=0 { unsafe { volatile_write64(xhci_state+4056,36); volatile_write64(xhci_state+4000,r61_gprc); } return 36; }
    r61_prep=r61_prep+4;
    let r61_idle=33+(10*256)+(r61_iface*4294967296);
    let r61_irc=v157_ehci_tt_control(xhci_state,2,r61_idle,0);
    if r61_irc!=1 { unsafe { volatile_write64(xhci_state+4056,37); volatile_write64(xhci_state+4000,r61_irc); } return 37; }
    r61_prep=r61_prep+8;
    let r61_est=130+(r61_ep*4294967296)+(2*281474976710656);
    var r61_erc=v157_ehci_tt_control(xhci_state,2,r61_est,2);
    if r61_erc!=1 { unsafe { volatile_write64(xhci_state+4056,38); volatile_write64(xhci_state+4000,r61_erc); } return 38; }
    if volatile_read8(dma+576)%2!=0 {
        let r61_clr=2+(1*256)+(r61_ep*4294967296);
        r61_erc=v157_ehci_tt_control(xhci_state,2,r61_clr,0);
        if r61_erc!=1 { unsafe { volatile_write64(xhci_state+4056,39); volatile_write64(xhci_state+4000,r61_erc); } return 39; }
        r61_erc=v157_ehci_tt_control(xhci_state,2,r61_est,2);
        if r61_erc!=1 || volatile_read8(dma+576)%2!=0 { unsafe { volatile_write64(xhci_state+4056,40); volatile_write64(xhci_state+4000,r61_erc); } return 40; }
    }
    r61_prep=r61_prep+16;
    let r61_ref_info2=1+(28*256)+(1*65536)+(volatile_read64(xhci_state+3928)*8388608)+1073741824;
    if r61_ref_info2!=1090591745 || mmps!=8 || mint!=4 { unsafe { volatile_write64(xhci_state+4056,41); volatile_write64(xhci_state+4000,r61_ref_info2); } return 41; }
    r61_prep=r61_prep+32;
    unsafe { volatile_write64(xhci_state+4000,r61_prep); }
'''
arm=rep_in(arm,restore,preflight+restore,'preflight insertion')
old_cmd='    cmd=volatile_read32(op); cmd=clear_flag(cmd,32); cmd=set_flag(cmd,1); cmd=set_flag(cmd,16); unsafe { volatile_write32(op,cmd); }'
new_cmd='    cmd=volatile_read32(op); cmd=clear_flag(cmd,32); cmd=clear_flag(cmd,4); cmd=clear_flag(cmd,8); cmd=set_flag(cmd,1); cmd=set_flag(cmd,16); unsafe { volatile_write32(op,cmd); }'
arm=rep_in(arm,old_cmd,new_cmd,'1024 frame-list size')
s=s.replace(fn_text(s,'v159_ehci_mouse_periodic_arm'),arm,1)

tick=fn_text(s,'v159_ehci_mouse_periodic_tick')
tick=rep_in(tick,'fn v159_ehci_mouse_periodic_tick(xhci_state:u64) -> u64 {','fn v159_ehci_mouse_periodic_tick(xhci_state:u64,input_state:u64) -> u64 {','tick input-state signature')
raw_anchor='    let raw=volatile_read64(data);'
raw_insert=r'''    let raw=volatile_read64(data); let r61_actual=8-rem;
    if input_state!=0 && r61_actual>=3 {
        let r61_buttons=(raw%256)%8; let r61_x=(raw/256)%256; let r61_y=(raw/65536)%256;
        var r61_xmag=r61_x; var r61_xneg:u64=0; if r61_x>=128 { r61_xmag=256-r61_x; r61_xneg=1; }
        var r61_ymag=r61_y; var r61_yneg:u64=0; if r61_y>=128 { r61_ymag=256-r61_y; r61_yneg=1; }
        let r61_packed=r61_buttons+(r61_xmag*256)+(r61_xneg*131072)+(r61_ymag*262144)+(r61_yneg*134217728);
        generic_pointer_emit_relative(input_state,1,r61_packed);
    }'''
tick=rep_in(tick,raw_anchor,raw_insert,'generic-pointer delivery')
rearm='volatile_write32(qh+16,qtdlo); volatile_write32(qh+20,1);'
rearm_new='let r61_toggle=(live_tok/2147483648)%2; volatile_write32(qh+16,qtdlo); volatile_write32(qh+20,1); volatile_write32(qh+24,r61_toggle*2147483648);'
tick=rep_in(tick,rearm,rearm_new,'QH toggle-preserving rearm')
s=s.replace(fn_text(s,'v159_ehci_mouse_periodic_tick'),tick,1)

if s.count('v159_ehci_mouse_periodic_tick(xhci);')!=1:
    raise SystemExit('r61 live tick call anchor mismatch')
s=s.replace('v159_ehci_mouse_periodic_tick(xhci);','v159_ehci_mouse_periodic_tick(xhci,input_state);',1)

old_label=fn_text(s,'v140_text_wifi_v140')
s=s.replace(old_label,label_fn('v140_text_wifi_v140','R61 S P N C B X Y'),1)
rs=s.index('    v140_text_wifi_v140(surface,px+10,py+748,white);')
re=s.index('\n    return 1;\n}',rs)
newrow='''    v140_text_wifi_v140(surface,px+10,py+748,white); if xhci!=0 { let r61_raw=volatile_read64(xhci+4088); v108_draw_small_u64(surface,((px+112)*65536)+(py+748),volatile_read64(xhci+4056),green); v108_draw_small_u64(surface,((px+150)*65536)+(py+748),volatile_read64(xhci+4000),amber); v108_draw_small_u64(surface,((px+188)*65536)+(py+748),volatile_read64(xhci+4064),white); v108_draw_small_u64(surface,((px+226)*65536)+(py+748),volatile_read64(xhci+4072),green); v108_draw_small_u64(surface,((px+264)*65536)+(py+748),r61_raw%256,amber); v108_draw_small_u64(surface,((px+306)*65536)+(py+748),(r61_raw/256)%256,white); v108_draw_small_u64(surface,((px+350)*65536)+(py+748),(r61_raw/65536)%256,white); }'''
s=s[:rs]+newrow+s[re:]

scope=s[s.index('fn v159_ehci_mouse_periodic_arm'):s.index('fn v135_hid_control_fallback_prepare')]
for q in (
    'usb_setup_length_v113(usb_setup_value_v113(128,6,512,0),r61_total)',
    'r61_ic==3 && r61_sub==1 && r61_pr==2',
    'r61_alt=volatile_read8(r61_data+r61_off+3)',
    'r61_ep!=mep || r61_mps!=mmps || r61_int!=mint',
    'let r61_setif=1+(11*256)',
    'let r61_getif=129+(10*256)',
    'let r61_boot=33+(11*256)',
    'volatile_read8(dma+576)!=0',
    'let r61_idle=33+(10*256)',
    'let r61_est=130+(r61_ep*4294967296)',
    'let r61_clr=2+(1*256)',
    'r61_ref_info2=1+(28*256)+(1*65536)',
    'generic_pointer_emit_relative(input_state,1,r61_packed)',
    'let r61_toggle=(live_tok/2147483648)%2',
    'volatile_write32(qh+24,r61_toggle*2147483648)',
):
    if q not in scope:
        raise SystemExit('r61 witness missing '+q)
for q in (
    'let info2=1090591745',
    'let token=527744',
    'volatile_write64(xhci_state+3984,gate)',
    'if cur!=qtdlo { return 0; }',
):
    if q not in scope:
        raise SystemExit('r61 inherited r59s witness lost '+q)
low=scope.lower()
for bad in ('write(10)','nvme_submit_write','ahci_write','fat_write','block_write','input_push('):
    if bad in low:
        raise SystemExit('r61 destructive/unsafe scope violation '+bad)
if s.count('{')!=s.count('}'):
    raise SystemExit('r61 brace mismatch')
out=hashlib.sha256(s.encode()).hexdigest()
p.write_text(s)
print('R61_DISCOVERED_SHA='+out)
