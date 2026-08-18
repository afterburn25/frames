#!/usr/bin/env python3
from pathlib import Path
import hashlib, subprocess, sys
if len(sys.argv)!=2: raise SystemExit('usage: patch_v108_r42_hid_nak_tolerant_running.py <kernel/main.nx>')
p=Path(sys.argv[1]); here=Path(__file__).parent
base=here/'patch_v108_r41b_maxxter_usb1_hid_babble_protocol.py'
subprocess.run([sys.executable,str(base),str(p)],check=True,stdout=subprocess.DEVNULL)
s=p.read_text()
BASE='17139d64aafd6d797bab85fc925da51cf13fc0849cfa4f2a3191fcc3e686c814'
if hashlib.sha256(s.encode()).hexdigest()!=BASE: raise SystemExit('r42 r41b base mismatch '+hashlib.sha256(s.encode()).hexdigest())

def rep(old,new,label,count=1):
    global s
    n=s.count(old)
    if n!=count: raise SystemExit(f'r42 {label} count {n}, expected {count}')
    s=s.replace(old,new,count)
def fn_text(name):
    st=s.index('fn '+name); op=s.index('{',st); d=0
    for i in range(op,len(s)):
        if s[i]=='{': d+=1
        elif s[i]=='}':
            d-=1
            if d==0:return s[st:i+1]
    raise SystemExit('unterminated '+name)
def label_fn(name,text):
    out=f'fn {name}(surface:u64,x:u64,y:u64,color:u64) -> u64 {{'
    for i,ch in enumerate(text): out+=f' if gui_draw_char_scaled(surface,((x+{i*6})*65536)+y,({ord(ch)}*65536)+1,color)==0 {{ return 0; }}'
    return out+' return 1; }'

old=fn_text('v136_hid_interrupt_recovery_tick')
new='''fn v136_hid_interrupt_recovery_tick(xhci_state:u64) -> u64 {
    if xhci_state==0 || volatile_read64(xhci_state+416)!=1 { return 1; }
    let state=v136_xhci_endpoint_snapshot(xhci_state); unsafe { volatile_write64(xhci_state+3240,state); }
    if volatile_read64(xhci_state+816)!=0 { return 1; }
    let slot=volatile_read64(xhci_state+136); let dci=volatile_read64(xhci_state+352); let doorbells=volatile_read64(xhci_state+88); if slot==0 || dci<2 || dci>31 || doorbells==0 { return 1; }
    if state==0 { v139_xhci_hid_reconfigure_disabled(xhci_state); return 1; }
    if state==1 {
        unsafe { volatile_write64(xhci_state+2728,0); }
        if volatile_read64(xhci_state+808)==0 { if xhci_hid_arm_continuous(xhci_state,0)==0 { unsafe { volatile_write64(xhci_state+2800,volatile_read64(xhci_state+2800)+1); } } }
        else { unsafe { volatile_write64(xhci_state+3256,volatile_read64(xhci_state+3256)+1); } }
        return 1;
    }
    let now=read_tsc(); let last=volatile_read64(xhci_state+2752); if last!=0 && now>last && now-last<1500000000 { return 1; } unsafe { volatile_write64(xhci_state+2752,now); }
    if (state==2 || state==3) && volatile_read64(xhci_state+2736)<2 {
        var ok:u64=1; if state==2 { if v136_xhci_command_endpoint(xhci_state,14,0)==0 { ok=0; } }
        let next=v137_xhci_hid_rebase_ring(xhci_state); if next==0 || v136_xhci_command_endpoint(xhci_state,16,next)==0 { ok=0; }
        unsafe { volatile_write64(xhci_state+2736,volatile_read64(xhci_state+2736)+1); volatile_write64(xhci_state+808,0); }
        if ok!=0 { if xhci_hid_arm_continuous(xhci_state,0)==0 { unsafe { volatile_write64(xhci_state+2800,volatile_read64(xhci_state+2800)+1); } } }
        return 1;
    }
    return 1;
}'''
rep(old,new,'NAK-tolerant recovery tick')

anchor='''    unsafe { volatile_write64(xhci_state+808,0); volatile_write64(xhci_state+2784,code); volatile_write64(xhci_state+2792,residue); volatile_write64(xhci_state+3224,residue); }
    if code==3 && target {'''
insert='''    unsafe { volatile_write64(xhci_state+808,0); volatile_write64(xhci_state+2784,code); volatile_write64(xhci_state+2792,residue); volatile_write64(xhci_state+3224,residue); }
    if code==26 || code==27 || code==28 {
        unsafe { volatile_write64(xhci_state+3248,volatile_read64(xhci_state+3248)+1); }
        let stopped_state=v136_xhci_endpoint_snapshot(xhci_state); unsafe { volatile_write64(xhci_state+3240,stopped_state); }
        if stopped_state==1 { if xhci_hid_arm_continuous(xhci_state,0)==0 { unsafe { volatile_write64(xhci_state+2800,volatile_read64(xhci_state+2800)+1); } } }
        return 1;
    }
    if code==3 && target {'''
rep(anchor,insert,'Stopped completion quarantine')

