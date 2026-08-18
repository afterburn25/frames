#!/usr/bin/env python3
from pathlib import Path
import hashlib, sys
if len(sys.argv)!=2: raise SystemExit('usage: patch_v108_r41_maxxter_ls_hid_babble_protocol.py <kernel/main.nx>')
p=Path(sys.argv[1]); s=p.read_text()
BASE='ae9598872e6806907e8bb623050f4314dbdda140ecd6b9c620f36e1c669b4c6c'
if hashlib.sha256(s.encode()).hexdigest()!=BASE: raise SystemExit('r40 base mismatch '+hashlib.sha256(s.encode()).hexdigest())

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
            if d==0:return s[st:i+1]
    raise SystemExit('unterminated '+name)

def fnrep(name,new): rep(fn_text(name),new,name)
def local_rep(text,old,new,label,count=1):
    n=text.count(old)
    if n!=count: raise SystemExit(f'{label} count {n}, expected {count}')
    return text.replace(old,new,count)
def label_fn(name,text):
    out=f'fn {name}(surface:u64,x:u64,y:u64,color:u64) -> u64 {{'
    for i,ch in enumerate(text): out+=f' if gui_draw_char_scaled(surface,((x+{i*6})*65536)+y,({ord(ch)}*65536)+1,color)==0 {{ return 0; }}'
    return out+' return 1; }'

d=fn_text('xhci_discover_boot_hid')
d=local_rep(d,
'''        volatile_write64(xhci_state+1144,0); volatile_write64(xhci_state+1152,0); volatile_write64(xhci_state+1160,0); volatile_write64(xhci_state+1168,0); volatile_write64(xhci_state+1176,0); volatile_write64(xhci_state+1184,0); volatile_write64(xhci_state+1192,0); volatile_write64(xhci_state+1200,0); volatile_write64(xhci_state+1208,0);''',
'''        volatile_write64(xhci_state+1144,0); volatile_write64(xhci_state+1152,0); volatile_write64(xhci_state+1160,0); volatile_write64(xhci_state+1168,0); volatile_write64(xhci_state+1176,0); volatile_write64(xhci_state+1184,0); volatile_write64(xhci_state+1192,0); volatile_write64(xhci_state+1200,0); volatile_write64(xhci_state+1208,0);
        volatile_write64(xhci_state+3136,0); volatile_write64(xhci_state+3144,0); volatile_write64(xhci_state+3152,0); volatile_write64(xhci_state+3160,255); volatile_write64(xhci_state+3168,0); volatile_write64(xhci_state+3176,0); volatile_write64(xhci_state+3184,0); volatile_write64(xhci_state+3192,0); volatile_write64(xhci_state+3200,0); volatile_write64(xhci_state+3208,0); volatile_write64(xhci_state+3216,0); volatile_write64(xhci_state+3224,0); volatile_write64(xhci_state+3232,0);''','r41 HID diagnostic state reset')
d=local_rep(d,'var off:u64=0; var active:u64=0; var interface_num:u64=0;','var off:u64=0; var active:u64=0; var interface_num:u64=0; var hid_report_len:u64=0;','r41 HID descriptor parser state')
d=local_rep(d,
'''        if typ==4 && len>=9 { active=0; let cls=volatile_read8(full+off+5); let sub=volatile_read8(full+off+6); let pro=volatile_read8(full+off+7); unsafe { volatile_write64(xhci_state+864,cls); volatile_write64(xhci_state+872,sub); volatile_write64(xhci_state+880,pro); } if cls==3 && sub==1 && (pro==1 || pro==2) { active=pro; interface_num=volatile_read8(full+off+2); } }
        if typ==5 && len>=7 && active!=0 {''',
'''        if typ==4 && len>=9 { active=0; hid_report_len=0; let cls=volatile_read8(full+off+5); let sub=volatile_read8(full+off+6); let pro=volatile_read8(full+off+7); unsafe { volatile_write64(xhci_state+864,cls); volatile_write64(xhci_state+872,sub); volatile_write64(xhci_state+880,pro); } if cls==3 && sub==1 && (pro==1 || pro==2) { active=pro; interface_num=volatile_read8(full+off+2); } }
        if typ==33 && len>=9 && active!=0 { let ndesc=volatile_read8(full+off+5); let dtype=volatile_read8(full+off+6); if ndesc!=0 && dtype==34 { hid_report_len=volatile_read8(full+off+7)+(volatile_read8(full+off+8)*256); } }
        if typ==5 && len>=7 && active!=0 {''','r41 HID report descriptor parse')
