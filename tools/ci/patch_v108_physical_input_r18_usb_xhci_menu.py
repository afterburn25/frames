#!/usr/bin/env python3
import hashlib,pathlib,subprocess,sys
root=pathlib.Path(__file__).resolve().parent
for name in [
    'patch_v108_r18_xhci_core.py',
    'patch_v108_r18_xhci_enum.py',
    'patch_v108_r18_menu_core.py',
    'patch_v108_r18_menu_runtime.py',
    'patch_v108_r18_abi_fix.py',
    'patch_v108_r18_telemetry.py',
]:
    subprocess.run([sys.executable,str(root/name),sys.argv[1]],check=True)
p=pathlib.Path(sys.argv[1])
print(hashlib.sha256(p.read_bytes()).hexdigest())
