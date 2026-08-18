#!/usr/bin/env python3
from pathlib import Path
import hashlib, subprocess, sys
if len(sys.argv)!=2: raise SystemExit('usage: patch_v108_r56_ehci_second_hub_census.py <kernel/main.nx>')
p=Path(sys.argv[1]); here=Path(__file__).parent
base=here/'patch_v108_r55c_ehci_hub_address_preflight.py'
subprocess.run([sys.executable,str(base),str(p)],check=True,stdout=subprocess.DEVNULL)
s=p.read_text()
BASE='8341c00a24f8dad89dec417dcaa93c1ff648344652cd6fda4ef47afd459f4595'
actual=hashlib.sha256(s.encode()).hexdigest()
if actual!=BASE: raise SystemExit('r56 exact r55c base mismatch '+actual)

def rep(old,new,label,count=1):
    global s
    n=s.count(old)
    if n!=count: raise SystemExit(f'r56 {label}: {n} expected {count}')
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

# r55c physical evidence: the first Intel 8087:8008 rate-matching hub
# enumerated cleanly with six downstream ports but reported zero connections.
# r52 previously proved both EHCI controllers are alive. r56 therefore keeps
# the entire proven first-hub path, then (only after a valid empty first-hub
# census) enumerates EHCI ordinal 2 and performs the same bounded root-hub /
# downstream-port census. No periodic schedule or HID transfer is introduced.
second=r'''
fn v156_ehci_second_hub_census(xhci_state:u64) -> u64 {
    if xhci_state==0 { return 0; }
    let first_state=volatile_read64(xhci_state+3920);
    if first_state==1 && volatile_read64(xhci_state+3944)!=0 { unsafe { volatile_write64(xhci_state+3928,1); } return 1; }
    if first_state!=7 || volatile_read64(xhci_state+3936)==0 { return first_state; }
    let dma=volatile_read64(xhci_state+3848); if dma==0 { unsafe { volatile_write64(xhci_state+3920,30); } return 30; }
    let ord:u64=2; let ebdf=v108_pci_nth_ehci_v121(1); if ebdf==0 { unsafe { volatile_write64(xhci_state+3920,20); volatile_write64(xhci_state+3928,2); } return 20; }
    if pci_enable_mmio_busmaster(ebdf)==0 { unsafe { volatile_write64(xhci_state+3920,20); volatile_write64(xhci_state+3928,2); } return 20; }
    let base=pci_bar_base(ebdf,0); if base==0 { unsafe { volatile_write64(xhci_state+3920,20); volatile_write64(xhci_state+3928,2); } return 20; }
    let caplen=volatile_read8(base); if caplen<16 || caplen>128 { unsafe { volatile_write64(xhci_state+3920,20); volatile_write64(xhci_state+3928,2); } return 20; }
    let hcs=volatile_read32(base+4); let ports=hcs%16; if ports==0 || ports>15 { unsafe { volatile_write64(xhci_state+3920,20); volatile_write64(xhci_state+3928,2); } return 20; }
    let op=base+caplen; unsafe { volatile_write32(op+8,0); volatile_write32(op+64,1); }
    var cmd=volatile_read32(op); cmd=clear_flag(cmd,16); cmd=clear_flag(cmd,32); cmd=clear_flag(cmd,64); cmd=set_flag(cmd,1); unsafe { volatile_write32(op,cmd); }
    if (hcs/16)%2!=0 { var rp:u64=0; while rp<ports { let ps=volatile_read32(op+68+(rp*4)); if (ps/4096)%2==0 { var pw=ps; pw=clear_flag(pw,2); pw=clear_flag(pw,8); pw=clear_flag(pw,32); pw=set_flag(pw,4096); unsafe { volatile_write32(op+68+(rp*4),pw); } } rp=rp+1; } }
    var runwait:u64=0; while (volatile_read32(op+4)/4096)%2!=0 && runwait<4000000 { cpu_pause(); runwait=runwait+1; }
    if runwait>=4000000 { unsafe { volatile_write64(xhci_state+3920,20); volatile_write64(xhci_state+3928,2); } return 20; }
    pit_wait(119320);
    var root:u64=0; var pre:u64=0; var rp:u64=1;
    while rp<=ports && root==0 { let ps=volatile_read32(op+68+((rp-1)*4)); if ps%2!=0 { root=rp; pre=ps; } rp=rp+1; }
    if root==0 { unsafe { volatile_write64(xhci_state+3920,20); volatile_write64(xhci_state+3928,2); } return 20; }
    let preg=op+68+((root-1)*4); var wr=pre; wr=clear_flag(wr,2); wr=clear_flag(wr,8); wr=clear_flag(wr,32); if (hcs/16)%2!=0 { wr=set_flag(wr,4096); } wr=set_flag(wr,256); unsafe { volatile_write32(preg,wr); }
    pit_wait(59660); var mid=volatile_read32(preg); wr=mid; wr=clear_flag(wr,2); wr=clear_flag(wr,8); wr=clear_flag(wr,32); wr=clear_flag(wr,256); if (hcs/16)%2!=0 { wr=set_flag(wr,4096); } unsafe { volatile_write32(preg,wr); }
    var rs:u64=0; while (volatile_read32(preg)/256)%2!=0 && rs<4000000 { cpu_pause(); rs=rs+1; }
    pit_wait(23864); let done=volatile_read32(preg);
    if rs>=4000000 || done%2==0 || (done/4)%2==0 || (done/8192)%2!=0 { unsafe { volatile_write64(xhci_state+3920,21); volatile_write64(xhci_state+3928,2); volatile_write64(xhci_state+3984,done); } return 21; }

    unsafe { volatile_write64(xhci_state+3800,ord); volatile_write64(xhci_state+4040,dma); volatile_write64(xhci_state+3920,9); volatile_write64(xhci_state+3928,2); volatile_write64(xhci_state+3936,0); volatile_write64(xhci_state+3944,0); volatile_write64(xhci_state+3952,0); volatile_write64(xhci_state+3960,0); volatile_write64(xhci_state+3968,0); volatile_write64(xhci_state+3976,3); volatile_write64(xhci_state+3984,done); volatile_write64(xhci_state+3992,0); volatile_write64(xhci_state+4000,0); volatile_write64(xhci_state+4008,0); volatile_write64(xhci_state+4016,0); volatile_write64(xhci_state+4024,0); volatile_write64(xhci_state+4032,0); }
    var rc=v155_ehci_control(xhci_state,0,5066549597570688,18); if rc!=1 { unsafe { volatile_write64(xhci_state+3920,22); volatile_write64(xhci_state+4000,rc); } return 22; }
    let data=dma+576; let dlen=volatile_read8(data); let dtype=volatile_read8(data+1); let cls=volatile_read8(data+4); let mps=volatile_read8(data+7); let vid=volatile_read8(data+8)+(volatile_read8(data+9)*256); let pid=volatile_read8(data+10)+(volatile_read8(data+11)*256);
    unsafe { volatile_write64(xhci_state+4008,vid); volatile_write64(xhci_state+3992,pid); }
    if dlen<18 || dtype!=1 || cls!=9 || mps!=64 || vid!=32903 { unsafe { volatile_write64(xhci_state+3920,23); } return 23; }
    rc=v155_ehci_control(xhci_state,0,66816,0); if rc!=1 { unsafe { volatile_write64(xhci_state+3920,24); volatile_write64(xhci_state+4000,rc); } return 24; }
    pit_wait(23864);
    rc=v155_ehci_control(xhci_state,1,2533274823952000,9); if rc!=1 { unsafe { volatile_write64(xhci_state+3920,25); volatile_write64(xhci_state+4000,rc); } return 25; }
    let clen=volatile_read8(data); let ctype=volatile_read8(data+1); let cfg=volatile_read8(data+5); if clen<9 || ctype!=2 || cfg==0 { unsafe { volatile_write64(xhci_state+3920,25); } return 25; }
    let setcfg=2304+(cfg*65536); rc=v155_ehci_control(xhci_state,1,setcfg,0); if rc!=1 { unsafe { volatile_write64(xhci_state+3920,25); volatile_write64(xhci_state+4000,rc); } return 25; }
    pit_wait(23864);
    rc=v155_ehci_control(xhci_state,1,2533275478263456,9); if rc!=1 { unsafe { volatile_write64(xhci_state+3920,25); volatile_write64(xhci_state+4000,rc); } return 25; }
    let hlen=volatile_read8(data); let htype=volatile_read8(data+1); let nports=volatile_read8(data+2); let chars=volatile_read8(data+3)+(volatile_read8(data+4)*256); let pgood=volatile_read8(data+5);
    if hlen<7 || htype!=41 || nports==0 || nports>15 { unsafe { volatile_write64(xhci_state+3920,25); } return 25; }
    unsafe { volatile_write64(xhci_state+3936,nports); }
    let power_mode=chars%4; var pnum:u64=1; var power_cmds:u64=0;
    if power_mode!=2 { while pnum<=nports { let req=525091+(pnum*4294967296); rc=v155_ehci_control(xhci_state,1,req,0); if rc==1 { power_cmds=power_cmds+1; } pnum=pnum+1; } let delay=(pgood*2387)+119320; pit_wait(delay); }
    var round:u64=0; var connected:u64=0; var enabled:u64=0; var bitmap:u64=0; var first:u64=0; var first_speed:u64=3; var first_status:u64=0;
    while round<5 && connected==0 {
        connected=0; enabled=0; bitmap=0; first=0; first_speed=3; first_status=0; pnum=1;
        while pnum<=nports {
            let req=1125899906842787+(pnum*4294967296); rc=v155_ehci_control(xhci_state,1,req,4); if rc!=1 { unsafe { volatile_write64(xhci_state+3920,26); volatile_write64(xhci_state+4000,rc); volatile_write64(xhci_state+4032,pnum); } return 26; }
            let st=volatile_read8(data)+(volatile_read8(data+1)*256); let conn=st%2; let ena=(st/2)%2;
            if conn!=0 { connected=connected+1; bitmap=bitmap+power2_u64(pnum-1); if first==0 { first=pnum; first_status=st; let low=(st/512)%2; let high=(st/1024)%2; if high!=0 { first_speed=2; } else { if low!=0 { first_speed=1; } else { first_speed=0; } } } }
            if ena!=0 { enabled=enabled+1; }
            pnum=pnum+1;
        }
        if connected==0 { pit_wait(238640); }
        round=round+1;
    }
    unsafe { volatile_write64(xhci_state+3944,connected); volatile_write64(xhci_state+3952,enabled); volatile_write64(xhci_state+3960,bitmap); volatile_write64(xhci_state+3968,first); volatile_write64(xhci_state+3976,first_speed); volatile_write64(xhci_state+3984,first_status); volatile_write64(xhci_state+4016,power_cmds); volatile_write64(xhci_state+4024,round); }
    if connected==0 { unsafe { volatile_write64(xhci_state+3920,7); } return 7; }
    unsafe { volatile_write64(xhci_state+3920,1); } return 1;
}
'''
pos=s.index('fn xhci_configure_boot_hid')
s=s[:pos]+second+s[pos:]
rep('v155_ehci_intel_hub_discovery(xhci,phys_state);','v155_ehci_intel_hub_discovery(xhci,phys_state); v156_ehci_second_hub_census(xhci);','second-hub call')
fnrep('v140_text_wifi_v140',label_fn('v140_text_wifi_v140','R56 S E N C B F T'))
rep('((px+150)*65536)+(py+748),volatile_read64(xhci+3936)','((px+150)*65536)+(py+748),volatile_read64(xhci+3928)','display E field')
rep('((px+188)*65536)+(py+748),volatile_read64(xhci+3944)','((px+188)*65536)+(py+748),volatile_read64(xhci+3936)','display N field')
rep('((px+226)*65536)+(py+748),volatile_read64(xhci+3952)','((px+226)*65536)+(py+748),volatile_read64(xhci+3944)','display C field')