d=local_rep(d,'volatile_write64(xhci_state+1136,burst); volatile_write64(xhci_state+1192,volatile_read64(xhci_state+1192)+1);','volatile_write64(xhci_state+1136,burst); volatile_write64(xhci_state+3136,hid_report_len); volatile_write64(xhci_state+1192,volatile_read64(xhci_state+1192)+1);','r41 keyboard report length capture')
d=local_rep(d,'volatile_write64(xhci_state+1184,burst); volatile_write64(xhci_state+1200,volatile_read64(xhci_state+1200)+1);','volatile_write64(xhci_state+1184,burst); volatile_write64(xhci_state+3144,hid_report_len); volatile_write64(xhci_state+1200,volatile_read64(xhci_state+1200)+1);','r41 mouse report length capture')
fnrep('xhci_discover_boot_hid',d)

sel=fn_text('v108_xhci_select_boot_hid_v117')
sel=local_rep(sel,'var iface:u64=0; var endpoint:u64=0; var dci:u64=0; var packet:u64=0; var interval:u64=0; var burst:u64=0;','var iface:u64=0; var endpoint:u64=0; var dci:u64=0; var packet:u64=0; var interval:u64=0; var burst:u64=0; var report_len:u64=0;','r41 selected report length local')
sel=local_rep(sel,'if wanted==1 { iface=volatile_read64(xhci_state+1096); endpoint=volatile_read64(xhci_state+1104); dci=volatile_read64(xhci_state+1112); packet=volatile_read64(xhci_state+1120); interval=volatile_read64(xhci_state+1128); burst=volatile_read64(xhci_state+1136); }','if wanted==1 { iface=volatile_read64(xhci_state+1096); endpoint=volatile_read64(xhci_state+1104); dci=volatile_read64(xhci_state+1112); packet=volatile_read64(xhci_state+1120); interval=volatile_read64(xhci_state+1128); burst=volatile_read64(xhci_state+1136); report_len=volatile_read64(xhci_state+3136); }','r41 keyboard selected report length')
sel=local_rep(sel,'if wanted==2 { iface=volatile_read64(xhci_state+1144); endpoint=volatile_read64(xhci_state+1152); dci=volatile_read64(xhci_state+1160); packet=volatile_read64(xhci_state+1168); interval=volatile_read64(xhci_state+1176); burst=volatile_read64(xhci_state+1184); }','if wanted==2 { iface=volatile_read64(xhci_state+1144); endpoint=volatile_read64(xhci_state+1152); dci=volatile_read64(xhci_state+1160); packet=volatile_read64(xhci_state+1168); interval=volatile_read64(xhci_state+1176); burst=volatile_read64(xhci_state+1184); report_len=volatile_read64(xhci_state+3144); }','r41 mouse selected report length')
sel=local_rep(sel,'volatile_write64(xhci_state+1208,wanted);','volatile_write64(xhci_state+1208,wanted); volatile_write64(xhci_state+3232,report_len);','r41 selected report state')
fnrep('v108_xhci_select_boot_hid_v117',sel)

