# Frames Physical-Fix Handoff Policy

Every Frames fix intended for real-hardware testing must end with a sealed physical-test handoff when its VM/evidence gates pass.

Required handoff artifacts:

1. A direct Rufus-compatible UEFI ISO whose filename ends in `-Rufus-UEFI.iso`.
2. `ISO-SHA256.txt` containing the exact SHA-256 of that ISO.
3. `CERTIFICATION.txt` stating the VM/evidence status, physical-test status, safety/write policy, and the purpose of the build.
4. When the fix requires a dedicated writable or diagnostic USB layout, a separate `.img` file plus its SHA-256 file. The ISO and writable image must not be conflated.

Rules:

- Do not hand off an ISO as certified if its required gates failed.
- A VM-certified physical candidate remains `PENDING_PHYSICAL` until tested on real hardware.
- Internal NVMe/SATA/system/ESP write restrictions remain in force unless an explicit controlled-write certification authorizes a specific target and range.
- The Rufus ISO must preserve the normal Frames UEFI boot path (`UEFI -> BOOTX64.EFI -> FramesKernel.fkrn`).
- Every subsequent bootable physical repair revision (input, USB, graphics, storage, networking, audio, power, installer, recovery, and later hardware fixes) must use this same handoff format.
- Diagnostic-only source changes that are not bootable do not require an ISO, but the first bootable candidate containing them does.

The reusable CI validator is `tools/ci/validate_physical_handoff.py`.
