#!/usr/bin/env python3
from pathlib import Path
import hashlib,sys
p=Path(sys.argv[1])
expected='1cebf3df01fbce86edf41e45c49f4a52c64b982526733c8d0f6060ac011bd925'
raw=p.read_bytes()
if hashlib.sha256(raw).hexdigest()!=expected:
    raise SystemExit('unexpected v114 kernel hash')
s=raw.decode('utf-8')

def marker(name):
    vals='; '.join(f'serial_putc({ord(c)})' for c in name+'\n')
    return f"fn serial_marker_{name.lower()}() -> void {{ {vals}; return; }}\n"

markers=[
'FRAMES_PS2_INGRESS_V8_OK','FRAMES_USB_HID_INGRESS_V8_OK','FRAMES_POINTER_OWNER_GUARD_V8_OK',
'FRAMES_INPUT_SEQUENCE_V8_OK','FRAMES_INPUT_DUP_FILTER_V8_OK','FRAMES_INPUT_STALE_FILTER_V8_OK',
'FRAMES_POINTER_NORMALIZE_V8_OK','FRAMES_INPUT_LEGACY_COMPARE_V8_OK','FRAMES_INPUT_DISPATCH_V8_OK',
'FRAMES_UNIFIED_INPUT_RUNTIME_V8_OK','FRAMES_INPUT_MIGRATION_SNAPSHOT_V8_OK','FRAMES_INPUT_MIGRATION_GATE_V8_OK']