cfg=fn_text('xhci_configure_boot_hid')
cfg=local_rep(cfg,
'''    serial_usb_config_diag(22,interface_num);
    let idle_setup=2593+(64000*65536)+(interface_num*4294967296); var idle_ok:u64=0; if xhci_control_no_data_out(xhci_state,idle_setup)!=0 { idle_ok=1; } unsafe { volatile_write64(xhci_state+2960,idle_ok); }''',
'''    serial_usb_config_diag(22,interface_num);
    let gp_setup=usb_setup_length_v113(usb_setup_value_v113(161,3,0,interface_num),1); var gp_ok:u64=0; var gp_val:u64=255; var gp=xhci_control_get(xhci_state,phys_state,gp_setup,1); if gp!=0 { gp_ok=1; gp_val=volatile_read8(gp); }
    if gp_ok==0 || gp_val!=0 { xhci_control_no_data_out(xhci_state,protocol_setup); pit_wait(11932); gp=xhci_control_get(xhci_state,phys_state,gp_setup,1); if gp!=0 { gp_ok=1; gp_val=volatile_read8(gp); } }
    unsafe { volatile_write64(xhci_state+3152,gp_ok); volatile_write64(xhci_state+3160,gp_val); }
    let rdecl=volatile_read64(xhci_state+3232); var rprobe:u64=rdecl; if rprobe>128 { rprobe=128; } var ractual:u64=0; var rsum:u64=0;
    if rprobe!=0 { let rsetup=usb_setup_length_v113(usb_setup_value_v113(129,6,8704,interface_num),rprobe); let rb=xhci_control_get(xhci_state,phys_state,rsetup,rprobe); if rb!=0 { let rem=volatile_read64(xhci_state+576); if rem<=rprobe { ractual=rprobe-rem; if ractual!=0 { rsum=nvme_read_checksum(rb,ractual); } } } }
    unsafe { volatile_write64(xhci_state+3168,ractual); volatile_write64(xhci_state+3176,rprobe); volatile_write64(xhci_state+3184,rsum); }
    let idle_setup=2593+(64000*65536)+(interface_num*4294967296); var idle_ok:u64=0; if xhci_control_no_data_out(xhci_state,idle_setup)!=0 { idle_ok=1; } unsafe { volatile_write64(xhci_state+2960,idle_ok); }''','r41 protocol/report descriptor probe')
cfg=local_rep(cfg,'volatile_write64(xhci_state+1256,0); }','volatile_write64(xhci_state+1256,0); volatile_write64(xhci_state+3192,mps); volatile_write64(xhci_state+3200,0); volatile_write64(xhci_state+3208,0); volatile_write64(xhci_state+3216,0); volatile_write64(xhci_state+3224,0); }','r41 adaptive state init')
fnrep('xhci_configure_boot_hid',cfg)

fnrep('xhci_hid_arm_continuous', '''fn xhci_hid_arm_continuous(xhci_state:u64,phys_state:u64) -> u64 {
    if xhci_state==0 || volatile_read64(xhci_state+416)!=1 { return 0; }
    if volatile_read64(xhci_state+808)!=0 { return 1; }
    let ring=volatile_read64(xhci_state+392); var buffer=volatile_read64(xhci_state+432); let packet=volatile_read64(xhci_state+360); let slot=volatile_read64(xhci_state+136); let dci=volatile_read64(xhci_state+352); let doorbells=volatile_read64(xhci_state+88);
    if buffer==0 { if phys_state==0 { return 0; } buffer=alloc_dma_page(phys_state,3); if buffer==0 { return 0; } zero_page(buffer); unsafe { volatile_write64(xhci_state+432,buffer); } }
    if ring==0 || buffer==0 || packet==0 || packet>1024 || slot==0 || dci<2 || dci>31 { return 0; }
    var request=packet; let speed=volatile_read64(xhci_state+184); let vid=volatile_read64(xhci_state+272); let pid=volatile_read64(xhci_state+280); let proto=volatile_read64(xhci_state+336);
    if speed==2 && vid==9354 && pid==4267 && proto==2 { let adaptive=volatile_read64(xhci_state+3192); if adaptive>=packet && adaptive<=32 { request=adaptive; } }
    var tail=volatile_read64(xhci_state+408); var cycle=volatile_read64(xhci_state+800); if cycle>1 { return 0; }
    if tail>=255 { tail=0; if cycle==1 { cycle=0; } else { cycle=1; } }
    zero_page(buffer); let trb=ring+(tail*16);
    unsafe { volatile_write64(trb,buffer); volatile_write32(trb+8,request); volatile_write32(trb+12,1060+cycle); volatile_write64(xhci_state+3192,request); }
    tail=tail+1; unsafe { volatile_write64(xhci_state+408,tail); volatile_write64(xhci_state+800,cycle); volatile_write64(xhci_state+808,1); volatile_write32(doorbells+(slot*4),dci); }
    if volatile_read64(xhci_state+832)==0 { unsafe { volatile_write64(xhci_state+832,1); } serial_marker_devprev_usb_poll_armed(); }
    return 1;
}''')

