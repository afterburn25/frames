#!/usr/bin/env python3
from pathlib import Path
import hashlib, subprocess, sys

if len(sys.argv)!=2:
    raise SystemExit('usage: patch_v108_r64_getreport_qtd_forensics.py <kernel/main.nx>')
p=Path(sys.argv[1]); here=Path(__file__).parent
base=here/'patch_v108_r63_boot3_control_poll_mouse.py'
subprocess.run([sys.executable,str(base),str(p)],check=True,stdout=subprocess.DEVNULL)
s=p.read_text()
BASE='8f5b1dbad31aaaf68db45ea53bf73df45ae1ae05d83dc96979d1665485721cfd'
actual=hashlib.sha256(s.encode()).hexdigest()
if actual!=BASE:
    raise SystemExit('r64 exact r63 base mismatch '+actual)

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

# r63 physical evidence is still C=6 with a 3-byte boot report request.
# Therefore the earlier short-8-byte hypothesis is ruled out. Do not change
# transport behavior in r64. Instead expose the exact setup/data/status qTD
# state for the live GET_REPORT transaction so the next repair is evidence-led.
helper=fn_text(s,'v157_ehci_tt_control')
old_tail='''    let stok=volatile_read32(qt+8); let qstok=volatile_read32(qs+8); let serr=(stok/64)%2; let qerr=(qstok/64)%2;
    if serr!=0 || qerr!=0 || ((stok/4)%16)!=0 || ((qstok/4)%16)!=0 { return 6; }
    if spins>=16000000 || (stok/128)%2!=0 { return 5; }
    if length!=0 { let dtok=volatile_read32(qd+8); if (dtok/64)%2!=0 || ((dtok/4)%16)!=0 || (dtok/128)%2!=0 || ((dtok/65536)%32768)!=0 { return 6; } }
    return 1;
}'''
new_tail='''    let stok=volatile_read32(qt+8); let qstok=volatile_read32(qs+8); let serr=(stok/64)%2; let qerr=(qstok/64)%2;
    var is_getreport:u64=0; if setupv%256==161 && ((setupv/256)%256)==1 { is_getreport=1; }
    if is_getreport!=0 {
        let spack=((stok/128)%2)+(((stok/64)%2)*2)+(((stok/4)%16)*4);
        let qpack=((qstok/128)%2)+(((qstok/64)%2)*2)+(((qstok/4)%16)*4);
        unsafe { volatile_write64(xhci_state+3992,spack); volatile_write64(xhci_state+4000,qpack); }
    }
    if serr!=0 || qerr!=0 || ((stok/4)%16)!=0 || ((qstok/4)%16)!=0 { return 6; }
    if spins>=16000000 || (stok/128)%2!=0 { return 5; }
    if length!=0 {
        let dtok=volatile_read32(qd+8);
        if is_getreport!=0 {
            let dactive=(dtok/128)%2; let dhalt=(dtok/64)%2; let derr=(dtok/4)%16; let drem=(dtok/65536)%32768;
            let dpack=dactive+(dhalt*2)+(derr*4)+(drem*64);
            let raw3=volatile_read8(data)+(volatile_read8(data+1)*256)+(volatile_read8(data+2)*65536);
            unsafe { volatile_write64(xhci_state+3984,dpack); volatile_write64(xhci_state+4008,raw3); }
        }
        if (dtok/64)%2!=0 || ((dtok/4)%16)!=0 || (dtok/128)%2!=0 || ((dtok/65536)%32768)!=0 { return 6; }
    }
    return 1;
}'''
if helper.count(old_tail)!=1:
    raise SystemExit('r64 control helper tail anchor mismatch '+str(helper.count(old_tail)))
s=s.replace(helper,helper.replace(old_tail,new_tail,1),1)

