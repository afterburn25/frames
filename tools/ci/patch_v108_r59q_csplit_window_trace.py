#!/usr/bin/env python3
from pathlib import Path
import hashlib, subprocess, sys

if len(sys.argv) != 2:
    raise SystemExit('usage: patch_v108_r59q_csplit_window_trace.py <kernel/main.nx>')
p=Path(sys.argv[1])
here=Path(__file__).parent
base=here/'patch_v108_r59p_longitudinal_split_forensics.py'
subprocess.run([sys.executable,str(base),str(p)],check=True,stdout=subprocess.DEVNULL)
s=p.read_text()
BASE='74014535e483d0fbc8ad41558b07df7435a4d082f4a6fb7b01989135f52f596e'
actual=hashlib.sha256(s.encode()).hexdigest()
if actual!=BASE:
    raise SystemExit('r59q exact r59p base mismatch '+actual)

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

# r59p physical proof: SplitXState+Active persists with M/T/H=0, R=8, N=0.
# Trace 20 ms of FRINDEX transitions after arm and count actual scheduled
# Start-Split/C-Split windows plus live overlay-token changes. No transport
# masks, routing, endpoint state, or input behavior are changed.
arm=fn_text(s,'v159_ehci_mouse_periodic_arm')
anchor='''    unsafe { volatile_write64(xhci_state+4048,frame); volatile_write64(xhci_state+4056,1); volatile_write64(xhci_state+4064,0); volatile_write64(xhci_state+4072,0); volatile_write64(xhci_state+4080,0); volatile_write64(xhci_state+4088,0); }\n    return 1;'''
trace='''    unsafe { volatile_write64(xhci_state+4048,frame); volatile_write64(xhci_state+4056,1); volatile_write64(xhci_state+4064,0); volatile_write64(xhci_state+4072,0); volatile_write64(xhci_state+4080,0); volatile_write64(xhci_state+4088,0); }\n    var tr_last:u64=volatile_read32(op+12)%16384; var tr_trans:u64=0; var tr_spins:u64=0; var tr_s:u64=0; var tr_c:u64=0; var tr_changes:u64=0; var tr_prev:u64=volatile_read32(qh+24); var tr_split:u64=0; var tr_active:u64=0; var tr_mmf:u64=0; var tr_xact:u64=0; var tr_halt:u64=0; var tr_min:u64=63;\n    while tr_trans<160 && tr_spins<3000000 {\n        let tr_now=volatile_read32(op+12)%16384;\n        if tr_now!=tr_last {\n            tr_last=tr_now; tr_trans=tr_trans+1; let tr_f=(tr_now/8)%1024; let tr_u=tr_now%8;\n            if volatile_read32(frame+(tr_f*4))==qlo+2 { if tr_u==0 { tr_s=tr_s+1; } if tr_u>=2 && tr_u<=4 { tr_c=tr_c+1; } }\n            let tr_tok=volatile_read32(qh+24); if tr_tok!=tr_prev { tr_changes=tr_changes+1; tr_prev=tr_tok; }\n            if (tr_tok/2)%2!=0 { tr_split=1; } if (tr_tok/128)%2!=0 { tr_active=1; } if (tr_tok/4)%2!=0 { tr_mmf=1; } if (tr_tok/8)%2!=0 { tr_xact=1; } if (tr_tok/64)%2!=0 { tr_halt=1; } let tr_rem=(tr_tok/65536)%32768; if tr_rem<tr_min { tr_min=tr_rem; }\n        } else { cpu_pause(); tr_spins=tr_spins+1; }\n    }\n    let tr_packed=65536+tr_split+(tr_active*2)+(tr_min*4)+(tr_mmf*131072)+(tr_xact*262144)+(tr_halt*524288); unsafe { volatile_write64(xhci_state+3984,tr_s); volatile_write64(xhci_state+4072,tr_c); volatile_write64(xhci_state+4088,tr_changes); volatile_write64(xhci_state+3992,tr_packed); volatile_write64(xhci_state+4080,tr_prev); }\n    return 1;'''
if arm.count(anchor)!=1:
    raise SystemExit('r59q arm trace anchor mismatch '+str(arm.count(anchor)))
s=s.replace(arm,arm.replace(anchor,trace,1),1)

# Preserve the trace counters during r59p's later longitudinal observer.
tick=fn_text(s,'v159_ehci_mouse_periodic_tick')
old="unsafe { volatile_write64(xhci_state+3984,volatile_read64(xhci_state+3984)+1); volatile_write64(xhci_state+3992,packed); volatile_write64(xhci_state+4072,qmatch); volatile_write64(xhci_state+4080,live_tok); volatile_write64(xhci_state+4088,fri+(pss*16384)); }"
new="unsafe { volatile_write64(xhci_state+3992,packed); volatile_write64(xhci_state+4080,live_tok); }"
if tick.count(old)!=1:
    raise SystemExit('r59q active tick preserve anchor mismatch '+str(tick.count(old)))
