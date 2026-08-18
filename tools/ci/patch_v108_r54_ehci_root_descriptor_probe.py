#!/usr/bin/env python3
from pathlib import Path
import hashlib, subprocess, sys
if len(sys.argv)!=2: raise SystemExit('usage: patch_v108_r54_ehci_root_descriptor_probe.py <kernel/main.nx>')
p=Path(sys.argv[1]); here=Path(__file__).parent
base=here/'patch_v108_r53_ehci_port_reset_companion_classifier_sealed.py'
subprocess.run([sys.executable,str(base),str(p)],check=True,stdout=subprocess.DEVNULL)
s=p.read_text()
BASE='815287063aae3e8d2ab56dbd4514de4cafdcd4ee763ff355f65b0867468d05d6'
actual=hashlib.sha256(s.encode()).hexdigest()
if actual!=BASE: raise SystemExit('r54 exact r53 base mismatch '+actual)

def rep(old,new,label,count=1):
    global s
    n=s.count(old)
    if n!=count: raise SystemExit(f'{label}: {n} expected {count}')
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

def label_fn(name,text):
    out=f'fn {name}(surface:u64,x:u64,y:u64,color:u64) -> u64 {{'
    for i,ch in enumerate(text): out+=f' if gui_draw_char_scaled(surface,((x+{i*6})*65536)+y,({ord(ch)}*65536)+1,color)==0 {{ return 0; }}'
    return out+' return 1; }'

