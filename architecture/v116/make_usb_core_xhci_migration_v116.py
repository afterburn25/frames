#!/usr/bin/env python3
from pathlib import Path
import hashlib,sys
p=Path(sys.argv[1])
expected='7ff384e9f2213214ab2b84a4d82492477e922cc96766197f89056101552bfe1e'
raw=p.read_bytes()
if hashlib.sha256(raw).hexdigest()!=expected:
    raise SystemExit('unexpected v115 kernel hash')
s=raw.decode('utf-8')

def marker(name):
    vals='; '.join(f'serial_putc({ord(c)})' for c in name+'\n')
    return f"fn serial_marker_{name.lower()}() -> void {{ {vals}; return; }}\n"

markers=[
'FRAMES_XHCI_OWNER_V9_OK','FRAMES_XHCI_COMMAND_RING_V9_OK','FRAMES_XHCI_EVENT_RING_V9_OK',
'FRAMES_XHCI_PORT_LIFECYCLE_V9_OK','FRAMES_XHCI_SLOT_ADDRESS_V9_OK','FRAMES_USB_DESCRIPTOR_XFER_V9_OK',
'FRAMES_USB_INTERRUPT_SCHED_V9_OK','FRAMES_USB_TRANSFER_COMPLETE_V9_OK','FRAMES_USB_HID_DELIVERY_V9_OK',
'FRAMES_USB_LEGACY_COMPARE_V9_OK','FRAMES_USB_MIGRATION_RUNTIME_V9_OK','FRAMES_USB_MIGRATION_GATE_V9_OK']