tick=tick.replace(old,new,1)
old2="let cur=volatile_read32(qh+12); var qmatch:u64=0; if cur==(qtd%4294967296) { qmatch=1; } let fri=volatile_read32(op+12)%16384; let pss=(volatile_read32(op+4)/16384)%2; unsafe { volatile_write64(xhci_state+4064,volatile_read64(xhci_state+4064)+1); volatile_write64(xhci_state+4072,qmatch); volatile_write64(xhci_state+4080,tok); volatile_write64(xhci_state+4088,fri+(pss*16384)); volatile_write64(data,0); volatile_write32(qtd+0,1); volatile_write32(qtd+4,1); volatile_write32(qtd+8,527744); volatile_write32(qh+16,qtd%4294967296); volatile_write32(qh+20,1); }"
new2="let cur=volatile_read32(qh+12); var qmatch:u64=0; if cur==(qtd%4294967296) { qmatch=1; } let fri=volatile_read32(op+12)%16384; let pss=(volatile_read32(op+4)/16384)%2; let compat_done=qmatch+fri+pss; unsafe { volatile_write64(xhci_state+4064,volatile_read64(xhci_state+4064)+1+(compat_done*0)); volatile_write64(xhci_state+4080,tok); volatile_write64(data,0); volatile_write32(qtd+0,1); volatile_write32(qtd+4,1); volatile_write32(qtd+8,527744); volatile_write32(qh+16,qtd%4294967296); volatile_write32(qh+20,1); }"
if tick.count(old2)!=1:
    raise SystemExit('r59q completion tick preserve anchor mismatch '+str(tick.count(old2)))
tick=tick.replace(old2,new2,1)
s=s.replace(fn_text(s,'v159_ehci_mouse_periodic_tick'),tick,1)

oldlabel=fn_text(s,'v140_text_wifi_v140')
s=s.replace(oldlabel,label_fn('v140_text_wifi_v140','R5Q S C D X A E R N'),1)
row_start=s.index('v140_text_wifi_v140(surface,px+10,py+748,white);')
row_end=s.index('\n    return 1;\n}',row_start)
newrow="v140_text_wifi_v140(surface,px+10,py+748,white); if xhci!=0 { let packed=volatile_read64(xhci+3992); let xseen=packed%2; let aseen=(packed/2)%2; let minrem=(packed/4)%64; let mmfseen=(packed/131072)%2; let xactseen=(packed/262144)%2; let haltseen=(packed/524288)%2; let errmask=mmfseen+(xactseen*2)+(haltseen*4); let compat=volatile_read64(xhci+4080)+(volatile_read64(xhci+4024)*0); v108_draw_small_u64(surface,((px+112)*65536)+(py+748),volatile_read64(xhci+3984)+(compat*0),green); v108_draw_small_u64(surface,((px+148)*65536)+(py+748),volatile_read64(xhci+4072),amber); v108_draw_small_u64(surface,((px+184)*65536)+(py+748),volatile_read64(xhci+4088),white); v108_draw_small_u64(surface,((px+220)*65536)+(py+748),xseen,green); v108_draw_small_u64(surface,((px+256)*65536)+(py+748),aseen,amber); v108_draw_small_u64(surface,((px+292)*65536)+(py+748),errmask,white); v108_draw_small_u64(surface,((px+328)*65536)+(py+748),minrem,white); v108_draw_small_u64(surface,((px+364)*65536)+(py+748),volatile_read64(xhci+4064),green); }"
s=s[:row_start]+newrow+s[row_end:]

for q in (
    'while tr_trans<160 && tr_spins<3000000',
    'if tr_u==0 { tr_s=tr_s+1; }',
    'if tr_u>=2 && tr_u<=4 { tr_c=tr_c+1; }',
    'if tr_tok!=tr_prev { tr_changes=tr_changes+1; tr_prev=tr_tok; }',
    'volatile_write64(xhci_state+3984,tr_s)',
    'volatile_write64(xhci_state+4072,tr_c)',
    'volatile_write64(xhci_state+4088,tr_changes)',
):
    if q not in s:
        raise SystemExit('r59q trace witness missing '+q)
scope=s[s.index('fn v159_ehci_mouse_periodic_arm'):s.index('fn v135_hid_control_fallback_prepare')].lower()
for bad in ('write(10)','nvme_submit_write','ahci_write','fat_write','block_write','input_push('):
    if bad in scope:
        raise SystemExit('r59q exceeds diagnostic/read-only scope '+bad)
if s.count('{')!=s.count('}'):
    raise SystemExit('r59q brace mismatch')
out=hashlib.sha256(s.encode()).hexdigest()
EXPECTED='0a607d7281065ab76102a9a3986ca3ee2713a88b112e8ccf99201e3d09ff5870'
if out!=EXPECTED:
    raise SystemExit('r59q output sha mismatch '+out)
p.write_text(s)
print(out)
