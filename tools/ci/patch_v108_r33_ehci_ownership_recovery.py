#!/usr/bin/env python3
from pathlib import Path
import hashlib,subprocess,sys
if len(sys.argv)!=2: raise SystemExit('usage: patch_v108_r33_ehci_ownership_recovery.py <kernel/main.nx>')
p=Path(sys.argv[1]); base=Path(__file__).with_name('patch_v108_r32_usb_settle_input_recovery.py')
subprocess.run([sys.executable,str(base),str(p)],check=True,stdout=subprocess.DEVNULL)
s=p.read_text()
BASE='dab5d471bf8cc80a38573fa52aa502f1bc488d9d3ecb655ce734350e123d732f'

if hashlib.sha256(s.encode()).hexdigest()!=BASE: raise SystemExit('r32 base mismatch')

def span(text,name):
    st=text.index('fn '+name); op=text.index('{',st); d=0
    for i in range(op,len(text)):
        if text[i]=='{': d+=1
        elif text[i]=='}':
            d-=1
            if d==0: return st,i+1
    raise RuntimeError(name)

def rep(old,new,label,count=1):
    global s
    n=s.count(old)
    if n!=count: raise RuntimeError(f'{label} count {n}')
    s=s.replace(old,new,count)

def label_fn(name,text):
    out=f'fn {name}(surface:u64,x:u64,y:u64,color:u64) -> u64 {{'
    for i,ch in enumerate(text):
        out+=f' if gui_draw_char_scaled(surface,((x+{i*6})*65536)+y,({ord(ch)}*65536)+1,color)==0 {{ return 0; }}'
    return out+' return 1; }\n'

helper=r'''fn v108_ehci_release_one_v133(bdf:u64,phys_state:u64,pml4:u64,out:u64) -> u64 {
    if bdf==0 || phys_state==0 || pml4==0 || out==0 { return 0; }
    unsafe { volatile_write64(out,0); volatile_write64(out+8,0); volatile_write64(out+16,0); volatile_write64(out+24,0); volatile_write64(out+32,0); volatile_write64(out+40,0); }
    let base=pci_bar_base(bdf,0); if base==0 || ensure_identity_mmio_page(phys_state,pml4,base)==0 { return 0; }
    let caplen=volatile_read8(base); if caplen<16 || caplen>128 { return 0; }
    let hcs=volatile_read32(base+4); let ports=hcs%16; if ports==0 || ports>15 { return 0; }
    let op=base+caplen; if ensure_identity_mmio_page(phys_state,pml4,op)==0 || ensure_identity_mmio_page(phys_state,pml4,op+68+(ports*4))==0 { return 0; }
    var cb:u64=0; var p:u64=0; while p<ports { if volatile_read32(op+68+(p*4))%2!=0 { cb=cb+1; } p=p+1; }
    let bus=bdf/65536; let dev=(bdf/256)%256; let fun=bdf%256; let hcc=volatile_read32(base+8); let eecp=(hcc/256)%256; var bb:u64=0; var ba:u64=0;
    if eecp>=64 && eecp<=248 {
        var leg=pci_cfg_read32(bus,dev,fun,eecp); bb=(leg/65536)%2;
        if (leg/16777216)%2==0 { leg=set_flag(leg,16777216); pci_cfg_write32(bdf,eecp,leg); }
        var spins:u64=0; while (pci_cfg_read32(bus,dev,fun,eecp)/65536)%2!=0 && spins<4000000 { cpu_pause(); spins=spins+1; }
        ba=(pci_cfg_read32(bus,dev,fun,eecp)/65536)%2;
        if ba==0 { pci_cfg_write32(bdf,eecp+4,0); }
    }
    var halted:u64=0;
    if ba==0 {
        unsafe { volatile_write32(op+8,0); }
        var cmd=volatile_read32(op+0); cmd=clear_flag(cmd,1); unsafe { volatile_write32(op+0,cmd); }
        var hs:u64=0; while (volatile_read32(op+4)/4096)%2==0 && hs<4000000 { cpu_pause(); hs=hs+1; }
        if (volatile_read32(op+4)/4096)%2!=0 { halted=1; }
    }
    var ca:u64=0; p=0; while p<ports { if volatile_read32(op+68+(p*4))%2!=0 { ca=ca+1; } p=p+1; }
    unsafe { volatile_write64(out,ports); volatile_write64(out+8,cb); volatile_write64(out+16,bb); volatile_write64(out+24,ba); volatile_write64(out+32,ca); volatile_write64(out+40,halted); }
    return 1;
}
fn v108_ehci_release_companions_v133(hardware_state:u64,phys_state:u64,xhci_state:u64,pml4:u64) -> u64 {
    if hardware_state==0 || phys_state==0 || xhci_state==0 || pml4==0 { return 0; }
    let b0=volatile_read64(hardware_state+520); let b1=volatile_read64(hardware_state+528); let o0=xhci_state+2400; let o1=xhci_state+2448;
    var n:u64=0; if b0!=0 { n=n+v108_ehci_release_one_v133(b0,phys_state,pml4,o0); } if b1!=0 { n=n+v108_ehci_release_one_v133(b1,phys_state,pml4,o1); }
    let cb=volatile_read64(o0+8)+volatile_read64(o1+8); let ca=volatile_read64(o0+32)+volatile_read64(o1+32); let bb=volatile_read64(o0+16)+volatile_read64(o1+16); let bs=volatile_read64(o0+24)+volatile_read64(o1+24); let h=volatile_read64(o0+40)+volatile_read64(o1+40);
    unsafe { volatile_write64(xhci_state+2312,n); volatile_write64(xhci_state+2320,cb); volatile_write64(xhci_state+2328,ca); volatile_write64(xhci_state+2336,bb); volatile_write64(xhci_state+2344,bs); volatile_write64(xhci_state+2352,h); }
    return n;
}
'''
rep('fn xhci_controller_init(hardware_state:u64, phys_state:u64, xhci_state:u64, pml4:u64) -> u64 {',helper+'fn xhci_controller_init(hardware_state:u64, phys_state:u64, xhci_state:u64, pml4:u64) -> u64 {','ehci helper insert')
old='''                    v108_intel_xhci_route_ports_v120(bdf,xhci_state,hardware_state);
                    let init_ok_v120=xhci_controller_init(hardware_state,phys_state,xhci_state,pml4);'''
