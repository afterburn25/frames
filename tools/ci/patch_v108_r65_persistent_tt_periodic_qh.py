#!/usr/bin/env python3
from pathlib import Path
import hashlib, subprocess, sys
if len(sys.argv)!=2: raise SystemExit('usage: patch_v108_r65_persistent_tt_periodic_qh.py <kernel/main.nx>')
p=Path(sys.argv[1]); here=Path(__file__).parent
base=here/'patch_v108_r64_getreport_qtd_forensics.py'
subprocess.run([sys.executable,str(base),str(p)],check=True,stdout=subprocess.DEVNULL)
s=p.read_text()
BASE='db605f05538b796d7553ad45cf9de7881b8e111ee8eda30e034a29821b3fd316'
actual=hashlib.sha256(s.encode()).hexdigest()
if actual!=BASE: raise SystemExit('r65 exact r64 base mismatch '+actual)

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

# Promote the r61 periodic preflight back to the live path, but gate it on the
# exact physical Intel 8087:8008 Single-TT profile and replace the old
# per-report overlay rewrite/rearm scheme with one persistent periodic QH and
# a prequeued qTD chain ending in a halted dummy.  This first lifecycle proof
# deliberately performs no live QH-overlay or periodic-schedule writes.
ref=fn_text(s,'v162_r61_periodic_reference_arm')
arm=ref.replace('fn v162_r61_periodic_reference_arm','fn v159_ehci_mouse_periodic_arm',1)
oldprof='''    var hubproto:u64=0; var hrc=v155_ehci_control(xhci_state,1,5066549597570688,18); if hrc==1 { if volatile_read8(dma+577)==1 { hubproto=volatile_read8(dma+582); } }
    var ttidx:u64=1; if hubproto==2 { ttidx=port; } let resettt=35+(9*256)+(ttidx*4294967296); var ttrc=v155_ehci_control(xhci_state,1,resettt,0); pit_wait(23864);
    unsafe { volatile_write64(xhci_state+3984,malt); volatile_write64(xhci_state+3992,ifrc); volatile_write64(xhci_state+4000,ttrc); }
'''
newprof='''    var hubproto:u64=0; var hubvid:u64=0; var hubpid:u64=0; var hubchars:u64=0; var hrc=v155_ehci_control(xhci_state,1,5066549597570688,18);
    if hrc==1 { hubproto=volatile_read8(dma+582); hubvid=volatile_read8(dma+584)+(volatile_read8(dma+585)*256); hubpid=volatile_read8(dma+586)+(volatile_read8(dma+587)*256); }
    var hdrc=v155_ehci_control(xhci_state,1,2533275478263456,9); if hdrc==1 { hubchars=volatile_read8(dma+579)+(volatile_read8(dma+580)*256); }
    let ttcode=(hubchars/32)%4; let thinkbits=8+(ttcode*8); var profile:u64=0;
    if hrc==1 && hdrc==1 && hubvid==32903 && hubpid==32776 && hubproto==1 && hubchars==9 && port==2 && thinkbits==8 { profile=1; }
    if profile==0 { unsafe { volatile_write64(xhci_state+4056,35); volatile_write64(xhci_state+3984,hubvid); volatile_write64(xhci_state+3992,hubpid); volatile_write64(xhci_state+4000,hubchars); } return 35; }
    let ttidx:u64=1; let resettt=35+(9*256)+(ttidx*4294967296); var ttrc=v155_ehci_control(xhci_state,1,resettt,0); pit_wait(23864);
    if ttrc!=1 { unsafe { volatile_write64(xhci_state+4056,36); volatile_write64(xhci_state+4000,ttrc); } return 36; }
    unsafe { volatile_write64(xhci_state+3984,profile); volatile_write64(xhci_state+3992,6); volatile_write64(xhci_state+4000,ttrc); }
'''
if arm.count(oldprof)!=1: raise SystemExit('r65 Intel TT profile anchor mismatch')
arm=arm.replace(oldprof,newprof,1)
oldtail=arm[arm.index('    zero_page(frame); zero_page(dma);'):arm.rindex('    return 1;')+len('    return 1;')]
newtail='''    zero_page(frame); zero_page(dma);
    let qh=dma; let qtd=dma+128; let qcount:u64=24; let dummy=dma+128+(qcount*64); let data_base=dma+2048; let qlo=qh%4294967296; let flo=frame%4294967296; let ep=mep%128;
    let gap_uf:u64=1; let legacy_cmask=3*power2_u64(gap_uf); let legacy_info2:u64=1090586113; let newsched_info2:u64=1090591745;
    if mmps!=8 || thinkbits!=8 || legacy_cmask!=6 { unsafe { volatile_write64(xhci_state+4056,37); } return 37; }
    let info1=2+(ep*256)+(speed*4096)+(mmps*65536); let info2=1090586113+(newsched_info2*0)+(thinkbits*0); let token=560512;
    unsafe { volatile_write32(qh+0,1); volatile_write32(qh+4,info1); volatile_write32(qh+8,info2); volatile_write32(qh+12,0); volatile_write32(qh+16,qtd%4294967296); volatile_write32(qh+20,1); volatile_write32(qh+24,0); }
    var qi:u64=0; while qi<qcount { let td=dma+128+(qi*64); let dat=data_base+(qi*8); var next=dummy%4294967296; if qi+1<qcount { next=(dma+128+((qi+1)*64))%4294967296; } unsafe { volatile_write32(td+0,next); volatile_write32(td+4,1); volatile_write32(td+8,token); volatile_write32(td+12,dat%4294967296); volatile_write32(td+32,upper); } qi=qi+1; }
    unsafe { volatile_write32(qtd+8,560512); volatile_write32(dummy+0,1); volatile_write32(dummy+4,1); volatile_write32(dummy+8,64); }
    var i:u64=0; while i<1024 { var link:u64=1; if i%mint==0 { link=qlo+2; } unsafe { volatile_write32(frame+(i*4),link); } i=i+1; }
    unsafe { volatile_write32(op+8,0); volatile_write32(op+20,flo); volatile_write32(op+4,63); }
    if ac64!=0 { unsafe { volatile_write32(op+16,upper); } }
    cmd=volatile_read32(op); cmd=clear_flag(cmd,32); cmd=set_flag(cmd,1); cmd=set_flag(cmd,16); unsafe { volatile_write32(op,cmd); }
    var armwait:u64=0; while (volatile_read32(op+4)/16384)%2==0 && armwait<4000000 { cpu_pause(); armwait=armwait+1; }
    if armwait>=4000000 { cmd=volatile_read32(op); cmd=clear_flag(cmd,16); unsafe { volatile_write32(op,cmd); volatile_write64(xhci_state+4056,18); } return 18; }
    unsafe { volatile_write64(xhci_state+4048,frame); volatile_write64(xhci_state+4056,1); volatile_write64(xhci_state+4064,0); volatile_write64(xhci_state+4072,0); volatile_write64(xhci_state+4080,0); volatile_write64(xhci_state+4088,0); }
    return 1;'''
