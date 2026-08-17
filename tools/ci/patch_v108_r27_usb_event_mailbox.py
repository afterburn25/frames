#!/usr/bin/env python3
from pathlib import Path
import hashlib,sys,subprocess
p=Path(sys.argv[1])
base=Path(__file__).with_name('patch_v108_r26b_identity.py')
subprocess.run([sys.executable,str(base),str(p)],check=True,stdout=subprocess.DEVNULL)
s=p.read_text()
BASE='7c8967f78588b37663db22c78f727bfa8685056045e88b7c126ffcd56a0cc66f'
if hashlib.sha256(s.encode()).hexdigest()!=BASE: raise SystemExit('base mismatch')

def span(name):
 st=s.index('fn '+name); op=s.index('{',st); d=0
 for i in range(op,len(s)):
  if s[i]=='{': d+=1
  elif s[i]=='}':
   d-=1
   if d==0:return st,i+1
 raise RuntimeError(name)
def repl(name,new):
 global s
 a,b=span(name);s=s[:a]+new+s[b:]
def rep(old,new,label):
 global s
 n=s.count(old)
 if n!=1: raise SystemExit(f'{label} count {n}')
 s=s.replace(old,new,1)
def text_fn(name,text):
 parts=[]
 for i,ch in enumerate(text): parts.append(f'if gui_draw_char_scaled(surface,((x+{i*6})*65536)+y,({ord(ch)}*65536)+1,color)==0 {{ return 0; }}')
 return f"fn {name}(surface:u64,x:u64,y:u64,color:u64) -> u64 {{ "+' '.join(parts)+" return 1; }\n"

# Shared software transfer-event mailbox. The mailbox page is allocated once
# per controller init and its pointer survives the MSC state snapshot, so HID,
# EP0 and BOT waiters share one completion-routing queue.
anchor='fn xhci_wait_command_completion(xhci_state:u64) -> u64 {'
helpers=r'''fn xhci_event_mailbox_put_v127(xhci_state:u64,slot:u64,endpoint:u64,packed:u64) -> u64 {
    if xhci_state==0 { return 0; } let box=volatile_read64(xhci_state+1840); if box==0 { return 0; }
    var i:u64=0; while i<16 { let e=box+64+(i*32); if volatile_read64(e)==0 { unsafe { volatile_write64(e+8,slot); volatile_write64(e+16,endpoint); volatile_write64(e+24,packed); volatile_write64(e,1); volatile_write64(box+8,volatile_read64(box+8)+1); } return 1; } i=i+1; }
    unsafe { volatile_write64(box,volatile_read64(box)+1); } return 0;
}
fn xhci_event_mailbox_take_v127(xhci_state:u64,slot:u64,endpoint:u64) -> u64 {
    if xhci_state==0 { return 0; } let box=volatile_read64(xhci_state+1840); if box==0 { return 0; }
    var i:u64=0; while i<16 { let e=box+64+(i*32); if volatile_read64(e)!=0 && volatile_read64(e+8)==slot && volatile_read64(e+16)==endpoint { let packed=volatile_read64(e+24); unsafe { volatile_write64(e,0); volatile_write64(box+16,volatile_read64(box+16)+1); } return packed+1; } i=i+1; } return 0;
}
fn xhci_event_mailbox_count_v127(xhci_state:u64) -> u64 {
    if xhci_state==0 { return 0; } let box=volatile_read64(xhci_state+1840); if box==0 { return 0; } var i:u64=0; var n:u64=0; while i<16 { if volatile_read64(box+64+(i*32))!=0 { n=n+1; } i=i+1; } return n;
}
'''
rep(anchor,helpers+anchor,'mailbox helpers')

