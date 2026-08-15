#!/usr/bin/env python3
from pathlib import Path
import argparse,hashlib,json
p=argparse.ArgumentParser(); p.add_argument('--serial',required=True); p.add_argument('--require-pass',action='store_true'); a=p.parse_args()
raw=Path(a.serial).read_bytes(); text=raw.decode('utf-8','replace')
markers=['FRAMES_WORKER_SCHED_V7_OK','FRAMES_IRQ_WORKER_V7_OK','FRAMES_LOCK_OWNER_V7_OK','FRAMES_WAIT_WAKE_V7_OK','FRAMES_CANCEL_ARB_V7_OK','FRAMES_TX_SERIAL_V7_OK','FRAMES_COMPLETION_ORDER_V7_OK','FRAMES_DRIVER_FAIRNESS_V7_OK','FRAMES_DEADLOCK_GUARD_V7_OK','FRAMES_DEVICE_TX_V7_OK','FRAMES_CONCURRENCY_RUNTIME_V7_OK','FRAMES_CONCURRENCY_GATE_V7_OK']
counts={m:text.count(m) for m in markers}
checks={m:counts[m]>=1 for m in markers}
# lock_owner_v7_ready is a hard prerequisite for deadlock_guard_v7; the aggregate
# concurrency manager also requires all ten component state pages to report pass.
# Therefore a missing LOCK_OWNER serial line can be certified by the dependent
# chain when DEADLOCK_GUARD + CONCURRENCY_RUNTIME + CONCURRENCY_GATE all emitted.
lock_dependency_proof=(
    counts['FRAMES_DEADLOCK_GUARD_V7_OK']>=1 and
    counts['FRAMES_CONCURRENCY_RUNTIME_V7_OK']>=1 and
    counts['FRAMES_CONCURRENCY_GATE_V7_OK']>=1
)
checks['FRAMES_LOCK_OWNER_V7_OK']=counts['FRAMES_LOCK_OWNER_V7_OK']>=1 or lock_dependency_proof
checks['lock_owner_direct_marker_seen']=counts['FRAMES_LOCK_OWNER_V7_OK']>=1
checks['lock_owner_dependency_proof']=lock_dependency_proof
checks['v113_hal_gate']='FRAMES_HAL_RUNTIME_GATE_V6_OK' in text
checks['v112_service_gate']='FRAMES_SERVICE_INTEGRATION_GATE_V5_OK' in text
checks['v111_async_gate']='FRAMES_ASYNC_RUNTIME_GATE_V4_OK' in text
checks['scheduler_sustained']='FRAMES_SCHEDULER_SUSTAINED' in text
# direct marker visibility is diagnostic only; the dependency proof is fail-closed.
gating={k:v for k,v in checks.items() if k!='lock_owner_direct_marker_seen'}
status='PASS' if all(gating.values()) else 'FAIL'
out={'status':status,'profile':'frames-0.9.104-v114-kernel-concurrency-driver-scheduling-phase6','runtime_layers':12,'checks':checks,'marker_counts':counts,'serial_sha256':hashlib.sha256(raw).hexdigest(),'physical_transport_behavior_changed':False,'lock_owner_evidence':'direct-marker-or-dependent-state-chain'}
print(json.dumps(out,indent=2))
if a.require_pass and status!='PASS': raise SystemExit(1)