fnrep('xhci_hid_poll_continuous', '''fn xhci_hid_poll_continuous(xhci_state:u64,input_state:u64) -> u64 {
    if xhci_state==0 || input_state==0 || volatile_read64(xhci_state+808)==0 { return 1; }
    let slot=volatile_read64(xhci_state+136); let dci=volatile_read64(xhci_state+352); let packet=volatile_read64(xhci_state+360); var request=packet; let speed=volatile_read64(xhci_state+184); let vid=volatile_read64(xhci_state+272); let pid=volatile_read64(xhci_state+280); let protocol=volatile_read64(xhci_state+336); let target=(speed==2 && vid==9354 && pid==4267 && protocol==2); if target { let a=volatile_read64(xhci_state+3192); if a>=packet && a<=32 { request=a; } }
    var code:u64=0; var residue:u64=0; var matched:u64=0;
    let queued=xhci_event_mailbox_take_v127(xhci_state,slot,dci);
    if queued!=0 { let packed=queued-1; code=packed/16777216; residue=packed%16777216; matched=1; }
    if matched==0 {
        let event_ring=volatile_read64(xhci_state+24); let index=volatile_read64(xhci_state+96); let cycle=volatile_read64(xhci_state+104); if event_ring==0 { unsafe { volatile_write64(xhci_state+2800,volatile_read64(xhci_state+2800)+1); } return 1; }
        let trb=event_ring+(index*16); let control=volatile_read32(trb+12); if control%2!=cycle { return 1; }
        let typ=(control/1024)%64; if typ!=32 { xhci_event_advance(xhci_state); return 1; }
        let status=volatile_read32(trb+8); code=(status/16777216)%256; residue=status%16777216; let event_ep=(control/65536)%32; let event_slot=(control/16777216)%256; xhci_event_advance(xhci_state);
        if event_slot!=slot || event_ep!=dci { xhci_event_mailbox_put_v127(xhci_state,event_slot,event_ep,(code*16777216)+residue); return 1; }
    }
    unsafe { volatile_write64(xhci_state+808,0); volatile_write64(xhci_state+2784,code); volatile_write64(xhci_state+2792,residue); volatile_write64(xhci_state+3224,residue); }
    if code==3 && target { let b=volatile_read64(xhci_state+3200)+1; var next=request; if request<16 { next=16; } else { if request<32 { next=32; } } unsafe { volatile_write64(xhci_state+3200,b); volatile_write64(xhci_state+3192,next); volatile_write64(xhci_state+3216,next); } if next>request { if xhci_hid_arm_continuous(xhci_state,0)==0 { unsafe { volatile_write64(xhci_state+2800,volatile_read64(xhci_state+2800)+1); } } } return 1; }
    if (code!=1 && code!=13) || residue>request { unsafe { volatile_write64(xhci_state+2800,volatile_read64(xhci_state+2800)+1); } return 1; }
    let actual=request-residue; unsafe { volatile_write64(xhci_state+3208,actual); } if actual==0 || (protocol==1 && actual<8) || (protocol==2 && actual<3) { unsafe { volatile_write64(xhci_state+2800,volatile_read64(xhci_state+2800)+1); } return 1; }
    let buffer=volatile_read64(xhci_state+432); let checksum=nvme_read_checksum(buffer,actual); unsafe { volatile_write64(xhci_state+440,actual); volatile_write64(xhci_state+448,checksum); volatile_write64(xhci_state+456,volatile_read8(buffer)); volatile_write64(xhci_state+464,volatile_read8(buffer+1)); volatile_write64(xhci_state+472,1); volatile_write64(xhci_state+816,volatile_read64(xhci_state+816)+1); }
    if input_decode_boot_hid(xhci_state,input_state)==0 { unsafe { volatile_write64(xhci_state+2800,volatile_read64(xhci_state+2800)+1); } return 1; }
    if volatile_read64(xhci_state+824)==0 { unsafe { volatile_write64(xhci_state+824,1); } serial_marker_devprev_usb_report_ok(); }
    if xhci_hid_arm_continuous(xhci_state,0)==0 { unsafe { volatile_write64(xhci_state+2800,volatile_read64(xhci_state+2800)+1); } }
    return 1;
}''')

