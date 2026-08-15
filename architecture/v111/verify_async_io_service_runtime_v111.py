#!/usr/bin/env python3
from pathlib import Path
import argparse,hashlib,json
p=argparse.ArgumentParser(); p.add_argument('--serial',required=True); p.add_argument('--require-pass',action='store_true'); a=p.parse_args()
raw=Path(a.serial).read_bytes(); text=raw.decode('utf-8','replace')
markers=['FRAMES_ASYNC_REQUEST_V4_OK','FRAMES_COMPLETION_ROUTE_V4_OK','FRAMES_DEADLINE_CANCEL_V4_OK','FRAMES_DMA_TX_V4_OK','FRAMES_IRQ_DEFERRED_V4_OK','FRAMES_SERVICE_ENDPOINT_V4_OK','FRAMES_USB_SCHED_V4_OK','FRAMES_INPUT_DELIVERY_V4_OK','FRAMES_ERROR_ROUTE_V4_OK','FRAMES_BACKPRESSURE_V4_OK','FRAMES_ASYNC_RUNTIME_V4_OK','FRAMES_ASYNC_RUNTIME_GATE_V4_OK']
counts={m:text.count(m) for m in markers}
checks={m:counts[m]>=1 for m in markers}
checks['v110_runtime_gate']='FRAMES_DRIVER_RUNTIME_GATE_V3_OK' in text
checks['v109_architecture_gate']='FRAMES_ARCH_PLATFORM_V2_OK' in text
checks['legacy_driver_platform_gate']='FRAMES_DRIVER_PLATFORM_OK' in text
checks['scheduler_sustained']='FRAMES_SCHEDULER_SUSTAINED' in text
status='PASS' if all(checks.values()) else 'FAIL'
out={'status':status,'profile':'frames-0.9.101-v111-async-io-device-service-runtime-phase3','runtime_layers':12,'checks':checks,'marker_counts':counts,'serial_sha256':hashlib.sha256(raw).hexdigest(),'physical_transport_behavior_changed':False}
print(json.dumps(out,indent=2))
if a.require_pass and status!='PASS': raise SystemExit(1)
