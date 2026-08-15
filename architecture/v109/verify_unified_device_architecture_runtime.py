#!/usr/bin/env python3
from pathlib import Path
import argparse,json,hashlib
p=argparse.ArgumentParser(); p.add_argument('--serial',required=True); p.add_argument('--require-pass',action='store_true'); a=p.parse_args()
raw=Path(a.serial).read_bytes(); text=raw.decode('utf-8','replace')
markers=['FRAMES_BUS_CORE_V2_OK','FRAMES_RESOURCE_CORE_V2_OK','FRAMES_IRQ_DOMAIN_V2_OK','FRAMES_WORK_QUEUE_V2_OK','FRAMES_IO_BROKER_V2_OK','FRAMES_DMA_MAP_V2_OK','FRAMES_DEVICE_GRAPH_V2_OK','FRAMES_DEVICE_LIFECYCLE_V2_OK','FRAMES_DRIVER_MATCH_V2_OK','FRAMES_USB_CORE_V2_OK','FRAMES_INPUT_CORE_V2_OK','FRAMES_COMPLETION_V2_OK','FRAMES_TIMER_QUEUE_V2_OK','FRAMES_PROBE_SCHED_V2_OK','FRAMES_PLATFORM_INVENTORY_V2_OK','FRAMES_USB_DESCRIPTOR_V2_OK','FRAMES_USB_TRANSFER_V2_OK','FRAMES_USB_ENUM_V2_OK','FRAMES_HID_CORE_V2_OK','FRAMES_INPUT_EVENT_V2_OK','FRAMES_ARCH_MANAGER_V2_OK','FRAMES_ARCH_PLATFORM_V2_OK']
counts={m:text.count(m) for m in markers}; checks={m:counts[m]>=1 for m in markers}; checks['legacy_driver_platform_gate']=text.count('FRAMES_DRIVER_PLATFORM_OK')>=1
status='PASS' if all(checks.values()) else 'FAIL'
out={'status':status,'profile':'frames-0.9.99-unified-device-driver-architecture-v2-runtime','base_version':'0.9.98','architecture_layers':20,'marker_counts':counts,'checks':checks,'serial_sha256':hashlib.sha256(raw).hexdigest(),'physical_pointer_fix_required':True,'physical_transport_behavior_changed_by_train':False}
print(json.dumps(out,indent=2))
if a.require_pass and status!='PASS': raise SystemExit(1)