insert = r'''
fn v154_ehci_root_descriptor_probe(xhci_state:u64,phys_state:u64) -> u64 {
    if xhci_state==0 || phys_state==0 { return 0; }
    let prior=volatile_read64(xhci_state+3792); if prior!=0 { return prior; }
    if volatile_read64(xhci_state+3696)!=1 || volatile_read64(xhci_state+3720)!=1 || volatile_read64(xhci_state+3728)!=0 { return 0; }
    unsafe { volatile_write64(xhci_state+3792,9); volatile_write64(xhci_state+3800,0); volatile_write64(xhci_state+3808,0); volatile_write64(xhci_state+3816,0); volatile_write64(xhci_state+3824,0); volatile_write64(xhci_state+3832,0); volatile_write64(xhci_state+3840,0); volatile_write64(xhci_state+3848,0); volatile_write64(xhci_state+3856,0); volatile_write64(xhci_state+3864,0); volatile_write64(xhci_state+3872,0); volatile_write64(xhci_state+3880,0); volatile_write64(xhci_state+3888,0); volatile_write64(xhci_state+3896,0); volatile_write64(xhci_state+3904,0); volatile_write64(xhci_state+3912,0); }
    let ord=volatile_read64(xhci_state+3704); let port=volatile_read64(xhci_state+3712); if ord==0 || port==0 { unsafe { volatile_write64(xhci_state+3792,2); } return 2; }
    let ebdf=v108_pci_nth_ehci_v121(ord-1); if ebdf==0 { unsafe { volatile_write64(xhci_state+3792,2); } return 2; }
    if pci_enable_mmio_busmaster(ebdf)==0 { unsafe { volatile_write64(xhci_state+3792,3); } return 3; }
    let base=pci_bar_base(ebdf,0); if base==0 { unsafe { volatile_write64(xhci_state+3792,2); } return 2; }
    let caplen=volatile_read8(base); if caplen<16 || caplen>128 { unsafe { volatile_write64(xhci_state+3792,2); } return 2; }
    let hcs=volatile_read32(base+4); let ports=hcs%16; if port>ports { unsafe { volatile_write64(xhci_state+3792,2); } return 2; }
    let hcc=volatile_read32(base+8); let ac64=hcc%2; let op=base+caplen; let preg=op+68+((port-1)*4); let ps=volatile_read32(preg);
    if ps%2==0 || (ps/4)%2==0 || (ps/8192)%2!=0 { unsafe { volatile_write64(xhci_state+3792,8); volatile_write64(xhci_state+3912,ps); } return 8; }
    let dma=alloc_dma_page(phys_state,3); if dma==0 { unsafe { volatile_write64(xhci_state+3792,3); } return 3; } zero_page(dma);
    let upper=dma/4294967296; if ac64==0 && upper!=0 { unsafe { volatile_write64(xhci_state+3792,3); } return 3; }
    let qh=dma; let qs=dma+128; let qd=dma+192; let qt=dma+256; let setup=dma+512; let data=dma+576;
    let qlo=qh%4294967296; let qslo=qs%4294967296; let qdlo=qd%4294967296; let qtlo=qt%4294967296; let setlo=setup%4294967296; let datlo=data%4294967296;
    unsafe {
        volatile_write64(setup,5066549597570688);
        volatile_write32(qs+0,qdlo); volatile_write32(qs+4,1); volatile_write32(qs+8,528000); volatile_write32(qs+12,setlo); volatile_write32(qs+32,upper);
        volatile_write32(qd+0,qtlo); volatile_write32(qd+4,qtlo); volatile_write32(qd+8,2148666752); volatile_write32(qd+12,datlo); volatile_write32(qd+32,upper);
        volatile_write32(qt+0,1); volatile_write32(qt+4,1); volatile_write32(qt+8,2147519616);
        volatile_write32(qh+0,qlo+2); volatile_write32(qh+4,1077993472); volatile_write32(qh+8,1073741824); volatile_write32(qh+12,0); volatile_write32(qh+16,qslo); volatile_write32(qh+20,1); volatile_write32(qh+24,0);
    }
    if volatile_read32(qh+4)!=1077993472 || volatile_read32(qs+8)!=528000 || volatile_read32(qd+8)!=2148666752 { unsafe { volatile_write64(xhci_state+3792,3); } return 3; }
    unsafe { volatile_write32(op+8,0); volatile_write32(op+24,qlo); volatile_write32(op+4,63); } if ac64!=0 { unsafe { volatile_write32(op+16,upper); } }
    var cmd=volatile_read32(op); cmd=clear_flag(cmd,16); cmd=clear_flag(cmd,64); cmd=set_flag(cmd,1); cmd=set_flag(cmd,32); unsafe { volatile_write32(op,cmd); }
    var arm:u64=0; while (volatile_read32(op+4)/32768)%2==0 && arm<4000000 { cpu_pause(); arm=arm+1; }
    if arm>=4000000 { cmd=volatile_read32(op); cmd=clear_flag(cmd,32); unsafe { volatile_write32(op,cmd); volatile_write64(xhci_state+3792,4); } return 4; }
    var spins:u64=0; while (volatile_read32(qt+8)/128)%2!=0 && spins<12000000 { cpu_pause(); spins=spins+1; }
    cmd=volatile_read32(op); cmd=clear_flag(cmd,32); unsafe { volatile_write32(op,cmd); }
    var stop:u64=0; while (volatile_read32(op+4)/32768)%2!=0 && stop<4000000 { cpu_pause(); stop=stop+1; }
    let stok=volatile_read32(qt+8); let dtok=volatile_read32(qd+8); let qstok=volatile_read32(qs+8); let remain=(dtok/65536)%32768; let err=((stok/4)%16)+((dtok/4)%16)+((qstok/4)%16); let liveps=volatile_read32(preg);
    unsafe { volatile_write64(xhci_state+3848,dma); volatile_write64(xhci_state+3856,stok); volatile_write64(xhci_state+3864,(volatile_read32(op+4)/32768)%2); volatile_write64(xhci_state+3872,remain); volatile_write64(xhci_state+3896,ac64); volatile_write64(xhci_state+3904,upper); volatile_write64(xhci_state+3912,liveps); }
    if (stok/64)%2!=0 || (dtok/64)%2!=0 || (qstok/64)%2!=0 || err!=0 { unsafe { volatile_write64(xhci_state+3792,6); } return 6; }
    if spins>=12000000 || (stok/128)%2!=0 { unsafe { volatile_write64(xhci_state+3792,5); } return 5; }
    let length=volatile_read8(data); let dtype=volatile_read8(data+1); let cls=volatile_read8(data+4); let mps=volatile_read8(data+7); let vid=volatile_read8(data+8)+(volatile_read8(data+9)*256); let pid=volatile_read8(data+10)+(volatile_read8(data+11)*256);
    unsafe { volatile_write64(xhci_state+3880,length); volatile_write64(xhci_state+3888,dtype); volatile_write64(xhci_state+3816,cls); volatile_write64(xhci_state+3824,mps); volatile_write64(xhci_state+3832,vid); volatile_write64(xhci_state+3840,pid); volatile_write64(xhci_state+3800,ord); volatile_write64(xhci_state+3808,port); }
    if length<18 || dtype!=1 || mps!=64 || remain!=0 { unsafe { volatile_write64(xhci_state+3792,7); } return 7; }
    if liveps%2==0 || (liveps/4)%2==0 || (liveps/8192)%2!=0 { unsafe { volatile_write64(xhci_state+3792,8); } return 8; }
    unsafe { volatile_write64(xhci_state+3792,1); } return 1;
}
'''
anchor='fn xhci_configure_boot_hid'
pos=s.index(anchor)
s=s[:pos]+insert+s[pos:]
rep('if xhci!=0 { v153_intel_ehci_port_reset_companion_classifier(xhci); }','if xhci!=0 { v153_intel_ehci_port_reset_companion_classifier(xhci); if volatile_read64(xhci+3696)==1 { v154_ehci_root_descriptor_probe(xhci,phys_state); } }','r54 call')
fnrep('v140_text_wifi_v140',label_fn('v140_text_wifi_v140','R54 S E R C M V D'))
oldrow='    v140_text_wifi_v140(surface,px+10,py+748,white); if xhci!=0 { v108_draw_small_u64(surface,((px+112)*65536)+(py+748),volatile_read64(xhci+3696),green); v108_draw_small_u64(surface,((px+150)*65536)+(py+748),volatile_read64(xhci+3704),amber); v108_draw_small_u64(surface,((px+188)*65536)+(py+748),volatile_read64(xhci+3712),white); v108_draw_small_u64(surface,((px+226)*65536)+(py+748),volatile_read64(xhci+3720),green); v108_draw_small_u64(surface,((px+264)*65536)+(py+748),volatile_read64(xhci+3728),amber); v108_draw_small_u64(surface,((px+306)*65536)+(py+748),volatile_read64(xhci+3736),white); v108_draw_small_u64(surface,((px+350)*65536)+(py+748),volatile_read64(xhci+3744),white); }'
newrow='    v140_text_wifi_v140(surface,px+10,py+748,white); if xhci!=0 { v108_draw_small_u64(surface,((px+112)*65536)+(py+748),volatile_read64(xhci+3792),green); v108_draw_small_u64(surface,((px+150)*65536)+(py+748),volatile_read64(xhci+3800),amber); v108_draw_small_u64(surface,((px+188)*65536)+(py+748),volatile_read64(xhci+3808),white); v108_draw_small_u64(surface,((px+226)*65536)+(py+748),volatile_read64(xhci+3816),green); v108_draw_small_u64(surface,((px+264)*65536)+(py+748),volatile_read64(xhci+3824),amber); v108_draw_small_u64(surface,((px+306)*65536)+(py+748),volatile_read64(xhci+3832),white); v108_draw_small_u64(surface,((px+350)*65536)+(py+748),volatile_read64(xhci+3840),white); }'
rep(oldrow,newrow,'r54 row')
# r54 is deliberately bounded to one asynchronous control transfer to the
# high-speed device exposed by the r53-enabled EHCI root port.  It must not
# enable periodic scheduling, retain asynchronous scheduling after completion,
# configure a downstream device, or touch storage.
r54fn=s[s.index('fn v154_ehci_root_descriptor_probe'):s.index('fn xhci_configure_boot_hid')]
for q in (
    'pci_enable_mmio_busmaster(ebdf)',
    'volatile_write64(setup,5066549597570688)',
    'volatile_write32(qh+0,qlo+2)',
    'volatile_write32(qh+4,1077993472)',
    'volatile_write32(qh+8,1073741824)',
    'volatile_write32(qs+8,528000)',
    'volatile_write32(qd+8,2148666752)',
    'volatile_write32(qt+8,2147519616)',
    'volatile_write32(op+24,qlo)',
    'cmd=set_flag(cmd,32)',
    'cmd=clear_flag(cmd,32)',
    'let cls=volatile_read8(data+4)',
    'let vid=volatile_read8(data+8)+(volatile_read8(data+9)*256)',
    'let pid=volatile_read8(data+10)+(volatile_read8(data+11)*256)',
):
    if q not in r54fn: raise SystemExit('r54 EHCI descriptor proof missing '+q)
if r54fn.count('cmd=set_flag(cmd,32)')!=1 or r54fn.count('cmd=clear_flag(cmd,32)')<2:
    raise SystemExit('r54 asynchronous schedule is not single-shot bounded')
for forbidden in ('set_flag(cmd,16)','periodiclistbase','set_configuration','set_address','interrupt endpoint','write(10)','nvme_submit_write','ahci_write'):
    if forbidden in r54fn.lower(): raise SystemExit('r54 exceeds bounded descriptor-probe scope '+forbidden)
if 'v154_ehci_root_descriptor_probe(xhci,phys_state)' not in s: raise SystemExit('r54 descriptor probe is not invoked')
if s.count('{')!=s.count('}'): raise SystemExit('r54 brace mismatch')
out=hashlib.sha256(s.encode()).hexdigest()
EXPECTED='ebcf7baf18422cc72804eec9e18a317ed5daf1baee65330528be66c07d599c19'
if out!=EXPECTED: raise SystemExit('r54 output sha mismatch '+out)
p.write_text(s)
print(out)
