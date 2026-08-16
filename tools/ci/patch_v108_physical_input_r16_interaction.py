#!/usr/bin/env python3
from pathlib import Path
import base64

parts = Path(__file__).resolve().parent / 'r16_patch_b64'
source = b''.join(base64.b64decode((parts / f'part{i}.b64').read_text().strip()) for i in range(1, 5))
exec(compile(source, 'patch_v108_physical_input_r16_interaction_embedded.py', 'exec'), {'__name__': '__main__', '__file__': __file__})
