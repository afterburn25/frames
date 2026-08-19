#!/usr/bin/env python3
from pathlib import Path
import hashlib, subprocess, sys

if len(sys.argv)!=2:
    raise SystemExit('usage: patch_v108_r63_boot3_control_poll_mouse.py <kernel/main.nx>')
p=Path(sys.argv[1]); here=Path(__file__).parent
base=here/'patch_v108_r62_hid_control_poll_mouse.py'
subprocess.run([sys.executable,str(base),str(p)],check=True,stdout=subprocess.DEVNULL)
s=p.read_text()
BASE='6b33eb57003c965d29e918a959df60d801ce79770ffbfdc47ea17177f613578b'
actual=hashlib.sha256(s.encode()).hexdigest()
if actual!=BASE:
    raise SystemExit('r63 exact r62 base mismatch '+actual)

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

# r62 physical evidence: C=6 N=0 D=0 B=0 X=0 Y=0.
# v157_ehci_tt_control returns 6 not only for hard transaction errors but also
# whenever a clean IN data qTD completes short (nonzero remaining-byte count).
# HID 1.11 boot-mouse format guarantees the first three bytes are buttons, X,
# and Y, with bytes 3..n optional. Request exactly those mandatory three bytes
# so a standards-compliant short boot report is no longer misclassified.
# Also do not suppress repeated equal relative-motion reports: identical X/Y
# deltas on consecutive polls are separate movement events.
tick=fn_text(s,'v159_ehci_mouse_periodic_tick')
tick2='''fn v159_ehci_mouse_periodic_tick(xhci_state:u64,input_state:u64) -> u64 {
    if xhci_state==0 || input_state==0 || volatile_read64(xhci_state+4056)!=1 || volatile_read64(input_state+32)!=1 { return 0; }
    let dma=volatile_read64(xhci_state+4040); let mif=volatile_read64(xhci_state+3952); let kep=volatile_read64(xhci_state+3936); if dma==0 || mif>31 || kep==0 { unsafe { volatile_write64(xhci_state+4056,20); } return 0; }
    let getreport=161+(1*256)+(256*65536)+(mif*4294967296)+(3*281474976710656);
    unsafe { volatile_write64(xhci_state+3936,8); } let rc=v157_ehci_tt_control(xhci_state,2,getreport,3); unsafe { volatile_write64(xhci_state+3936,kep); volatile_write64(xhci_state+4088,rc); }
    if rc!=1 { return 0; }
    let data=dma+576; let raw=volatile_read64(data); let prev=volatile_read64(xhci_state+4080); let buttons=volatile_read8(data); let dx=volatile_read8(data+1); let dy=volatile_read8(data+2); var delivered:u64=0;
    unsafe { volatile_write64(xhci_state+4064,volatile_read64(xhci_state+4064)+1); volatile_write64(xhci_state+4080,raw); }
    if buttons!=(prev%256) { input_push(input_state,4,0,buttons); delivered=1; }
    if dx!=0 { input_push(input_state,5,0,dx); delivered=1; }
    if dy!=0 { input_push(input_state,6,0,dy); delivered=1; }
    if delivered!=0 { unsafe { volatile_write64(input_state+3104,1); volatile_write64(input_state+3128,1); volatile_write64(xhci_state+4072,volatile_read64(xhci_state+4072)+1); } }
    return delivered;
}'''
if s.count(tick)!=1: raise SystemExit('r63 live tick anchor mismatch')
s=s.replace(tick,tick2,1)
s=s.replace(fn_text(s,'v140_text_wifi_v140'),label_fn('v140_text_wifi_v140','R63 C N D B X Y'),1)

live=s[s.index('fn v159_ehci_mouse_periodic_arm'):s.index('fn v162_r61_periodic_reference_arm')]
for q in (
    'let getreport=161+(1*256)+(256*65536)+(mif*4294967296)+(3*281474976710656)',
    'v157_ehci_tt_control(xhci_state,2,getreport,3)',
    'if buttons!=(prev%256)',
    'if dx!=0 { input_push(input_state,5,0,dx); delivered=1; }',
    'if dy!=0 { input_push(input_state,6,0,dy); delivered=1; }',
    'volatile_write64(xhci_state+4064,volatile_read64(xhci_state+4064)+1)',
    'volatile_write64(xhci_state+4072,volatile_read64(xhci_state+4072)+1)',
):
    if q not in live: raise SystemExit('r63 boot3 control-poll witness missing '+q)
if 'if raw!=prev' in live: raise SystemExit('r63 still suppresses repeated equal relative reports')
if '(8*281474976710656)' in live or 'v157_ehci_tt_control(xhci_state,2,getreport,8)' in live:
    raise SystemExit('r63 live GET_REPORT still requests eight bytes')
for forbidden in ('volatile_write32(op+20,flo)','cmd=set_flag(cmd,16)','volatile_write32(qtd+8,560512)'):
    if forbidden in live: raise SystemExit('r63 live periodic path rearmed '+forbidden)
for bad in ('write(10)','nvme_submit_write','ahci_write','fat_write','block_write'):
    if bad in live.lower(): raise SystemExit('r63 exceeds read-only input scope '+bad)
if s.count('v162_r61_periodic_reference_arm(')!=1 or s.count('v162_r61_periodic_reference_tick(')!=1 or s.count('v162_r61_gate_reference(')!=1:
    raise SystemExit('r63 reference helper reachability contract failed')
if s.count('{')!=s.count('}'):
    raise SystemExit('r63 brace mismatch')
out=hashlib.sha256(s.encode()).hexdigest()
EXPECTED='8f5b1dbad31aaaf68db45ea53bf73df45ae1ae05d83dc96979d1665485721cfd'
if out!=EXPECTED:
    raise SystemExit('r63 output sha mismatch '+out)
p.write_text(s)
print(out)