oldbab='''    if code==3 && target { let b=volatile_read64(xhci_state+3200)+1; var next=request; if request<16 { next=16; } else { if request<32 { next=32; } } unsafe { volatile_write64(xhci_state+3200,b); volatile_write64(xhci_state+3192,next); volatile_write64(xhci_state+3216,next); } if next>request { if xhci_hid_arm_continuous(xhci_state,0)==0 { unsafe { volatile_write64(xhci_state+2800,volatile_read64(xhci_state+2800)+1); } } } return 1; }'''
newbab='''    if code==3 && target { let b=volatile_read64(xhci_state+3200)+1; var next=request; if request<16 { next=16; } else { if request<32 { next=32; } } unsafe { volatile_write64(xhci_state+3200,b); volatile_write64(xhci_state+3192,next); volatile_write64(xhci_state+3216,next); } let es=v136_xhci_endpoint_snapshot(xhci_state); unsafe { volatile_write64(xhci_state+3240,es); } if es==2 || es==3 { var ok:u64=1; if es==2 { if v136_xhci_command_endpoint(xhci_state,14,0)==0 { ok=0; } } let first=v137_xhci_hid_rebase_ring(xhci_state); if first==0 || v136_xhci_command_endpoint(xhci_state,16,first)==0 { ok=0; } if ok!=0 { if xhci_hid_arm_continuous(xhci_state,0)==0 { unsafe { volatile_write64(xhci_state+2800,volatile_read64(xhci_state+2800)+1); } } } } else { if next>request { if xhci_hid_arm_continuous(xhci_state,0)==0 { unsafe { volatile_write64(xhci_state+2800,volatile_read64(xhci_state+2800)+1); } } } } return 1; }'''
rep(oldbab,newbab,'Babble state recovery')

rep(fn_text('v141_text_r41_v141'),label_fn('v141_text_r41_v141','R42 S I L B R E'),'r42 row label')
oldrow='''    v141_text_r41_v141(surface,px+10,py+730,white); if xhci!=0 { v108_draw_small_u64(surface,((px+112)*65536)+(py+730),volatile_read64(xhci+3152),green); v108_draw_small_u64(surface,((px+150)*65536)+(py+730),volatile_read64(xhci+3160),amber); v108_draw_small_u64(surface,((px+188)*65536)+(py+730),volatile_read64(xhci+3232),white); v108_draw_small_u64(surface,((px+246)*65536)+(py+730),volatile_read64(xhci+3192),white); v108_draw_small_u64(surface,((px+306)*65536)+(py+730),volatile_read64(xhci+3200),amber); v108_draw_small_u64(surface,((px+370)*65536)+(py+730),volatile_read64(xhci+2784),red); }'''
newrow='''    v141_text_r41_v141(surface,px+10,py+730,white); if xhci!=0 { v108_draw_small_u64(surface,((px+112)*65536)+(py+730),volatile_read64(xhci+2696),green); v108_draw_small_u64(surface,((px+150)*65536)+(py+730),volatile_read64(xhci+808),amber); v108_draw_small_u64(surface,((px+188)*65536)+(py+730),volatile_read64(xhci+3192),white); v108_draw_small_u64(surface,((px+246)*65536)+(py+730),volatile_read64(xhci+3200),amber); v108_draw_small_u64(surface,((px+306)*65536)+(py+730),volatile_read64(xhci+816),green); v108_draw_small_u64(surface,((px+370)*65536)+(py+730),volatile_read64(xhci+2784),red); }'''
rep(oldrow,newrow,'r42 full row')
oldcompact='''        v108_draw_small_u64(surface,((px+112)*65536)+(py+730),volatile_read64(xhci+3152),green);
        v108_draw_small_u64(surface,((px+150)*65536)+(py+730),volatile_read64(xhci+3160),amber);
        v108_draw_small_u64(surface,((px+188)*65536)+(py+730),volatile_read64(xhci+3232),white);
        v108_draw_small_u64(surface,((px+246)*65536)+(py+730),volatile_read64(xhci+3192),white);
        v108_draw_small_u64(surface,((px+306)*65536)+(py+730),volatile_read64(xhci+3200),amber);
        v108_draw_small_u64(surface,((px+370)*65536)+(py+730),volatile_read64(xhci+2784),red);'''
newcompact='''        v108_draw_small_u64(surface,((px+112)*65536)+(py+730),volatile_read64(xhci+2696),green);
        v108_draw_small_u64(surface,((px+150)*65536)+(py+730),volatile_read64(xhci+808),amber);
        v108_draw_small_u64(surface,((px+188)*65536)+(py+730),volatile_read64(xhci+3192),white);
        v108_draw_small_u64(surface,((px+246)*65536)+(py+730),volatile_read64(xhci+3200),amber);
        v108_draw_small_u64(surface,((px+306)*65536)+(py+730),volatile_read64(xhci+816),green);
        v108_draw_small_u64(surface,((px+370)*65536)+(py+730),volatile_read64(xhci+2784),red);'''
rep(oldcompact,newcompact,'r42 compact row')

out=hashlib.sha256(s.encode()).hexdigest()
EXPECTED='7e3d5194be2f22792460ffe2f028b1ec39c7a7dd28624f3de9ffba0763cd2c6a'
if out!=EXPECTED: raise SystemExit('r42 output sha mismatch '+out)
p.write_text(s); print(out)
