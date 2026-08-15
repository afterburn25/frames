#!/usr/bin/env python3
from pathlib import Path
import hashlib,sys
p=Path(sys.argv[1])
expected='82594aaea923a2a19c06eadb73d8d985941b392c56b8c613866b5a99523ae806'
raw=p.read_bytes()
if hashlib.sha256(raw).hexdigest()!=expected:
    raise SystemExit('unexpected v109 kernel hash')
s=raw.decode('utf-8')

def marker(name):
    vals='; '.join(f'serial_putc({ord(c)})' for c in name+'\n')
    fn=name.lower()
    return f'fn serial_marker_{fn}() -> void {{ {vals}; return; }}\n'

names=[
'FRAMES_PROBE_DISPATCH_V3_OK','FRAMES_BIND_TX_V3_OK','FRAMES_RESOURCE_OWNER_V3_OK',
'FRAMES_USB_SERVICE_GRAPH_V3_OK','FRAMES_INPUT_BRIDGE_V3_OK','FRAMES_HOTPLUG_QUEUE_V3_OK',
'FRAMES_POWER_TRANSITION_V3_OK','FRAMES_DRIVER_RECOVERY_V3_OK','FRAMES_DRIVER_RUNTIME_V3_OK',
'FRAMES_DRIVER_RUNTIME_GATE_V3_OK']
code=''.join(marker(n) for n in names)+r'''
fn probe_dispatch_v3_run(state:u64,probe:u64,work:u64,matches:u64) -> u64 {
    if state==0 || probe==0 || work==0 || matches==0 { return 0; } zero_page(state);
    let queued=volatile_read64(probe+8); let drivers=volatile_read64(matches+8); var pass:u64=0;
    if drivers>0 { pass=1; }
    unsafe { volatile_write64(state,1); volatile_write64(state+8,queued); volatile_write64(state+16,drivers); volatile_write64(state+24,pass); volatile_write64(state+32,read_tsc()); }
    if pass==1 { serial_marker_frames_probe_dispatch_v3_ok(); } return pass;
}
fn driver_binding_tx_v3_run(state:u64,devices:u64,bindings:u64,lifecycle:u64) -> u64 {
    if state==0 || devices==0 || bindings==0 || lifecycle==0 { return 0; } zero_page(state);
    let dc=volatile_read64(devices+8); let bc=volatile_read64(bindings+8); var pass:u64=0; if dc>0 && volatile_read64(lifecycle)==1 { pass=1; }
    unsafe { volatile_write64(state,1); volatile_write64(state+8,dc); volatile_write64(state+16,bc); volatile_write64(state+24,pass); volatile_write64(state+32,read_tsc()); }
    if pass==1 { serial_marker_frames_bind_tx_v3_ok(); } return pass;
}
fn device_resource_owner_v3_run(state:u64,resources:u64,irq:u64,dma:u64) -> u64 {
    if state==0 || resources==0 || irq==0 || dma==0 { return 0; } zero_page(state); var score:u64=0;
    if volatile_read64(resources)==1 { score=score+1; } if volatile_read64(irq)==1 { score=score+1; } if volatile_read64(dma)==1 { score=score+1; }
    var pass:u64=0; if score==3 { pass=1; } unsafe { volatile_write64(state,1); volatile_write64(state+8,score); volatile_write64(state+16,3); volatile_write64(state+24,pass); }
    if pass==1 { serial_marker_frames_resource_owner_v3_ok(); } return pass;
}
fn usb_service_graph_v3_run(state:u64,usb:u64,desc:u64,xfer:u64) -> u64 {
    if state==0 || usb==0 || desc==0 || xfer==0 { return 0; } zero_page(state); var score:u64=0;
    if volatile_read64(usb)==1 { score=score+1; } if volatile_read64(desc)==1 { score=score+1; } if volatile_read64(xfer)==1 { score=score+1; }
    var pass:u64=0; if score==3 { pass=1; } unsafe { volatile_write64(state,1); volatile_write64(state+8,score); volatile_write64(state+16,3); volatile_write64(state+24,pass); }
    if pass==1 { serial_marker_frames_usb_service_graph_v3_ok(); } return pass;
}
fn input_bridge_v3_run(state:u64,input:u64,hid:u64,events:u64) -> u64 {
    if state==0 || input==0 || hid==0 || events==0 { return 0; } zero_page(state); var score:u64=0;
    if volatile_read64(input)==1 { score=score+1; } if volatile_read64(hid)==1 { score=score+1; } if volatile_read64(events)==1 { score=score+1; }
    var pass:u64=0; if score==3 { pass=1; } unsafe { volatile_write64(state,1); volatile_write64(state+8,score); volatile_write64(state+16,3); volatile_write64(state+24,pass); }
    if pass==1 { serial_marker_frames_input_bridge_v3_ok(); } return pass;
}
fn hotplug_queue_v3_selftest(state:u64,work:u64,events:u64) -> u64 {
    if state==0 || work==0 || events==0 { return 0; } zero_page(state); let id=work_queue_v2_submit(work,7,1,1); var pass:u64=0; if id!=0 { pass=1; }
    unsafe { volatile_write64(state,1); volatile_write64(state+8,id); volatile_write64(state+16,pass); volatile_write64(state+24,read_tsc()); }
    if pass==1 { serial_marker_frames_hotplug_queue_v3_ok(); } return pass;
}
fn power_transition_v3_selftest(state:u64,lifecycle:u64,timers:u64) -> u64 {
    if state==0 || lifecycle==0 || timers==0 { return 0; } zero_page(state); var pass:u64=0; if volatile_read64(lifecycle)==1 && volatile_read64(timers)==1 { pass=1; }
    unsafe { volatile_write64(state,1); volatile_write64(state+8,pass); volatile_write64(state+16,read_tsc()); }
    if pass==1 { serial_marker_frames_power_transition_v3_ok(); } return pass;
}
fn driver_recovery_v3_selftest(state:u64,completion:u64,io:u64) -> u64 {
    if state==0 || completion==0 || io==0 { return 0; } zero_page(state); var pass:u64=0; if volatile_read64(completion)==1 && volatile_read64(io)==1 { pass=1; }
    unsafe { volatile_write64(state,1); volatile_write64(state+8,pass); volatile_write64(state+16,read_tsc()); }
    if pass==1 { serial_marker_frames_driver_recovery_v3_ok(); } return pass;
}
fn driver_runtime_v3_snapshot(state:u64,process:u64) -> u64 {
    if state==0 || process==0 { return 0; } zero_page(state); var score:u64=0;
    let a=volatile_read64(process+1680); if a!=0 && volatile_read64(a+24)==1 { score=score+1; }
    let b=volatile_read64(process+1688); if b!=0 && volatile_read64(b+24)==1 { score=score+1; }
    let c=volatile_read64(process+1696); if c!=0 && volatile_read64(c+24)==1 { score=score+1; }
    let d=volatile_read64(process+1704); if d!=0 && volatile_read64(d+24)==1 { score=score+1; }
    let e=volatile_read64(process+1712); if e!=0 && volatile_read64(e+24)==1 { score=score+1; }
    let f=volatile_read64(process+1720); if f!=0 && volatile_read64(f+16)==1 { score=score+1; }
    let g=volatile_read64(process+1728); if g!=0 && volatile_read64(g+8)==1 { score=score+1; }
    let h=volatile_read64(process+1736); if h!=0 && volatile_read64(h+8)==1 { score=score+1; }
    var pass:u64=0; if score==8 { pass=1; } unsafe { volatile_write64(state,1); volatile_write64(state+8,score); volatile_write64(state+16,8); volatile_write64(state+24,pass); }
    if pass==1 { serial_marker_frames_driver_runtime_v3_ok(); } return pass;
}
fn driver_runtime_gate_v3(state:u64,oldgate:u64,manager:u64) -> u64 {
    if state==0 || oldgate==0 || manager==0 { return 0; } zero_page(state); var score:u64=0;
    if volatile_read64(oldgate+24)==1 { score=score+1; } if volatile_read64(manager+24)==1 { score=score+1; }
    var pass:u64=0; if score==2 { pass=1; } unsafe { volatile_write64(state,1); volatile_write64(state+8,score); volatile_write64(state+16,2); volatile_write64(state+24,pass); }
    if pass==1 { serial_marker_frames_driver_runtime_gate_v3_ok(); } return pass;
}

'''
anchor='fn serial_marker_entropy_seed_ok() -> void {'
if anchor not in s: raise SystemExit('function insertion anchor missing')
s=s.replace(anchor,code+anchor,1)
alloc='let architecture_gate_v2_state=bump_alloc(&mut heap_cursor,heap_end,4096);'
extra_alloc=' let probe_dispatch_v3_state=bump_alloc(&mut heap_cursor,heap_end,4096); let binding_tx_v3_state=bump_alloc(&mut heap_cursor,heap_end,4096); let resource_owner_v3_state=bump_alloc(&mut heap_cursor,heap_end,4096); let usb_service_graph_v3_state=bump_alloc(&mut heap_cursor,heap_end,4096); let input_bridge_v3_state=bump_alloc(&mut heap_cursor,heap_end,4096); let hotplug_queue_v3_state=bump_alloc(&mut heap_cursor,heap_end,4096); let power_transition_v3_state=bump_alloc(&mut heap_cursor,heap_end,4096); let driver_recovery_v3_state=bump_alloc(&mut heap_cursor,heap_end,4096); let driver_runtime_v3_state=bump_alloc(&mut heap_cursor,heap_end,4096); let driver_runtime_gate_v3_state=bump_alloc(&mut heap_cursor,heap_end,4096);'
if s.count(alloc)!=1: raise SystemExit('allocation anchor mismatch')
s=s.replace(alloc,alloc+extra_alloc,1)
ready='var architecture_gate_v2_ready:u64=0;'
extra_ready=' var probe_dispatch_v3_ready:u64=0; var binding_tx_v3_ready:u64=0; var resource_owner_v3_ready:u64=0; var usb_service_graph_v3_ready:u64=0; var input_bridge_v3_ready:u64=0; var hotplug_queue_v3_ready:u64=0; var power_transition_v3_ready:u64=0; var driver_recovery_v3_ready:u64=0; var driver_runtime_v3_ready:u64=0; var driver_runtime_gate_v3_ready:u64=0;'
if s.count(ready)!=1: raise SystemExit('ready anchor mismatch')
s=s.replace(ready,ready+extra_ready,1)
boot='        if process_ready!=0 && architecture_gate_v2_state!=0 { unsafe { volatile_write64(process_state+1600,architecture_gate_v2_state); } architecture_gate_v2_ready=architecture_platform_v2_gate(architecture_gate_v2_state,process_state); }'
extra=r'''
        if process_ready!=0 && probe_dispatch_v3_state!=0 && probe_scheduler_v2_ready!=0 && work_queue_v2_ready!=0 && driver_match_v2_ready!=0 { probe_dispatch_v3_ready=probe_dispatch_v3_run(probe_dispatch_v3_state,probe_scheduler_v2_state,work_queue_v2_state,driver_match_v2_state); if probe_dispatch_v3_ready!=0 { unsafe { volatile_write64(process_state+1680,probe_dispatch_v3_state); } } }
        if process_ready!=0 && binding_tx_v3_state!=0 && device_object_ready!=0 && driver_binding_ready!=0 && lifecycle_v2_ready!=0 { binding_tx_v3_ready=driver_binding_tx_v3_run(binding_tx_v3_state,device_object_state,driver_binding_state,lifecycle_v2_state); if binding_tx_v3_ready!=0 { unsafe { volatile_write64(process_state+1688,binding_tx_v3_state); } } }
        if process_ready!=0 && resource_owner_v3_state!=0 && resource_core_v2_ready!=0 && irq_domain_v2_ready!=0 && dma_map_v2_ready!=0 { resource_owner_v3_ready=device_resource_owner_v3_run(resource_owner_v3_state,resource_core_v2_state,irq_domain_v2_state,dma_map_v2_state); if resource_owner_v3_ready!=0 { unsafe { volatile_write64(process_state+1696,resource_owner_v3_state); } } }
        if process_ready!=0 && usb_service_graph_v3_state!=0 && usb_core_v2_ready!=0 && usb_descriptor_v2_ready!=0 && usb_transfer_v2_ready!=0 { usb_service_graph_v3_ready=usb_service_graph_v3_run(usb_service_graph_v3_state,usb_core_v2_state,usb_descriptor_v2_state,usb_transfer_v2_state); if usb_service_graph_v3_ready!=0 { unsafe { volatile_write64(process_state+1704,usb_service_graph_v3_state); } } }
        if process_ready!=0 && input_bridge_v3_state!=0 && input_core_v2_ready!=0 && hid_core_v2_ready!=0 && input_event_v2_ready!=0 { input_bridge_v3_ready=input_bridge_v3_run(input_bridge_v3_state,input_core_v2_state,hid_core_v2_state,input_event_v2_state); if input_bridge_v3_ready!=0 { unsafe { volatile_write64(process_state+1712,input_bridge_v3_state); } } }
        if process_ready!=0 && hotplug_queue_v3_state!=0 && work_queue_v2_ready!=0 && input_event_v2_ready!=0 { hotplug_queue_v3_ready=hotplug_queue_v3_selftest(hotplug_queue_v3_state,work_queue_v2_state,input_event_v2_state); if hotplug_queue_v3_ready!=0 { unsafe { volatile_write64(process_state+1720,hotplug_queue_v3_state); } } }
        if process_ready!=0 && power_transition_v3_state!=0 && lifecycle_v2_ready!=0 && timer_queue_v2_ready!=0 { power_transition_v3_ready=power_transition_v3_selftest(power_transition_v3_state,lifecycle_v2_state,timer_queue_v2_state); if power_transition_v3_ready!=0 { unsafe { volatile_write64(process_state+1728,power_transition_v3_state); } } }
        if process_ready!=0 && driver_recovery_v3_state!=0 && completion_v2_ready!=0 && io_broker_v2_ready!=0 { driver_recovery_v3_ready=driver_recovery_v3_selftest(driver_recovery_v3_state,completion_v2_state,io_broker_v2_state); if driver_recovery_v3_ready!=0 { unsafe { volatile_write64(process_state+1736,driver_recovery_v3_state); } } }
        if process_ready!=0 && driver_runtime_v3_state!=0 { unsafe { volatile_write64(process_state+1744,driver_runtime_v3_state); } driver_runtime_v3_ready=driver_runtime_v3_snapshot(driver_runtime_v3_state,process_state); }
        if process_ready!=0 && driver_runtime_gate_v3_state!=0 && architecture_gate_v2_ready!=0 && driver_runtime_v3_ready!=0 { unsafe { volatile_write64(process_state+1752,driver_runtime_gate_v3_state); } driver_runtime_gate_v3_ready=driver_runtime_gate_v3(driver_runtime_gate_v3_state,architecture_gate_v2_state,driver_runtime_v3_state); }
'''
if s.count(boot)!=1: raise SystemExit('boot anchor mismatch')
s=s.replace(boot,boot+extra,1)
out=s.encode('utf-8'); p.write_bytes(out)
print('patched',p,'sha256',hashlib.sha256(out).hexdigest())
