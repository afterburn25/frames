from pathlib import Path
import hashlib,sys
p=Path(sys.argv[1])
raw=p.read_bytes(); expected='5b2384f8e128b1ec6922f34c14478918c3388179937c2000dd12135fefcf682c'
actual=hashlib.sha256(raw).hexdigest()
if actual!=expected: raise SystemExit(f'unexpected r9 hash {actual}')
s=raw.decode()

def fn_span(text,name):
    st=text.index(name); op=text.index('{',st); d=0; j=op
    while j<len(text):
        if text[j]=='{': d+=1
        elif text[j]=='}':
            d-=1
            if d==0: return st,j+1
        j+=1
    raise RuntimeError(name)

def repl_fn(name,new):
    global s
    st,en=fn_span(s,name); s=s[:st]+new+s[en:]

st,en=fn_span(s,'fn xhci_wait_transfer_event')
blk=s[st:en]
old='let status=volatile_read32(trb+8); let code=(status/16777216)%256; let event_ep=(control/65536)%32; let event_slot=(control/16777216)%256; unsafe { volatile_write64(xhci_state+504,code); volatile_write64(xhci_state+512,event_slot); volatile_write64(xhci_state+520,event_ep); }'
new='let status=volatile_read32(trb+8); let code=(status/16777216)%256; let remain=status%16777216; let event_ep=(control/65536)%32; let event_slot=(control/16777216)%256; unsafe { volatile_write64(xhci_state+504,code); volatile_write64(xhci_state+512,event_slot); volatile_write64(xhci_state+520,event_ep); volatile_write64(xhci_state+576,remain); }'
if blk.count(old)!=1: raise SystemExit('xhci event anchor')
blk=blk.replace(old,new,1); s=s[:st]+blk+s[en:]

st,en=fn_span(s,'fn xhci_finalize_address_and_descriptor')
blk=s[st:en]
old='''    let completed=xhci_command_submit_address(xhci_state,input,slot,0); if completed!=slot { return 0; }
    unsafe { volatile_write64(xhci_state+192,mps); volatile_write64(xhci_state+256,1); } serial_marker_xhci_addressed_ok();
    var full:u64=0; var full_ok:u64=0; var tries:u64=0;
    while tries<3 && full_ok==0 {
        full=xhci_control_get(xhci_state,phys_state,5066549597570688,18); tries=tries+1;
        if full!=0 { let dl=volatile_read8(full); let dt=volatile_read8(full+1); unsafe { volatile_write64(xhci_state+552,dl); volatile_write64(xhci_state+560,dt); } if dl>=18 && dt==1 { full_ok=1; } }
    }
'''
new='''    let completed=xhci_command_submit_address(xhci_state,input,slot,0); if completed!=slot { return 0; }
    unsafe { volatile_write64(xhci_state+192,mps); volatile_write64(xhci_state+256,1); } serial_marker_xhci_addressed_ok();
    pit_wait(11932);
    var full:u64=0; var full_ok:u64=0; var tries:u64=0;
    while tries<3 && full_ok==0 {
        full=xhci_control_get(xhci_state,phys_state,5066549597570688,18); tries=tries+1;
        if full!=0 { let dl=volatile_read8(full); let dt=volatile_read8(full+1); unsafe { volatile_write64(xhci_state+552,dl); volatile_write64(xhci_state+560,dt); } if dl>=18 && dt==1 { full_ok=1; } }
        if full_ok==0 { pit_wait(11932); }
    }
'''
if blk.count(old)!=1: raise SystemExit('xhci finalize anchor')
blk=blk.replace(old,new,1); s=s[:st]+blk+s[en:]