# Allocate the mailbox with the controller's other persistent software rings.
a,b=span('xhci_controller_init'); f=s[a:b]
old='let command_ring=alloc_dma_page(phys_state,3); let event_ring=alloc_dma_page(phys_state,3); let erst=alloc_dma_page(phys_state,3); let dcbaa=alloc_dma_page(phys_state,3); if command_ring==0 || event_ring==0 || erst==0 || dcbaa==0 {'
new='let command_ring=alloc_dma_page(phys_state,3); let event_ring=alloc_dma_page(phys_state,3); let erst=alloc_dma_page(phys_state,3); let dcbaa=alloc_dma_page(phys_state,3); let event_mailbox=alloc_dma_page(phys_state,3); if command_ring==0 || event_ring==0 || erst==0 || dcbaa==0 || event_mailbox==0 {'
if f.count(old)!=1: raise SystemExit('controller alloc anchor')
f=f.replace(old,new,1)
f=f.replace('zero_page(command_ring); zero_page(event_ring); zero_page(erst); zero_page(dcbaa);','zero_page(command_ring); zero_page(event_ring); zero_page(erst); zero_page(dcbaa); zero_page(event_mailbox);',1)
old='volatile_write64(xhci_state+96,0); volatile_write64(xhci_state+104,1); volatile_write64(xhci_state+1264,9);'
new='volatile_write64(xhci_state+96,0); volatile_write64(xhci_state+104,1); volatile_write64(xhci_state+1840,event_mailbox); volatile_write64(xhci_state+1264,9);'
if f.count(old)!=1: raise SystemExit('controller state anchor')
f=f.replace(old,new,1); s=s[:a]+f+s[b:]

new_cmd=r'''fn xhci_wait_command_completion(xhci_state:u64) -> u64 {
    let event_ring=volatile_read64(xhci_state+24); var spins:u64=0;
    while spins<8000000 {
        let index=volatile_read64(xhci_state+96); let cycle=volatile_read64(xhci_state+104); let trb=event_ring+(index*16); let control=volatile_read32(trb+12);
        if control%2==cycle {
            let typ=(control/1024)%64;
            if typ==33 { let status=volatile_read32(trb+8); let code=(status/16777216)%256; let slot=(control/16777216)%256; unsafe { volatile_write64(xhci_state+488,code); volatile_write64(xhci_state+496,slot); } xhci_event_advance(xhci_state); if code==1 && slot>0 { return slot; } return 0; }
            if typ==32 { let status=volatile_read32(trb+8); let code=(status/16777216)%256; let residue=status%16777216; let ep=(control/65536)%32; let slot=(control/16777216)%256; xhci_event_advance(xhci_state); xhci_event_mailbox_put_v127(xhci_state,slot,ep,(code*16777216)+residue); }
            else { xhci_event_advance(xhci_state); }
        }
        cpu_pause(); spins=spins+1;
    }
    unsafe { volatile_write64(xhci_state+488,255); volatile_write64(xhci_state+496,0); } return 0;
}'''
repl('xhci_wait_command_completion',new_cmd)

new_transfer=r'''fn xhci_wait_transfer_event(xhci_state:u64, slot:u64, endpoint:u64) -> u64 {
    let event_ring=volatile_read64(xhci_state+24); var spins:u64=0;
    while spins<12000000 {
        let queued=xhci_event_mailbox_take_v127(xhci_state,slot,endpoint);
        if queued!=0 { let packed=queued-1; let code=packed/16777216; let remain=packed%16777216; unsafe { volatile_write64(xhci_state+504,code); volatile_write64(xhci_state+512,slot); volatile_write64(xhci_state+520,endpoint); volatile_write64(xhci_state+576,remain); } if code==1 || code==13 { return code; } return 0; }
        let index=volatile_read64(xhci_state+96); let cycle=volatile_read64(xhci_state+104); let trb=event_ring+(index*16); let control=volatile_read32(trb+12);
        if control%2==cycle {
            let typ=(control/1024)%64;
            if typ==32 {
                let status=volatile_read32(trb+8); let code=(status/16777216)%256; let remain=status%16777216; let event_ep=(control/65536)%32; let event_slot=(control/16777216)%256; xhci_event_advance(xhci_state);
                if event_slot==slot && event_ep==endpoint { unsafe { volatile_write64(xhci_state+504,code); volatile_write64(xhci_state+512,event_slot); volatile_write64(xhci_state+520,event_ep); volatile_write64(xhci_state+576,remain); } if code==1 || code==13 { return code; } return 0; }
                xhci_event_mailbox_put_v127(xhci_state,event_slot,event_ep,(code*16777216)+remain);
            } else { xhci_event_advance(xhci_state); }
        }
        cpu_pause(); spins=spins+1;
    }
    unsafe { volatile_write64(xhci_state+504,255); volatile_write64(xhci_state+512,0); volatile_write64(xhci_state+520,0); } return 0;
}'''
repl('xhci_wait_transfer_event',new_transfer)