fnrep('v140_text_r40_v140', label_fn('v141_text_r41_v141','R41 G P D L B E'))
rep(
'''    v140_text_r40_v140(surface,px+10,py+730,white); if xhci!=0 { v108_draw_small_u64(surface,((px+112)*65536)+(py+730),volatile_read64(xhci+2696),green); v108_draw_small_u64(surface,((px+150)*65536)+(py+730),volatile_read64(xhci+2960),green); v108_draw_small_u64(surface,((px+188)*65536)+(py+730),volatile_read64(xhci+336),white); v108_draw_small_u64(surface,((px+226)*65536)+(py+730),volatile_read64(xhci+272),white); v108_draw_small_u64(surface,((px+290)*65536)+(py+730),volatile_read64(xhci+280),white); v108_draw_small_u64(surface,((px+370)*65536)+(py+730),volatile_read64(xhci+2784),red); }''',
'''    v141_text_r41_v141(surface,px+10,py+730,white); if xhci!=0 { v108_draw_small_u64(surface,((px+112)*65536)+(py+730),volatile_read64(xhci+3152),green); v108_draw_small_u64(surface,((px+150)*65536)+(py+730),volatile_read64(xhci+3160),amber); v108_draw_small_u64(surface,((px+188)*65536)+(py+730),volatile_read64(xhci+3232),white); v108_draw_small_u64(surface,((px+246)*65536)+(py+730),volatile_read64(xhci+3192),white); v108_draw_small_u64(surface,((px+306)*65536)+(py+730),volatile_read64(xhci+3200),amber); v108_draw_small_u64(surface,((px+370)*65536)+(py+730),volatile_read64(xhci+2784),red); }''','r41 full telemetry row')
compact=fn_text('v108_input_overlay_r37_draw_v137')
compact=local_rep(compact,'v140_text_r40_v140(surface,px+10,py+730,white);','v141_text_r41_v141(surface,px+10,py+730,white);','r41 compact label')
compact=local_rep(compact,
'''        v108_draw_small_u64(surface,((px+112)*65536)+(py+730),volatile_read64(xhci+2696),green);
        v108_draw_small_u64(surface,((px+150)*65536)+(py+730),volatile_read64(xhci+2960),green);
        v108_draw_small_u64(surface,((px+188)*65536)+(py+730),volatile_read64(xhci+336),white);
        v108_draw_small_u64(surface,((px+226)*65536)+(py+730),volatile_read64(xhci+272),white);
        v108_draw_small_u64(surface,((px+290)*65536)+(py+730),volatile_read64(xhci+280),white);
        v108_draw_small_u64(surface,((px+370)*65536)+(py+730),volatile_read64(xhci+2784),red);''',
'''        v108_draw_small_u64(surface,((px+112)*65536)+(py+730),volatile_read64(xhci+3152),green);
        v108_draw_small_u64(surface,((px+150)*65536)+(py+730),volatile_read64(xhci+3160),amber);
        v108_draw_small_u64(surface,((px+188)*65536)+(py+730),volatile_read64(xhci+3232),white);
        v108_draw_small_u64(surface,((px+246)*65536)+(py+730),volatile_read64(xhci+3192),white);
        v108_draw_small_u64(surface,((px+306)*65536)+(py+730),volatile_read64(xhci+3200),amber);
        v108_draw_small_u64(surface,((px+370)*65536)+(py+730),volatile_read64(xhci+2784),red);''','r41 compact telemetry fields')
fnrep('v108_input_overlay_r37_draw_v137',compact)

if s.count('{')!=s.count('}'): raise SystemExit('brace mismatch')
out=hashlib.sha256(s.encode()).hexdigest(); EXPECTED='2e201d05458889915040ad726cbd756c41a5429199bee0738f32dd9fe8a9aed4';
if out!=EXPECTED: raise SystemExit('r41 output sha mismatch '+out)
p.write_text(s); print(out)
