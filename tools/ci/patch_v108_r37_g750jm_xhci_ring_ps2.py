#!/usr/bin/env python3
from pathlib import Path
import hashlib, subprocess, sys
if len(sys.argv)!=2: raise SystemExit('usage: patch_v108_r37_g750jm_xhci_ring_ps2.py <kernel/main.nx>')
p=Path(sys.argv[1])
base=Path(__file__).with_name('patch_v108_r36_nonblocking_interrupt_recovery.py')
subprocess.run([sys.executable,str(base),str(p)],check=True,stdout=subprocess.DEVNULL)
s=p.read_text()
BASE='442befd5d051dccd4fa5b1303557f7f131b3653d6be35db7e05abad20b722db6'
if hashlib.sha256(s.encode()).hexdigest()!=BASE: raise SystemExit('r36 base mismatch')

def rep(old,new,label):
 global s
 n=s.count(old)
 if n!=1: raise SystemExit(f'{label} count {n}')
 s=s.replace(old,new,1)

def fn_text(name):
 st=s.index('fn '+name); op=s.index('{',st); d=0
 for i in range(op,len(s)):
  if s[i]=='{': d+=1
  elif s[i]=='}':
   d-=1
   if d==0: return s[st:i+1]
 raise SystemExit('unterminated '+name)

def fnrep(name,new):
 rep(fn_text(name),new,name)

def label_fn(name,text):
 out=f'fn {name}(surface:u64,x:u64,y:u64,color:u64) -> u64 {{'
 for i,ch in enumerate(text): out+=f' if gui_draw_char_scaled(surface,((x+{i*6})*65536)+y,({ord(ch)}*65536)+1,color)==0 {{ return 0; }}'
 return out+' return 1; }'

rep('volatile_write64(tring+4080,tring); volatile_write64(tring+4088,6147);','volatile_write64(tring+4080,tring); volatile_write32(tring+4088,0); volatile_write32(tring+4092,6147);','HID Link TRB control placement')

fnrep('v136_xhci_endpoint_snapshot','''fn v136_xhci_endpoint_snapshot(xhci_state:u64) -> u64 {
    if xhci_state==0 { return 0; }
    let output=volatile_read64(xhci_state+160); let ctxsize=volatile_read64(xhci_state+176); let dci=volatile_read64(xhci_state+352); if output==0 || ctxsize==0 || dci<2 || dci>31 { return 0; }
    let ep=output+(dci*ctxsize); let dw0=volatile_read32(ep); let dw1=volatile_read32(ep+4); let state=dw0%8; let interval=(dw0/65536)%256; let mps=(dw1/65536)%65536; let deq=volatile_read64(ep+8); let dcs=deq%2; let ptr=deq-(deq%16); let ring=volatile_read64(xhci_state+392); var qidx:u64=255; var inring:u64=0;
    if ring!=0 && ptr>=ring && ptr<ring+4080 { qidx=(ptr-ring)/16; inring=1; }
    unsafe { volatile_write64(xhci_state+2696,state); volatile_write64(xhci_state+2704,interval); volatile_write64(xhci_state+2712,dci); volatile_write64(xhci_state+2720,mps); volatile_write64(xhci_state+2824,qidx); volatile_write64(xhci_state+2832,dcs); volatile_write64(xhci_state+2840,inring); }
    return state;
}''')

fnrep('v136_xhci_command_endpoint','''fn v136_xhci_command_endpoint(xhci_state:u64,typ:u64,param:u64) -> u64 {
    if xhci_state==0 || (typ!=14 && typ!=15 && typ!=16) { return 0; }
    let ring=volatile_read64(xhci_state+16); let doorbells=volatile_read64(xhci_state+88); let slot=volatile_read64(xhci_state+136); let dci=volatile_read64(xhci_state+352); if ring==0 || doorbells==0 || slot==0 || dci<2 || dci>31 { return 0; }
    var tail=volatile_read64(xhci_state+64); var cycle=volatile_read64(xhci_state+72); if tail>=255 { tail=0; if cycle==1 { cycle=0; } else { cycle=1; } }
    let trb=ring+(tail*16); unsafe { volatile_write64(trb,param); volatile_write32(trb+8,0); volatile_write32(trb+12,(typ*1024)+cycle+(dci*65536)+(slot*16777216)); }
    tail=tail+1; unsafe { volatile_write64(xhci_state+64,tail); volatile_write64(xhci_state+72,cycle); volatile_write32(doorbells,0); }
    let done=xhci_wait_command_completion(xhci_state); unsafe { volatile_write64(xhci_state+2744,volatile_read64(xhci_state+488)); } if done==slot { return 1; } return 0;
}''')

