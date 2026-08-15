#!/usr/bin/env python3
from pathlib import Path
import argparse,hashlib,json
p=argparse.ArgumentParser(); p.add_argument('--serial',required=True); p.add_argument('--require-pass',action='store_true'); a=p.parse_args()
raw=Path(a.serial).read_bytes(); text=raw.decode('utf-8','replace')
markers=['FRAMES_HAL_MMIO_V6_OK','FRAMES_HAL_IRQ_V6_OK','FRAMES_HAL_DMA_V6_OK','FRAMES_DRIVER_EXEC_V6_OK','FRAMES_CONTROLLER_QUEUE_V6_OK','FRAMES_USB_HAL_V6_OK','FRAMES_INPUT_HAL_V6_OK','FRAMES_STORAGE_HAL_V6_OK','FRAMES_NETWORK_HAL_V6_OK','FRAMES_GRAPHICS_HAL_V6_OK','FRAMES_HAL_RUNTIME_V6_OK','FRAMES_HAL_RUNTIME_GATE_V6_OK']
counts={m:text.count(m) for m in markers}
checks={m:counts[m]>=1 for m in markers}
checks['v112_integration_gate']='FRAMES_SERVICE_INTEGRATION_GATE_V5_OK' in text
checks['v111_async_gate']='FRAMES_ASYNC_RUNTIME_GATE_V4_OK' in text
checks['v110_driver_runtime_gate']='FRAMES_DRIVER_RUNTIME_GATE_V3_OK' in text
checks['v109_architecture_gate']='FRAMES_ARCH_PLATFORM_V2_OK' in text
checks['legacy_driver_platform_gate']='FRAMES_DRIVER_PLATFORM_OK' in text
checks['scheduler_sustained']='FRAMES_SCHEDULER_SUSTAINED' in text
status='PASS' if all(checks.values()) else 'FAIL'
out={'status':status,'profile':'frames-0.9.103-v113-driver-execution-hardware-abstraction-phase5','runtime_layers':12,'checks':checks,'marker_counts':counts,'serial_sha256':hashlib.sha256(raw).hexdigest(),'physical_transport_behavior_changed':False,'controller_register_programming_added':False}
print(json.dumps(out,indent=2))
if a.require_pass and status!='PASS': raise SystemExit(1)