new='''                    v108_intel_xhci_route_ports_v120(bdf,xhci_state,hardware_state); v108_ehci_release_companions_v133(hardware_state,phys_state,xhci_state,pml4); let route_pre_v133=v108_intel_xhci_route_ports_v120(bdf,xhci_state,hardware_state); unsafe { volatile_write64(xhci_state+2360,route_pre_v133); }
                    let init_ok_v120=xhci_controller_init(hardware_state,phys_state,xhci_state,pml4); if init_ok_v120!=0 { let route_post_v133=v108_intel_xhci_route_ports_v120(bdf,xhci_state,hardware_state); pit_wait(119320); let post_v133=xhci_root_port_settle_v132(xhci_state); unsafe { volatile_write64(xhci_state+2360,route_post_v133); volatile_write64(xhci_state+2368,post_v133); volatile_write64(xhci_state+1320,post_v133); } }'''
rep(old,new,'ehci release scan order')

rep('fn v108_input_overlay_draw(surface:u64,state:u64,input_state:u64,xhci:u64) -> u64 {',label_fn('v108_text_r33_v133','R33 EH N CB CA BS H X')+'fn v108_input_overlay_draw(surface:u64,state:u64,input_state:u64,xhci:u64) -> u64 {','r33 label')
rep('(410*65536)+742','(410*65536)+760','r33 overlay height',count=s.count('(410*65536)+742'))
a,b=span(s,'v108_input_overlay_draw'); ov=s[a:b]
oldrow='''    v108_text_r32_v132(surface,px+10,py+694,white); if xhci!=0 { v108_draw_small_u64(surface,((px+130)*65536)+(py+694),volatile_read64(xhci+2288),amber); v108_draw_small_u64(surface,((px+202)*65536)+(py+694),volatile_read64(xhci+2296),green); v108_draw_small_u64(surface,((px+274)*65536)+(py+694),volatile_read64(xhci+2304),white); }
    return 1;'''
newrow='''    v108_text_r32_v132(surface,px+10,py+694,white); if xhci!=0 { v108_draw_small_u64(surface,((px+130)*65536)+(py+694),volatile_read64(xhci+2288),amber); v108_draw_small_u64(surface,((px+202)*65536)+(py+694),volatile_read64(xhci+2296),green); v108_draw_small_u64(surface,((px+274)*65536)+(py+694),volatile_read64(xhci+2304),white); }
    v108_text_r33_v133(surface,px+10,py+712,white); if xhci!=0 { v108_draw_small_u64(surface,((px+130)*65536)+(py+712),volatile_read64(xhci+2312),white); v108_draw_small_u64(surface,((px+178)*65536)+(py+712),volatile_read64(xhci+2320),amber); v108_draw_small_u64(surface,((px+226)*65536)+(py+712),volatile_read64(xhci+2328),green); v108_draw_small_u64(surface,((px+274)*65536)+(py+712),volatile_read64(xhci+2344),red); v108_draw_small_u64(surface,((px+322)*65536)+(py+712),volatile_read64(xhci+2352),green); v108_draw_small_u64(surface,((px+370)*65536)+(py+712),volatile_read64(xhci+2368),green); }
    return 1;'''
assert ov.count(oldrow)==1, ov.count(oldrow)
ov=ov.replace(oldrow,newrow,1); s=s[:a]+ov+s[b:]

# contracts
assert 'v108_ehci_release_companions_v133' in s
scan=s[span(s,'v108_xhci_scan_pointer_v116')[0]:span(s,'v108_xhci_scan_pointer_v116')[1]]
assert scan.index('v108_ehci_release_companions_v133') < scan.index('xhci_controller_init')
assert 'route_post_v133' in scan and 'volatile_write64(xhci_state+2368,post_v133)' in scan
release=s[span(s,'v108_ehci_release_one_v133')[0]:span(s,'v108_ehci_release_one_v133')[1]]
assert 'pci_cfg_write32(bdf,eecp+4,0)' in release and 'clear_flag(cmd,1)' in release
assert 'volatile_write32(op+8,0)' in release
assert s.count('{')==s.count('}')
expected='d81cf6d3a6ff53c57d18748e1fcf7da49f03f9b580f26e59b21a01a08a1495cf'
actual=hashlib.sha256(s.encode()).hexdigest()
if actual!=expected: raise SystemExit(f'r33 identity mismatch {actual}')
p.write_text(s); print(actual)
