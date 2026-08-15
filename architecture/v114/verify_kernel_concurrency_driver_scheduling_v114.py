#!/usr/bin/env python3
from pathlib import Path
import argparse,hashlib,json
p=argparse.ArgumentParser(); p.add_argument('--serial',required=True); p.add_argument('--require-pass',action='store_true'); a=p.parse_args()
raw=Path(a.serial).read_bytes(); text=raw.decode('utf-8','replace')
markers=['FRAMES_WORKER_SCHED_V7_OK','FRAMES_IRQ_WORKER_V7_OK','FRAMES_LOCK_OWNER_V7_OK','FRAMES_WAIT_WAKE_V7_OK','FRAMES_CANCEL_ARB_V7_OK','FRAMES_TX_SERIAL_V7_OK','FRAMES_COMPLETION_ORDER_V7_OK','FRAMES_DRIVER_FAIRNESS_V7_OK','FRAMES_DEADLOCK_GUARD_V7_OK','FRAMES_DEVICE_TX_V7_OK','FRAMES_CONCURRENCY_RUNTIME_V7_OK','FRAMES_CONCURRENCY_GATE_V7_OK']
counts={m:text.count(m) for m in markers}
checks={m:counts[m]>=1 for m in markers}
checks['v113_hal_gate']='FRAMES_HAL_RUNTIME_GATE_V6_OK' in text
checks['v112_service_gate']='FRAMES_SERVICE_INTEGRATION_GATE_V5_OK' in text
checks['v111_async_gate']='FRAMES_ASYNC_RUNTIME_GATE_V4_OK' in text
checks['scheduler_sustained']='FRAMES_SCHEDULER_SUSTAINED' in text
status='PASS' if all(checks.values()) else 'FAIL'
out={'status':status,'profile':'frames-0.9.104-v114-kernel-concurrency-driver-scheduling-phase6','runtime_layers':12,'checks':checks,'marker_counts':counts,'serial_sha256':hashlib.sha256(raw).hexdigest(),'physical_transport_behavior_changed':False}
print(json.dumps(out,indent=2))
if a.require_pass and status!='PASS': raise SystemExit(1)
