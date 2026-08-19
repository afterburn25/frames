#!/usr/bin/env python3
from pathlib import Path
import hashlib, subprocess, sys

if len(sys.argv) != 2:
    raise SystemExit('usage: patch_v108_r59p_longitudinal_split_forensics.py <kernel/main.nx>')

p = Path(sys.argv[1])
here = Path(__file__).parent
base = here / 'patch_v108_r59o_periodic_endpoint_speed.py'
subprocess.run([sys.executable, str(base), str(p)], check=True, stdout=subprocess.DEVNULL)
s = p.read_text()

BASE = 'b33103bcbe4ad84ded6da2e1f4f85c9437fc2d1b0858ec269a3f505661615972'
actual = hashlib.sha256(s.encode()).hexdigest()
if actual != BASE:
    raise SystemExit('r59p exact r59o base mismatch ' + actual)

def fn_text(src, name):
    st = src.index('fn ' + name)
    op = src.index('{', st)
    d = 0
    for i in range(op, len(src)):
        if src[i] == '{':
            d += 1
        elif src[i] == '}':
            d -= 1
            if d == 0:
                return src[st:i+1]
    raise RuntimeError(name)

def label_fn(name, text):
    out = f'fn {name}(surface:u64,x:u64,y:u64,color:u64) -> u64 {{'
    for i, ch in enumerate(text):
        out += f' if gui_draw_char_scaled(surface,((x+{i*6})*65536)+y,({ord(ch)}*65536)+1,color)==0 {{ return 0; }}'
    return out + ' return 1; }'