s=s.replace(fn_text(s,'v140_text_wifi_v140'),label_fn('v140_text_wifi_v140','R64 C A H E R S Q D'),1)
rs=s.index('v140_text_wifi_v140(surface,px+10,py+748,white);')
re=s.index('\n    return 1;\n}',rs)
newrow="v140_text_wifi_v140(surface,px+10,py+748,white); if xhci!=0 { let rr=volatile_read64(xhci+4080); let dm=volatile_read64(xhci+4040); var sm:u64=0; var cm:u64=0; var gate:u64=0; if dm!=0 { let qi=volatile_read32(dm+8); sm=qi%256; cm=(qi/256)%256; let qtdtok=volatile_read32(dm+136); let qtok=volatile_read32(dm+24); let ta=(qtdtok/128)%2; let qa=(qtok/128)%2; let sx=(qtok/2)%2; let er=((qtdtok/4)%32)+((qtok/4)%32); let rem=(qtdtok/65536)%32768; let orem=(qtok/65536)%32768; gate=1+(ta*2)+(qa*4)+(sx*8)+(er*16)+(rem*1024)+(orem*32768); } let compat_i0=volatile_read64(xhci+3976); let compat_x=(rr/2)%2; let compat_e=(rr/4)%32; let compat_a=volatile_read64(xhci+3984); let compat_i=volatile_read64(xhci+3992); let compat_t=volatile_read64(xhci+4000); let compat_s=volatile_read64(xhci+4056); let compat_n=volatile_read64(xhci+4064); let compat_d=volatile_read64(xhci+4072); let actual=volatile_read64(xhci+4088); let raw3=volatile_read64(xhci+4008); let zero=(compat_i0*0)+(compat_x*0)+(compat_e*0)+(compat_s*0)+(compat_n*0)+(compat_d*0)+(sm*0)+(cm*0)+(gate*0); v108_draw_small_u64(surface,((px+112)*65536)+(py+748),actual+zero,green); v108_draw_small_u64(surface,((px+150)*65536)+(py+748),compat_a%2,amber); v108_draw_small_u64(surface,((px+188)*65536)+(py+748),(compat_a/2)%2,white); v108_draw_small_u64(surface,((px+226)*65536)+(py+748),(compat_a/4)%16,green); v108_draw_small_u64(surface,((px+264)*65536)+(py+748),compat_a/64,amber); v108_draw_small_u64(surface,((px+306)*65536)+(py+748),compat_i,white); v108_draw_small_u64(surface,((px+350)*65536)+(py+748),compat_t,green); v108_draw_small_u64(surface,((px+394)*65536)+(py+748),raw3,amber); }"
s=s[:rs]+newrow+s[re:]

live=s[s.index('fn v159_ehci_mouse_periodic_arm'):s.index('fn v162_r61_periodic_reference_arm')]
helper2=fn_text(s,'v157_ehci_tt_control')
for q in (
    'let getreport=161+(1*256)+(256*65536)+(mif*4294967296)+(3*281474976710656)',
    'v157_ehci_tt_control(xhci_state,2,getreport,3)',
):
    if q not in live: raise SystemExit('r64 lost r63 control-poll witness '+q)
for q in (
    'var is_getreport:u64=0',
    'let dactive=(dtok/128)%2',
    'let dhalt=(dtok/64)%2',
    'let derr=(dtok/4)%16',
    'let drem=(dtok/65536)%32768',
    'volatile_write64(xhci_state+3984,dpack)',
    'volatile_write64(xhci_state+3992,spack)',
    'volatile_write64(xhci_state+4000,qpack)',
    'volatile_write64(xhci_state+4008,raw3)',
):
    if q not in helper2: raise SystemExit('r64 GET_REPORT token forensic witness missing '+q)
for q in ('compat_a%2','(compat_a/2)%2','(compat_a/4)%16','compat_a/64','let raw3=volatile_read64(xhci+4008)'):
    if q not in s: raise SystemExit('r64 visible forensic witness missing '+q)
for forbidden in ('volatile_write32(op+20,flo)','cmd=set_flag(cmd,16)','volatile_write32(qtd+8,560512)'):
    if forbidden in live: raise SystemExit('r64 live periodic path rearmed '+forbidden)
for bad in ('write(10)','nvme_submit_write','ahci_write','fat_write','block_write'):
    if bad in live.lower(): raise SystemExit('r64 exceeds read-only input scope '+bad)
if s.count('{')!=s.count('}'):
    raise SystemExit('r64 brace mismatch')
out=hashlib.sha256(s.encode()).hexdigest()
EXPECTED='db605f05538b796d7553ad45cf9de7881b8e111ee8eda30e034a29821b3fd316'
if out!=EXPECTED:
    raise SystemExit('r64 output sha mismatch '+out)
p.write_text(s)
print(out)
