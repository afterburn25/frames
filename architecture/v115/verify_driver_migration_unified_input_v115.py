#!/usr/bin/env python3
from pathlib import Path
import argparse,hashlib,json
p=argparse.ArgumentParser(); p.add_argument('--serial',required=True); p.add_argument('--require-pass',action='store_true'); a=p.parse_args()
raw=Path(a.serial).read_bytes(); text=raw.decode('utf-8','replace')
markers=['FRAMES_PS2_INGRESS_V8_OK','FRAMES_USB_HID_INGRESS_V8_OK','FRAMES_POINTER_OWNER_GUARD_V8_OK','FRAMES_INPUT_SEQUENCE_V8_OK','FRAMES_INPUT_DUP_FILTER_V8_OK','FRAMES_INPUT_STALE_FILTER_V8_OK','FRAMES_POINTER_NORMALIZE_V8_OK','FRAMES_INPUT_LEGACY_COMPARE_V8_OK','FRAMES_INPUT_DISPATCH_V8_OK','FRAMES_UNIFIED_INPUT_RUNTIME_V8_OK','FRAMES_INPUT_MIGRATION_SNAPSHOT_V8_OK','FRAMES_INPUT_MIGRATION_GATE_V8_OK']
counts={m:text.count(m) for m in markers}
checks={m:counts[m]>=1 for m in markers}
checks['v114_concurrency_gate']='FRAMES_CONCURRENCY_GATE_V7_OK' in text
checks['v113_hal_gate']='FRAMES_HAL_RUNTIME_GATE_V6_OK' in text
checks['v112_service_gate']='FRAMES_SERVICE_INTEGRATION_GATE_V5_OK' in text
checks['scheduler_sustained']='FRAMES_SCHEDULER_SUSTAINED' in text
status='PASS' if all(checks.values()) else 'FAIL'
out={'status':status,'profile':'frames-0.9.105-v115-driver-migration-unified-input-phase7','runtime_layers':12,'checks':checks,'marker_counts':counts,'serial_sha256':hashlib.sha256(raw).hexdigest(),'legacy_transport_retained':True,'physical_controller_register_programming_changed':False}
print(json.dumps(out,indent=2))
if a.require_pass and status!='PASS': raise SystemExit(1)