anchor='fn ps2_mouse_decode_v108(input_state:u64,data:u64) -> u64 {'
if s.count(anchor)!=1: raise SystemExit('ps2 decoder anchor')
helpers=r'''fn ps2_elan4_type_v110(a:u64,b:u64) -> u64 {
    let b0=(a/65536)%256; let b3=(b/65536)%256; let low=b0%16; if low<4 || low>7 { return 0; }
    let sig=b3%32; if sig==16 { return 1; } if sig==17 { return 2; } if sig==18 { return 3; } return 0;
}
fn ps2_elan4_xy_v110(a:u64,b:u64) -> u64 {
    let b1=(a/256)%256; let b2=a%256; let b4=(b/256)%256; let b5=b%256;
    let x=((b1%16)*256)+b2; let y=((b4%16)*256)+b5; return (x*65536)+y;
}
fn ps2_elan4_rel_v110(oldxy:u64,newxy:u64) -> u64 {
    let ox=oldxy/65536; let oy=oldxy%65536; let x=newxy/65536; let y=newxy%65536; var ax:u64=0; var ay:u64=0; var xr:u64=0; var yr:u64=0;
    if x>=ox { ax=x-ox; } else { ax=ox-x; } if y>=oy { ay=y-oy; } else { ay=oy-y; } if ax>512 || ay>512 { return 0; }
    if ax!=0 { var sx=(ax+7)/8; if sx==0 { sx=1; } if sx>40 { sx=40; } if x>=ox { xr=sx; } else { xr=256-sx; } }
    if ay!=0 { var sy=(ay+7)/8; if sy==0 { sy=1; } if sy>40 { sy=40; } if y>=oy { yr=256-sy; } else { yr=sy; } } return (xr*256)+yr;
}
fn ps2_elan4_emit_v110(input_state:u64,a:u64,b:u64,typ:u64) -> u64 {
    if input_state==0 { return 0; }
    if typ==1 { let fingers=(a/256)%256; if fingers==0 { unsafe { volatile_write64(input_state+3512,0); } } return 1; }
    if typ!=2 { return 1; }
    let xy=ps2_elan4_xy_v110(a,b); let x=xy/65536; let y=xy%65536;
    if volatile_read64(input_state+3512)==0 { unsafe { volatile_write64(input_state+3496,x); volatile_write64(input_state+3504,y); volatile_write64(input_state+3512,1); } return 1; }
    let ox=volatile_read64(input_state+3496); let oy=volatile_read64(input_state+3504); unsafe { volatile_write64(input_state+3496,x); volatile_write64(input_state+3504,y); }
    let rel=ps2_elan4_rel_v110((ox*65536)+oy,xy); let xr=rel/256; let yr=rel%256;
    unsafe { volatile_write64(input_state+3104,2); volatile_write64(input_state+3176,volatile_read64(input_state+3176)+1); volatile_write64(input_state+3520,volatile_read64(input_state+3520)+1); }
    if volatile_read64(input_state+3168)==0 { unsafe { volatile_write64(input_state+3168,1); } serial_marker_v108_ps2_packet_ok(); }
    let buttons=(a/65536)%4; input_push(input_state,4,0,buttons); if xr!=0 { input_push(input_state,5,0,xr); } if yr!=0 { input_push(input_state,6,0,yr); } return 1;
}
'''
s=s.replace(anchor,helpers+anchor,1)

