#!/usr/bin/env python3
from pathlib import Path
import hashlib, subprocess, sys, re
if len(sys.argv)!=2: raise SystemExit('usage: patch_v108_r42_maxxter_idle_stop_suppression.py <kernel/main.nx>')
p=Path(sys.argv[1])
base=Path(__file__).with_name('patch_v108_r41b_maxxter_usb1_hid_babble_protocol.py')
subprocess.run([sys.executable,str(base),str(p)],check=True,stdout=subprocess.DEVNULL)
s=p.read_text()
BASE='17139d64aafd6d797bab85fc925da51cf13fc0849cfa4f2a3191fcc3e686c814'
if hashlib.sha256(s.encode()).hexdigest()!=BASE: raise SystemExit('r41b base mismatch '+hashlib.sha256(s.encode()).hexdigest())

def fn_text(name):
    st=s.index('fn '+name); op=s.index('{',st); d=0
    for i in range(op,len(s)):
        if s[i]=='{': d+=1
        elif s[i]=='}':
            d-=1
            if d==0:return s[st:i+1]
    raise SystemExit('unterminated '+name)
def fnrep(name,new):
    global s
    old=fn_text(name)
    if s.count(old)!=1: raise SystemExit(name+' replacement ambiguity')
    s=s.replace(old,new,1)
def label_fn(name,text):
    out=f'fn {name}(surface:u64,x:u64,y:u64,color:u64) -> u64 {{'
    for i,ch in enumerate(text): out+=f' if gui_draw_char_scaled(surface,((x+{i*6})*65536)+y,({ord(ch)}*65536)+1,color)==0 {{ return 0; }}'
    return out+' return 1; }'

r=fn_text('v136_hid_interrupt_recovery_tick')
old='''    let slot=volatile_read64(xhci_state+136); let dci=volatile_read64(xhci_state+352); let doorbells=volatile_read64(xhci_state+88); if slot==0 || dci<2 || dci>31 || doorbells==0 { return 1; }\n    if state==0 { v139_xhci_hid_reconfigure_disabled(xhci_state); return 1; }\n    if state==1 {'''
new='''    let slot=volatile_read64(xhci_state+136); let dci=volatile_read64(xhci_state+352); let doorbells=volatile_read64(xhci_state+88); if slot==0 || dci<2 || dci>31 || doorbells==0 { return 1; }\n    let speed=volatile_read64(xhci_state+184); let vid=volatile_read64(xhci_state+272); let pid=volatile_read64(xhci_state+280); let protocol=volatile_read64(xhci_state+336); let maxxter_idle=((speed==1 || speed==2) && vid==9354 && pid==4267 && protocol==2);\n    if state==0 { v139_xhci_hid_reconfigure_disabled(xhci_state); return 1; }\n    if state==1 {\n        // A healthy idle interrupt-IN HID endpoint may NAK indefinitely. Never\n        // manufacture Stop Endpoint solely because this exact mouse is idle.\n        if maxxter_idle { if volatile_read64(xhci_state+808)==0 { if xhci_hid_arm_continuous(xhci_state,0)==0 { unsafe { volatile_write64(xhci_state+2800,volatile_read64(xhci_state+2800)+1); } } } return 1; }'''
if r.count(old)!=1: raise SystemExit('r42 idle recovery anchor mismatch')
fnrep('v136_hid_interrupt_recovery_tick',r.replace(old,new,1))

r=fn_text('xhci_hid_poll_continuous')
old='''    unsafe { volatile_write64(xhci_state+808,0); volatile_write64(xhci_state+2784,code); volatile_write64(xhci_state+2792,residue); volatile_write64(xhci_state+3224,residue); }\n    if code==3 && target {'''
new='''    unsafe { volatile_write64(xhci_state+808,0); volatile_write64(xhci_state+2784,code); volatile_write64(xhci_state+2792,residue); volatile_write64(xhci_state+3224,residue); }\n    if code==26 && target { let seen=volatile_read64(xhci_state+3240)+1; let epstate=v136_xhci_endpoint_snapshot(xhci_state); unsafe { volatile_write64(xhci_state+3240,seen); volatile_write64(xhci_state+3248,epstate); } if epstate==1 { if xhci_hid_arm_continuous(xhci_state,0)==0 { unsafe { volatile_write64(xhci_state+2800,volatile_read64(xhci_state+2800)+1); } } } return 1; }\n    if code==3 && target {'''
if r.count(old)!=1: raise SystemExit('r42 stopped-completion anchor mismatch')
fnrep('xhci_hid_poll_continuous',r.replace(old,new,1))

old='volatile_write64(xhci_state+3208,0); volatile_write64(xhci_state+3216,0); volatile_write64(xhci_state+3224,0); }'
if s.count(old)<1: raise SystemExit('r42 telemetry reset anchor missing')
s=s.replace(old,'volatile_write64(xhci_state+3208,0); volatile_write64(xhci_state+3216,0); volatile_write64(xhci_state+3224,0); volatile_write64(xhci_state+3240,0); volatile_write64(xhci_state+3248,0); }',1)
fnrep('v141_text_r41_v141',label_fn('v141_text_r41_v141','R42 S N A O E'))
pat=re.compile(r'v141_text_r41_v141\(surface,px\+10,py\+730,white\);\s*if xhci!=0 \{\s*v108_draw_small_u64\(surface,\(\(px\+112\)\*65536\)\+\(py\+730\),volatile_read64\(xhci\+3152\),green\);\s*v108_draw_small_u64\(surface,\(\(px\+150\)\*65536\)\+\(py\+730\),volatile_read64\(xhci\+3160\),amber\);\s*v108_draw_small_u64\(surface,\(\(px\+188\)\*65536\)\+\(py\+730\),volatile_read64\(xhci\+3232\),white\);\s*v108_draw_small_u64\(surface,\(\(px\+246\)\*65536\)\+\(py\+730\),volatile_read64\(xhci\+3192\),white\);\s*v108_draw_small_u64\(surface,\(\(px\+306\)\*65536\)\+\(py\+730\),volatile_read64\(xhci\+3200\),amber\);\s*v108_draw_small_u64\(surface,\(\(px\+370\)\*65536\)\+\(py\+730\),volatile_read64\(xhci\+2784\),red\);\s*\}')
row='v141_text_r41_v141(surface,px+10,py+730,white); if xhci!=0 { v108_draw_small_u64(surface,((px+112)*65536)+(py+730),volatile_read64(xhci+2696),green); v108_draw_small_u64(surface,((px+170)*65536)+(py+730),volatile_read64(xhci+3240),amber); v108_draw_small_u64(surface,((px+228)*65536)+(py+730),volatile_read64(xhci+808),white); v108_draw_small_u64(surface,((px+286)*65536)+(py+730),volatile_read64(xhci+2816),amber); v108_draw_small_u64(surface,((px+370)*65536)+(py+730),volatile_read64(xhci+2784),red); }'
s,n=pat.subn(row,s)
if n!=2: raise SystemExit(f'r42 diagnostic row replacement count {n}')

out=hashlib.sha256(s.encode()).hexdigest(); EXPECTED='0e39870fa395f225c23d4027a51f08054026e450c7ed675c9912d005002bcb9f'
if out!=EXPECTED: raise SystemExit('r42 output sha mismatch '+out)
p.write_text(s); print(out)
