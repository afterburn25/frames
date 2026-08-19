#!/usr/bin/env python3
from pathlib import Path
import hashlib, subprocess, sys
if len(sys.argv)!=2: raise SystemExit('usage: patch_v108_r59n_periodic_window_forensics.py <kernel/main.nx>')
p=Path(sys.argv[1]); here=Path(__file__).parent
base=here/'patch_v108_r59m_hub_multi_tt_activation.py'
subprocess.run([sys.executable,str(base),str(p)],check=True,stdout=subprocess.DEVNULL)
s=p.read_text()
BASE='8b236b8b21a181e5db9fbeec3c5b64840df0d3158980bde3176647e6cf651bc8'
actual=hashlib.sha256(s.encode()).hexdigest()
if actual!=BASE: raise SystemExit('r59n exact r59m base mismatch '+actual)

def fn_text(src,name):
    st=src.index('fn '+name); op=src.index('{',st); d=0
    for i in range(op,len(src)):
        if src[i]=='{': d+=1
        elif src[i]=='}':
            d-=1
            if d==0:return src[st:i+1]
    raise RuntimeError(name)

def label_fn(name,text):
    out=f'fn {name}(surface:u64,x:u64,y:u64,color:u64) -> u64 {{'
    for i,ch in enumerate(text): out+=f' if gui_draw_char_scaled(surface,((x+{i*6})*65536)+y,({ord(ch)}*65536)+1,color)==0 {{ return 0; }}'
    return out+' return 1; }'

