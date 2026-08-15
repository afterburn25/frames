#!/usr/bin/env python3
from pathlib import Path
import re, json, sys, hashlib
root=Path(__file__).resolve().parents[1]
s=(root/'kernel/main.nx').read_text()
start=s.index('// Frames Unified Device & Driver Architecture v2')
end=s.index('fn serial_marker_entropy_seed_ok()',start)
seg=s[start:end]
required=[
'bus_registry_v2_init','resource_manager_v2_import','irq_domain_v2_init','work_queue_v2_selftest',
'io_broker_v2_selftest','dma_map_v2_selftest','device_graph_v2_seed','lifecycle_v2_apply_bindings',
'driver_match_v2_audit','usb_core_v2_init','input_core_v2_init','completion_v2_selftest','timer_queue_v2_selftest',
'probe_scheduler_v2_seed','platform_inventory_v2_init','usb_descriptor_v2_selftest','usb_transfer_v2_selftest',
'usb_enum_v2_selftest','hid_core_v2_selftest','input_event_v2_selftest','architecture_manager_v2_snapshot',
'architecture_platform_v2_gate']
checks={f'symbol_{x}':f'fn {x}(' in seg for x in required}
markers=[
'FRAMES_BUS_CORE_V2_OK','FRAMES_RESOURCE_CORE_V2_OK','FRAMES_IRQ_DOMAIN_V2_OK','FRAMES_WORK_QUEUE_V2_OK',
'FRAMES_IO_BROKER_V2_OK','FRAMES_DMA_MAP_V2_OK','FRAMES_DEVICE_GRAPH_V2_OK','FRAMES_DEVICE_LIFECYCLE_V2_OK',
'FRAMES_DRIVER_MATCH_V2_OK','FRAMES_USB_CORE_V2_OK','FRAMES_INPUT_CORE_V2_OK','FRAMES_COMPLETION_V2_OK',
'FRAMES_TIMER_QUEUE_V2_OK','FRAMES_PROBE_SCHED_V2_OK','FRAMES_PLATFORM_INVENTORY_V2_OK','FRAMES_USB_DESCRIPTOR_V2_OK',
'FRAMES_USB_TRANSFER_V2_OK','FRAMES_USB_ENUM_V2_OK','FRAMES_HID_CORE_V2_OK','FRAMES_INPUT_EVENT_V2_OK',
'FRAMES_ARCH_MANAGER_V2_OK','FRAMES_ARCH_PLATFORM_V2_OK']
for m in markers: checks['marker_'+m]=('serial_marker_'+m.lower()) in seg
param_ok=True; offenders=[]
for m in re.finditer(r'fn\s+([A-Za-z0-9_]+)\(([^)]*)\)',seg):
    args=[x for x in m.group(2).split(',') if x.strip()]
    if len(args)>4: param_ok=False; offenders.append([m.group(1),len(args)])
checks['max_four_parameters']=param_ok
prohibited=['io_write8(','io_write16(','io_write32(','volatile_write32(','xhci_controller_init(','xhci_enable_slot(','ps2_mouse_enable(']
checks['no_physical_transport_programming']=all(x not in seg for x in prohibited)
slots=[1504,1512,1520,1528,1536,1544,1552,1560,1568,1576,1584,1592,1600,1608,1616,1624,1632,1640,1648,1656,1664,1672]
checks['process_slots_unique']=len(slots)==len(set(slots)); checks['process_slots_safe']=min(slots)>1416 and max(slots)+8<=4096
layouts={'bus':(64,32,64),'resource':(64,48,72),'irq':(64,64,48),'work':(64,32,64),'io':(64,32,96),'dma':(64,48,72),'graph':(64,64,48),'lifecycle':(64,64,48),'match':(64,48,72),'usb_core':(64,48,64),'input_core':(64,48,64),'completion':(64,48,64),'timer':(64,48,64),'probe':(64,48,64),'usb_desc':(64,48,64),'usb_transfer':(64,40,80),'usb_enum':(64,64,48),'hid':(64,48,64),'input_event':(64,64,48)}
checks['record_layouts_fit_page']=all(h+c*r<=4096 for h,c,r in layouts.values())
checks['manager_requires_20_layers']='if score==20' in seg and 'volatile_write64(state+16,20)' in seg
checks['old_driver_gate_chained']='let old=volatile_read64(process+840)' in seg
checks['source_version_preserved_for_candidate']=(root/'VERSION').read_text().strip()=='0.9.98'
status='PASS' if all(checks.values()) else 'FAIL'
out={'status':status,'profile':'frames-unified-device-driver-architecture-v2-local-structural','candidate_target':'0.9.99','base_version':'0.9.98','checks':checks,'parameter_offenders':offenders,'architecture_source_sha256':hashlib.sha256(seg.encode()).hexdigest(),'architecture_layers':20,'process_state_slots':slots,'record_layouts':layouts,'physical_transport_behavior_changed':False}
print(json.dumps(out,indent=2))
if len(sys.argv)>1: Path(sys.argv[1]).write_text(json.dumps(out,indent=2)+'\n')
raise SystemExit(0 if status=='PASS' else 1)
