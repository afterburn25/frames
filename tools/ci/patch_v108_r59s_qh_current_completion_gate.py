#!/usr/bin/env python3
from pathlib import Path
import hashlib, subprocess, sys

if len(sys.argv)!=2:
    raise SystemExit('usage: patch_v108_r59s_qh_current_completion_gate.py <kernel/main.nx>')
p=Path(sys.argv[1]); here=Path(__file__).parent
base=here/'patch_v108_r59r_qh_overlay_completion_capture.py'
subprocess.run([sys.executable,str(base),str(p)],check=True,stdout=subprocess.DEVNULL)
s=p.read_text()
BASE='cb5144a7abb7e610cf893f942360e1b9321fd402494f77e07513cbdcb231a324'
actual=hashlib.sha256(s.encode()).hexdigest()
if actual!=BASE:
    raise SystemExit('r59s exact r59r base mismatch '+actual)

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

# r59r physical result: N remains zero and all report bytes remain zero even
# though r59q already proved a QH-overlay transition to inactive/no-error/zero
# remaining. The only new pre-completion condition introduced by r59r was the
# QH.Next==Terminate requirement. QH.Current==qTD already proves hardware
# fetched this qTD, so Next need not be Terminate to distinguish an untouched
# overlay. Remove only that redundant blocker and preserve every other safety
# condition. Also publish a packed gate snapshot before the decision:
#   bit/value 0..4 stage base=1, +32 QH.current match, +64 Next.T,
#   +128 Active, +256*error-mask, +8192*remaining-bytes.
tick=fn_text(s,'v159_ehci_mouse_periodic_tick')
old='''    let op=base+caplen; let qh=dma; let qtd=dma+128; let data=dma+256; let qtdlo=qtd%4294967296; let qtd_tok=volatile_read32(qtd+8); let cur=volatile_read32(qh+12); let next=volatile_read32(qh+16); let live_tok=volatile_read32(qh+24);\n    if cur!=qtdlo || next!=1 { return 0; }\n    if (live_tok/128)%2!=0 {'''
new='''    let op=base+caplen; let qh=dma; let qtd=dma+128; let data=dma+256; let qtdlo=qtd%4294967296; let qtd_tok=volatile_read32(qtd+8); let cur=volatile_read32(qh+12); let next=volatile_read32(qh+16); let live_tok=volatile_read32(qh+24);\n    var qmatch:u64=0; if cur==qtdlo { qmatch=1; } let nterm=next%2; let active=(live_tok/128)%2; let errs=(live_tok/4)%32; let rem=(live_tok/65536)%32768; let gate=1+(qmatch*32)+(nterm*64)+(active*128)+(errs*256)+(rem*8192); unsafe { volatile_write64(xhci_state+3984,gate); }\n    if cur!=qtdlo { return 0; }\n    if active!=0 {'''
if tick.count(old)!=1:
    raise SystemExit('r59s QH completion-gate anchor mismatch '+str(tick.count(old)))
tick=tick.replace(old,new,1)
old2='''    let errs=(live_tok/4)%32; if errs!=0 { var cmd=volatile_read32(op); cmd=clear_flag(cmd,16); unsafe { volatile_write32(op,cmd); volatile_write64(xhci_state+4056,22); volatile_write64(xhci_state+4080,live_tok); } return 0; }\n    let rem=(live_tok/65536)%32768; if rem>8 { unsafe { volatile_write64(xhci_state+4056,23); volatile_write64(xhci_state+4080,live_tok); } return 0; }'''
new2='''    if errs!=0 { var cmd=volatile_read32(op); cmd=clear_flag(cmd,16); unsafe { volatile_write32(op,cmd); volatile_write64(xhci_state+4056,22); volatile_write64(xhci_state+4080,live_tok); } return 0; }\n    if rem>8 { unsafe { volatile_write64(xhci_state+4056,23); volatile_write64(xhci_state+4080,live_tok); } return 0; }'''
if tick.count(old2)!=1:
    raise SystemExit('r59s status-field anchor mismatch '+str(tick.count(old2)))