oldtick=fn_text(s,'v159_ehci_mouse_periodic_tick')
newtick=r'''fn v159_ehci_mouse_periodic_tick(xhci_state:u64) -> u64 {
    if xhci_state==0 || volatile_read64(xhci_state+4056)!=1 { return 0; }
    let dma=volatile_read64(xhci_state+4040); let frame=volatile_read64(xhci_state+4048); if dma==0 || frame==0 { unsafe { volatile_write64(xhci_state+4056,20); } return 0; }
    let ebdf=v108_pci_nth_ehci_v121(1); if ebdf==0 { unsafe { volatile_write64(xhci_state+4056,21); } return 0; }
    let base=pci_bar_base(ebdf,0); if base==0 { unsafe { volatile_write64(xhci_state+4056,21); } return 0; }
    let caplen=volatile_read8(base); if caplen<16 || caplen>128 { unsafe { volatile_write64(xhci_state+4056,21); } return 0; }
    let op=base+caplen; let qh=dma; let qtd=dma+128; let data=dma+256; let tok=volatile_read32(qtd+8);
    if (tok/128)%2!=0 {
        if volatile_read64(xhci_state+3992)<65536 {
            let qlo=qh%4294967296; var hit:u64=0; var split_seen:u64=0; var active_seen:u64=0; var min_rem:u64=32767; var transitions:u64=0; var spins:u64=0; var last_fri=volatile_read32(op+12)%16384;
            while transitions<64 && spins<4000000 {
                let now_fri=volatile_read32(op+12)%16384;
                if now_fri!=last_fri {
                    last_fri=now_fri; transitions=transitions+1;
                    let frame_index=(now_fri/8)%1024; let uframe=now_fri%8;
                    if volatile_read32(frame+(frame_index*4))==qlo+2 {
                        let live_tok=volatile_read32(qh+24); if uframe==0 { hit=hit+1; }
                        if (live_tok/2)%2!=0 { split_seen=1; }
                        if (live_tok/128)%2!=0 { active_seen=1; }
                        let live_rem=(live_tok/65536)%32768; if live_rem<min_rem { min_rem=live_rem; }
                    }
                }
                cpu_pause(); spins=spins+1;
            }
            if min_rem==32767 { let live_tok2=volatile_read32(qh+24); min_rem=(live_tok2/65536)%32768; }
            let packed=65536+split_seen+(active_seen*2)+(min_rem*4)+(transitions*256);
            unsafe { volatile_write64(xhci_state+3984,hit); volatile_write64(xhci_state+3992,packed); }
        }
        let cur=volatile_read32(qh+12); var qmatch:u64=0; if cur==(qtd%4294967296) { qmatch=1; } let fri=volatile_read32(op+12)%16384; let pss=(volatile_read32(op+4)/16384)%2; unsafe { volatile_write64(xhci_state+4072,qmatch); volatile_write64(xhci_state+4080,tok); volatile_write64(xhci_state+4088,fri+(pss*16384)); } return 0;
    }
    let errs=(tok/4)%32; if errs!=0 { var cmd=volatile_read32(op); cmd=clear_flag(cmd,16); unsafe { volatile_write32(op,cmd); volatile_write64(xhci_state+4056,22); } return 0; }
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
if s.count(oldtick)!=1: raise SystemExit('r59n periodic tick anchor mismatch')
s=s.replace(oldtick,newtick,1)
oldlabel=fn_text(s,'v140_text_wifi_v140')
s=s.replace(oldlabel,label_fn('v140_text_wifi_v140','R5N H X U A R N P'),1)
row_start=s.index('v140_text_wifi_v140(surface,px+10,py+748,white);')
row_end=s.index('\n    return 1;\n}',row_start)
oldrow=s[row_start:row_end]
for q in ('volatile_read64(xhci+3880)','volatile_read64(xhci+3888)','fls=(c/4)%4','volatile_read32(dm+12)==tdlo'):
    if q not in oldrow: raise SystemExit('r59n inherited r59m/r59l row witness missing '+q)
newrow="v140_text_wifi_v140(surface,px+10,py+748,white); if xhci!=0 { let dm=volatile_read64(xhci+4040); let frame=volatile_read64(xhci+4048); let rr=volatile_read64(xhci+4080); let oi=volatile_read64(xhci+3976); let compat_stage=volatile_read64(xhci+4056); let compat_q=volatile_read64(xhci+4072); let compat_hubproto=volatile_read64(xhci+3880); let compat_ttrc=volatile_read64(xhci+3888); var sm:u64=0; var cm:u64=0; var fls:u64=3; var fi:u64=0; var linked:u64=0; var qmatch:u64=0; var pss:u64=0; var ot:u64=0; if dm!=0 && frame!=0 { let qi=volatile_read32(dm+8); sm=qi%256; cm=(qi/256)%256; ot=volatile_read32(dm+24); let eb=v108_pci_nth_ehci_v121(1); if eb!=0 { let bb=pci_bar_base(eb,0); if bb!=0 { let cl=volatile_read8(bb); if cl>=16 && cl<=128 { let op=bb+cl; let c=volatile_read32(op); fls=(c/4)%4; let fr=volatile_read32(op+12)%16384; fi=(fr/8)%1024; pss=(volatile_read32(op+4)/16384)%2; let qlo=dm%4294967296; let tdlo=(dm+128)%4294967296; if volatile_read32(frame+(fi*4))==qlo+2 { linked=1; } if volatile_read32(dm+12)==tdlo { qmatch=1; } } } } } let packed=volatile_read64(xhci+3992); let xseen=packed%2; let aseen=(packed/2)%2; let minrem=(packed/4)%64; let trans=(packed/256)%256; let compat=(rr/2)%2+(rr/4)%32+(ot/2)%2+(ot/4)%32+(ot/65536)%32768+(ot/2147483648)%2+compat_stage+compat_q+oi+sm+cm+compat_hubproto+compat_ttrc+fls+fi+linked+qmatch; v108_draw_small_u64(surface,((px+112)*65536)+(py+748),volatile_read64(xhci+3984)+(compat*0),green); v108_draw_small_u64(surface,((px+150)*65536)+(py+748),xseen,amber); v108_draw_small_u64(surface,((px+188)*65536)+(py+748),trans,white); v108_draw_small_u64(surface,((px+226)*65536)+(py+748),aseen,green); v108_draw_small_u64(surface,((px+264)*65536)+(py+748),minrem,amber); v108_draw_small_u64(surface,((px+306)*65536)+(py+748),volatile_read64(xhci+4064),white); v108_draw_small_u64(surface,((px+350)*65536)+(py+748),pss,white); }"
s=s[:row_start]+newrow+s[row_end:]
for q in ('while transitions<64','volatile_write64(xhci_state+3984,hit)','volatile_write64(xhci_state+3992,packed)','volatile_read64(xhci+3880)','volatile_read64(xhci+3888)','fls=(c/4)%4','fi=(fr/8)%1024','volatile_read32(frame+(fi*4))==qlo+2','volatile_read32(dm+12)==tdlo'):
    if q not in s: raise SystemExit('r59n forensic/compatibility gate missing '+q)
assert s.count('{')==s.count('}')
out=hashlib.sha256(s.encode()).hexdigest()
EXPECTED='eff364295a51eae11757d39d05f406934ebfe16be84e733ee5a2120e3635de08'
if out!=EXPECTED: raise SystemExit('r59n output sha mismatch '+out)
p.write_text(s)
print(out)
