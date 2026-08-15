#!/usr/bin/env python3
from pathlib import Path
import argparse,hashlib,json
p=argparse.ArgumentParser(); p.add_argument('--serial',required=True); p.add_argument('--require-pass',action='store_true'); a=p.parse_args()
raw=Path(a.serial).read_bytes(); text=raw.decode('utf-8','replace')
markers=['FRAMES_PCI_SERVICE_V5_OK','FRAMES_USB_SERVICE_V5_OK','FRAMES_PS2_INPUT_SERVICE_V5_OK','FRAMES_STORAGE_SERVICE_V5_OK','FRAMES_NETWORK_SERVICE_V5_OK','FRAMES_GRAPHICS_SERVICE_V5_OK','FRAMES_DEVICE_NAMESPACE_V5_OK','FRAMES_SERVICE_ROUTE_V5_OK','FRAMES_SERVICE_INTEGRATION_V5_OK','FRAMES_SERVICE_INTEGRATION_GATE_V5_OK']
counts={m:text.count(m) for m in markers}
checks={m:counts[m]>=1 for m in markers}
checks['v111_async_gate']='FRAMES_ASYNC_RUNTIME_GATE_V4_OK' in text
checks['v110_driver_gate']='FRAMES_DRIVER_RUNTIME_GATE_V3_OK' in text
checks['v109_architecture_gate']='FRAMES_ARCH_PLATFORM_V2_OK' in text
checks['legacy_driver_platform_gate']='FRAMES_DRIVER_PLATFORM_OK' in text
checks['scheduler_sustained']='FRAMES_SCHEDULER_SUSTAINED' in text
status='PASS' if all(checks.values()) else 'FAIL'
out={'status':status,'profile':'frames-0.9.102-v112-device-service-integration-phase4','integration_layers':10,'checks':checks,'marker_counts':counts,'serial_sha256':hashlib.sha256(raw).hexdigest(),'physical_transport_behavior_changed':False}
print(json.dumps(out,indent=2))
if a.require_pass and status!='PASS': raise SystemExit(1)