tick=tick.replace(old2,new2,1)
old3='''    var qmatch:u64=0; if cur==qtdlo { qmatch=1; } let fri=volatile_read32(op+12)%16384; let pss=(volatile_read32(op+4)/16384)%2; let compat_done=qmatch+fri+pss+(qtd_tok*0);'''
new3='''    let fri=volatile_read32(op+12)%16384; let pss=(volatile_read32(op+4)/16384)%2; let compat_done=qmatch+fri+pss+(qtd_tok*0);'''
if tick.count(old3)!=1:
    raise SystemExit('r59s qmatch reuse anchor mismatch '+str(tick.count(old3)))
tick=tick.replace(old3,new3,1)
s=s.replace(fn_text(s,'v159_ehci_mouse_periodic_tick'),tick,1)

# Make one compact physical row useful whether this repair succeeds or not.
# G is the packed pre-decision gate snapshot, N the completion count, followed
# by the first four report bytes (boot-mouse buttons/X/Y/wheel-sized payload).
# Keep bytes 4-7 as invisible compatibility witnesses for the prior r59r cert.
s=s.replace(fn_text(s,'v140_text_wifi_v140'),label_fn('v140_text_wifi_v140','R5S G N 0 1 2 3'),1)
row_start=s.index('v140_text_wifi_v140(surface,px+10,py+748,white);')
row_end=s.index('\n    return 1;\n}',row_start)
row=s[row_start:row_end]
marker='let raw=volatile_read64(xhci+4088); '
if row.count(marker)!=1:
    raise SystemExit('r59s r59r row prefix anchor mismatch '+str(row.count(marker)))
prefix=row[:row.index(marker)+len(marker)]
newdraw="let rawcompat=((raw/4294967296)%256)+((raw/1099511627776)%256)+((raw/281474976710656)%256)+((raw/72057594037927936)%256); v108_draw_small_u64(surface,((px+108)*65536)+(py+748),volatile_read64(xhci+3984)+(compat*0)+(rawcompat*0),green); v108_draw_small_u64(surface,((px+160)*65536)+(py+748),volatile_read64(xhci+4064),amber); v108_draw_small_u64(surface,((px+212)*65536)+(py+748),raw%256,white); v108_draw_small_u64(surface,((px+252)*65536)+(py+748),(raw/256)%256,green); v108_draw_small_u64(surface,((px+292)*65536)+(py+748),(raw/65536)%256,amber); v108_draw_small_u64(surface,((px+332)*65536)+(py+748),(raw/16777216)%256,white); }"
s=s[:row_start]+prefix+newdraw+s[row_end:]

scope=s[s.index('fn v159_ehci_mouse_periodic_arm'):s.index('fn v135_hid_control_fallback_prepare')]
for q in (
    'let next=volatile_read32(qh+16)',
    'let live_tok=volatile_read32(qh+24)',
    'if cur!=qtdlo { return 0; }',
    'let nterm=next%2',
    'let active=(live_tok/128)%2',
    'let errs=(live_tok/4)%32',
    'let rem=(live_tok/65536)%32768',
    'volatile_write64(xhci_state+3984,gate)',
    'let raw=volatile_read64(data)',
    'volatile_write64(xhci_state+4088,raw)',
    'volatile_write32(qh+16,qtdlo)',
):
    if q not in scope:
        raise SystemExit('r59s current-only completion witness missing '+q)
if 'if cur!=qtdlo || next!=1 { return 0; }' in scope:
    raise SystemExit('r59s redundant QH.Next completion blocker remains')
for q in ('volatile_read64(xhci+4056)','volatile_read64(xhci+4064)','volatile_read64(xhci+4072)','volatile_read64(xhci+4080)','sm=qi%256','cm=(qi/256)%256','(raw/4294967296)%256','(raw/72057594037927936)%256'):
    if q not in s:
        raise SystemExit('r59s inherited compatibility witness missing '+q)
for bad in ('write(10)','nvme_submit_write','ahci_write','fat_write','block_write','input_push('):
    if bad in scope.lower():
        raise SystemExit('r59s exceeds raw diagnostic/read-only scope '+bad)
if s.count('{')!=s.count('}'):
    raise SystemExit('r59s brace mismatch')
out=hashlib.sha256(s.encode()).hexdigest()
EXPECTED='dde4777ee5be0e925c2ec487310008343e27cba2b30ba881c996b9cfcad1cb14'
if out!=EXPECTED:
    raise SystemExit('r59s output sha mismatch '+out)
p.write_text(s)
print(out)