r56=s[s.index('fn v156_ehci_second_hub_census'):s.index('fn xhci_configure_boot_hid')]
for q in (
    'v108_pci_nth_ehci_v121(1)',
    'volatile_write64(xhci_state+3800,ord)',
    'wr=set_flag(wr,256)',
    'wr=clear_flag(wr,256)',
    'done%2==0 || (done/4)%2==0 || (done/8192)%2!=0',
    'v155_ehci_control(xhci_state,0,5066549597570688,18)',
    'cls!=9 || mps!=64 || vid!=32903',
    'v155_ehci_control(xhci_state,0,66816,0)',
    '2533274823952000',
    '2533275478263456',
    '525091+(pnum*4294967296)',
    '1125899906842787+(pnum*4294967296)',
    'while round<5 && connected==0',
):
    if q not in r56: raise SystemExit('r56 second-hub model missing '+q)
if 'set_flag(cmd,16)' in r56: raise SystemExit('r56 periodic schedule unexpectedly enabled')
for bad in ('ehci_interrupt','interrupt endpoint','write(10)','nvme_submit_write','ahci_write'):
    if bad in r56.lower(): raise SystemExit('r56 exceeds bounded census scope '+bad)
if 'v156_ehci_second_hub_census(xhci)' not in s: raise SystemExit('r56 second-hub census not invoked')
if s.count('{')!=s.count('}'): raise SystemExit('r56 brace mismatch')
out=hashlib.sha256(s.encode()).hexdigest()
EXPECTED='0000000000000000000000000000000000000000000000000000000000000000'
if out!=EXPECTED: raise SystemExit('r56 output sha mismatch '+out)
p.write_text(s)
print(out)
