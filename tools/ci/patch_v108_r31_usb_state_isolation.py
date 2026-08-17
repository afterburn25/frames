#!/usr/bin/env python3
from pathlib import Path
import hashlib,subprocess,sys
if len(sys.argv)!=2: raise SystemExit('usage: patch_v108_r31_usb_state_isolation.py <kernel/main.nx>')
p=Path(sys.argv[1]); base=Path(__file__).with_name('patch_v108_r30b_hid_first_device_state.py')
subprocess.run([sys.executable,str(base),str(p)],check=True,stdout=subprocess.DEVNULL)
s=p.read_text()
BASE='d947d603112369340749e6be8397bfed08bf1de49651a0a0602571afcb754c3b'
if hashlib.sha256(s.encode()).hexdigest()!=BASE: raise SystemExit('r30b base mismatch')

def span(text,name):
 st=text.index('fn '+name);op=text.index('{',st);d=0
 for i in range(op,len(text)):
  if text[i]=='{':d+=1
  elif text[i]=='}':
   d-=1
   if d==0:return st,i+1
 raise RuntimeError(name)
def repl_fn(name,new):
 global s
 a,b=span(s,name);s=s[:a]+new+s[b:]
def rep(old,new,label,count=1):
 global s
 n=s.count(old)
 if n!=count: raise RuntimeError(f'{label} {n}')
 s=s.replace(old,new,count)

# Fallback MSC/log discovery must not zero the primary controller state used for
# physical HID telemetry. Allocate a dedicated temporary xHCI controller state.
rep('let xhci_state = bump_alloc(&mut heap_cursor, heap_end, 4096); let usb_log_state = bump_alloc(&mut heap_cursor, heap_end, 4096); let flight_state',
    'let xhci_state = bump_alloc(&mut heap_cursor, heap_end, 4096); let usb_log_state = bump_alloc(&mut heap_cursor, heap_end, 4096); let usb_scan_state = bump_alloc(&mut heap_cursor, heap_end, 4096); let flight_state',
    'usb scan allocation')
rep('if input_queue_ready!=0 && flight_state!=0 && flight_buffer!=0 && usb_log_state!=0 { if flight_recorder_init_v125(flight_state,flight_buffer,262144)!=0 { unsafe { volatile_write64(input_state+3792,flight_state); volatile_write64(hardware_state+640,usb_log_state); volatile_write64(hardware_state+648,flight_state); }',
    'if input_queue_ready!=0 && flight_state!=0 && flight_buffer!=0 && usb_log_state!=0 && usb_scan_state!=0 { if flight_recorder_init_v125(flight_state,flight_buffer,262144)!=0 { unsafe { volatile_write64(input_state+3792,flight_state); volatile_write64(hardware_state+640,usb_log_state); volatile_write64(hardware_state+648,flight_state); volatile_write64(hardware_state+920,usb_scan_state); }',
    'store usb scan state')

