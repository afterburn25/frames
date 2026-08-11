# Frames 0.9.9 Runtime Certification Kit

This kit is the external runtime handoff for the Frames 0.9.9 final pre-1.0 gate.

## What it does
- Boots the Frames EFI media under QEMU/OVMF.
- Attaches an emulated xHCI controller and USB keyboard for the input path.
- Uses a per-run writable copy of OVMF VARS when a VARS template is supplied.
- Captures the serial log and derives runtime/storage evidence JSON.
- Never converts source/static verification into runtime or physical-hardware PASS evidence.

## GitHub Actions path
The complete Frames source archive already contains `.github/workflows/frames-runtime-certify.yml` and a bundled Nexus 5.15.0 toolchain. Put the extracted source tree in a GitHub repository and run the `Frames Runtime Certification` workflow (or push to `main`). The workflow installs QEMU/OVMF, builds the source, runs `tools/qemu_certify.sh`, and uploads runtime evidence.

## Local path
Required tools: Python 3, clang, lld-link, QEMU x86-64 and OVMF firmware.

From the Frames 0.9.9 source root:

```bash
export OVMF_CODE=/path/to/OVMF_CODE.fd
export OVMF_VARS=/path/to/OVMF_VARS.fd   # optional but recommended
./tools/qemu_certify.sh
```

Expected evidence is written below `build/`, including the serial log and certification JSON.

## Promotion policy
A QEMU PASS is necessary but is not physical-machine certification. Frames 1.0 remains blocked until the final pre-1.0 gate has all required external subsystem certification and stress/fault records. Physical boot remains diagnostic-only until that evidence exists.
