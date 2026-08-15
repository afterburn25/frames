#!/usr/bin/env python3
from pathlib import Path
import argparse,hashlib,json
p=argparse.ArgumentParser()
p.add_argument('--serial',required=True)
p.add_argument('--require-pass',action='store_true')
a=p.parse_args()
raw=Path(a.serial).read_bytes()
text=raw.decode('utf-8','replace')
markers=[
'FRAMES_XHCI_OWNER_V9_OK','FRAMES_XHCI_COMMAND_RING_V9_OK','FRAMES_XHCI_EVENT_RING_V9_OK',
'FRAMES_XHCI_PORT_LIFECYCLE_V9_OK','FRAMES_XHCI_SLOT_ADDRESS_V9_OK','FRAMES_USB_DESCRIPTOR_XFER_V9_OK',
'FRAMES_USB_INTERRUPT_SCHED_V9_OK','FRAMES_USB_TRANSFER_COMPLETE_V9_OK','FRAMES_USB_HID_DELIVERY_V9_OK',
'FRAMES_USB_LEGACY_COMPARE_V9_OK','FRAMES_USB_MIGRATION_RUNTIME_V9_OK','FRAMES_USB_MIGRATION_GATE_V9_OK']
counts={m:text.count(m) for m in markers}
checks={m:counts[m]>=1 for m in markers}
checks['v115_input_gate']='FRAMES_INPUT_MIGRATION_GATE_V8_OK' in text
checks['v114_concurrency_gate']='FRAMES_CONCURRENCY_GATE_V7_OK' in text
checks['v113_hal_gate']='FRAMES_HAL_RUNTIME_GATE_V6_OK' in text
checks['scheduler_sustained']='FRAMES_SCHEDULER_SUSTAINED' in text
status='PASS' if all(checks.values()) else 'FAIL'
out={'status':status,'profile':'frames-0.9.106-v116-usb-core-xhci-driver-migration-phase8','runtime_layers':12,'checks':checks,'marker_counts':counts,'serial_sha256':hashlib.sha256(raw).hexdigest(),'legacy_usb_diagnostics_retained':True,'unified_input_handoff_required':True}
print(json.dumps(out,indent=2))
if a.require_pass and status!='PASS':
    raise SystemExit(1)