new_hidwait=r'''fn xhci_wait_hid_event(xhci_state:u64, requested:u64) -> u64 {
    let slot=volatile_read64(xhci_state+136); let dci=volatile_read64(xhci_state+352); let event_ring=volatile_read64(xhci_state+24); var spins:u64=0;
    while spins<16000000 {
        let queued=xhci_event_mailbox_take_v127(xhci_state,slot,dci);
        if queued!=0 { let packed=queued-1; let code=packed/16777216; let residue=packed%16777216; if (code!=1 && code!=13) || residue>requested { return 0; } return requested-residue; }
        let index=volatile_read64(xhci_state+96); let cycle=volatile_read64(xhci_state+104); let trb=event_ring+(index*16); let control=volatile_read32(trb+12);
        if control%2==cycle {
            let typ=(control/1024)%64;
            if typ==32 { let status=volatile_read32(trb+8); let code=(status/16777216)%256; let residue=status%16777216; let event_ep=(control/65536)%32; let event_slot=(control/16777216)%256; xhci_event_advance(xhci_state); if event_slot==slot && event_ep==dci { if (code!=1 && code!=13) || residue>requested { return 0; } return requested-residue; } xhci_event_mailbox_put_v127(xhci_state,event_slot,event_ep,(code*16777216)+residue); }
            else { xhci_event_advance(xhci_state); }
        }
        cpu_pause(); spins=spins+1;
    }
    return 0;
}'''
repl('xhci_wait_hid_event',new_hidwait)

new_bulk=r'''fn xhci_wait_bulk_event(xhci_state:u64, slot:u64, dci:u64, requested:u64) -> u64 {
    let event_ring=volatile_read64(xhci_state+24); var spins:u64=0; var limit:u64=16000000; if volatile_read64(xhci_state+1800)==1 { limit=500000; }
    while spins<limit {
        let queued=xhci_event_mailbox_take_v127(xhci_state,slot,dci);
        if queued!=0 { let packed=queued-1; let code=packed/16777216; let residue=packed%16777216; serial_usb_msc_diag(47,(code*72057594037927936)+(slot*281474976710656)+(dci*4294967296)+residue); if (code!=1 && code!=13) || residue>requested { return 0; } return requested-residue; }
        let index=volatile_read64(xhci_state+96); let cycle=volatile_read64(xhci_state+104); let trb=event_ring+(index*16); let control=volatile_read32(trb+12);
        if control%2==cycle { let typ=(control/1024)%64; if typ==32 { let status=volatile_read32(trb+8); let code=(status/16777216)%256; let residue=status%16777216; let ep=(control/65536)%32; let eslot=(control/16777216)%256; serial_usb_msc_diag(40,(code*72057594037927936)+(eslot*281474976710656)+(ep*4294967296)+residue); xhci_event_advance(xhci_state); if eslot==slot && ep==dci { if (code!=1 && code!=13) || residue>requested { return 0; } return requested-residue; } xhci_event_mailbox_put_v127(xhci_state,eslot,ep,(code*16777216)+residue); serial_usb_msc_diag(46,(eslot*281474976710656)+(ep*4294967296)+residue); } else { xhci_event_advance(xhci_state); } }
        cpu_pause(); spins=spins+1;
    }
    serial_usb_msc_diag(41,(slot*4294967296)+(dci*65536)+requested); return 0;
}'''
repl('xhci_wait_bulk_event',new_bulk)

