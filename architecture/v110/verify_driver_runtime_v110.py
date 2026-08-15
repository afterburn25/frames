#!/usr/bin/env python3
from pathlib import Path
import argparse,hashlib,json
p=argparse.ArgumentParser(); p.add_argument('--serial',required=True); p.add_argument('--require-pass',action='store_true'); a=p.parse_args()
raw=Path(a.serial).read_bytes(); text=raw.decode('utf-8','replace')
markers=['FRAMES_PROBE_DISPATCH_V3_OK','FRAMES_BIND_TX_V3_OK','FRAMES_RESOURCE_OWNER_V3_OK','FRAMES_USB_SERVICE_GRAPH_V3_OK','FRAMES_INPUT_BRIDGE_V3_OK','FRAMES_HOTPLUG_QUEUE_V3_OK','FRAMES_POWER_TRANSITION_V3_OK','FRAMES_DRIVER_RECOVERY_V3_OK','FRAMES_DRIVER_RUNTIME_V3_OK','FRAMES_DRIVER_RUNTIME_GATE_V3_OK']
counts={m:text.count(m) for m in markers}
checks={m:counts[m]>=1 for m in markers}
checks['v109_architecture_gate']='FRAMES_ARCH_PLATFORM_V2_OK' in text
checks['legacy_driver_platform_gate']='FRAMES_DRIVER_PLATFORM_OK' in text
checks['scheduler_sustained']='FRAMES_SCHEDULER_SUSTAINED' in text
status='PASS' if all(checks.values()) else 'FAIL'
out={'status':status,'profile':'frames-0.9.100-v110-unified-driver-runtime-phase2','runtime_layers':10,'checks':checks,'marker_counts':counts,'serial_sha256':hashlib.sha256(raw).hexdigest(),'physical_transport_behavior_changed':False}
print(json.dumps(out,indent=2))
if a.require_pass and status!='PASS': raise SystemExit(1)