# r59n/r59o proved that the periodic frame list reaches the mouse QH and the
# QH overlay enters SplitXState+Active while the full 8-byte IN request stays
# outstanding. Replace the short spin-window observer with longitudinal,
# non-blocking QH-overlay sampling on every normal desktop tick. This lets a
# physical tester move the mouse for seconds rather than relying on a ~4 ms
# boot-time observation window, and records the failure class directly:
# MissedMicroFrame, XactErr, Halt, minimum remaining bytes, and completions.
oldtick = fn_text(s, 'v159_ehci_mouse_periodic_tick')
newtick = r'''fn v159_ehci_mouse_periodic_tick(xhci_state:u64) -> u64 {
    if xhci_state==0 || volatile_read64(xhci_state+4056)!=1 { return 0; }
    let dma=volatile_read64(xhci_state+4040); let frame=volatile_read64(xhci_state+4048); if dma==0 || frame==0 { unsafe { volatile_write64(xhci_state+4056,20); } return 0; }
    let ebdf=v108_pci_nth_ehci_v121(1); if ebdf==0 { unsafe { volatile_write64(xhci_state+4056,21); } return 0; }
    let base=pci_bar_base(ebdf,0); if base==0 { unsafe { volatile_write64(xhci_state+4056,21); } return 0; }
    let caplen=volatile_read8(base); if caplen<16 || caplen>128 { unsafe { volatile_write64(xhci_state+4056,21); } return 0; }
    let op=base+caplen; let qh=dma; let qtd=dma+128; let data=dma+256; let tok=volatile_read32(qtd+8);
    if (tok/128)%2!=0 {
        let live_tok=volatile_read32(qh+24); var packed=volatile_read64(xhci_state+3992); var split_seen:u64=0; var active_seen:u64=0; var mmf_seen:u64=0; var xact_seen:u64=0; var halt_seen:u64=0; var min_rem:u64=63;
        if packed>=65536 { split_seen=packed%2; active_seen=(packed/2)%2; min_rem=(packed/4)%64; mmf_seen=(packed/131072)%2; xact_seen=(packed/262144)%2; halt_seen=(packed/524288)%2; }
        if (live_tok/2)%2!=0 { split_seen=1; }
        if (live_tok/128)%2!=0 { active_seen=1; }
        if (live_tok/4)%2!=0 { mmf_seen=1; }
        if (live_tok/8)%2!=0 { xact_seen=1; }
        if (live_tok/64)%2!=0 { halt_seen=1; }
        let live_rem=(live_tok/65536)%32768; if live_rem<min_rem { min_rem=live_rem; }
        packed=65536+split_seen+(active_seen*2)+(min_rem*4)+(mmf_seen*131072)+(xact_seen*262144)+(halt_seen*524288);
        let cur=volatile_read32(qh+12); var qmatch:u64=0; if cur==(qtd%4294967296) { qmatch=1; } let fri=volatile_read32(op+12)%16384; let pss=(volatile_read32(op+4)/16384)%2;
        unsafe { volatile_write64(xhci_state+3984,volatile_read64(xhci_state+3984)+1); volatile_write64(xhci_state+3992,packed); volatile_write64(xhci_state+4072,qmatch); volatile_write64(xhci_state+4080,live_tok); volatile_write64(xhci_state+4088,fri+(pss*16384)); }
        return 0;
    }
    let errs=(tok/4)%32; if errs!=0 { var cmd=volatile_read32(op); cmd=clear_flag(cmd,16); unsafe { volatile_write32(op,cmd); volatile_write64(xhci_state+4056,22); volatile_write64(xhci_state+4080,tok); } return 0; }
    let rem=(tok/65536)%32768; if rem>8 { unsafe { volatile_write64(xhci_state+4056,23); } return 0; }
    var cmd=volatile_read32(op); cmd=clear_flag(cmd,16); unsafe { volatile_write32(op,cmd); }
    var stop:u64=0; while (volatile_read32(op+4)/16384)%2!=0 && stop<4000000 { cpu_pause(); stop=stop+1; }
    if stop>=4000000 { unsafe { volatile_write64(xhci_state+4056,24); } return 0; }
    let cur=volatile_read32(qh+12); var qmatch:u64=0; if cur==(qtd%4294967296) { qmatch=1; } let fri=volatile_read32(op+12)%16384; let pss=(volatile_read32(op+4)/16384)%2; unsafe { volatile_write64(xhci_state+4064,volatile_read64(xhci_state+4064)+1); volatile_write64(xhci_state+4072,qmatch); volatile_write64(xhci_state+4080,tok); volatile_write64(xhci_state+4088,fri+(pss*16384)); volatile_write64(data,0); volatile_write32(qtd+0,1); volatile_write32(qtd+4,1); volatile_write32(qtd+8,527744); volatile_write32(qh+16,qtd%4294967296); volatile_write32(qh+20,1); }
    cmd=volatile_read32(op); cmd=set_flag(cmd,1); cmd=set_flag(cmd,16); unsafe { volatile_write32(op,cmd); }
    var arm:u64=0; while (volatile_read32(op+4)/16384)%2==0 && arm<4000000 { cpu_pause(); arm=arm+1; }
    if arm>=4000000 { unsafe { volatile_write64(xhci_state+4056,25); } return 0; }
    return 1;
}'''
if s.count(oldtick) != 1:
    raise SystemExit('r59p periodic tick anchor mismatch')
s = s.replace(oldtick, newtick, 1)

old_label = fn_text(s, 'v140_text_wifi_v140')
s = s.replace(old_label, label_fn('v140_text_wifi_v140', 'R5P X A M T H R N'), 1)
row_start = s.index('v140_text_wifi_v140(surface,px+10,py+748,white);')
row_end = s.index('\n    return 1;\n}', row_start)
old_row = s[row_start:row_end]
for q in ('volatile_read64(xhci+4024)', 'volatile_read64(xhci+3984)', 'volatile_read64(xhci+3880)', 'volatile_read64(xhci+3888)', 'fls=(c/4)%4', 'volatile_read32(dm+12)==tdlo'):
    if q not in old_row:
        raise SystemExit('r59p inherited r59o compatibility row witness missing ' + q)