new_cont=r'''fn xhci_hid_poll_continuous(xhci_state:u64,input_state:u64) -> u64 {
    if xhci_state==0 || input_state==0 || volatile_read64(xhci_state+808)==0 { return 1; }
    let slot=volatile_read64(xhci_state+136); let dci=volatile_read64(xhci_state+352); let packet=volatile_read64(xhci_state+360); var code:u64=0; var residue:u64=0; var matched:u64=0;
    let queued=xhci_event_mailbox_take_v127(xhci_state,slot,dci);
    if queued!=0 { let packed=queued-1; code=packed/16777216; residue=packed%16777216; matched=1; }
    if matched==0 {
        let event_ring=volatile_read64(xhci_state+24); let index=volatile_read64(xhci_state+96); let cycle=volatile_read64(xhci_state+104); if event_ring==0 { return 0; }
        let trb=event_ring+(index*16); let control=volatile_read32(trb+12); if control%2!=cycle { return 1; }
        let typ=(control/1024)%64; if typ!=32 { xhci_event_advance(xhci_state); return 1; }
        let status=volatile_read32(trb+8); code=(status/16777216)%256; residue=status%16777216; let event_ep=(control/65536)%32; let event_slot=(control/16777216)%256; xhci_event_advance(xhci_state);
        if event_slot!=slot || event_ep!=dci { xhci_event_mailbox_put_v127(xhci_state,event_slot,event_ep,(code*16777216)+residue); return 1; }
    }
    unsafe { volatile_write64(xhci_state+808,0); }
    if (code!=1 && code!=13) || residue>packet { return 0; }
    let actual=packet-residue; let protocol=volatile_read64(xhci_state+336); if actual==0 || (protocol==1 && actual<8) || (protocol==2 && actual<3) { return 0; }
    let buffer=volatile_read64(xhci_state+432); let checksum=nvme_read_checksum(buffer,actual); unsafe { volatile_write64(xhci_state+440,actual); volatile_write64(xhci_state+448,checksum); volatile_write64(xhci_state+456,volatile_read8(buffer)); volatile_write64(xhci_state+464,volatile_read8(buffer+1)); volatile_write64(xhci_state+472,1); volatile_write64(xhci_state+816,volatile_read64(xhci_state+816)+1); }
    if input_decode_boot_hid(xhci_state,input_state)==0 { return 0; }
    if volatile_read64(xhci_state+824)==0 { unsafe { volatile_write64(xhci_state+824,1); } serial_marker_devprev_usb_report_ok(); }
    return xhci_hid_arm_continuous(xhci_state,0);
}'''
repl('xhci_hid_poll_continuous',new_cont)