new_retain=r'''fn v108_log_msc_retain_v125(hardware_state:u64,phys_state:u64,xhci_state:u64,pml4:u64) -> u64 {
    if hardware_state==0 || phys_state==0 || xhci_state==0 || pml4==0 { return 0; }
    let scan=volatile_read64(hardware_state+920); if scan==0 || scan==xhci_state { return 0; }
    let total=volatile_read64(hardware_state+24); let fr=volatile_read64(hardware_state+648);
    let save_bdf=volatile_read64(hardware_state+80); let save_id=volatile_read64(hardware_state+144); let save_base=volatile_read64(hardware_state+192);
    var ci:u64=0; unsafe { volatile_write64(hardware_state+928,1); volatile_write64(hardware_state+936,0); volatile_write64(hardware_state+944,0); volatile_write64(hardware_state+952,0); volatile_write64(hardware_state+960,0); volatile_write64(hardware_state+968,0); }
    while ci<total && ci<4 {
        let bdf=v108_pci_nth_xhci_v116(ci);
        if bdf==0 { ci=total; }
        else {
            let base=pci_bar_base(bdf,0);
            if base!=0 && ensure_identity_mmio_page(phys_state,pml4,base)!=0 {
                let id=pci_cfg_read32(bdf/65536,(bdf/256)%256,bdf%256,0);
                unsafe { volatile_write64(hardware_state+80,bdf); volatile_write64(hardware_state+144,id); volatile_write64(hardware_state+192,base); volatile_write64(hardware_state+936,bdf); }
                zero_page(scan); v108_intel_xhci_route_ports_v120(bdf,scan,hardware_state);
                let init=xhci_controller_init(hardware_state,phys_state,scan,pml4); unsafe { volatile_write64(hardware_state+944,volatile_read64(scan+1264)); volatile_write64(hardware_state+952,volatile_read64(scan+1272)); volatile_write64(hardware_state+960,volatile_read64(scan+1320)); }
                if init!=0 {
                    var start:u64=0; var tries:u64=0;
                    while tries<32 {
                        let port=xhci_reset_connected_port_from(scan,start);
                        if port==0 { tries=32; }
                        else {
                            start=port; tries=tries+1; unsafe { volatile_write64(hardware_state+968,port); }
                            if fr!=0 { flight_record_v125(fr,196609,2,port); }
                            xhci_prepare_new_device_v130(scan); let slot=xhci_enable_slot(scan);
                            if slot!=0 {
                                if fr!=0 { flight_record_v125(fr,196609,3,(slot*256)+volatile_read64(scan+488)); }
                                if xhci_address_default_device(scan,phys_state)!=0 {
                                    if fr!=0 { flight_record_v125(fr,196609,4,volatile_read64(scan+488)); }
                                    if xhci_get_device_descriptor8(scan,phys_state)!=0 {
                                        if fr!=0 { flight_record_v125(fr,196609,5,volatile_read64(scan+504)); }
                                        if xhci_finalize_address_and_descriptor(scan,phys_state)!=0 {
                                            if fr!=0 { flight_record_v125(fr,196609,6,(volatile_read64(scan+272)*65536)+volatile_read64(scan+280)); }
                                            if v108_msc_snapshot_v125(scan,hardware_state,phys_state,fr)!=0 && volatile_read64(hardware_state+728)!=0 {
                                                let msc=volatile_read64(hardware_state+640); if msc!=0 { unsafe { volatile_write64(msc+2176,1); } }
                                                unsafe { volatile_write64(hardware_state+680,6); volatile_write64(hardware_state+688,0); volatile_write64(hardware_state+696,volatile_read64(scan+272)); volatile_write64(hardware_state+704,volatile_read64(scan+280)); volatile_write64(hardware_state+80,save_bdf); volatile_write64(hardware_state+144,save_id); volatile_write64(hardware_state+192,save_base); }
                                                return 1;
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
            ci=ci+1;
        }
    }
    unsafe { volatile_write64(hardware_state+80,save_bdf); volatile_write64(hardware_state+144,save_id); volatile_write64(hardware_state+192,save_base); }
    return 0;
}'''
repl_fn('v108_log_msc_retain_v125',new_retain)

# An isolated fallback MSC controller state owns its own event ring. Do not copy
# primary state event indexes into it during a persistent log flush.
new_sync=r'''fn flight_sync_events_v125(msc:u64,active:u64,back:u64) -> u64 {
    if msc==0 || active==0 || volatile_read64(msc)!=volatile_read64(active) { return 1; }
    if volatile_read64(msc+2176)!=0 { return 1; }
    if back==0 { unsafe { volatile_write64(msc+96,volatile_read64(active+96)); volatile_write64(msc+104,volatile_read64(active+104)); } }
    else { unsafe { volatile_write64(active+96,volatile_read64(msc+96)); volatile_write64(active+104,volatile_read64(msc+104)); } }
    return 1;
}'''
repl_fn('flight_sync_events_v125',new_sync)