repl_fn('fn ps2_mouse_decode_v108',r'''fn ps2_mouse_decode_v108(input_state:u64,data:u64) -> u64 {
    if input_state==0 || volatile_read64(input_state+32)!=1 { return 0; }
    let byte=data%256; unsafe { volatile_write64(input_state+3184,volatile_read64(input_state+3184)+1); }
    if byte==250 || byte==170 { return 1; }
    let n=volatile_read64(input_state+3424); unsafe {
        volatile_write64(input_state+3432,volatile_read64(input_state+3440)); volatile_write64(input_state+3440,volatile_read64(input_state+3448)); volatile_write64(input_state+3448,volatile_read64(input_state+3456));
        volatile_write64(input_state+3456,volatile_read64(input_state+3464)); volatile_write64(input_state+3464,volatile_read64(input_state+3472)); volatile_write64(input_state+3472,byte);
        if n<6 { volatile_write64(input_state+3424,n+1); } volatile_write64(input_state+3536,volatile_read64(input_state+3536)+1);
    }
    let mode=volatile_read64(input_state+3488);
    if volatile_read64(input_state+3424)>=6 && mode!=1 {
        let a=(volatile_read64(input_state+3432)*65536)+(volatile_read64(input_state+3440)*256)+volatile_read64(input_state+3448);
        let b=(volatile_read64(input_state+3456)*65536)+(volatile_read64(input_state+3464)*256)+volatile_read64(input_state+3472);
        let typ=ps2_elan4_type_v110(a,b);
        if typ!=0 {
            let idx=volatile_read64(input_state+3536); let last=volatile_read64(input_state+3544); var hits:u64=1; if last!=0 && idx>=last && idx-last<=8 { hits=volatile_read64(input_state+3552)+1; }
            if hits>3 { hits=3; } unsafe { volatile_write64(input_state+3544,idx); volatile_write64(input_state+3552,hits); volatile_write64(input_state+3528,volatile_read64(input_state+3528)+1); }
            if hits>=2 && mode==0 { unsafe { volatile_write64(input_state+3488,4); } }
            if volatile_read64(input_state+3488)==4 { return ps2_elan4_emit_v110(input_state,a,b,typ); }
        }
        if mode==4 { return 1; }
    }
    var count=volatile_read64(input_state+3376);
    if count==0 { unsafe { volatile_write64(input_state+3384,byte); volatile_write64(input_state+3376,1); } return 1; }
    if count==1 { unsafe { volatile_write64(input_state+3392,byte); volatile_write64(input_state+3376,2); } return 1; }
    let h=volatile_read64(input_state+3384)%256; let dx=volatile_read64(input_state+3392)%256; let dy=byte;
    unsafe { volatile_write64(input_state+3400,dy); volatile_write64(input_state+3296,h); volatile_write64(input_state+3304,dx); volatile_write64(input_state+3312,dy); }
    let xsign=(h/16)%2; let ysign=(h/32)%2; var valid:u64=1;
    if (h/8)%2==0 || (h/64)%2!=0 || (h/128)%2!=0 { valid=0; unsafe { volatile_write64(input_state+3280,volatile_read64(input_state+3280)+1); } }
    if valid!=0 && (xsign!=(dx/128)%2 || ysign!=(dy/128)%2) { valid=0; unsafe { volatile_write64(input_state+3288,volatile_read64(input_state+3288)+1); } }
    var ax=dx; if xsign!=0 { ax=256-dx; } var ay=dy; if ysign!=0 { ay=256-dy; }
    if valid!=0 && (ax>80 || ay>80) { valid=0; unsafe { volatile_write64(input_state+3416,volatile_read64(input_state+3416)+1); } }
    if valid==0 {
        unsafe { volatile_write64(input_state+3384,dx); volatile_write64(input_state+3392,dy); volatile_write64(input_state+3376,2); volatile_write64(input_state+3408,0); volatile_write64(input_state+3272,volatile_read64(input_state+3272)+1); }
        return 1;
    }
    unsafe { volatile_write64(input_state+3376,0); }
    var run=volatile_read64(input_state+3408)+1; if run>3 { run=3; } unsafe { volatile_write64(input_state+3408,run); }
    if run<2 { return 1; }
    if volatile_read64(input_state+3488)==0 { unsafe { volatile_write64(input_state+3488,1); } }
    let buttons=h%8; let yscreen=(256-dy)%256;
    unsafe { volatile_write64(input_state+3104,2); volatile_write64(input_state+3176,volatile_read64(input_state+3176)+1); }
    if volatile_read64(input_state+3168)==0 { unsafe { volatile_write64(input_state+3168,1); } serial_marker_v108_ps2_packet_ok(); }
    input_push(input_state,4,0,buttons); input_push(input_state,5,0,dx); input_push(input_state,6,0,yscreen);
    return 1;
}''')

st,en=fn_span(s,'fn ps2_mouse_enable_v108')
blk=s[st:en]
old='''        volatile_write64(input_state+3408,0); volatile_write64(input_state+3416,0);
'''
new='''        volatile_write64(input_state+3408,0); volatile_write64(input_state+3416,0);
        volatile_write64(input_state+3424,0); volatile_write64(input_state+3432,0); volatile_write64(input_state+3440,0); volatile_write64(input_state+3448,0); volatile_write64(input_state+3456,0); volatile_write64(input_state+3464,0); volatile_write64(input_state+3472,0);
        volatile_write64(input_state+3488,0); volatile_write64(input_state+3496,0); volatile_write64(input_state+3504,0); volatile_write64(input_state+3512,0); volatile_write64(input_state+3520,0); volatile_write64(input_state+3528,0); volatile_write64(input_state+3536,0); volatile_write64(input_state+3544,0); volatile_write64(input_state+3552,0);
'''
if blk.count(old)!=1: raise SystemExit('ps2 reset anchor')
blk=blk.replace(old,new,1); s=s[:st]+blk+s[en:]