# USB-only overlay: replace mature desktop/right-click rows with shared-event
# routing and live EHCI ownership/port evidence for the physical gate.
overlay_anchor='fn v108_input_overlay_draw(surface:u64,state:u64,input_state:u64,xhci:u64) -> u64 {'
rep(overlay_anchor,text_fn('v108_text_xevt_v127','XEVT Q P T L')+text_fn('v108_text_eown_v127','EOWN B0 O0 B1 O1')+text_fn('v108_text_eprt_v127','EPRT P0 C0 P1 C1')+overlay_anchor,'overlay labels')
a,b=span('v108_input_overlay_draw'); f=s[a:b]
old='''    v108_text_drep_v119(surface,px+10,py+424,white); v108_draw_small_u64(surface,((px+100)*65536)+(py+424),volatile_read64(state+384),amber); v108_draw_small_u64(surface,((px+160)*65536)+(py+424),volatile_read64(state+376),green); v108_draw_small_u64(surface,((px+220)*65536)+(py+424),volatile_read64(state+296),white); v108_draw_small_u64(surface,((px+280)*65536)+(py+424),volatile_read64(state+128),white);'''
new='''    v108_text_xevt_v127(surface,px+10,py+424,white); if xhci!=0 { let xb=volatile_read64(xhci+1840); v108_draw_small_u64(surface,((px+112)*65536)+(py+424),xhci_event_mailbox_count_v127(xhci),amber); if xb!=0 { v108_draw_small_u64(surface,((px+166)*65536)+(py+424),volatile_read64(xb+8),white); v108_draw_small_u64(surface,((px+220)*65536)+(py+424),volatile_read64(xb+16),green); v108_draw_small_u64(surface,((px+274)*65536)+(py+424),volatile_read64(xb),red); } }'''
if f.count(old)!=1: raise SystemExit('DREP overlay anchor')
f=f.replace(old,new,1)
old='''    v108_text_rbtn_v120(surface,px+10,py+460,white); v108_draw_small_u64(surface,((px+136)*65536)+(py+460),volatile_read64(input_state+3760),amber); v108_draw_small_u64(surface,((px+196)*65536)+(py+460),volatile_read64(state+320),red); v108_draw_small_u64(surface,((px+274)*65536)+(py+460),volatile_read64(state+328),green);
    v108_text_rflt_v121(surface,px+10,py+478,white); v108_draw_small_u64(surface,((px+136)*65536)+(py+478),volatile_read64(input_state+3760),amber); v108_draw_small_u64(surface,((px+196)*65536)+(py+478),volatile_read64(input_state+3768),white); v108_draw_small_u64(surface,((px+256)*65536)+(py+478),volatile_read64(input_state+2816),green); v108_draw_small_u64(surface,((px+316)*65536)+(py+478),volatile_read64(input_state+2824),red);'''
new='''    v108_text_eown_v127(surface,px+10,py+460,white); if xhci!=0 { v108_draw_small_u64(surface,((px+136)*65536)+(py+460),volatile_read64(xhci+1504),amber); v108_draw_small_u64(surface,((px+196)*65536)+(py+460),volatile_read64(xhci+1512),green); v108_draw_small_u64(surface,((px+256)*65536)+(py+460),volatile_read64(xhci+1544),amber); v108_draw_small_u64(surface,((px+316)*65536)+(py+460),volatile_read64(xhci+1552),green); }
    v108_text_eprt_v127(surface,px+10,py+478,white); if xhci!=0 { v108_draw_small_u64(surface,((px+136)*65536)+(py+478),volatile_read64(xhci+1488),white); v108_draw_small_u64(surface,((px+196)*65536)+(py+478),volatile_read64(xhci+1496),green); v108_draw_small_u64(surface,((px+256)*65536)+(py+478),volatile_read64(xhci+1528),white); v108_draw_small_u64(surface,((px+316)*65536)+(py+478),volatile_read64(xhci+1536),green); }'''
if f.count(old)!=1: raise SystemExit('right rows anchor')
f=f.replace(old,new,1); s=s[:a]+f+s[b:]

# Model invariants.
for name in ('xhci_wait_transfer_event','xhci_wait_hid_event','xhci_wait_bulk_event','xhci_hid_poll_continuous'):
 a,b=span(name); f=s[a:b]
 if 'xhci_event_mailbox_put_v127' not in f or 'xhci_event_mailbox_take_v127' not in f: raise SystemExit('mailbox missing '+name)
a,b=span('xhci_controller_init')
if 'volatile_write64(xhci_state+1840,event_mailbox)' not in s[a:b]: raise SystemExit('mailbox pointer not retained')

expected='6504e3d3210821592acffb0e86c96aa6aa5aaa5e42e23699e44a830f185b2450'
actual=hashlib.sha256(s.encode()).hexdigest()
if actual!=expected: raise SystemExit(f'r27 identity mismatch {actual}')
p.write_text(s)
print(actual)