# Program the runtime event ring/interrupter while the controller is halted,
# then assert Run/Stop. QEMU tolerated the reverse ordering; real silicon does
# not need to.
old='''    cmd=volatile_read32(op+0); cmd=set_flag(cmd,1); unsafe { volatile_write32(op+0,cmd); } if xhci_wait_halted(op,0)==0 { unsafe { volatile_write64(xhci_state+1272,15); } return 0; }
    unsafe { volatile_write64(xhci_state+1264,8); }
    let rtsoff_raw=volatile_read32(base+24); let dboff_raw=volatile_read32(base+20); let runtime=base+(rtsoff_raw-(rtsoff_raw%32)); let doorbells=base+(dboff_raw-(dboff_raw%4));
    if pml4==0 || ensure_identity_mmio_page(phys_state,pml4,runtime)==0 || ensure_identity_mmio_page(phys_state,pml4,doorbells)==0 { unsafe { volatile_write64(xhci_state+1272,16); } return 0; }
    let intr=runtime+32; unsafe { volatile_write32(intr+8,1); volatile_write32(intr+16,erst%4294967296); volatile_write32(intr+20,erst/4294967296); volatile_write32(intr+24,event_ring%4294967296); volatile_write32(intr+28,event_ring/4294967296); }
    unsafe { volatile_write64(xhci_state+0,base); volatile_write64(xhci_state+8,op); volatile_write64(xhci_state+16,command_ring); volatile_write64(xhci_state+24,event_ring); volatile_write64(xhci_state+32,erst); volatile_write64(xhci_state+40,dcbaa); volatile_write64(xhci_state+48,maxslots); volatile_write64(xhci_state+56,1); volatile_write64(xhci_state+64,0); volatile_write64(xhci_state+72,1); volatile_write64(xhci_state+80,runtime); volatile_write64(xhci_state+88,doorbells); volatile_write64(xhci_state+96,0); volatile_write64(xhci_state+104,1); volatile_write64(xhci_state+1840,event_mailbox); volatile_write64(xhci_state+1264,9); volatile_write64(xhci_state+1272,0); }
'''
new='''    unsafe { volatile_write64(xhci_state+1264,8); }
    let rtsoff_raw=volatile_read32(base+24); let dboff_raw=volatile_read32(base+20); let runtime=base+(rtsoff_raw-(rtsoff_raw%32)); let doorbells=base+(dboff_raw-(dboff_raw%4));
    if pml4==0 || ensure_identity_mmio_page(phys_state,pml4,runtime)==0 || ensure_identity_mmio_page(phys_state,pml4,doorbells)==0 { unsafe { volatile_write64(xhci_state+1272,16); } return 0; }
    let intr=runtime+32; unsafe { volatile_write32(intr+8,1); volatile_write32(intr+16,erst%4294967296); volatile_write32(intr+20,erst/4294967296); volatile_write32(intr+24,event_ring%4294967296); volatile_write32(intr+28,event_ring/4294967296); }
    unsafe { volatile_write64(xhci_state+0,base); volatile_write64(xhci_state+8,op); volatile_write64(xhci_state+16,command_ring); volatile_write64(xhci_state+24,event_ring); volatile_write64(xhci_state+32,erst); volatile_write64(xhci_state+40,dcbaa); volatile_write64(xhci_state+48,maxslots); volatile_write64(xhci_state+56,1); volatile_write64(xhci_state+64,0); volatile_write64(xhci_state+72,1); volatile_write64(xhci_state+80,runtime); volatile_write64(xhci_state+88,doorbells); volatile_write64(xhci_state+96,0); volatile_write64(xhci_state+104,1); volatile_write64(xhci_state+1840,event_mailbox); }
    cmd=volatile_read32(op+0); cmd=set_flag(cmd,1); unsafe { volatile_write32(op+0,cmd); } if xhci_wait_halted(op,0)==0 { unsafe { volatile_write64(xhci_state+1272,15); } return 0; }
    unsafe { volatile_write64(xhci_state+2184,1); volatile_write64(xhci_state+1264,9); volatile_write64(xhci_state+1272,0); }
'''
rep(old,new,'xhci start order')

# Freeze primary HID/controller evidence before a fallback storage rescan can
# reinitialize the physical controller.
rep('v108_ehci_ro_probe_v122(hardware_state,phys_state,xhci_state,pml4); if volatile_read64(hardware_state+728)==0 { v108_log_msc_retain_v125(hardware_state,phys_state,xhci_state,pml4); }',
    'unsafe { volatile_write64(hardware_state+976,volatile_read64(xhci_state+1264)); volatile_write64(hardware_state+984,volatile_read64(xhci_state+1272)); volatile_write64(hardware_state+992,volatile_read64(xhci_state+1320)); volatile_write64(hardware_state+1000,volatile_read64(xhci_state+1640)); volatile_write64(hardware_state+1008,volatile_read64(xhci_state+1672)); volatile_write64(hardware_state+1016,volatile_read64(xhci_state+2184)); } v108_ehci_ro_probe_v122(hardware_state,phys_state,xhci_state,pml4); if volatile_read64(hardware_state+728)==0 { v108_log_msc_retain_v125(hardware_state,phys_state,xhci_state,pml4); }',
    'freeze primary USB evidence')

def label_fn(name,text):
 out=f'fn {name}(surface:u64,x:u64,y:u64,color:u64) -> u64 {{'
 for i,ch in enumerate(text): out+=f' if gui_draw_char_scaled(surface,((x+{i*6})*65536)+y,({ord(ch)}*65536)+1,color)==0 {{ return 0; }}'
 return out+' return 1; }\n'
rep('fn v108_input_overlay_draw(surface:u64,state:u64,input_state:u64,xhci:u64) -> u64 {',
    label_fn('v108_text_xpri_v131','XPRI S F C P R O')+label_fn('v108_text_xlog_v131','XLOG S F C P R A')+'fn v108_input_overlay_draw(surface:u64,state:u64,input_state:u64,xhci:u64) -> u64 {',
    'r31 labels')
