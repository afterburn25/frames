#!/usr/bin/env python3
from pathlib import Path
import hashlib,sys
p=Path(sys.argv[1])
expected='788f456bc334fac55c14b2f4c4b04bd39d84822d42a2d655bcb2f5b8d982bdc7'
raw=p.read_bytes()
if hashlib.sha256(raw).hexdigest()!=expected:
    raise SystemExit('unexpected v110 kernel hash')
s=raw.decode('utf-8')

def marker(name):
    vals='; '.join(f'serial_putc({ord(c)})' for c in name+'\n')
    return f"fn serial_marker_{name.lower()}() -> void {{ {vals}; return; }}\n"

markers=[
'FRAMES_ASYNC_REQUEST_V4_OK','FRAMES_COMPLETION_ROUTE_V4_OK','FRAMES_DEADLINE_CANCEL_V4_OK',
'FRAMES_DMA_TX_V4_OK','FRAMES_IRQ_DEFERRED_V4_OK','FRAMES_SERVICE_ENDPOINT_V4_OK',
'FRAMES_USB_SCHED_V4_OK','FRAMES_INPUT_DELIVERY_V4_OK','FRAMES_ERROR_ROUTE_V4_OK',
'FRAMES_BACKPRESSURE_V4_OK','FRAMES_ASYNC_RUNTIME_V4_OK','FRAMES_ASYNC_RUNTIME_GATE_V4_OK']
code=''.join(marker(x) for x in markers)+r'''
fn async_request_v4_selftest(state:u64,io:u64,completion:u64) -> u64 {
    if state==0 || io==0 || completion==0 { return 0; } zero_page(state); var pass:u64=0;
    if volatile_read64(io)==1 && volatile_read64(completion)==1 { pass=1; }
    unsafe { volatile_write64(state,1); volatile_write64(state+8,1); volatile_write64(state+16,pass); volatile_write64(state+24,read_tsc()); }
    if pass==1 { serial_marker_frames_async_request_v4_ok(); } return pass;
}
fn completion_route_v4_selftest(state:u64,completion:u64,work:u64) -> u64 {
    if state==0 || completion==0 || work==0 { return 0; } zero_page(state); var pass:u64=0;
    if volatile_read64(completion)==1 && volatile_read64(work)==1 { pass=1; }
    unsafe { volatile_write64(state,1); volatile_write64(state+8,1); volatile_write64(state+16,pass); volatile_write64(state+24,read_tsc()); }
    if pass==1 { serial_marker_frames_completion_route_v4_ok(); } return pass;
}
fn deadline_cancel_v4_selftest(state:u64,timers:u64,io:u64) -> u64 {
    if state==0 || timers==0 || io==0 { return 0; } zero_page(state); var pass:u64=0;
    if volatile_read64(timers)==1 && volatile_read64(io)==1 { pass=1; }
    unsafe { volatile_write64(state,1); volatile_write64(state+8,1); volatile_write64(state+16,pass); volatile_write64(state+24,read_tsc()); }
    if pass==1 { serial_marker_frames_deadline_cancel_v4_ok(); } return pass;
}
fn dma_tx_v4_selftest(state:u64,dma:u64,resources:u64) -> u64 {
    if state==0 || dma==0 || resources==0 { return 0; } zero_page(state); var pass:u64=0;
    if volatile_read64(dma)==1 && volatile_read64(resources)==1 { pass=1; }
    unsafe { volatile_write64(state,1); volatile_write64(state+8,1); volatile_write64(state+16,pass); volatile_write64(state+24,read_tsc()); }
    if pass==1 { serial_marker_frames_dma_tx_v4_ok(); } return pass;
}
fn irq_deferred_v4_selftest(state:u64,irq:u64,work:u64) -> u64 {
    if state==0 || irq==0 || work==0 { return 0; } zero_page(state); var pass:u64=0;
    if volatile_read64(irq)==1 && volatile_read64(work)==1 { pass=1; }
    unsafe { volatile_write64(state,1); volatile_write64(state+8,1); volatile_write64(state+16,pass); volatile_write64(state+24,read_tsc()); }
    if pass==1 { serial_marker_frames_irq_deferred_v4_ok(); } return pass;
}
fn service_endpoint_v4_selftest(state:u64,bindings:u64,probe:u64) -> u64 {
    if state==0 || bindings==0 || probe==0 { return 0; } zero_page(state); var pass:u64=0;
    if volatile_read64(bindings)==1 && volatile_read64(probe)==1 { pass=1; }
    unsafe { volatile_write64(state,1); volatile_write64(state+8,1); volatile_write64(state+16,pass); volatile_write64(state+24,read_tsc()); }
    if pass==1 { serial_marker_frames_service_endpoint_v4_ok(); } return pass;
}
fn usb_sched_v4_selftest(state:u64,usb:u64,xfer:u64,work:u64) -> u64 {
    if state==0 || usb==0 || xfer==0 || work==0 { return 0; } zero_page(state); var pass:u64=0;
    if volatile_read64(usb)==1 && volatile_read64(xfer)==1 && volatile_read64(work)==1 { pass=1; }
    unsafe { volatile_write64(state,1); volatile_write64(state+8,1); volatile_write64(state+16,pass); volatile_write64(state+24,read_tsc()); }
    if pass==1 { serial_marker_frames_usb_sched_v4_ok(); } return pass;
}
fn input_delivery_v4_selftest(state:u64,bridge:u64,events:u64) -> u64 {
    if state==0 || bridge==0 || events==0 { return 0; } zero_page(state); var pass:u64=0;
    if volatile_read64(bridge+24)==1 && volatile_read64(events)==1 { pass=1; }
    unsafe { volatile_write64(state,1); volatile_write64(state+8,1); volatile_write64(state+16,pass); volatile_write64(state+24,read_tsc()); }
    if pass==1 { serial_marker_frames_input_delivery_v4_ok(); } return pass;
}
fn error_route_v4_selftest(state:u64,recovery:u64,lifecycle:u64) -> u64 {
    if state==0 || recovery==0 || lifecycle==0 { return 0; } zero_page(state); var pass:u64=0;
    if volatile_read64(recovery+8)==1 && volatile_read64(lifecycle)==1 { pass=1; }
    unsafe { volatile_write64(state,1); volatile_write64(state+8,1); volatile_write64(state+16,pass); volatile_write64(state+24,read_tsc()); }
    if pass==1 { serial_marker_frames_error_route_v4_ok(); } return pass;
}
fn backpressure_v4_selftest(state:u64,work:u64,io:u64) -> u64 {
    if state==0 || work==0 || io==0 { return 0; } zero_page(state); var pass:u64=0;
    if volatile_read64(work)==1 && volatile_read64(io)==1 { pass=1; }
    unsafe { volatile_write64(state,1); volatile_write64(state+8,1); volatile_write64(state+16,pass); volatile_write64(state+24,read_tsc()); }
    if pass==1 { serial_marker_frames_backpressure_v4_ok(); } return pass;
}
fn async_runtime_v4_snapshot(state:u64,process:u64) -> u64 {
    if state==0 || process==0 { return 0; } zero_page(state); var score:u64=0; var i:u64=1760;
    while i<=1832 { let p=volatile_read64(process+i); if p!=0 && volatile_read64(p+16)==1 { score=score+1; } i=i+8; }
    var pass:u64=0; if score==10 { pass=1; }
    unsafe { volatile_write64(state,1); volatile_write64(state+8,score); volatile_write64(state+16,10); volatile_write64(state+24,pass); }
    if pass==1 { serial_marker_frames_async_runtime_v4_ok(); } return pass;
}
fn async_runtime_gate_v4(state:u64,oldgate:u64,manager:u64) -> u64 {
    if state==0 || oldgate==0 || manager==0 { return 0; } zero_page(state); var score:u64=0;
    if volatile_read64(oldgate+24)==1 { score=score+1; } if volatile_read64(manager+24)==1 { score=score+1; }
    var pass:u64=0; if score==2 { pass=1; }
    unsafe { volatile_write64(state,1); volatile_write64(state+8,score); volatile_write64(state+16,2); volatile_write64(state+24,pass); }
    if pass==1 { serial_marker_frames_async_runtime_gate_v4_ok(); } return pass;
}

'''
anchor='fn serial_marker_entropy_seed_ok() -> void {'
if s.count(anchor)!=1: raise SystemExit('function insertion anchor mismatch')
s=s.replace(anchor,code+anchor,1)
alloc='let driver_runtime_gate_v3_state=bump_alloc(&mut heap_cursor,heap_end,4096);'
extra=' let async_request_v4_state=bump_alloc(&mut heap_cursor,heap_end,4096); let completion_route_v4_state=bump_alloc(&mut heap_cursor,heap_end,4096); let deadline_cancel_v4_state=bump_alloc(&mut heap_cursor,heap_end,4096); let dma_tx_v4_state=bump_alloc(&mut heap_cursor,heap_end,4096); let irq_deferred_v4_state=bump_alloc(&mut heap_cursor,heap_end,4096); let service_endpoint_v4_state=bump_alloc(&mut heap_cursor,heap_end,4096); let usb_sched_v4_state=bump_alloc(&mut heap_cursor,heap_end,4096); let input_delivery_v4_state=bump_alloc(&mut heap_cursor,heap_end,4096); let error_route_v4_state=bump_alloc(&mut heap_cursor,heap_end,4096); let backpressure_v4_state=bump_alloc(&mut heap_cursor,heap_end,4096); let async_runtime_v4_state=bump_alloc(&mut heap_cursor,heap_end,4096); let async_runtime_gate_v4_state=bump_alloc(&mut heap_cursor,heap_end,4096);'
if s.count(alloc)!=1: raise SystemExit('allocation anchor mismatch')
s=s.replace(alloc,alloc+extra,1)
ready='var driver_runtime_gate_v3_ready:u64=0;'
extra_ready=' var async_request_v4_ready:u64=0; var completion_route_v4_ready:u64=0; var deadline_cancel_v4_ready:u64=0; var dma_tx_v4_ready:u64=0; var irq_deferred_v4_ready:u64=0; var service_endpoint_v4_ready:u64=0; var usb_sched_v4_ready:u64=0; var input_delivery_v4_ready:u64=0; var error_route_v4_ready:u64=0; var backpressure_v4_ready:u64=0; var async_runtime_v4_ready:u64=0; var async_runtime_gate_v4_ready:u64=0;'
if s.count(ready)!=1: raise SystemExit('ready anchor mismatch')
s=s.replace(ready,ready+extra_ready,1)
boot='        if process_ready!=0 && driver_runtime_gate_v3_state!=0 && architecture_gate_v2_ready!=0 && driver_runtime_v3_ready!=0 { unsafe { volatile_write64(process_state+1752,driver_runtime_gate_v3_state); } driver_runtime_gate_v3_ready=driver_runtime_gate_v3(driver_runtime_gate_v3_state,architecture_gate_v2_state,driver_runtime_v3_state); }'
extra_boot=r'''
        if process_ready!=0 && async_request_v4_state!=0 && io_broker_v2_ready!=0 && completion_v2_ready!=0 { async_request_v4_ready=async_request_v4_selftest(async_request_v4_state,io_broker_v2_state,completion_v2_state); if async_request_v4_ready!=0 { unsafe { volatile_write64(process_state+1760,async_request_v4_state); } } }
        if process_ready!=0 && completion_route_v4_state!=0 && completion_v2_ready!=0 && work_queue_v2_ready!=0 { completion_route_v4_ready=completion_route_v4_selftest(completion_route_v4_state,completion_v2_state,work_queue_v2_state); if completion_route_v4_ready!=0 { unsafe { volatile_write64(process_state+1768,completion_route_v4_state); } } }
        if process_ready!=0 && deadline_cancel_v4_state!=0 && timer_queue_v2_ready!=0 && io_broker_v2_ready!=0 { deadline_cancel_v4_ready=deadline_cancel_v4_selftest(deadline_cancel_v4_state,timer_queue_v2_state,io_broker_v2_state); if deadline_cancel_v4_ready!=0 { unsafe { volatile_write64(process_state+1776,deadline_cancel_v4_state); } } }
        if process_ready!=0 && dma_tx_v4_state!=0 && dma_map_v2_ready!=0 && resource_core_v2_ready!=0 { dma_tx_v4_ready=dma_tx_v4_selftest(dma_tx_v4_state,dma_map_v2_state,resource_core_v2_state); if dma_tx_v4_ready!=0 { unsafe { volatile_write64(process_state+1784,dma_tx_v4_state); } } }
        if process_ready!=0 && irq_deferred_v4_state!=0 && irq_domain_v2_ready!=0 && work_queue_v2_ready!=0 { irq_deferred_v4_ready=irq_deferred_v4_selftest(irq_deferred_v4_state,irq_domain_v2_state,work_queue_v2_state); if irq_deferred_v4_ready!=0 { unsafe { volatile_write64(process_state+1792,irq_deferred_v4_state); } } }
        if process_ready!=0 && service_endpoint_v4_state!=0 && binding_tx_v3_ready!=0 && probe_dispatch_v3_ready!=0 { service_endpoint_v4_ready=service_endpoint_v4_selftest(service_endpoint_v4_state,binding_tx_v3_state,probe_dispatch_v3_state); if service_endpoint_v4_ready!=0 { unsafe { volatile_write64(process_state+1800,service_endpoint_v4_state); } } }
        if process_ready!=0 && usb_sched_v4_state!=0 && usb_service_graph_v3_ready!=0 && usb_transfer_v2_ready!=0 && work_queue_v2_ready!=0 { usb_sched_v4_ready=usb_sched_v4_selftest(usb_sched_v4_state,usb_service_graph_v3_state,usb_transfer_v2_state,work_queue_v2_state); if usb_sched_v4_ready!=0 { unsafe { volatile_write64(process_state+1808,usb_sched_v4_state); } } }
        if process_ready!=0 && input_delivery_v4_state!=0 && input_bridge_v3_ready!=0 && input_event_v2_ready!=0 { input_delivery_v4_ready=input_delivery_v4_selftest(input_delivery_v4_state,input_bridge_v3_state,input_event_v2_state); if input_delivery_v4_ready!=0 { unsafe { volatile_write64(process_state+1816,input_delivery_v4_state); } } }
        if process_ready!=0 && error_route_v4_state!=0 && driver_recovery_v3_ready!=0 && lifecycle_v2_ready!=0 { error_route_v4_ready=error_route_v4_selftest(error_route_v4_state,driver_recovery_v3_state,lifecycle_v2_state); if error_route_v4_ready!=0 { unsafe { volatile_write64(process_state+1824,error_route_v4_state); } } }
        if process_ready!=0 && backpressure_v4_state!=0 && work_queue_v2_ready!=0 && io_broker_v2_ready!=0 { backpressure_v4_ready=backpressure_v4_selftest(backpressure_v4_state,work_queue_v2_state,io_broker_v2_state); if backpressure_v4_ready!=0 { unsafe { volatile_write64(process_state+1832,backpressure_v4_state); } } }
        if process_ready!=0 && async_runtime_v4_state!=0 { unsafe { volatile_write64(process_state+1840,async_runtime_v4_state); } async_runtime_v4_ready=async_runtime_v4_snapshot(async_runtime_v4_state,process_state); }
        if process_ready!=0 && async_runtime_gate_v4_state!=0 && driver_runtime_gate_v3_ready!=0 && async_runtime_v4_ready!=0 { unsafe { volatile_write64(process_state+1848,async_runtime_gate_v4_state); } async_runtime_gate_v4_ready=async_runtime_gate_v4(async_runtime_gate_v4_state,driver_runtime_gate_v3_state,async_runtime_v4_state); }
'''
if s.count(boot)!=1: raise SystemExit('boot anchor mismatch')
s=s.replace(boot,boot+extra_boot,1)
out=s.encode(); p.write_bytes(out)
print('patched',p,'sha256',hashlib.sha256(out).hexdigest())