anchor='fn v136_hid_interrupt_recovery_tick(xhci_state:u64) -> u64 {'
helper='''fn v137_xhci_hid_rebase_ring(xhci_state:u64) -> u64 {
    if xhci_state==0 { return 0; } let ring=volatile_read64(xhci_state+392); if ring==0 { return 0; }
    var off:u64=0; while off<4080 { unsafe { volatile_write64(ring+off,0); } off=off+8; }
    unsafe { volatile_write64(ring+4080,ring); volatile_write32(ring+4088,0); volatile_write32(ring+4092,6147); volatile_write64(xhci_state+408,0); volatile_write64(xhci_state+800,1); volatile_write64(xhci_state+808,0); }
    return ring+1;
}
'''+anchor
rep(anchor,helper,'r37 ring rebase helper')

fnrep('v136_hid_interrupt_recovery_tick','''fn v136_hid_interrupt_recovery_tick(xhci_state:u64) -> u64 {
    if xhci_state==0 || volatile_read64(xhci_state+416)!=1 { return 1; }
    let state=v136_xhci_endpoint_snapshot(xhci_state); if volatile_read64(xhci_state+816)!=0 { return 1; }
    let now=read_tsc(); let last=volatile_read64(xhci_state+2752); if last!=0 && now>last && now-last<1500000000 { return 1; } unsafe { volatile_write64(xhci_state+2752,now); }
    let slot=volatile_read64(xhci_state+136); let dci=volatile_read64(xhci_state+352); let doorbells=volatile_read64(xhci_state+88); if slot==0 || dci<2 || dci>31 || doorbells==0 { return 1; }
    if state==1 {
        if volatile_read64(xhci_state+808)==0 { if xhci_hid_arm_continuous(xhci_state,0)==0 { unsafe { volatile_write64(xhci_state+2800,volatile_read64(xhci_state+2800)+1); } } return 1; }
        let kicks=volatile_read64(xhci_state+2728); if kicks<3 { unsafe { volatile_write32(doorbells+(slot*4),dci); volatile_write64(xhci_state+2728,kicks+1); } return 1; }
        if volatile_read64(xhci_state+2816)<2 {
            var ok:u64=1; if v136_xhci_command_endpoint(xhci_state,15,0)==0 { ok=0; }
            let first=v137_xhci_hid_rebase_ring(xhci_state); if first==0 || v136_xhci_command_endpoint(xhci_state,16,first)==0 { ok=0; }
            unsafe { volatile_write64(xhci_state+2816,volatile_read64(xhci_state+2816)+1); volatile_write64(xhci_state+2728,0); }
            if ok!=0 { if xhci_hid_arm_continuous(xhci_state,0)==0 { unsafe { volatile_write64(xhci_state+2800,volatile_read64(xhci_state+2800)+1); } } }
        }
        return 1;
    }
    if (state==2 || state==3) && volatile_read64(xhci_state+2736)<2 {
        var ok:u64=1; if state==2 { if v136_xhci_command_endpoint(xhci_state,14,0)==0 { ok=0; } }
        let next=v137_xhci_hid_rebase_ring(xhci_state); if next==0 || v136_xhci_command_endpoint(xhci_state,16,next)==0 { ok=0; }
        unsafe { volatile_write64(xhci_state+2736,volatile_read64(xhci_state+2736)+1); volatile_write64(xhci_state+808,0); }
        if ok!=0 { if xhci_hid_arm_continuous(xhci_state,0)==0 { unsafe { volatile_write64(xhci_state+2800,volatile_read64(xhci_state+2800)+1); } } }
        return 1;
    }
    return 1;
}''')

rep('if typ==1 || typ==2 {','if typ>=1 && typ<=3 {','Elantech v4 buttons on all packet classes')
rep('if typ==3 { unsafe { volatile_write64(input_state+3608,volatile_read64(input_state+3608)+1); } return 1; }','if typ==3 { unsafe { volatile_write64(input_state+3608,volatile_read64(input_state+3608)+1); } return ps2_elan4_motion_v112(input_state,a,b); }','Elantech v4 motion delivery')