rep('(410*65536)+688','(410*65536)+724','r31 overlay bounds',count=s.count('(410*65536)+688'))
a,b=span(s,'v108_input_overlay_draw'); ov=s[a:b]
oldrow='''    v108_text_rbtn_v130(surface,px+10,py+658,white); v108_draw_small_u64(surface,((px+112)*65536)+(py+658),volatile_read64(input_state+3760),amber); v108_draw_small_u64(surface,((px+166)*65536)+(py+658),volatile_read64(input_state+2808),white); v108_draw_small_u64(surface,((px+220)*65536)+(py+658),volatile_read64(input_state+2816),green); v108_draw_small_u64(surface,((px+274)*65536)+(py+658),volatile_read64(input_state+3768),green); v108_draw_small_u64(surface,((px+328)*65536)+(py+658),volatile_read64(state+128),green); v108_draw_small_u64(surface,((px+376)*65536)+(py+658),volatile_read64(state+152),green);'''
newrows='''    v108_text_xpri_v131(surface,px+10,py+658,white); v108_draw_small_u64(surface,((px+112)*65536)+(py+658),volatile_read64(hardware_state+976),amber); v108_draw_small_u64(surface,((px+166)*65536)+(py+658),volatile_read64(hardware_state+984),red); v108_draw_small_u64(surface,((px+220)*65536)+(py+658),volatile_read64(hardware_state+992),green); v108_draw_small_u64(surface,((px+274)*65536)+(py+658),volatile_read64(hardware_state+1000),white); v108_draw_small_u64(surface,((px+328)*65536)+(py+658),volatile_read64(hardware_state+1008),red); v108_draw_small_u64(surface,((px+376)*65536)+(py+658),volatile_read64(hardware_state+1016),green);
    v108_text_xlog_v131(surface,px+10,py+676,white); v108_draw_small_u64(surface,((px+112)*65536)+(py+676),volatile_read64(hardware_state+944),amber); v108_draw_small_u64(surface,((px+166)*65536)+(py+676),volatile_read64(hardware_state+952),red); v108_draw_small_u64(surface,((px+220)*65536)+(py+676),volatile_read64(hardware_state+960),green); v108_draw_small_u64(surface,((px+274)*65536)+(py+676),volatile_read64(hardware_state+968),white); v108_draw_small_u64(surface,((px+328)*65536)+(py+676),volatile_read64(hardware_state+928),amber); v108_draw_small_u64(surface,((px+376)*65536)+(py+676),volatile_read64(hardware_state+728),green);'''
if ov.count(oldrow)!=1: raise RuntimeError('rbtn row '+str(ov.count(oldrow)))
ov=ov.replace(oldrow,newrows,1);s=s[:a]+ov+s[b:]

if 'let usb_scan_state = bump_alloc' not in s: raise SystemExit('r31 scan state missing')
if 'volatile_write64(hardware_state+920,usb_scan_state)' not in s: raise SystemExit('r31 scan state not published')
a,b=span(s,'v108_log_msc_retain_v125'); retain=s[a:b]
if 'zero_page(xhci_state)' in retain or 'zero_page(scan)' not in retain: raise SystemExit('r31 fallback state isolation failed')
if 'xhci_controller_init(hardware_state,phys_state,scan,pml4)' not in retain: raise SystemExit('r31 fallback controller not isolated')
if 'volatile_write64(msc+2176,1)' not in retain: raise SystemExit('r31 isolated MSC marker missing')
a,b=span(s,'flight_sync_events_v125'); sync=s[a:b]
if 'volatile_read64(msc+2176)!=0' not in sync: raise SystemExit('r31 isolated event sync guard missing')
a,b=span(s,'xhci_controller_init'); ci=s[a:b]
if ci.index('volatile_write32(intr+8,1)') >= ci.index('cmd=set_flag(cmd,1)'): raise SystemExit('r31 xHCI runtime ring still programmed after Run')
if 'volatile_write64(xhci_state+2184,1)' not in ci: raise SystemExit('r31 controller-order proof marker missing')
if 'v108_text_xpri_v131' not in s or 'v108_text_xlog_v131' not in s: raise SystemExit('r31 physical telemetry missing')
if s.count('{')!=s.count('}'): raise SystemExit('brace imbalance')
expected='cf7a3f890811d6ff245ec822bf5fd38d01f405c990c7dce6161efb117699797c'
actual=hashlib.sha256(s.encode()).hexdigest()
if actual!=expected: raise SystemExit(f'r31 identity mismatch {actual}')
p.write_text(s); print(actual)