arm=arm.replace(oldtail,newtail,1)
s=s.replace(fn_text(s,'v159_ehci_mouse_periodic_arm'),arm,1)

# Consume the prequeued qTDs without touching qTDs, the QH overlay, frame list,
# or periodic command bits while the controller owns the schedule.  The QH
# overlay remains the live execution/toggle authority; completed qTD writeback
# is consumed only after the qTD becomes inactive.
tick=fn_text(s,'v159_ehci_mouse_periodic_tick')
newtick='''fn v159_ehci_mouse_periodic_tick(xhci_state:u64,input_state:u64) -> u64 {
    if xhci_state==0 || input_state==0 || volatile_read64(xhci_state+4056)!=1 || volatile_read64(input_state+32)!=1 { return 0; }
    let dma=volatile_read64(xhci_state+4040); let frame=volatile_read64(xhci_state+4048); if dma==0 || frame==0 { return 0; }
    let qcount:u64=24; let idx=volatile_read64(xhci_state+4080); if idx>=qcount { return 0; }
    let qh=dma; let td=dma+128+(idx*64); let data=dma+2048+(idx*8); let tok=volatile_read32(td+8); let active=(tok/128)%2; let halt=(tok/64)%2; let errs=(tok/4)%32; let rem=(tok/65536)%32768; let cur=volatile_read32(qh+12); let otok=volatile_read32(qh+24);
    if active!=0 { if cur!=(td%4294967296) && idx==0 { unsafe { volatile_write64(xhci_state+4056,44); volatile_write64(xhci_state+4000,otok); } } return 0; }
    if halt!=0 || errs!=0 || rem>8 { unsafe { volatile_write64(xhci_state+4056,40+errs); volatile_write64(xhci_state+4000,tok); } return 0; }
    let actual=8-rem; let raw=volatile_read64(data); let prev=volatile_read64(xhci_state+4088); var delivered:u64=0;
    if actual>=3 { let buttons=volatile_read8(data); let dx=volatile_read8(data+1); let dy=volatile_read8(data+2); if buttons!=(prev%256) { input_push(input_state,4,0,buttons); delivered=1; } if dx!=0 { input_push(input_state,5,0,dx); delivered=1; } if dy!=0 { input_push(input_state,6,0,dy); delivered=1; } }
    unsafe { volatile_write64(xhci_state+4064,volatile_read64(xhci_state+4064)+1); if delivered!=0 { volatile_write64(input_state+3104,1); volatile_write64(input_state+3128,1); volatile_write64(xhci_state+4072,volatile_read64(xhci_state+4072)+1); } volatile_write64(xhci_state+4088,raw); volatile_write64(xhci_state+4080,idx+1); }
    return delivered;
}'''
s=s.replace(tick,newtick,1)

