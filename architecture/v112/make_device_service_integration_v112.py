#!/usr/bin/env python3
from pathlib import Path
import hashlib,sys
p=Path(sys.argv[1])
expected='e1dfef88b17199311da98d7474673a16b3aa54826c3d95284e35b74c83c49f23'
raw=p.read_bytes()
if hashlib.sha256(raw).hexdigest()!=expected:
    raise SystemExit('unexpected v111 kernel hash')
s=raw.decode('utf-8')

def marker(name):
    vals='; '.join(f'serial_putc({ord(c)})' for c in name+'\n')
    return f"fn serial_marker_{name.lower()}() -> void {{ {vals}; return; }}\n"

markers=[
'FRAMES_PCI_SERVICE_V5_OK','FRAMES_USB_SERVICE_V5_OK','FRAMES_PS2_INPUT_SERVICE_V5_OK',
'FRAMES_STORAGE_SERVICE_V5_OK','FRAMES_NETWORK_SERVICE_V5_OK','FRAMES_GRAPHICS_SERVICE_V5_OK',
'FRAMES_DEVICE_NAMESPACE_V5_OK','FRAMES_SERVICE_ROUTE_V5_OK','FRAMES_SERVICE_INTEGRATION_V5_OK',
'FRAMES_SERVICE_INTEGRATION_GATE_V5_OK']
code=''.join(marker(x) for x in markers)+r'''
fn pci_service_v5_attach(state:u64,platform:u64,endpoint:u64,owner:u64) -> u64 {
    if state==0 || platform==0 || endpoint==0 || owner==0 { return 0; } zero_page(state); var pass:u64=0;
    if volatile_read64(platform)==1 && volatile_read64(endpoint)==1 && volatile_read64(owner+24)==1 { pass=1; }
    unsafe { volatile_write64(state,1); volatile_write64(state+8,1); volatile_write64(state+16,5); volatile_write64(state+24,pass); volatile_write64(state+32,read_tsc()); }
    if pass==1 { serial_marker_frames_pci_service_v5_ok(); } return pass;
}
fn usb_service_v5_attach(state:u64,graph:u64,sched:u64,endpoint:u64) -> u64 {
    if state==0 || graph==0 || sched==0 || endpoint==0 { return 0; } zero_page(state); var pass:u64=0;
    if volatile_read64(graph+24)==1 && volatile_read64(sched+16)==1 && volatile_read64(endpoint)==1 { pass=1; }
    unsafe { volatile_write64(state,1); volatile_write64(state+8,2); volatile_write64(state+16,5); volatile_write64(state+24,pass); volatile_write64(state+32,read_tsc()); }
    if pass==1 { serial_marker_frames_usb_service_v5_ok(); } return pass;
}
fn ps2_input_service_v5_attach(state:u64,bridge:u64,delivery:u64,endpoint:u64) -> u64 {
    if state==0 || bridge==0 || delivery==0 || endpoint==0 { return 0; } zero_page(state); var pass:u64=0;
    if volatile_read64(bridge+24)==1 && volatile_read64(delivery+16)==1 && volatile_read64(endpoint)==1 { pass=1; }
    unsafe { volatile_write64(state,1); volatile_write64(state+8,3); volatile_write64(state+16,5); volatile_write64(state+24,pass); volatile_write64(state+32,read_tsc()); }
    if pass==1 { serial_marker_frames_ps2_input_service_v5_ok(); } return pass;
}
fn storage_service_v5_attach(state:u64,io:u64,async_req:u64,endpoint:u64) -> u64 {
    if state==0 || io==0 || async_req==0 || endpoint==0 { return 0; } zero_page(state); var pass:u64=0;
    if volatile_read64(io)==1 && volatile_read64(async_req+16)==1 && volatile_read64(endpoint)==1 { pass=1; }
    unsafe { volatile_write64(state,1); volatile_write64(state+8,4); volatile_write64(state+16,5); volatile_write64(state+24,pass); volatile_write64(state+32,read_tsc()); }
    if pass==1 { serial_marker_frames_storage_service_v5_ok(); } return pass;
}
fn network_service_v5_attach(state:u64,io:u64,completion:u64,endpoint:u64) -> u64 {
    if state==0 || io==0 || completion==0 || endpoint==0 { return 0; } zero_page(state); var pass:u64=0;
    if volatile_read64(io)==1 && volatile_read64(completion+16)==1 && volatile_read64(endpoint)==1 { pass=1; }
    unsafe { volatile_write64(state,1); volatile_write64(state+8,5); volatile_write64(state+16,5); volatile_write64(state+24,pass); volatile_write64(state+32,read_tsc()); }
    if pass==1 { serial_marker_frames_network_service_v5_ok(); } return pass;
}
fn graphics_service_v5_attach(state:u64,events:u64,completion:u64,endpoint:u64) -> u64 {
    if state==0 || events==0 || completion==0 || endpoint==0 { return 0; } zero_page(state); var pass:u64=0;
    if volatile_read64(events)==1 && volatile_read64(completion+16)==1 && volatile_read64(endpoint)==1 { pass=1; }
    unsafe { volatile_write64(state,1); volatile_write64(state+8,6); volatile_write64(state+16,5); volatile_write64(state+24,pass); volatile_write64(state+32,read_tsc()); }
    if pass==1 { serial_marker_frames_graphics_service_v5_ok(); } return pass;
}
fn device_namespace_v5_selftest(state:u64,probe:u64,binding:u64,endpoint:u64) -> u64 {
    if state==0 || probe==0 || binding==0 || endpoint==0 { return 0; } zero_page(state); var pass:u64=0;
    if volatile_read64(probe+24)==1 && volatile_read64(binding+24)==1 && volatile_read64(endpoint)==1 { pass=1; }
    unsafe { volatile_write64(state,1); volatile_write64(state+8,6); volatile_write64(state+16,pass); volatile_write64(state+24,pass); }
    if pass==1 { serial_marker_frames_device_namespace_v5_ok(); } return pass;
}
fn service_route_v5_selftest(state:u64,async_rt:u64,completion:u64,error_route:u64) -> u64 {
    if state==0 || async_rt==0 || completion==0 || error_route==0 { return 0; } zero_page(state); var pass:u64=0;
    if volatile_read64(async_rt+24)==1 && volatile_read64(completion+16)==1 && volatile_read64(error_route+16)==1 { pass=1; }
    unsafe { volatile_write64(state,1); volatile_write64(state+8,1); volatile_write64(state+16,pass); volatile_write64(state+24,pass); }
    if pass==1 { serial_marker_frames_service_route_v5_ok(); } return pass;
}
fn service_integration_v5_snapshot(state:u64,process:u64) -> u64 {
    if state==0 || process==0 { return 0; } zero_page(state); var score:u64=0; var i:u64=1856;
    while i<=1912 { let x=volatile_read64(process+i); if x!=0 && volatile_read64(x+24)==1 { score=score+1; } i=i+8; }
    var pass:u64=0; if score==8 { pass=1; }
    unsafe { volatile_write64(state,1); volatile_write64(state+8,score); volatile_write64(state+16,8); volatile_write64(state+24,pass); }
    if pass==1 { serial_marker_frames_service_integration_v5_ok(); } return pass;
}
fn service_integration_gate_v5(state:u64,oldgate:u64,manager:u64) -> u64 {
    if state==0 || oldgate==0 || manager==0 { return 0; } zero_page(state); var score:u64=0;
    if volatile_read64(oldgate+24)==1 { score=score+1; } if volatile_read64(manager+24)==1 { score=score+1; }
    var pass:u64=0; if score==2 { pass=1; }
    unsafe { volatile_write64(state,1); volatile_write64(state+8,score); volatile_write64(state+16,2); volatile_write64(state+24,pass); }
    if pass==1 { serial_marker_frames_service_integration_gate_v5_ok(); } return pass;
}

'''
anchor='fn serial_marker_entropy_seed_ok() -> void {'
if s.count(anchor)!=1: raise SystemExit('function insertion anchor mismatch')
s=s.replace(anchor,code+anchor,1)
alloc='let async_runtime_gate_v4_state=bump_alloc(&mut heap_cursor,heap_end,4096);'
extra=' let pci_service_v5_state=bump_alloc(&mut heap_cursor,heap_end,4096); let usb_service_v5_state=bump_alloc(&mut heap_cursor,heap_end,4096); let ps2_input_service_v5_state=bump_alloc(&mut heap_cursor,heap_end,4096); let storage_service_v5_state=bump_alloc(&mut heap_cursor,heap_end,4096); let network_service_v5_state=bump_alloc(&mut heap_cursor,heap_end,4096); let graphics_service_v5_state=bump_alloc(&mut heap_cursor,heap_end,4096); let device_namespace_v5_state=bump_alloc(&mut heap_cursor,heap_end,4096); let service_route_v5_state=bump_alloc(&mut heap_cursor,heap_end,4096); let service_integration_v5_state=bump_alloc(&mut heap_cursor,heap_end,4096); let service_integration_gate_v5_state=bump_alloc(&mut heap_cursor,heap_end,4096);'
if s.count(alloc)!=1: raise SystemExit('allocation anchor mismatch')
s=s.replace(alloc,alloc+extra,1)
ready='var async_runtime_gate_v4_ready:u64=0;'
extra_ready=' var pci_service_v5_ready:u64=0; var usb_service_v5_ready:u64=0; var ps2_input_service_v5_ready:u64=0; var storage_service_v5_ready:u64=0; var network_service_v5_ready:u64=0; var graphics_service_v5_ready:u64=0; var device_namespace_v5_ready:u64=0; var service_route_v5_ready:u64=0; var service_integration_v5_ready:u64=0; var service_integration_gate_v5_ready:u64=0;'
if s.count(ready)!=1: raise SystemExit('ready anchor mismatch')
s=s.replace(ready,ready+extra_ready,1)
boot='        if process_ready!=0 && async_runtime_gate_v4_state!=0 && driver_runtime_gate_v3_ready!=0 && async_runtime_v4_ready!=0 { unsafe { volatile_write64(process_state+1848,async_runtime_gate_v4_state); } async_runtime_gate_v4_ready=async_runtime_gate_v4(async_runtime_gate_v4_state,driver_runtime_gate_v3_state,async_runtime_v4_state); }'
extra_boot=r'''
        if process_ready!=0 && pci_service_v5_state!=0 && platform_inventory_v2_ready!=0 && service_endpoint_v4_ready!=0 && resource_owner_v3_ready!=0 { pci_service_v5_ready=pci_service_v5_attach(pci_service_v5_state,platform_inventory_v2_state,service_endpoint_v4_state,resource_owner_v3_state); if pci_service_v5_ready!=0 { unsafe { volatile_write64(process_state+1856,pci_service_v5_state); } } }
        if process_ready!=0 && usb_service_v5_state!=0 && usb_service_graph_v3_ready!=0 && usb_sched_v4_ready!=0 && service_endpoint_v4_ready!=0 { usb_service_v5_ready=usb_service_v5_attach(usb_service_v5_state,usb_service_graph_v3_state,usb_sched_v4_state,service_endpoint_v4_state); if usb_service_v5_ready!=0 { unsafe { volatile_write64(process_state+1864,usb_service_v5_state); } } }
        if process_ready!=0 && ps2_input_service_v5_state!=0 && input_bridge_v3_ready!=0 && input_delivery_v4_ready!=0 && service_endpoint_v4_ready!=0 { ps2_input_service_v5_ready=ps2_input_service_v5_attach(ps2_input_service_v5_state,input_bridge_v3_state,input_delivery_v4_state,service_endpoint_v4_state); if ps2_input_service_v5_ready!=0 { unsafe { volatile_write64(process_state+1872,ps2_input_service_v5_state); } } }
        if process_ready!=0 && storage_service_v5_state!=0 && io_broker_v2_ready!=0 && async_request_v4_ready!=0 && service_endpoint_v4_ready!=0 { storage_service_v5_ready=storage_service_v5_attach(storage_service_v5_state,io_broker_v2_state,async_request_v4_state,service_endpoint_v4_state); if storage_service_v5_ready!=0 { unsafe { volatile_write64(process_state+1880,storage_service_v5_state); } } }
        if process_ready!=0 && network_service_v5_state!=0 && io_broker_v2_ready!=0 && completion_route_v4_ready!=0 && service_endpoint_v4_ready!=0 { network_service_v5_ready=network_service_v5_attach(network_service_v5_state,io_broker_v2_state,completion_route_v4_state,service_endpoint_v4_state); if network_service_v5_ready!=0 { unsafe { volatile_write64(process_state+1888,network_service_v5_state); } } }
        if process_ready!=0 && graphics_service_v5_state!=0 && input_event_v2_ready!=0 && completion_route_v4_ready!=0 && service_endpoint_v4_ready!=0 { graphics_service_v5_ready=graphics_service_v5_attach(graphics_service_v5_state,input_event_v2_state,completion_route_v4_state,service_endpoint_v4_state); if graphics_service_v5_ready!=0 { unsafe { volatile_write64(process_state+1896,graphics_service_v5_state); } } }
        if process_ready!=0 && device_namespace_v5_state!=0 && probe_dispatch_v3_ready!=0 && binding_tx_v3_ready!=0 && service_endpoint_v4_ready!=0 { device_namespace_v5_ready=device_namespace_v5_selftest(device_namespace_v5_state,probe_dispatch_v3_state,binding_tx_v3_state,service_endpoint_v4_state); if device_namespace_v5_ready!=0 { unsafe { volatile_write64(process_state+1904,device_namespace_v5_state); } } }
        if process_ready!=0 && service_route_v5_state!=0 && async_runtime_v4_ready!=0 && completion_route_v4_ready!=0 && error_route_v4_ready!=0 { service_route_v5_ready=service_route_v5_selftest(service_route_v5_state,async_runtime_v4_state,completion_route_v4_state,error_route_v4_state); if service_route_v5_ready!=0 { unsafe { volatile_write64(process_state+1912,service_route_v5_state); } } }
        if process_ready!=0 && service_integration_v5_state!=0 { unsafe { volatile_write64(process_state+1920,service_integration_v5_state); } service_integration_v5_ready=service_integration_v5_snapshot(service_integration_v5_state,process_state); }
        if process_ready!=0 && service_integration_gate_v5_state!=0 && async_runtime_gate_v4_ready!=0 && service_integration_v5_ready!=0 { unsafe { volatile_write64(process_state+1928,service_integration_gate_v5_state); } service_integration_gate_v5_ready=service_integration_gate_v5(service_integration_gate_v5_state,async_runtime_gate_v4_state,service_integration_v5_state); }
'''
if s.count(boot)!=1: raise SystemExit('boot anchor mismatch')
s=s.replace(boot,boot+extra_boot,1)
out=s.encode('utf-8'); p.write_bytes(out)
print('patched',p,'sha256',hashlib.sha256(out).hexdigest())
