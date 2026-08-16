# Frames v116 Physical Hardware Full-GUI Validation

This kit validates the exact VM/ISO-certified full interactive desktop candidate on real UEFI hardware. It does not modify the certified candidate and does not authorize destructive writes.

## Candidate identity

- Frames architecture/product label: `0.9.106 / v116`
- Certified GUI commit: `8a730a580b98026189eac897d0dec9efde58c07e`
- GitHub Actions run: `31923853583`
- ISO: `Frames-0.9.106-v116-Full-Interactive-Desktop-GUI-UEFI.iso`
- ISO SHA-256: `abeead78504b6562ee6ecef47027c95803594dd21527cfc3120205a5ef9b7068`
- ISO size: `67,160,064 bytes`
- Approved splash SHA-256: `70e9ca0c9e31b56b720f3cf0bd22c5eacc35b51797782ad0f03172c2038b9fbd`

Do not accept evidence from an ISO with a different SHA-256.

## Safety boundary

- Physical destructive writes are NOT certified by this image.
- Internal NVMe/SATA/system media must remain outside the destructive-write certification scope.
- `promotion_allowed` remains false.
- Frames 1.0 remains NOT promoted.

## Before boot

1. Verify the ISO with `verify-certified-iso.ps1` or another SHA-256 tool.
2. Write the exact ISO to sacrificial/removable test media using the user's normal trusted imaging method.
3. Boot the target machine in UEFI mode from that removable media.
4. Do not enable or add any destructive-write override/configuration.

## Required physical observations

Record PASS/FAIL for each item in `PHYSICAL-BOOT-REPORT.template.json`:

1. Firmware detects and launches the Frames boot media.
2. Approved Frames splash appears.
3. Kernel/desktop transition completes.
4. The boot reaches the full multi-window desktop, not the older dashboard shell.
5. File Manager is visibly open with content.
6. Settings is visibly open with content.
7. Nexus/terminal-style application window is visibly open.
8. Desktop/taskbar is visible.
9. Mouse cursor is visible.
10. Physical pointer movement changes the cursor position.
11. Pointer buttons can be exercised without a hang.
12. Keyboard input/focus can be exercised.
13. No unexpected reboot, freeze, panic, or destructive-write prompt appears.

## Minimum evidence

Capture at least:

- one photo of the approved splash on the physical machine;
- one clear photo of the final full desktop showing all three application windows;
- the completed physical boot report;
- a short note describing pointer movement and keyboard behavior.

If boot fails, capture the exact screen where progress stops. Do not keep retrying with modified boot settings unless the failure is understood; preserve the first clean failure as evidence.

## Pass condition

The physical milestone can pass only when the exact certified ISO hash boots on the real UEFI machine and the required desktop, pointer, and keyboard observations pass without crossing the write-safety boundary.

A QEMU/OVMF pass cannot substitute for this physical evidence.