fnrep('v108_text_r36_v136',label_fn('v108_text_r37_v137','R37 S Q C K F E'))
rep('''v108_text_r36_v136(surface,px+10,py+730,white); if xhci!=0 { v108_draw_small_u64(surface,((px+112)*65536)+(py+730),volatile_read64(xhci+2696),green); v108_draw_small_u64(surface,((px+160)*65536)+(py+730),volatile_read64(xhci+2704),amber); v108_draw_small_u64(surface,((px+208)*65536)+(py+730),volatile_read64(xhci+2712),white); v108_draw_small_u64(surface,((px+256)*65536)+(py+730),volatile_read64(xhci+2720),white); v108_draw_small_u64(surface,((px+316)*65536)+(py+730),volatile_read64(xhci+2728),green); v108_draw_small_u64(surface,((px+376)*65536)+(py+730),volatile_read64(xhci+2784),red); }''','''v108_text_r37_v137(surface,px+10,py+730,white); if xhci!=0 { v108_draw_small_u64(surface,((px+112)*65536)+(py+730),volatile_read64(xhci+2696),green); v108_draw_small_u64(surface,((px+160)*65536)+(py+730),volatile_read64(xhci+2824),amber); v108_draw_small_u64(surface,((px+208)*65536)+(py+730),volatile_read64(xhci+2832),white); v108_draw_small_u64(surface,((px+256)*65536)+(py+730),volatile_read64(xhci+2728),white); v108_draw_small_u64(surface,((px+316)*65536)+(py+730),volatile_read64(xhci+2816),green); v108_draw_small_u64(surface,((px+376)*65536)+(py+730),volatile_read64(xhci+2784),red); }''','r37 physical row')

rep('''var last_raw=volatile_read64(input_state+3224); var last_usb_r=volatile_read64(input_state+3128); var last_src=volatile_read64(input_state+3104); var last_r36_s:u64=0; var last_r36_k:u64=0; var last_r36_e:u64=0; if xhci!=0 { last_r36_s=volatile_read64(xhci+2696); last_r36_k=volatile_read64(xhci+2728); last_r36_e=volatile_read64(xhci+2784); } var raw_budget:u64=0;''','''var last_raw=volatile_read64(input_state+3224); var last_usb_r=volatile_read64(input_state+3128); var last_src=volatile_read64(input_state+3104); var last_r37_s:u64=0; var last_r37_q:u64=255; var last_r37_c:u64=0; var last_r37_f:u64=0; var last_r37_e:u64=0; var last_r37_draw=read_tsc(); if xhci!=0 { last_r37_s=volatile_read64(xhci+2696); last_r37_q=volatile_read64(xhci+2824); last_r37_c=volatile_read64(xhci+2832); last_r37_f=volatile_read64(xhci+2816); last_r37_e=volatile_read64(xhci+2784); } var raw_budget:u64=0;''','r37 telemetry baseline')
rep('''if xhci!=0 && volatile_read64(xhci+808)!=0 { xhci_hid_poll_continuous(xhci,input_state); }
        if xhci!=0 { v136_hid_interrupt_recovery_tick(xhci); }
        ps2_poll_fallback_burst_v112(input_state,24);
        var telemetry_redraw:u64=0; if xhci!=0 { let rs=volatile_read64(xhci+2696); let rk=volatile_read64(xhci+2728); let re=volatile_read64(xhci+2784); if rs!=last_r36_s || rk!=last_r36_k || re!=last_r36_e { telemetry_redraw=1; } last_r36_s=rs; last_r36_k=rk; last_r36_e=re; } var motion_telemetry_redraw:u64=0;''','''ps2_poll_fallback_burst_v112(input_state,48);
        if xhci!=0 && volatile_read64(xhci+808)!=0 { xhci_hid_poll_continuous(xhci,input_state); }
        if xhci!=0 { v136_hid_interrupt_recovery_tick(xhci); }
        var telemetry_redraw:u64=0; if xhci!=0 { let rs=volatile_read64(xhci+2696); let rq=volatile_read64(xhci+2824); let rc=volatile_read64(xhci+2832); let rf=volatile_read64(xhci+2816); let re=volatile_read64(xhci+2784); var changed:u64=0; if rs!=last_r37_s || rq!=last_r37_q || rc!=last_r37_c || rf!=last_r37_f || re!=last_r37_e { changed=1; } let dnow=read_tsc(); if changed!=0 && (dnow<last_r37_draw || dnow-last_r37_draw>=1000000000) { telemetry_redraw=1; last_r37_draw=dnow; } last_r37_s=rs; last_r37_q=rq; last_r37_c=rc; last_r37_f=rf; last_r37_e=re; } var motion_telemetry_redraw:u64=0;''','PS2 priority and diagnostic flicker throttle')

p.write_text(s)
out=hashlib.sha256(s.encode()).hexdigest()
EXPECTED='03f446845e111e35b8cff6b216c5fee2d214dc0a4d6e25898f8a03b891c0c511'
if out!=EXPECTED: raise SystemExit(f'r37 output sha mismatch {out}')
print(out)