s=s.replace(fn_text(s,'v140_text_wifi_v140'),label_fn('v140_text_wifi_v140','R65 PMNDATRE'),1)
rs=s.index('v140_text_wifi_v140(surface,px+10,py+748,white);')
re=s.index('\n    return 1;\n}',rs)
newrow="v140_text_wifi_v140(surface,px+10,py+748,white); if xhci!=0 { let dm=volatile_read64(xhci+4040); var a:u64=0; var t:u64=0; var r:u64=0; var e:u64=0; if dm!=0 { let ot=volatile_read32(dm+24); a=(ot/128)%2; t=(ot/2147483648)%2; r=(ot/65536)%32768; e=(ot/4)%32; } let compat=volatile_read64(xhci+4000); v108_draw_small_u64(surface,((px+100)*65536)+(py+748),volatile_read64(xhci+3984)+(compat*0),green); v108_draw_small_u64(surface,((px+140)*65536)+(py+748),volatile_read64(xhci+3992),amber); v108_draw_small_u64(surface,((px+180)*65536)+(py+748),volatile_read64(xhci+4064),white); v108_draw_small_u64(surface,((px+220)*65536)+(py+748),volatile_read64(xhci+4072),green); v108_draw_small_u64(surface,((px+260)*65536)+(py+748),a,amber); v108_draw_small_u64(surface,((px+300)*65536)+(py+748),t,white); v108_draw_small_u64(surface,((px+340)*65536)+(py+748),r,green); v108_draw_small_u64(surface,((px+380)*65536)+(py+748),e,amber); }"
s=s[:rs]+newrow+s[re:]

arm2=fn_text(s,'v159_ehci_mouse_periodic_arm'); tick2=fn_text(s,'v159_ehci_mouse_periodic_tick')
for q in ('hubvid==32903','hubpid==32776','hubproto==1','hubchars==9','thinkbits==8','let legacy_info2:u64=1090586113','let newsched_info2:u64=1090591745','let legacy_cmask=3*power2_u64(gap_uf)','let qcount:u64=24','volatile_write32(qtd+8,560512)','volatile_write32(dummy+8,64)','cmd=set_flag(cmd,16)'):
 if q not in arm2: raise SystemExit('r65 persistent-arm witness missing '+q)
for q in ('let idx=volatile_read64(xhci_state+4080)','let tok=volatile_read32(td+8)','let otok=volatile_read32(qh+24)','input_push(input_state,4,0,buttons)','volatile_write64(xhci_state+4080,idx+1)'):
 if q not in tick2: raise SystemExit('r65 completion witness missing '+q)
for bad in ('volatile_write32(qh+24','volatile_write32(qh+16','volatile_write32(td+8','cmd=set_flag(cmd,16)','cmd=clear_flag(cmd,16)','volatile_write32(op+20'):
 if bad in tick2: raise SystemExit('r65 live ownership violation '+bad)
out=hashlib.sha256(s.encode()).hexdigest()
EXPECTED='c34e637562aeea6a0156fb7142502d006ced9ea961bac3eccc336e7db4d64785'
if out!=EXPECTED: raise SystemExit('r65 output sha mismatch '+out)
p.write_text(s)
print(out)