anchor='fn v108_input_backend_prepare(input_state:u64) -> u64 {'
if s.count(anchor)!=1: raise SystemExit('backend anchor')
selftest=r'''fn ps2_elan4_selftest_v110() -> u64 {
    let a=(4*65536)+(18*256)+52; let b=(17*65536)+(86*256)+120;
    if ps2_elan4_type_v110(a,b)!=2 { return 0; } let xy=ps2_elan4_xy_v110(a,b); if xy!=((564*65536)+1656) { return 0; }
    let st=(4*65536)+(1*256)+0; let sb=(16*65536)+0; if ps2_elan4_type_v110(st,sb)!=1 { return 0; }
    let base=(1000*65536)+1000; if ps2_elan4_rel_v110(base,(1080*65536)+1000)!=(10*256) { return 0; } if ps2_elan4_rel_v110(base,(920*65536)+1000)!=(246*256) { return 0; }
    if ps2_elan4_rel_v110(base,(1000*65536)+1080)!=246 { return 0; } if ps2_elan4_rel_v110(base,(1000*65536)+920)!=10 { return 0; } if ps2_elan4_rel_v110(base,(1700*65536)+1000)!=0 { return 0; } return 1;
}
'''
s=s.replace(anchor,selftest+anchor,1)
st,en=fn_span(s,'fn v108_input_backend_prepare')
blk=s[st:en]
old='''fn v108_input_backend_prepare(input_state:u64) -> u64 {
    ps2_mouse_enable_v108(input_state); return 1;
}'''
new='''fn v108_input_backend_prepare(input_state:u64) -> u64 {
    if ps2_elan4_selftest_v110()==0 { return 0; } ps2_mouse_enable_v108(input_state); return 1;
}'''
if blk!=old: raise SystemExit('backend exact mismatch')
s=s[:st]+new+s[en:]

insert_at=s.index('fn v108_input_overlay_draw')
def label_fn(name,text):
    body=' '.join(f'if gui_draw_char_scaled(surface,((x+{i*6})*65536)+y,({ord(c)}*65536)+1,color)==0 {{ return 0; }}' for i,c in enumerate(text))
    return f'fn {name}(surface:u64,x:u64,y:u64,color:u64) -> u64 {{ {body} return 1; }}\n'
labels=label_fn('v108_text_usbd','USB D L T C R')+label_fn('v108_text_p2a','P2 A0 A1 A2')
s=s[:insert_at]+labels+s[insert_at:]