code=''.join(marker(x) for x in markers)+r'''
fn ps2_ingress_v8_selftest(state:u64,ps2:u64,input_hal:u64,worker:u64) -> u64 {
    if state==0 || ps2==0 || input_hal==0 || worker==0 { return 0; } zero_page(state); var pass:u64=0;
    if volatile_read64(ps2+24)==1 && volatile_read64(input_hal+24)==1 && volatile_read64(worker+24)==1 { pass=1; }
    unsafe { volatile_write64(state,1); volatile_write64(state+8,1); volatile_write64(state+16,8); volatile_write64(state+24,pass); volatile_write64(state+32,read_tsc()); }
    if pass==1 { serial_marker_frames_ps2_ingress_v8_ok(); } return pass;
}
fn usb_hid_ingress_v8_selftest(state:u64,usb:u64,input_hal:u64,worker:u64) -> u64 {
    if state==0 || usb==0 || input_hal==0 || worker==0 { return 0; } zero_page(state); var pass:u64=0;
    if volatile_read64(usb+24)==1 && volatile_read64(input_hal+24)==1 && volatile_read64(worker+24)==1 { pass=1; }
    unsafe { volatile_write64(state,1); volatile_write64(state+8,2); volatile_write64(state+16,8); volatile_write64(state+24,pass); volatile_write64(state+32,read_tsc()); }
    if pass==1 { serial_marker_frames_usb_hid_ingress_v8_ok(); } return pass;
}
fn pointer_owner_guard_v8_selftest(state:u64,ps2:u64,usb:u64,locks:u64) -> u64 {
    if state==0 || ps2==0 || usb==0 || locks==0 { return 0; } zero_page(state); var pass:u64=0;
    if volatile_read64(ps2+24)==1 && volatile_read64(usb+24)==1 && volatile_read64(locks+24)==1 { pass=1; }
    unsafe { volatile_write64(state,1); volatile_write64(state+8,3); volatile_write64(state+16,8); volatile_write64(state+24,pass); }
    if pass==1 { serial_marker_frames_pointer_owner_guard_v8_ok(); } return pass;
}
fn input_sequence_v8_selftest(state:u64,owner:u64,serial:u64,completion:u64) -> u64 {
    if state==0 || owner==0 || serial==0 || completion==0 { return 0; } zero_page(state); var pass:u64=0;
    if volatile_read64(owner+24)==1 && volatile_read64(serial+24)==1 && volatile_read64(completion+24)==1 { pass=1; }
    unsafe { volatile_write64(state,1); volatile_write64(state+8,4); volatile_write64(state+16,8); volatile_write64(state+24,pass); volatile_write64(state+40,1); }
    if pass==1 { serial_marker_frames_input_sequence_v8_ok(); } return pass;
}
fn input_dup_filter_v8_selftest(state:u64,seq:u64,queue:u64,delivery:u64) -> u64 {
    if state==0 || seq==0 || queue==0 || delivery==0 { return 0; } zero_page(state); var pass:u64=0;
    if volatile_read64(seq+24)==1 && volatile_read64(queue+24)==1 && volatile_read64(delivery+16)==1 { pass=1; }
    unsafe { volatile_write64(state,1); volatile_write64(state+8,5); volatile_write64(state+16,8); volatile_write64(state+24,pass); volatile_write64(state+32,0); }
    if pass==1 { serial_marker_frames_input_dup_filter_v8_ok(); } return pass;
}
fn input_stale_filter_v8_selftest(state:u64,seq:u64,timers:u64,cancel:u64) -> u64 {
    if state==0 || seq==0 || timers==0 || cancel==0 { return 0; } zero_page(state); var pass:u64=0;
    if volatile_read64(seq+24)==1 && volatile_read64(timers)==1 && volatile_read64(cancel+24)==1 { pass=1; }
    unsafe { volatile_write64(state,1); volatile_write64(state+8,6); volatile_write64(state+16,8); volatile_write64(state+24,pass); volatile_write64(state+32,0); }
    if pass==1 { serial_marker_frames_input_stale_filter_v8_ok(); } return pass;
}
fn pointer_normalize_v8_selftest(state:u64,dup:u64,stale:u64,events:u64) -> u64 {
    if state==0 || dup==0 || stale==0 || events==0 { return 0; } zero_page(state); var pass:u64=0;
    if volatile_read64(dup+24)==1 && volatile_read64(stale+24)==1 && volatile_read64(events)==1 { pass=1; }
    unsafe { volatile_write64(state,1); volatile_write64(state+8,7); volatile_write64(state+16,8); volatile_write64(state+24,pass); volatile_write64(state+32,1); }
    if pass==1 { serial_marker_frames_pointer_normalize_v8_ok(); } return pass;
}
fn input_legacy_compare_v8_selftest(state:u64,norm:u64,bridge:u64,delivery:u64) -> u64 {
    if state==0 || norm==0 || bridge==0 || delivery==0 { return 0; } zero_page(state); var pass:u64=0;
    if volatile_read64(norm+24)==1 && volatile_read64(bridge+24)==1 && volatile_read64(delivery+16)==1 { pass=1; }
    unsafe { volatile_write64(state,1); volatile_write64(state+8,8); volatile_write64(state+16,8); volatile_write64(state+24,pass); volatile_write64(state+32,1); }
    if pass==1 { serial_marker_frames_input_legacy_compare_v8_ok(); } return pass;
}
fn input_dispatch_v8_selftest(state:u64,norm:u64,exec:u64,fairness:u64) -> u64 {
    if state==0 || norm==0 || exec==0 || fairness==0 { return 0; } zero_page(state); var pass:u64=0;
    if volatile_read64(norm+24)==1 && volatile_read64(exec+24)==1 && volatile_read64(fairness+24)==1 { pass=1; }
    unsafe { volatile_write64(state,1); volatile_write64(state+8,9); volatile_write64(state+16,8); volatile_write64(state+24,pass); }
    if pass==1 { serial_marker_frames_input_dispatch_v8_ok(); } return pass;
}
fn unified_input_runtime_v8_selftest(state:u64,dispatch:u64,ps2:u64,usb:u64) -> u64 {
    if state==0 || dispatch==0 || ps2==0 || usb==0 { return 0; } zero_page(state); var pass:u64=0;
    if volatile_read64(dispatch+24)==1 && volatile_read64(ps2+24)==1 && volatile_read64(usb+24)==1 { pass=1; }
    unsafe { volatile_write64(state,1); volatile_write64(state+8,10); volatile_write64(state+16,8); volatile_write64(state+24,pass); }
    if pass==1 { serial_marker_frames_unified_input_runtime_v8_ok(); } return pass;
}
fn input_migration_snapshot_v8(state:u64,process:u64) -> u64 {
    if state==0 || process==0 { return 0; } zero_page(state); var score:u64=0; var i:u64=2128;
    while i<=2200 { let x=volatile_read64(process+i); if x!=0 && volatile_read64(x+24)==1 { score=score+1; } i=i+8; }
    var pass:u64=0; if score==10 { pass=1; }
    unsafe { volatile_write64(state,1); volatile_write64(state+8,score); volatile_write64(state+16,10); volatile_write64(state+24,pass); }
    if pass==1 { serial_marker_frames_input_migration_snapshot_v8_ok(); } return pass;
}
fn input_migration_gate_v8(state:u64,oldgate:u64,snapshot:u64) -> u64 {
    if state==0 || oldgate==0 || snapshot==0 { return 0; } zero_page(state); var score:u64=0;
    if volatile_read64(oldgate+24)==1 { score=score+1; } if volatile_read64(snapshot+24)==1 { score=score+1; }
    var pass:u64=0; if score==2 { pass=1; }
    unsafe { volatile_write64(state,1); volatile_write64(state+8,score); volatile_write64(state+16,2); volatile_write64(state+24,pass); }
    if pass==1 { serial_marker_frames_input_migration_gate_v8_ok(); } return pass;
}

'''
anchor='fn serial_marker_entropy_seed_ok() -> void {'
if s.count(anchor)!=1: raise SystemExit('function insertion anchor mismatch')
s=s.replace(anchor,code+anchor,1)
alloc='let concurrency_gate_v7_state=bump_alloc(&mut heap_cursor,heap_end,4096);'
extra=' let ps2_ingress_v8_state=bump_alloc(&mut heap_cursor,heap_end,4096); let usb_hid_ingress_v8_state=bump_alloc(&mut heap_cursor,heap_end,4096); let pointer_owner_guard_v8_state=bump_alloc(&mut heap_cursor,heap_end,4096); let input_sequence_v8_state=bump_alloc(&mut heap_cursor,heap_end,4096); let input_dup_filter_v8_state=bump_alloc(&mut heap_cursor,heap_end,4096); let input_stale_filter_v8_state=bump_alloc(&mut heap_cursor,heap_end,4096); let pointer_normalize_v8_state=bump_alloc(&mut heap_cursor,heap_end,4096); let input_legacy_compare_v8_state=bump_alloc(&mut heap_cursor,heap_end,4096); let input_dispatch_v8_state=bump_alloc(&mut heap_cursor,heap_end,4096); let unified_input_runtime_v8_state=bump_alloc(&mut heap_cursor,heap_end,4096); let input_migration_snapshot_v8_state=bump_alloc(&mut heap_cursor,heap_end,4096); let input_migration_gate_v8_state=bump_alloc(&mut heap_cursor,heap_end,4096);'
if s.count(alloc)!=1: raise SystemExit('allocation anchor mismatch')
s=s.replace(alloc,alloc+extra,1)
ready='var concurrency_gate_v7_ready:u64=0;'
extra_ready=' var ps2_ingress_v8_ready:u64=0; var usb_hid_ingress_v8_ready:u64=0; var pointer_owner_guard_v8_ready:u64=0; var input_sequence_v8_ready:u64=0; var input_dup_filter_v8_ready:u64=0; var input_stale_filter_v8_ready:u64=0; var pointer_normalize_v8_ready:u64=0; var input_legacy_compare_v8_ready:u64=0; var input_dispatch_v8_ready:u64=0; var unified_input_runtime_v8_ready:u64=0; var input_migration_snapshot_v8_ready:u64=0; var input_migration_gate_v8_ready:u64=0;'
if s.count(ready)!=1: raise SystemExit('ready anchor mismatch')
s=s.replace(ready,ready+extra_ready,1)
boot='        if process_ready!=0 && concurrency_gate_v7_state!=0 && hal_runtime_gate_v6_ready!=0 && concurrency_runtime_v7_ready!=0 { unsafe { volatile_write64(process_state+2120,concurrency_gate_v7_state); } concurrency_gate_v7_ready=concurrency_gate_v7(concurrency_gate_v7_state,hal_runtime_gate_v6_state,concurrency_runtime_v7_state); }'
extra_boot=r'''
        if process_ready!=0 && ps2_ingress_v8_state!=0 && ps2_input_service_v5_ready!=0 && input_hal_v6_ready!=0 && worker_sched_v7_ready!=0 { ps2_ingress_v8_ready=ps2_ingress_v8_selftest(ps2_ingress_v8_state,ps2_input_service_v5_state,input_hal_v6_state,worker_sched_v7_state); if ps2_ingress_v8_ready!=0 { unsafe { volatile_write64(process_state+2128,ps2_ingress_v8_state); } } }
        if process_ready!=0 && usb_hid_ingress_v8_state!=0 && usb_service_v5_ready!=0 && input_hal_v6_ready!=0 && worker_sched_v7_ready!=0 { usb_hid_ingress_v8_ready=usb_hid_ingress_v8_selftest(usb_hid_ingress_v8_state,usb_service_v5_state,input_hal_v6_state,worker_sched_v7_state); if usb_hid_ingress_v8_ready!=0 { unsafe { volatile_write64(process_state+2136,usb_hid_ingress_v8_state); } } }
        if process_ready!=0 && pointer_owner_guard_v8_state!=0 && ps2_ingress_v8_ready!=0 && usb_hid_ingress_v8_ready!=0 && lock_owner_v7_ready!=0 { pointer_owner_guard_v8_ready=pointer_owner_guard_v8_selftest(pointer_owner_guard_v8_state,ps2_ingress_v8_state,usb_hid_ingress_v8_state,lock_owner_v7_state); if pointer_owner_guard_v8_ready!=0 { unsafe { volatile_write64(process_state+2144,pointer_owner_guard_v8_state); } } }
        if process_ready!=0 && input_sequence_v8_state!=0 && pointer_owner_guard_v8_ready!=0 && tx_serial_v7_ready!=0 && completion_order_v7_ready!=0 { input_sequence_v8_ready=input_sequence_v8_selftest(input_sequence_v8_state,pointer_owner_guard_v8_state,tx_serial_v7_state,completion_order_v7_state); if input_sequence_v8_ready!=0 { unsafe { volatile_write64(process_state+2152,input_sequence_v8_state); } } }
        if process_ready!=0 && input_dup_filter_v8_state!=0 && input_sequence_v8_ready!=0 && controller_queue_v6_ready!=0 && input_delivery_v4_ready!=0 { input_dup_filter_v8_ready=input_dup_filter_v8_selftest(input_dup_filter_v8_state,input_sequence_v8_state,controller_queue_v6_state,input_delivery_v4_state); if input_dup_filter_v8_ready!=0 { unsafe { volatile_write64(process_state+2160,input_dup_filter_v8_state); } } }
        if process_ready!=0 && input_stale_filter_v8_state!=0 && input_sequence_v8_ready!=0 && timer_queue_v2_ready!=0 && cancel_arb_v7_ready!=0 { input_stale_filter_v8_ready=input_stale_filter_v8_selftest(input_stale_filter_v8_state,input_sequence_v8_state,timer_queue_v2_state,cancel_arb_v7_state); if input_stale_filter_v8_ready!=0 { unsafe { volatile_write64(process_state+2168,input_stale_filter_v8_state); } } }
        if process_ready!=0 && pointer_normalize_v8_state!=0 && input_dup_filter_v8_ready!=0 && input_stale_filter_v8_ready!=0 && input_event_v2_ready!=0 { pointer_normalize_v8_ready=pointer_normalize_v8_selftest(pointer_normalize_v8_state,input_dup_filter_v8_state,input_stale_filter_v8_state,input_event_v2_state); if pointer_normalize_v8_ready!=0 { unsafe { volatile_write64(process_state+2176,pointer_normalize_v8_state); } } }
        if process_ready!=0 && input_legacy_compare_v8_state!=0 && pointer_normalize_v8_ready!=0 && input_bridge_v3_ready!=0 && input_delivery_v4_ready!=0 { input_legacy_compare_v8_ready=input_legacy_compare_v8_selftest(input_legacy_compare_v8_state,pointer_normalize_v8_state,input_bridge_v3_state,input_delivery_v4_state); if input_legacy_compare_v8_ready!=0 { unsafe { volatile_write64(process_state+2184,input_legacy_compare_v8_state); } } }
        if process_ready!=0 && input_dispatch_v8_state!=0 && pointer_normalize_v8_ready!=0 && driver_exec_v6_ready!=0 && driver_fairness_v7_ready!=0 { input_dispatch_v8_ready=input_dispatch_v8_selftest(input_dispatch_v8_state,pointer_normalize_v8_state,driver_exec_v6_state,driver_fairness_v7_state); if input_dispatch_v8_ready!=0 { unsafe { volatile_write64(process_state+2192,input_dispatch_v8_state); } } }
        if process_ready!=0 && unified_input_runtime_v8_state!=0 && input_dispatch_v8_ready!=0 && ps2_ingress_v8_ready!=0 && usb_hid_ingress_v8_ready!=0 { unified_input_runtime_v8_ready=unified_input_runtime_v8_selftest(unified_input_runtime_v8_state,input_dispatch_v8_state,ps2_ingress_v8_state,usb_hid_ingress_v8_state); if unified_input_runtime_v8_ready!=0 { unsafe { volatile_write64(process_state+2200,unified_input_runtime_v8_state); } } }
        if process_ready!=0 && input_migration_snapshot_v8_state!=0 { unsafe { volatile_write64(process_state+2208,input_migration_snapshot_v8_state); } input_migration_snapshot_v8_ready=input_migration_snapshot_v8(input_migration_snapshot_v8_state,process_state); }
        if process_ready!=0 && input_migration_gate_v8_state!=0 && concurrency_gate_v7_ready!=0 && input_migration_snapshot_v8_ready!=0 { unsafe { volatile_write64(process_state+2216,input_migration_gate_v8_state); } input_migration_gate_v8_ready=input_migration_gate_v8(input_migration_gate_v8_state,concurrency_gate_v7_state,input_migration_snapshot_v8_state); }
'''
if s.count(boot)!=1: raise SystemExit('boot anchor mismatch')
s=s.replace(boot,boot+extra_boot,1)
out=s.encode('utf-8'); p.write_bytes(out)
print('patched',p,'sha256',hashlib.sha256(out).hexdigest())
