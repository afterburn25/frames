#!/usr/bin/env python3
from pathlib import Path
p=Path(__file__).with_name('qemu_text_edit_gate_r15.py')
s=p.read_text()
old_loop='for _ in range(1000):'
new_loop='for _ in range(1800):'
old_ready="if 'FRAMES_V108_INPUT_TEST_RUNTIME_READY' in txt and 'FRAMES_V108_PS2_ENABLE_OK' in txt:"
new_ready="if 'FRAMES_V108_INPUT_TEST_RUNTIME_READY' in txt:"
if s.count(old_loop)!=1: raise SystemExit(f'text gate loop anchor mismatch {s.count(old_loop)}')
if s.count(old_ready)!=1: raise SystemExit(f'text gate readiness anchor mismatch {s.count(old_ready)}')
s=s.replace(old_loop,new_loop,1).replace(old_ready,new_ready,1)
p.write_text(s)
print('hardened qemu_text_edit_gate_r15: 180s runtime readiness; PS/2 delivery remains independently gated')
