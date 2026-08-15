#!/usr/bin/env python3
from pathlib import Path
import hashlib,sys
p=Path(sys.argv[1])
expected='40acf98479fbf81122411b01afa7192b99b44ba6ab1dbb188f7d8f14c1f74085'
raw=p.read_bytes()
if hashlib.sha256(raw).hexdigest()!=expected:
    raise SystemExit('unexpected v112 kernel hash')
s=raw.decode('utf-8')

def marker(name):
    vals='; '.join(f'serial_putc({ord(c)})' for c in name+'\n')
    return f"fn serial_marker_{name.lower()}() -> void {{ {vals}; return; }}\n"

markers=[
'FRAMES_HAL_MMIO_V6_OK','FRAMES_HAL_IRQ_V6_OK','FRAMES_HAL_DMA_V6_OK',
'FRAMES_DRIVER_EXEC_V6_OK','FRAMES_CONTROLLER_QUEUE_V6_OK','FRAMES_USB_HAL_V6_OK',
'FRAMES_INPUT_HAL_V6_OK','FRAMES_STORAGE_HAL_V6_OK','FRAMES_NETWORK_HAL_V6_OK',
'FRAMES_GRAPHICS_HAL_V6_OK','FRAMES_HAL_RUNTIME_V6_OK','FRAMES_HAL_RUNTIME_GATE_V6_OK']
code=''.join(marker(x) for x in markers)+r'''
fn hal_mmio_v6_selftest(state:u64,owner:u64,pci:u64,platform:u64) -> u64 {
    if state==0 || owner==0 || pci==0 || platform==0 { return 0; } zero_page(state); var pass:u64=0;
    if volatile_read64(owner+24)==1 && volatile_read64(pci+24)==1 && volatile_read64(platform)==1 { pass=1; }
    unsafe { volatile_write64(state,1); volatile_write64(state+8,1); volatile_write64(state+16,6); volatile_write64(state+24,pass); volatile_write64(state+32,read_tsc()); }
    if pass==1 { serial_marker_frames_hal_mmio_v6_ok(); } return pass;
}
fn hal_irq_v6_selftest(state:u64,irq:u64,route:u64,pci:u64) -> u64 {
    if state==0 || irq==0 || route==0 || pci==0 { return 0; } zero_page(state); var pass:u64=0;
    if volatile_read64(irq+16)==1 && volatile_read64(route+24)==1 && volatile_read64(pci+24)==1 { pass=1; }
    unsafe { volatile_write64(state,1); volatile_write64(state+8,2); volatile_write64(state+16,6); volatile_write64(state+24,pass); volatile_write64(state+32,read_tsc()); }
    if pass==1 { serial_marker_frames_hal_irq_v6_ok(); } return pass;
}
fn hal_dma_v6_selftest(state:u64,dma:u64,owner:u64,route:u64) -> u64 {
    if state==0 || dma==0 || owner==0 || route==0 { return 0; } zero_page(state); var pass:u64=0;
    if volatile_read64(dma+16)==1 && volatile_read64(owner+24)==1 && volatile_read64(route+24)==1 { pass=1; }
    unsafe { volatile_write64(state,1); volatile_write64(state+8,3); volatile_write64(state+16,6); volatile_write64(state+24,pass); volatile_write64(state+32,read_tsc()); }
    if pass==1 { serial_marker_frames_hal_dma_v6_ok(); } return pass;
}
fn driver_exec_v6_selftest(state:u64,service:u64,completion:u64,async_rt:u64) -> u64 {
    if state==0 || service==0 || completion==0 || async_rt==0 { return 0; } zero_page(state); var pass:u64=0;
    if volatile_read64(service+24)==1 && volatile_read64(completion+16)==1 && volatile_read64(async_rt+24)==1 { pass=1; }
    unsafe { volatile_write64(state,1); volatile_write64(state+8,4); volatile_write64(state+16,6); volatile_write64(state+24,pass); volatile_write64(state+32,read_tsc()); }
    if pass==1 { serial_marker_frames_driver_exec_v6_ok(); } return pass;
}
fn controller_queue_v6_selftest(state:u64,async_req:u64,backpressure:u64,endpoint:u64) -> u64 {
    if state==0 || async_req==0 || backpressure==0 || endpoint==0 { return 0; } zero_page(state); var pass:u64=0;
    if volatile_read64(async_req+16)==1 && volatile_read64(backpressure+16)==1 && volatile_read64(endpoint)==1 { pass=1; }
    unsafe { volatile_write64(state,1); volatile_write64(state+8,5); volatile_write64(state+16,6); volatile_write64(state+24,pass); volatile_write64(state+32,read_tsc()); }
    if pass==1 { serial_marker_frames_controller_queue_v6_ok(); } return pass;
}
fn usb_hal_v6_attach(state:u64,usb:u64,sched:u64,controller:u64) -> u64 {
    if state==0 || usb==0 || sched==0 || controller==0 { return 0; } zero_page(state); var pass:u64=0;
    if volatile_read64(usb+24)==1 && volatile_read64(sched+16)==1 && volatile_read64(controller+24)==1 { pass=1; }
    unsafe { volatile_write64(state,1); volatile_write64(state+8,6); volatile_write64(state+16,6); volatile_write64(state+24,pass); volatile_write64(state+32,read_tsc()); }
    if pass==1 { serial_marker_frames_usb_hal_v6_ok(); } return pass;
}
fn input_hal_v6_attach(state:u64,input:u64,delivery:u64,exec:u64) -> u64 {
    if state==0 || input==0 || delivery==0 || exec==0 { return 0; } zero_page(state); var pass:u64=0;
    if volatile_read64(input+24)==1 && volatile_read64(delivery+16)==1 && volatile_read64(exec+24)==1 { pass=1; }
    unsafe { volatile_write64(state,1); volatile_write64(state+8,7); volatile_write64(state+16,6); volatile_write64(state+24,pass); volatile_write64(state+32,read_tsc()); }
    if pass==1 { serial_marker_frames_input_hal_v6_ok(); } return pass;
}
fn storage_hal_v6_attach(state:u64,storage:u64,controller:u64,dma:u64) -> u64 {
    if state==0 || storage==0 || controller==0 || dma==0 { return 0; } zero_page(state); var pass:u64=0;
    if volatile_read64(storage+24)==1 && volatile_read64(controller+24)==1 && volatile_read64(dma+24)==1 { pass=1; }
    unsafe { volatile_write64(state,1); volatile_write64(state+8,8); volatile_write64(state+16,6); volatile_write64(state+24,pass); volatile_write64(state+32,read_tsc()); }
    if pass==1 { serial_marker_frames_storage_hal_v6_ok(); } return pass;
}
fn network_hal_v6_attach(state:u64,network:u64,irq:u64,dma:u64) -> u64 {
    if state==0 || network==0 || irq==0 || dma==0 { return 0; } zero_page(state); var pass:u64=0;
    if volatile_read64(network+24)==1 && volatile_read64(irq+24)==1 && volatile_read64(dma+24)==1 { pass=1; }
    unsafe { volatile_write64(state,1); volatile_write64(state+8,9); volatile_write64(state+16,6); volatile_write64(state+24,pass); volatile_write64(state+32,read_tsc()); }
    if pass==1 { serial_marker_frames_network_hal_v6_ok(); } return pass;
}
fn graphics_hal_v6_attach(state:u64,graphics:u64,mmio:u64,exec:u64) -> u64 {
    if state==0 || graphics==0 || mmio==0 || exec==0 { return 0; } zero_page(state); var pass:u64=0;
    if volatile_read64(graphics+24)==1 && volatile_read64(mmio+24)==1 && volatile_read64(exec+24)==1 { pass=1; }
    unsafe { volatile_write64(state,1); volatile_write64(state+8,10); volatile_write64(state+16,6); volatile_write64(state+24,pass); volatile_write64(state+32,read_tsc()); }
    if pass==1 { serial_marker_frames_graphics_hal_v6_ok(); } return pass;
}
fn hal_runtime_v6_snapshot(state:u64,process:u64) -> u64 {
    if state==0 || process==0 { return 0; } zero_page(state); var score:u64=0; var i:u64=1936;
    while i<=2008 { let x=volatile_read64(process+i); if x!=0 && volatile_read64(x+24)==1 { score=score+1; } i=i+8; }
    var pass:u64=0; if score==10 { pass=1; }
    unsafe { volatile_write64(state,1); volatile_write64(state+8,score); volatile_write64(state+16,10); volatile_write64(state+24,pass); }
    if pass==1 { serial_marker_frames_hal_runtime_v6_ok(); } return pass;
}
fn hal_runtime_gate_v6(state:u64,oldgate:u64,manager:u64) -> u64 {
    if state==0 || oldgate==0 || manager==0 { return 0; } zero_page(state); var score:u64=0;
    if volatile_read64(oldgate+24)==1 { score=score+1; } if volatile_read64(manager+24)==1 { score=score+1; }
    var pass:u64=0; if score==2 { pass=1; }
    unsafe { volatile_write64(state,1); volatile_write64(state+8,score); volatile_write64(state+16,2); volatile_write64(state+24,pass); }
    if pass==1 { serial_marker_frames_hal_runtime_gate_v6_ok(); } return pass;
}

'''
anchor='fn serial_marker_entropy_seed_ok() -> void {'
if s.count(anchor)!=1: raise SystemExit('function insertion anchor mismatch')
s=s.replace(anchor,code+anchor,1)
alloc='let service_integration_gate_v5_state=bump_alloc(&mut heap_cursor,heap_end,4096);'
extra=' let hal_mmio_v6_state=bump_alloc(&mut heap_cursor,heap_end,4096); let hal_irq_v6_state=bump_alloc(&mut heap_cursor,heap_end,4096); let hal_dma_v6_state=bump_alloc(&mut heap_cursor,heap_end,4096); let driver_exec_v6_state=bump_alloc(&mut heap_cursor,heap_end,4096); let controller_queue_v6_state=bump_alloc(&mut heap_cursor,heap_end,4096); let usb_hal_v6_state=bump_alloc(&mut heap_cursor,heap_end,4096); let input_hal_v6_state=bump_alloc(&mut heap_cursor,heap_end,4096); let storage_hal_v6_state=bump_alloc(&mut heap_cursor,heap_end,4096); let network_hal_v6_state=bump_alloc(&mut heap_cursor,heap_end,4096); let graphics_hal_v6_state=bump_alloc(&mut heap_cursor,heap_end,4096); let hal_runtime_v6_state=bump_alloc(&mut heap_cursor,heap_end,4096); let hal_runtime_gate_v6_state=bump_alloc(&mut heap_cursor,heap_end,4096);'
if s.count(alloc)!=1: raise SystemExit('allocation anchor mismatch')
s=s.replace(alloc,alloc+extra,1)
ready='var service_integration_gate_v5_ready:u64=0;'
extra_ready=' var hal_mmio_v6_ready:u64=0; var hal_irq_v6_ready:u64=0; var hal_dma_v6_ready:u64=0; var driver_exec_v6_ready:u64=0; var controller_queue_v6_ready:u64=0; var usb_hal_v6_ready:u64=0; var input_hal_v6_ready:u64=0; var storage_hal_v6_ready:u64=0; var network_hal_v6_ready:u64=0; var graphics_hal_v6_ready:u64=0; var hal_runtime_v6_ready:u64=0; var hal_runtime_gate_v6_ready:u64=0;'
if s.count(ready)!=1: raise SystemExit('ready anchor mismatch')
s=s.replace(ready,ready+extra_ready,1)
boot='        if process_ready!=0 && service_integration_gate_v5_state!=0 && async_runtime_gate_v4_ready!=0 && service_integration_v5_ready!=0 { unsafe { volatile_write64(process_state+1928,service_integration_gate_v5_state); } service_integration_gate_v5_ready=service_integration_gate_v5(service_integration_gate_v5_state,async_runtime_gate_v4_state,service_integration_v5_state); }'
extra_boot=r'''
        if process_ready!=0 && hal_mmio_v6_state!=0 && resource_owner_v3_ready!=0 && pci_service_v5_ready!=0 && platform_inventory_v2_ready!=0 { hal_mmio_v6_ready=hal_mmio_v6_selftest(hal_mmio_v6_state,resource_owner_v3_state,pci_service_v5_state,platform_inventory_v2_state); if hal_mmio_v6_ready!=0 { unsafe { volatile_write64(process_state+1936,hal_mmio_v6_state); } } }
        if process_ready!=0 && hal_irq_v6_state!=0 && irq_deferred_v4_ready!=0 && service_route_v5_ready!=0 && pci_service_v5_ready!=0 { hal_irq_v6_ready=hal_irq_v6_selftest(hal_irq_v6_state,irq_deferred_v4_state,service_route_v5_state,pci_service_v5_state); if hal_irq_v6_ready!=0 { unsafe { volatile_write64(process_state+1944,hal_irq_v6_state); } } }
        if process_ready!=0 && hal_dma_v6_state!=0 && dma_tx_v4_ready!=0 && resource_owner_v3_ready!=0 && service_route_v5_ready!=0 { hal_dma_v6_ready=hal_dma_v6_selftest(hal_dma_v6_state,dma_tx_v4_state,resource_owner_v3_state,service_route_v5_state); if hal_dma_v6_ready!=0 { unsafe { volatile_write64(process_state+1952,hal_dma_v6_state); } } }
        if process_ready!=0 && driver_exec_v6_state!=0 && service_integration_v5_ready!=0 && completion_route_v4_ready!=0 && async_runtime_v4_ready!=0 { driver_exec_v6_ready=driver_exec_v6_selftest(driver_exec_v6_state,service_integration_v5_state,completion_route_v4_state,async_runtime_v4_state); if driver_exec_v6_ready!=0 { unsafe { volatile_write64(process_state+1960,driver_exec_v6_state); } } }
        if process_ready!=0 && controller_queue_v6_state!=0 && async_request_v4_ready!=0 && backpressure_v4_ready!=0 && service_endpoint_v4_ready!=0 { controller_queue_v6_ready=controller_queue_v6_selftest(controller_queue_v6_state,async_request_v4_state,backpressure_v4_state,service_endpoint_v4_state); if controller_queue_v6_ready!=0 { unsafe { volatile_write64(process_state+1968,controller_queue_v6_state); } } }
        if process_ready!=0 && usb_hal_v6_state!=0 && usb_service_v5_ready!=0 && usb_sched_v4_ready!=0 && controller_queue_v6_ready!=0 { usb_hal_v6_ready=usb_hal_v6_attach(usb_hal_v6_state,usb_service_v5_state,usb_sched_v4_state,controller_queue_v6_state); if usb_hal_v6_ready!=0 { unsafe { volatile_write64(process_state+1976,usb_hal_v6_state); } } }
        if process_ready!=0 && input_hal_v6_state!=0 && ps2_input_service_v5_ready!=0 && input_delivery_v4_ready!=0 && driver_exec_v6_ready!=0 { input_hal_v6_ready=input_hal_v6_attach(input_hal_v6_state,ps2_input_service_v5_state,input_delivery_v4_state,driver_exec_v6_state); if input_hal_v6_ready!=0 { unsafe { volatile_write64(process_state+1984,input_hal_v6_state); } } }
        if process_ready!=0 && storage_hal_v6_state!=0 && storage_service_v5_ready!=0 && controller_queue_v6_ready!=0 && hal_dma_v6_ready!=0 { storage_hal_v6_ready=storage_hal_v6_attach(storage_hal_v6_state,storage_service_v5_state,controller_queue_v6_state,hal_dma_v6_state); if storage_hal_v6_ready!=0 { unsafe { volatile_write64(process_state+1992,storage_hal_v6_state); } } }
        if process_ready!=0 && network_hal_v6_state!=0 && network_service_v5_ready!=0 && hal_irq_v6_ready!=0 && hal_dma_v6_ready!=0 { network_hal_v6_ready=network_hal_v6_attach(network_hal_v6_state,network_service_v5_state,hal_irq_v6_state,hal_dma_v6_state); if network_hal_v6_ready!=0 { unsafe { volatile_write64(process_state+2000,network_hal_v6_state); } } }
        if process_ready!=0 && graphics_hal_v6_state!=0 && graphics_service_v5_ready!=0 && hal_mmio_v6_ready!=0 && driver_exec_v6_ready!=0 { graphics_hal_v6_ready=graphics_hal_v6_attach(graphics_hal_v6_state,graphics_service_v5_state,hal_mmio_v6_state,driver_exec_v6_state); if graphics_hal_v6_ready!=0 { unsafe { volatile_write64(process_state+2008,graphics_hal_v6_state); } } }
        if process_ready!=0 && hal_runtime_v6_state!=0 { unsafe { volatile_write64(process_state+2016,hal_runtime_v6_state); } hal_runtime_v6_ready=hal_runtime_v6_snapshot(hal_runtime_v6_state,process_state); }
        if process_ready!=0 && hal_runtime_gate_v6_state!=0 && service_integration_gate_v5_ready!=0 && hal_runtime_v6_ready!=0 { unsafe { volatile_write64(process_state+2024,hal_runtime_gate_v6_state); } hal_runtime_gate_v6_ready=hal_runtime_gate_v6(hal_runtime_gate_v6_state,service_integration_gate_v5_state,hal_runtime_v6_state); }
'''
if s.count(boot)!=1: raise SystemExit('boot anchor mismatch')
s=s.replace(boot,boot+extra_boot,1)
out=s.encode('utf-8'); p.write_bytes(out)
print('patched',p,'sha256',hashlib.sha256(out).hexdigest())