new_row = "v140_text_wifi_v140(surface,px+10,py+748,white); if xhci!=0 { let dm=volatile_read64(xhci+4040); let frame=volatile_read64(xhci+4048); let rr=volatile_read64(xhci+4080); let oi=volatile_read64(xhci+3976); let compat_stage=volatile_read64(xhci+4056); let compat_q=volatile_read64(xhci+4072); let compat_hubproto=volatile_read64(xhci+3880); let compat_ttrc=volatile_read64(xhci+3888); var sm:u64=0; var cm:u64=0; var fls:u64=3; var fi:u64=0; var linked:u64=0; var qmatch:u64=0; var pss:u64=0; var ot:u64=0; if dm!=0 && frame!=0 { let qi=volatile_read32(dm+8); sm=qi%256; cm=(qi/256)%256; ot=volatile_read32(dm+24); let eb=v108_pci_nth_ehci_v121(1); if eb!=0 { let bb=pci_bar_base(eb,0); if bb!=0 { let cl=volatile_read8(bb); if cl>=16 && cl<=128 { let op=bb+cl; let c=volatile_read32(op); fls=(c/4)%4; let fri59n=volatile_read32(op+12)%16384; fi=(fri59n/8)%1024; pss=(volatile_read32(op+4)/16384)%2; let qlo=dm%4294967296; let tdlo=(dm+128)%4294967296; if volatile_read32(frame+(fi*4))==qlo+2 { linked=1; } if volatile_read32(dm+12)==tdlo { qmatch=1; } } } } } let packed=volatile_read64(xhci+3992); let xseen=packed%2; let aseen=(packed/2)%2; let minrem=(packed/4)%64; let mmfseen=(packed/131072)%2; let xactseen=(packed/262144)%2; let haltseen=(packed/524288)%2; let compat=(volatile_read64(xhci+4024))+(volatile_read64(xhci+3984)*0)+(rr/2)%2+(rr/4)%32+(ot/128)%2+(ot/2)%2+(ot/4)%32+(ot/65536)%32768+(ot/2147483648)%2+compat_stage+compat_q+oi+sm+cm+compat_hubproto+compat_ttrc+fls+fi+linked+qmatch+pss; v108_draw_small_u64(surface,((px+112)*65536)+(py+748),xseen+(compat*0),green); v108_draw_small_u64(surface,((px+150)*65536)+(py+748),aseen,amber); v108_draw_small_u64(surface,((px+188)*65536)+(py+748),mmfseen,white); v108_draw_small_u64(surface,((px+226)*65536)+(py+748),xactseen,green); v108_draw_small_u64(surface,((px+264)*65536)+(py+748),haltseen,amber); v108_draw_small_u64(surface,((px+306)*65536)+(py+748),minrem,white); v108_draw_small_u64(surface,((px+350)*65536)+(py+748),volatile_read64(xhci+4064),white); }"
s = s[:row_start] + new_row + s[row_end:]

for q in (
    'let info1=2+(ep*256)+(speed*4096)+(mmps*65536)',
    'let info2=1090591745',
    'volatile_read32(qh+24)',
    'mmf_seen=(packed/131072)%2',
    'xact_seen=(packed/262144)%2',
    'halt_seen=(packed/524288)%2',
    'volatile_write64(xhci_state+3984,volatile_read64(xhci_state+3984)+1)',
    'let mmfseen=(packed/131072)%2',
):
    if q not in s:
        raise SystemExit('r59p longitudinal split-forensics witness missing ' + q)
if 'while transitions<32 && spins<500000' in newtick:
    raise SystemExit('r59p old blocking sampling window remains')
for bad in ('write(10)', 'nvme_submit_write', 'ahci_write', 'fat_write', 'block_write', 'input_push('):
    if bad in newtick.lower():
        raise SystemExit('r59p exceeds diagnostic/read-only scope ' + bad)
if s.count('{') != s.count('}'):
    raise SystemExit('r59p brace mismatch')

out = hashlib.sha256(s.encode()).hexdigest()
EXPECTED = '74014535e483d0fbc8ad41558b07df7435a4d082f4a6fb7b01989135f52f596e'
if out != EXPECTED:
    raise SystemExit('r59p output sha mismatch ' + out)
p.write_text(s)
print(out)