repl_fn('fn v108_input_overlay_draw',r'''fn v108_input_overlay_draw(surface:u64,state:u64,input_state:u64,xhci:u64) -> u64 {
    if surface==0 || state==0 || input_state==0 { return 0; }
    let w=volatile_read64(surface+16); var px:u64=8; if w>430 { px=w-420; }
    let py:u64=8; let bg:u64=4279308561; let edge:u64=4283268350; let white:u64=4294244347; let green:u64=4286644030; let amber:u64=4294934528; let red:u64=4294907956;
    if display_fill_rect(surface,(px*65536)+py,(410*65536)+220,bg)==0 { return 0; }
    display_fill_rect(surface,(px*65536)+py,(410*65536)+2,edge); display_fill_rect(surface,(px*65536)+(py+218),(410*65536)+2,edge);
    v108_text_input(surface,px+10,py+8,white);
    v108_text_usb(surface,px+10,py+28,white);
    var usb_h:u64=0; var usb_p:u64=0; if xhci!=0 { usb_h=volatile_read64(xhci+416); usb_p=volatile_read64(xhci+112); }
    let usb_r=volatile_read64(input_state+3128); var usb_cc:u64=0; var usb_xfer:u64=0; if xhci!=0 { usb_cc=volatile_read64(xhci+488); usb_xfer=volatile_read64(xhci+504); }
    v108_draw_small_u64(surface,((px+82)*65536)+(py+28),usb_h,green); v108_draw_small_u64(surface,((px+130)*65536)+(py+28),usb_r,green); v108_draw_small_u64(surface,((px+178)*65536)+(py+28),usb_p,amber);
    v108_text_us2(surface,px+10,py+46,white);
    v108_draw_small_u64(surface,((px+82)*65536)+(py+46),volatile_read64(input_state+3192),amber); v108_draw_small_u64(surface,((px+130)*65536)+(py+46),volatile_read64(input_state+3200),white); v108_draw_small_u64(surface,((px+178)*65536)+(py+46),usb_xfer,red); v108_draw_small_u64(surface,((px+232)*65536)+(py+46),usb_cc,red);
    v108_text_usbd(surface,px+10,py+64,white); if xhci!=0 { v108_draw_small_u64(surface,((px+82)*65536)+(py+64),volatile_read64(xhci+576),white); v108_draw_small_u64(surface,((px+130)*65536)+(py+64),volatile_read64(xhci+552),amber); v108_draw_small_u64(surface,((px+178)*65536)+(py+64),volatile_read64(xhci+560),amber); v108_draw_small_u64(surface,((px+226)*65536)+(py+64),volatile_read64(xhci+568),green); v108_draw_small_u64(surface,((px+274)*65536)+(py+64),volatile_read64(xhci+544),white); }
    v108_text_ps2(surface,px+10,py+82,white); v108_draw_small_u64(surface,((px+82)*65536)+(py+82),volatile_read64(input_state+3136),green); v108_draw_small_u64(surface,((px+142)*65536)+(py+82),volatile_read64(input_state+3176),green);
    v108_text_p2raw(surface,px+10,py+100,white); v108_draw_small_u64(surface,((px+82)*65536)+(py+100),volatile_read64(input_state+3224),white); v108_draw_small_u64(surface,((px+148)*65536)+(py+100),volatile_read64(input_state+3232),green); v108_draw_small_u64(surface,((px+214)*65536)+(py+100),volatile_read64(input_state+3240),red);
    v108_text_p2dec(surface,px+10,py+118,white); v108_draw_small_u64(surface,((px+82)*65536)+(py+118),volatile_read64(input_state+3184),white); v108_draw_small_u64(surface,((px+148)*65536)+(py+118),volatile_read64(input_state+3488),amber); v108_draw_small_u64(surface,((px+214)*65536)+(py+118),volatile_read64(input_state+3176),green);
    v108_text_p2rej(surface,px+10,py+136,white); v108_draw_small_u64(surface,((px+82)*65536)+(py+136),volatile_read64(input_state+3528),white); v108_draw_small_u64(surface,((px+148)*65536)+(py+136),volatile_read64(input_state+3272)+volatile_read64(input_state+3280),red); v108_draw_small_u64(surface,((px+214)*65536)+(py+136),volatile_read64(input_state+3288),red);
    v108_text_p2a(surface,px+10,py+154,white); v108_draw_small_u64(surface,((px+82)*65536)+(py+154),volatile_read64(input_state+3432),white); v108_draw_small_u64(surface,((px+148)*65536)+(py+154),volatile_read64(input_state+3440),white); v108_draw_small_u64(surface,((px+214)*65536)+(py+154),volatile_read64(input_state+3448),white);
    v108_text_p2lst(surface,px+10,py+172,white); v108_draw_small_u64(surface,((px+82)*65536)+(py+172),volatile_read64(input_state+3456),white); v108_draw_small_u64(surface,((px+148)*65536)+(py+172),volatile_read64(input_state+3464),white); v108_draw_small_u64(surface,((px+214)*65536)+(py+172),volatile_read64(input_state+3472),white);
    v108_text_src(surface,px+10,py+190,white); v108_draw_small_u64(surface,((px+58)*65536)+(py+190),volatile_read64(input_state+3104),amber); v108_draw_small_u64(surface,((px+112)*65536)+(py+190),volatile_read64(state+8),white); v108_draw_small_u64(surface,((px+220)*65536)+(py+190),volatile_read64(state+16),white);
    return 1;
}''')

st,en=fn_span(s,'fn v108_input_overlay_present')
blk=s[st:en]
if blk.count('(410*65536)+184')!=2: raise SystemExit('present size anchors')
blk=blk.replace('(410*65536)+184','(410*65536)+220')
s=s[:st]+blk+s[en:]

p.write_text(s)
out=hashlib.sha256(p.read_bytes()).hexdigest(); print(out)
if out!='b2dee4fc2c1ca3ad68d4428febf564a2143948ee797ea74ee532ac87b2c14ab6': raise SystemExit(f'unexpected r10 output hash: {out}')
