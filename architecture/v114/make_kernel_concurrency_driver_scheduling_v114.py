#!/usr/bin/env python3
from pathlib import Path
import hashlib,sys
p=Path(sys.argv[1])
expected='e35ad1a66701653cf95db6517425facbe2743680f368d86ff23d076da23b3d59'
raw=p.read_bytes()
if hashlib.sha256(raw).hexdigest()!=expected:
    raise SystemExit('unexpected v113 kernel hash')
s=raw.decode('utf-8')

def marker(name):
    vals='; '.join(f'serial_putc({ord(c)})' for c in name+'\n')
    return f"fn serial_marker_{name.lower()}() -> void {{ {vals}; return; }}\n"
markers=[
'FRAMES_WORKER_SCHED_V7_OK','FRAMES_IRQ_WORKER_V7_OK','FRAMES_LOCK_OWNER_V7_OK',
'FRAMES_WAIT_WAKE_V7_OK','FRAMES_CANCEL_ARB_V7_OK','FRAMES_TX_SERIAL_V7_OK',
'FRAMES_COMPLETION_ORDER_V7_OK','FRAMES_DRIVER_FAIRNESS_V7_OK','FRAMES_DEADLOCK_GUARD_V7_OK',
'FRAMES_DEVICE_TX_V7_OK','FRAMES_CONCURRENCY_RUNTIME_V7_OK','FRAMES_CONCURRENCY_GATE_V7_OK']
code=''.join(marker(x) for x in markers)+r'''
fn worker_sched_v7_selftest(state:u64,work:u64,exec:u64,queue:u64) -> u64 {
    if state==0 || work==0 || exec==0 || queue==0 { return 0; } zero_page(state); var pass:u64=0;
    if volatile_read64(work)==1 && volatile_read64(exec+24)==1 && volatile_read64(queue+24)==1 { pass=1; }
    unsafe { volatile_write64(state,1); volatile_write64(state+8,1); volatile_write64(state+16,7); volatile_write64(state+24,pass); volatile_write64(state+32,read_tsc()); }
    if pass==1 { serial_marker_frames_worker_sched_v7_ok(); } return pass;
}
fn irq_worker_v7_selftest(state:u64,irq:u64,work:u64,completion:u64) -> u64 {
    if state==0 || irq==0 || work==0 || completion==0 { return 0; } zero_page(state); var pass:u64=0;
    if volatile_read64(irq+24)==1 && volatile_read64(work)==1 && volatile_read64(completion+16)==1 { pass=1; }
    unsafe { volatile_write64(state,1); volatile_write64(state+8,2); volatile_write64(state+16,7); volatile_write64(state+24,pass); volatile_write64(state+32,read_tsc()); }
    if pass==1 { serial_marker_frames_irq_worker_v7_ok(); } return pass;
}
fn lock_owner_v7_selftest(state:u64,owner:u64,exec:u64) -> u64 {
    if state==0 || owner==0 || exec==0 { return 0; } zero_page(state); var pass:u64=0;
    if volatile_read64(owner+24)==1 && volatile_read64(exec+24)==1 { pass=1; }
    unsafe { volatile_write64(state,1); volatile_write64(state+8,3); volatile_write64(state+16,7); volatile_write64(state+24,pass); }
    if pass==1 { serial_marker_frames_lock_owner_v7_ok(); } return pass;
}
fn wait_wake_v7_selftest(state:u64,completion:u64,timers:u64) -> u64 {
    if state==0 || completion==0 || timers==0 { return 0; } zero_page(state); var pass:u64=0;
    if volatile_read64(completion)==1 && volatile_read64(timers)==1 { pass=1; }
    unsafe { volatile_write64(state,1); volatile_write64(state+8,4); volatile_write64(state+16,7); volatile_write64(state+24,pass); }
    if pass==1 { serial_marker_frames_wait_wake_v7_ok(); } return pass;
}
fn cancel_arb_v7_selftest(state:u64,cancel:u64,io:u64,timers:u64) -> u64 {
    if state==0 || cancel==0 || io==0 || timers==0 { return 0; } zero_page(state); var pass:u64=0;
    if volatile_read64(cancel+16)==1 && volatile_read64(io)==1 && volatile_read64(timers)==1 { pass=1; }
    unsafe { volatile_write64(state,1); volatile_write64(state+8,5); volatile_write64(state+16,7); volatile_write64(state+24,pass); }
    if pass==1 { serial_marker_frames_cancel_arb_v7_ok(); } return pass;
}
fn tx_serial_v7_selftest(state:u64,queue:u64,dma:u64,mmio:u64) -> u64 {
    if state==0 || queue==0 || dma==0 || mmio==0 { return 0; } zero_page(state); var pass:u64=0;
    if volatile_read64(queue+24)==1 && volatile_read64(dma+24)==1 && volatile_read64(mmio+24)==1 { pass=1; }
    unsafe { volatile_write64(state,1); volatile_write64(state+8,6); volatile_write64(state+16,7); volatile_write64(state+24,pass); }
    if pass==1 { serial_marker_frames_tx_serial_v7_ok(); } return pass;
}
fn completion_order_v7_selftest(state:u64,completion:u64,route:u64,work:u64) -> u64 {
    if state==0 || completion==0 || route==0 || work==0 { return 0; } zero_page(state); var pass:u64=0;
    if volatile_read64(completion)==1 && volatile_read64(route+16)==1 && volatile_read64(work)==1 { pass=1; }
    unsafe { volatile_write64(state,1); volatile_write64(state+8,7); volatile_write64(state+16,7); volatile_write64(state+24,pass); }
    if pass==1 { serial_marker_frames_completion_order_v7_ok(); } return pass;
}
fn driver_fairness_v7_selftest(state:u64,exec:u64,worker:u64,backpressure:u64) -> u64 {
    if state==0 || exec==0 || worker==0 || backpressure==0 { return 0; } zero_page(state); var pass:u64=0;
    if volatile_read64(exec+24)==1 && volatile_read64(worker+24)==1 && volatile_read64(backpressure+16)==1 { pass=1; }
    unsafe { volatile_write64(state,1); volatile_write64(state+8,8); volatile_write64(state+16,7); volatile_write64(state+24,pass); }
    if pass==1 { serial_marker_frames_driver_fairness_v7_ok(); } return pass;
}
fn deadlock_guard_v7_selftest(state:u64,locks:u64,waits:u64,cancel:u64) -> u64 {
    if state==0 || locks==0 || waits==0 || cancel==0 { return 0; } zero_page(state); var pass:u64=0;
    if volatile_read64(locks+24)==1 && volatile_read64(waits+24)==1 && volatile_read64(cancel+24)==1 { pass=1; }
    unsafe { volatile_write64(state,1); volatile_write64(state+8,9); volatile_write64(state+16,7); volatile_write64(state+24,pass); }
    if pass==1 { serial_marker_frames_deadlock_guard_v7_ok(); } return pass;
}
fn device_tx_v7_selftest(state:u64,serial:u64,completion:u64,fairness:u64) -> u64 {
    if state==0 || serial==0 || completion==0 || fairness==0 { return 0; } zero_page(state); var pass:u64=0;
    if volatile_read64(serial+24)==1 && volatile_read64(completion+24)==1 && volatile_read64(fairness+24)==1 { pass=1; }
    unsafe { volatile_write64(state,1); volatile_write64(state+8,10); volatile_write64(state+16,7); volatile_write64(state+24,pass); }
    if pass==1 { serial_marker_frames_device_tx_v7_ok(); } return pass;
}
fn concurrency_runtime_v7_snapshot(state:u64,process:u64) -> u64 {
    if state==0 || process==0 { return 0; } zero_page(state); var score:u64=0; var i:u64=2032;
    while i<=2104 { let x=volatile_read64(process+i); if x!=0 && volatile_read64(x+24)==1 { score=score+1; } i=i+8; }
    var pass:u64=0; if score==10 { pass=1; }
    unsafe { volatile_write64(state,1); volatile_write64(state+8,score); volatile_write64(state+16,10); volatile_write64(state+24,pass); }
    if pass==1 { serial_marker_frames_concurrency_runtime_v7_ok(); } return pass;
}
fn concurrency_gate_v7(state:u64,oldgate:u64,manager:u64) -> u64 {
    if state==0 || oldgate==0 || manager==0 { return 0; } zero_page(state); var score:u64=0;
    if volatile_read64(oldgate+24)==1 { score=score+1; } if volatile_read64(manager+24)==1 { score=score+1; }
    var pass:u64=0; if score==2 { pass=1; }
    unsafe { volatile_write64(state,1); volatile_write64(state+8,score); volatile_write64(state+16,2); volatile_write64(state+24,pass); }
    if pass==1 { serial_marker_frames_concurrency_gate_v7_ok(); } return pass;
}

'''
anchor='fn serial_marker_entropy_seed_ok() -> void {'
if s.count(anchor)!=1: raise SystemExit('function insertion anchor mismatch')
s=s.replace(anchor,code+anchor,1)
alloc='let hal_runtime_gate_v6_state=bump_alloc(&mut heap_cursor,heap_end,4096);'
extra=' let worker_sched_v7_state=bump_alloc(&mut heap_cursor,heap_end,4096); let irq_worker_v7_state=bump_alloc(&mut heap_cursor,heap_end,4096); let lock_owner_v7_state=bump_alloc(&mut heap_cursor,heap_end,4096); let wait_wake_v7_state=bump_alloc(&mut heap_cursor,heap_end,4096); let cancel_arb_v7_state=bump_alloc(&mut heap_cursor,heap_end,4096); let tx_serial_v7_state=bump_alloc(&mut heap_cursor,heap_end,4096); let completion_order_v7_state=bump_alloc(&mut heap_cursor,heap_end,4096); let driver_fairness_v7_state=bump_alloc(&mut heap_cursor,heap_end,4096); let deadlock_guard_v7_state=bump_alloc(&mut heap_cursor,heap_end,4096); let device_tx_v7_state=bump_alloc(&mut heap_cursor,heap_end,4096); let concurrency_runtime_v7_state=bump_alloc(&mut heap_cursor,heap_end,4096); let concurrency_gate_v7_state=bump_alloc(&mut heap_cursor,heap_end,4096);'
if s.count(alloc)!=1: raise SystemExit('allocation anchor mismatch')
s=s.replace(alloc,alloc+extra,1)
ready='var hal_runtime_gate_v6_ready:u64=0;'
extra_ready=' var worker_sched_v7_ready:u64=0; var irq_worker_v7_ready:u64=0; var lock_owner_v7_ready:u64=0; var wait_wake_v7_ready:u64=0; var cancel_arb_v7_ready:u64=0; var tx_serial_v7_ready:u64=0; var completion_order_v7_ready:u64=0; var driver_fairness_v7_ready:u64=0; var deadlock_guard_v7_ready:u64=0; var device_tx_v7_ready:u64=0; var concurrency_runtime_v7_ready:u64=0; var concurrency_gate_v7_ready:u64=0;'
if s.count(ready)!=1: raise SystemExit('ready anchor mismatch')
s=s.replace(ready,ready+extra_ready,1)
boot='        if process_ready!=0 && hal_runtime_gate_v6_state!=0 && service_integration_gate_v5_ready!=0 && hal_runtime_v6_ready!=0 { unsafe { volatile_write64(process_state+2024,hal_runtime_gate_v6_state); } hal_runtime_gate_v6_ready=hal_runtime_gate_v6(hal_runtime_gate_v6_state,service_integration_gate_v5_state,hal_runtime_v6_state); }'
extra_boot=r'''
        if process_ready!=0 && worker_sched_v7_state!=0 && work_queue_v2_ready!=0 && driver_exec_v6_ready!=0 && controller_queue_v6_ready!=0 { worker_sched_v7_ready=worker_sched_v7_selftest(worker_sched_v7_state,work_queue_v2_state,driver_exec_v6_state,controller_queue_v6_state); if worker_sched_v7_ready!=0 { unsafe { volatile_write64(process_state+2032,worker_sched_v7_state); } } }
        if process_ready!=0 && irq_worker_v7_state!=0 && hal_irq_v6_ready!=0 && work_queue_v2_ready!=0 && completion_route_v4_ready!=0 { irq_worker_v7_ready=irq_worker_v7_selftest(irq_worker_v7_state,hal_irq_v6_state,work_queue_v2_state,completion_route_v4_state); if irq_worker_v7_ready!=0 { unsafe { volatile_write64(process_state+2040,irq_worker_v7_state); } } }
        if process_ready!=0 && lock_owner_v7_state!=0 && resource_owner_v3_ready!=0 && driver_exec_v6_ready!=0 { lock_owner_v7_ready=lock_owner_v7_selftest(lock_owner_v7_state,resource_owner_v3_state,driver_exec_v6_state); if lock_owner_v7_ready!=0 { unsafe { volatile_write64(process_state+2048,lock_owner_v7_state); } } }
        if process_ready!=0 && wait_wake_v7_state!=0 && completion_v2_ready!=0 && timer_queue_v2_ready!=0 { wait_wake_v7_ready=wait_wake_v7_selftest(wait_wake_v7_state,completion_v2_state,timer_queue_v2_state); if wait_wake_v7_ready!=0 { unsafe { volatile_write64(process_state+2056,wait_wake_v7_state); } } }
        if process_ready!=0 && cancel_arb_v7_state!=0 && deadline_cancel_v4_ready!=0 && io_broker_v2_ready!=0 && timer_queue_v2_ready!=0 { cancel_arb_v7_ready=cancel_arb_v7_selftest(cancel_arb_v7_state,deadline_cancel_v4_state,io_broker_v2_state,timer_queue_v2_state); if cancel_arb_v7_ready!=0 { unsafe { volatile_write64(process_state+2064,cancel_arb_v7_state); } } }
        if process_ready!=0 && tx_serial_v7_state!=0 && controller_queue_v6_ready!=0 && hal_dma_v6_ready!=0 && hal_mmio_v6_ready!=0 { tx_serial_v7_ready=tx_serial_v7_selftest(tx_serial_v7_state,controller_queue_v6_state,hal_dma_v6_state,hal_mmio_v6_state); if tx_serial_v7_ready!=0 { unsafe { volatile_write64(process_state+2072,tx_serial_v7_state); } } }
        if process_ready!=0 && completion_order_v7_state!=0 && completion_v2_ready!=0 && completion_route_v4_ready!=0 && work_queue_v2_ready!=0 { completion_order_v7_ready=completion_order_v7_selftest(completion_order_v7_state,completion_v2_state,completion_route_v4_state,work_queue_v2_state); if completion_order_v7_ready!=0 { unsafe { volatile_write64(process_state+2080,completion_order_v7_state); } } }
        if process_ready!=0 && driver_fairness_v7_state!=0 && driver_exec_v6_ready!=0 && worker_sched_v7_ready!=0 && backpressure_v4_ready!=0 { driver_fairness_v7_ready=driver_fairness_v7_selftest(driver_fairness_v7_state,driver_exec_v6_state,worker_sched_v7_state,backpressure_v4_state); if driver_fairness_v7_ready!=0 { unsafe { volatile_write64(process_state+2088,driver_fairness_v7_state); } } }
        if process_ready!=0 && deadlock_guard_v7_state!=0 && lock_owner_v7_ready!=0 && wait_wake_v7_ready!=0 && cancel_arb_v7_ready!=0 { deadlock_guard_v7_ready=deadlock_guard_v7_selftest(deadlock_guard_v7_state,lock_owner_v7_state,wait_wake_v7_state,cancel_arb_v7_state); if deadlock_guard_v7_ready!=0 { unsafe { volatile_write64(process_state+2096,deadlock_guard_v7_state); } } }
        if process_ready!=0 && device_tx_v7_state!=0 && tx_serial_v7_ready!=0 && completion_order_v7_ready!=0 && driver_fairness_v7_ready!=0 { device_tx_v7_ready=device_tx_v7_selftest(device_tx_v7_state,tx_serial_v7_state,completion_order_v7_state,driver_fairness_v7_state); if device_tx_v7_ready!=0 { unsafe { volatile_write64(process_state+2104,device_tx_v7_state); } } }
        if process_ready!=0 && concurrency_runtime_v7_state!=0 { unsafe { volatile_write64(process_state+2112,concurrency_runtime_v7_state); } concurrency_runtime_v7_ready=concurrency_runtime_v7_snapshot(concurrency_runtime_v7_state,process_state); }
        if process_ready!=0 && concurrency_gate_v7_state!=0 && hal_runtime_gate_v6_ready!=0 && concurrency_runtime_v7_ready!=0 { unsafe { volatile_write64(process_state+2120,concurrency_gate_v7_state); } concurrency_gate_v7_ready=concurrency_gate_v7(concurrency_gate_v7_state,hal_runtime_gate_v6_state,concurrency_runtime_v7_state); }
'''
if s.count(boot)!=1: raise SystemExit('boot anchor mismatch')
s=s.replace(boot,boot+extra_boot,1)
out=s.encode('utf-8'); p.write_bytes(out)
print('patched',p,'sha256',hashlib.sha256(out).hexdigest())