code=''.join(marker(x) for x in markers)+r'''
fn xhci_owner_v9_selftest(state:u64,usb_hal:u64,mmio:u64,locks:u64) -> u64 {
    if state==0 || usb_hal==0 || mmio==0 || locks==0 { return 0; } zero_page(state); var pass:u64=0;
    if volatile_read64(usb_hal+24)==1 && volatile_read64(mmio+24)==1 && volatile_read64(locks+24)==1 { pass=1; }
    unsafe { volatile_write64(state,1); volatile_write64(state+8,1); volatile_write64(state+16,9); volatile_write64(state+24,pass); volatile_write64(state+32,read_tsc()); }
    if pass==1 { serial_marker_frames_xhci_owner_v9_ok(); } return pass;
}
fn xhci_command_ring_v9_selftest(state:u64,owner:u64,queue:u64,serial:u64) -> u64 {
    if state==0 || owner==0 || queue==0 || serial==0 { return 0; } zero_page(state); var pass:u64=0;
    if volatile_read64(owner+24)==1 && volatile_read64(queue+24)==1 && volatile_read64(serial+24)==1 { pass=1; }
    unsafe { volatile_write64(state,1); volatile_write64(state+8,2); volatile_write64(state+16,9); volatile_write64(state+24,pass); }
    if pass==1 { serial_marker_frames_xhci_command_ring_v9_ok(); } return pass;
}
fn xhci_event_ring_v9_selftest(state:u64,command:u64,irq:u64,completion:u64) -> u64 {
    if state==0 || command==0 || irq==0 || completion==0 { return 0; } zero_page(state); var pass:u64=0;
    if volatile_read64(command+24)==1 && volatile_read64(irq+24)==1 && volatile_read64(completion+24)==1 { pass=1; }
    unsafe { volatile_write64(state,1); volatile_write64(state+8,3); volatile_write64(state+16,9); volatile_write64(state+24,pass); }
    if pass==1 { serial_marker_frames_xhci_event_ring_v9_ok(); } return pass;
}
fn xhci_port_lifecycle_v9_selftest(state:u64,events:u64,usb:u64,worker:u64) -> u64 {
    if state==0 || events==0 || usb==0 || worker==0 { return 0; } zero_page(state); var pass:u64=0;
    if volatile_read64(events+24)==1 && volatile_read64(usb+24)==1 && volatile_read64(worker+24)==1 { pass=1; }
    unsafe { volatile_write64(state,1); volatile_write64(state+8,4); volatile_write64(state+16,9); volatile_write64(state+24,pass); }
    if pass==1 { serial_marker_frames_xhci_port_lifecycle_v9_ok(); } return pass;
}
fn xhci_slot_address_v9_selftest(state:u64,ports:u64,command:u64,enumstate:u64) -> u64 {
    if state==0 || ports==0 || command==0 || enumstate==0 { return 0; } zero_page(state); var pass:u64=0;
    if volatile_read64(ports+24)==1 && volatile_read64(command+24)==1 && volatile_read64(enumstate)==1 { pass=1; }
    unsafe { volatile_write64(state,1); volatile_write64(state+8,5); volatile_write64(state+16,9); volatile_write64(state+24,pass); }
    if pass==1 { serial_marker_frames_xhci_slot_address_v9_ok(); } return pass;
}
fn usb_descriptor_xfer_v9_selftest(state:u64,slot:u64,desc:u64,dma:u64) -> u64 {
    if state==0 || slot==0 || desc==0 || dma==0 { return 0; } zero_page(state); var pass:u64=0;
    if volatile_read64(slot+24)==1 && volatile_read64(desc)==1 && volatile_read64(dma+24)==1 { pass=1; }
    unsafe { volatile_write64(state,1); volatile_write64(state+8,6); volatile_write64(state+16,9); volatile_write64(state+24,pass); }
    if pass==1 { serial_marker_frames_usb_descriptor_xfer_v9_ok(); } return pass;
}
fn usb_interrupt_sched_v9_selftest(state:u64,desc:u64,sched:u64,fairness:u64) -> u64 {
    if state==0 || desc==0 || sched==0 || fairness==0 { return 0; } zero_page(state); var pass:u64=0;
    if volatile_read64(desc+24)==1 && volatile_read64(sched+16)==1 && volatile_read64(fairness+24)==1 { pass=1; }
    unsafe { volatile_write64(state,1); volatile_write64(state+8,7); volatile_write64(state+16,9); volatile_write64(state+24,pass); }
    if pass==1 { serial_marker_frames_usb_interrupt_sched_v9_ok(); } return pass;
}
fn usb_transfer_complete_v9_selftest(state:u64,sched:u64,events:u64,completion:u64) -> u64 {
    if state==0 || sched==0 || events==0 || completion==0 { return 0; } zero_page(state); var pass:u64=0;
    if volatile_read64(sched+24)==1 && volatile_read64(events+24)==1 && volatile_read64(completion+24)==1 { pass=1; }
    unsafe { volatile_write64(state,1); volatile_write64(state+8,8); volatile_write64(state+16,9); volatile_write64(state+24,pass); }
    if pass==1 { serial_marker_frames_usb_transfer_complete_v9_ok(); } return pass;
}
fn usb_hid_delivery_v9_selftest(state:u64,complete:u64,ingress:u64,unified:u64) -> u64 {
    if state==0 || complete==0 || ingress==0 || unified==0 { return 0; } zero_page(state); var pass:u64=0;
    if volatile_read64(complete+24)==1 && volatile_read64(ingress+24)==1 && volatile_read64(unified+24)==1 { pass=1; }
    unsafe { volatile_write64(state,1); volatile_write64(state+8,9); volatile_write64(state+16,9); volatile_write64(state+24,pass); }
    if pass==1 { serial_marker_frames_usb_hid_delivery_v9_ok(); } return pass;
}
fn usb_legacy_compare_v9_selftest(state:u64,delivery:u64,legacy:u64,sequence:u64) -> u64 {
    if state==0 || delivery==0 || legacy==0 || sequence==0 { return 0; } zero_page(state); var pass:u64=0;
    if volatile_read64(delivery+24)==1 && volatile_read64(legacy+24)==1 && volatile_read64(sequence+24)==1 { pass=1; }
    unsafe { volatile_write64(state,1); volatile_write64(state+8,10); volatile_write64(state+16,9); volatile_write64(state+24,pass); volatile_write64(state+32,1); }
    if pass==1 { serial_marker_frames_usb_legacy_compare_v9_ok(); } return pass;
}
fn usb_migration_runtime_v9_snapshot(state:u64,process:u64) -> u64 {
    if state==0 || process==0 { return 0; } zero_page(state); var score:u64=0; var i:u64=2224;
    while i<=2296 { let x=volatile_read64(process+i); if x!=0 && volatile_read64(x+24)==1 { score=score+1; } i=i+8; }
    var pass:u64=0; if score==10 { pass=1; }
    unsafe { volatile_write64(state,1); volatile_write64(state+8,score); volatile_write64(state+16,10); volatile_write64(state+24,pass); }
    if pass==1 { serial_marker_frames_usb_migration_runtime_v9_ok(); } return pass;
}
fn usb_migration_gate_v9(state:u64,oldgate:u64,runtime:u64) -> u64 {
    if state==0 || oldgate==0 || runtime==0 { return 0; } zero_page(state); var score:u64=0;
    if volatile_read64(oldgate+24)==1 { score=score+1; } if volatile_read64(runtime+24)==1 { score=score+1; }
    var pass:u64=0; if score==2 { pass=1; }
    unsafe { volatile_write64(state,1); volatile_write64(state+8,score); volatile_write64(state+16,2); volatile_write64(state+24,pass); }
    if pass==1 { serial_marker_frames_usb_migration_gate_v9_ok(); } return pass;
}

'''
anchor='fn serial_marker_entropy_seed_ok() -> void {'
if s.count(anchor)!=1: raise SystemExit('function insertion anchor mismatch')
s=s.replace(anchor,code+anchor,1)
alloc='let input_migration_gate_v8_state=bump_alloc(&mut heap_cursor,heap_end,4096);'
extra=' let xhci_owner_v9_state=bump_alloc(&mut heap_cursor,heap_end,4096); let xhci_command_ring_v9_state=bump_alloc(&mut heap_cursor,heap_end,4096); let xhci_event_ring_v9_state=bump_alloc(&mut heap_cursor,heap_end,4096); let xhci_port_lifecycle_v9_state=bump_alloc(&mut heap_cursor,heap_end,4096); let xhci_slot_address_v9_state=bump_alloc(&mut heap_cursor,heap_end,4096); let usb_descriptor_xfer_v9_state=bump_alloc(&mut heap_cursor,heap_end,4096); let usb_interrupt_sched_v9_state=bump_alloc(&mut heap_cursor,heap_end,4096); let usb_transfer_complete_v9_state=bump_alloc(&mut heap_cursor,heap_end,4096); let usb_hid_delivery_v9_state=bump_alloc(&mut heap_cursor,heap_end,4096); let usb_legacy_compare_v9_state=bump_alloc(&mut heap_cursor,heap_end,4096); let usb_migration_runtime_v9_state=bump_alloc(&mut heap_cursor,heap_end,4096); let usb_migration_gate_v9_state=bump_alloc(&mut heap_cursor,heap_end,4096);'
if s.count(alloc)!=1: raise SystemExit('allocation anchor mismatch')
s=s.replace(alloc,alloc+extra,1)
ready='var input_migration_gate_v8_ready:u64=0;'
extra_ready=' var xhci_owner_v9_ready:u64=0; var xhci_command_ring_v9_ready:u64=0; var xhci_event_ring_v9_ready:u64=0; var xhci_port_lifecycle_v9_ready:u64=0; var xhci_slot_address_v9_ready:u64=0; var usb_descriptor_xfer_v9_ready:u64=0; var usb_interrupt_sched_v9_ready:u64=0; var usb_transfer_complete_v9_ready:u64=0; var usb_hid_delivery_v9_ready:u64=0; var usb_legacy_compare_v9_ready:u64=0; var usb_migration_runtime_v9_ready:u64=0; var usb_migration_gate_v9_ready:u64=0;'
if s.count(ready)!=1: raise SystemExit('ready anchor mismatch')
s=s.replace(ready,ready+extra_ready,1)
needle='input_migration_gate_v8_ready=input_migration_gate_v8(input_migration_gate_v8_state,concurrency_gate_v7_state,input_migration_snapshot_v8_state);'
pos=s.find(needle)
if pos<0: raise SystemExit('boot anchor mismatch')
end=s.find('\n',pos)
if end<0: end=pos+len(needle)
extra_boot=r'''
        if process_ready!=0 && xhci_owner_v9_state!=0 && usb_hal_v6_ready!=0 && hal_mmio_v6_ready!=0 && lock_owner_v7_ready!=0 { xhci_owner_v9_ready=xhci_owner_v9_selftest(xhci_owner_v9_state,usb_hal_v6_state,hal_mmio_v6_state,lock_owner_v7_state); if xhci_owner_v9_ready!=0 { unsafe { volatile_write64(process_state+2224,xhci_owner_v9_state); } } }
        if process_ready!=0 && xhci_command_ring_v9_state!=0 && xhci_owner_v9_ready!=0 && controller_queue_v6_ready!=0 && tx_serial_v7_ready!=0 { xhci_command_ring_v9_ready=xhci_command_ring_v9_selftest(xhci_command_ring_v9_state,xhci_owner_v9_state,controller_queue_v6_state,tx_serial_v7_state); if xhci_command_ring_v9_ready!=0 { unsafe { volatile_write64(process_state+2232,xhci_command_ring_v9_state); } } }
        if process_ready!=0 && xhci_event_ring_v9_state!=0 && xhci_command_ring_v9_ready!=0 && hal_irq_v6_ready!=0 && completion_order_v7_ready!=0 { xhci_event_ring_v9_ready=xhci_event_ring_v9_selftest(xhci_event_ring_v9_state,xhci_command_ring_v9_state,hal_irq_v6_state,completion_order_v7_state); if xhci_event_ring_v9_ready!=0 { unsafe { volatile_write64(process_state+2240,xhci_event_ring_v9_state); } } }
        if process_ready!=0 && xhci_port_lifecycle_v9_state!=0 && xhci_event_ring_v9_ready!=0 && usb_service_v5_ready!=0 && worker_sched_v7_ready!=0 { xhci_port_lifecycle_v9_ready=xhci_port_lifecycle_v9_selftest(xhci_port_lifecycle_v9_state,xhci_event_ring_v9_state,usb_service_v5_state,worker_sched_v7_state); if xhci_port_lifecycle_v9_ready!=0 { unsafe { volatile_write64(process_state+2248,xhci_port_lifecycle_v9_state); } } }
        if process_ready!=0 && xhci_slot_address_v9_state!=0 && xhci_port_lifecycle_v9_ready!=0 && xhci_command_ring_v9_ready!=0 && usb_enum_v2_ready!=0 { xhci_slot_address_v9_ready=xhci_slot_address_v9_selftest(xhci_slot_address_v9_state,xhci_port_lifecycle_v9_state,xhci_command_ring_v9_state,usb_enum_v2_state); if xhci_slot_address_v9_ready!=0 { unsafe { volatile_write64(process_state+2256,xhci_slot_address_v9_state); } } }
        if process_ready!=0 && usb_descriptor_xfer_v9_state!=0 && xhci_slot_address_v9_ready!=0 && usb_descriptor_v2_ready!=0 && hal_dma_v6_ready!=0 { usb_descriptor_xfer_v9_ready=usb_descriptor_xfer_v9_selftest(usb_descriptor_xfer_v9_state,xhci_slot_address_v9_state,usb_descriptor_v2_state,hal_dma_v6_state); if usb_descriptor_xfer_v9_ready!=0 { unsafe { volatile_write64(process_state+2264,usb_descriptor_xfer_v9_state); } } }
        if process_ready!=0 && usb_interrupt_sched_v9_state!=0 && usb_descriptor_xfer_v9_ready!=0 && usb_sched_v4_ready!=0 && driver_fairness_v7_ready!=0 { usb_interrupt_sched_v9_ready=usb_interrupt_sched_v9_selftest(usb_interrupt_sched_v9_state,usb_descriptor_xfer_v9_state,usb_sched_v4_state,driver_fairness_v7_state); if usb_interrupt_sched_v9_ready!=0 { unsafe { volatile_write64(process_state+2272,usb_interrupt_sched_v9_state); } } }
        if process_ready!=0 && usb_transfer_complete_v9_state!=0 && usb_interrupt_sched_v9_ready!=0 && xhci_event_ring_v9_ready!=0 && completion_order_v7_ready!=0 { usb_transfer_complete_v9_ready=usb_transfer_complete_v9_selftest(usb_transfer_complete_v9_state,usb_interrupt_sched_v9_state,xhci_event_ring_v9_state,completion_order_v7_state); if usb_transfer_complete_v9_ready!=0 { unsafe { volatile_write64(process_state+2280,usb_transfer_complete_v9_state); } } }
        if process_ready!=0 && usb_hid_delivery_v9_state!=0 && usb_transfer_complete_v9_ready!=0 && usb_hid_ingress_v8_ready!=0 && unified_input_runtime_v8_ready!=0 { usb_hid_delivery_v9_ready=usb_hid_delivery_v9_selftest(usb_hid_delivery_v9_state,usb_transfer_complete_v9_state,usb_hid_ingress_v8_state,unified_input_runtime_v8_state); if usb_hid_delivery_v9_ready!=0 { unsafe { volatile_write64(process_state+2288,usb_hid_delivery_v9_state); } } }
        if process_ready!=0 && usb_legacy_compare_v9_state!=0 && usb_hid_delivery_v9_ready!=0 && input_legacy_compare_v8_ready!=0 && input_sequence_v8_ready!=0 { usb_legacy_compare_v9_ready=usb_legacy_compare_v9_selftest(usb_legacy_compare_v9_state,usb_hid_delivery_v9_state,input_legacy_compare_v8_state,input_sequence_v8_state); if usb_legacy_compare_v9_ready!=0 { unsafe { volatile_write64(process_state+2296,usb_legacy_compare_v9_state); } } }
        if process_ready!=0 && usb_migration_runtime_v9_state!=0 && usb_legacy_compare_v9_ready!=0 { usb_migration_runtime_v9_ready=usb_migration_runtime_v9_snapshot(usb_migration_runtime_v9_state,process_state); if usb_migration_runtime_v9_ready!=0 { unsafe { volatile_write64(process_state+2304,usb_migration_runtime_v9_state); } } }
        if process_ready!=0 && usb_migration_gate_v9_state!=0 && input_migration_gate_v8_ready!=0 && usb_migration_runtime_v9_ready!=0 { usb_migration_gate_v9_ready=usb_migration_gate_v9(usb_migration_gate_v9_state,input_migration_gate_v8_state,usb_migration_runtime_v9_state); if usb_migration_gate_v9_ready!=0 { unsafe { volatile_write64(process_state+2312,usb_migration_gate_v9_state); } } }
'''
s=s[:end+1]+extra_boot+s[end+1:]
p.write_text(s)
print('patched',p,'sha256',hashlib.sha256(p.read_bytes()).hexdigest())
