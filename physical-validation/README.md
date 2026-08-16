# Frames v116 Physical Hardware Full-GUI Validation

This kit validates the current USB-compatible, VM/ISO-certified full interactive desktop candidate on real UEFI hardware. It does not authorize destructive writes.

## Candidate identity

- Frames architecture/product label: `0.9.106 / v116`
- Full-GUI source commit: `8a730a580b98026189eac897d0dec9efde58c07e`
- Full-GUI baseline run: `31923853583`
- Physical-media compatibility run: `31924483046`
- Extracted xHCI USB proof run: `31924646428`
- ISO: `Frames-0.9.106-v116-Full-Interactive-Desktop-GUI-USB-Compatible-UEFI.iso`
- ISO SHA-256: `7d1c212ad71778a84579e91c2e12ebafe3801a8bcd8a0a0856e506d47ebe20c7`
- ISO size: `67,401,728 bytes`
- Approved splash SHA-256: `70e9ca0c9e31b56b720f3cf0bd22c5eacc35b51797782ad0f03172c2038b9fbd`

Do not accept physical evidence from an ISO with a different SHA-256.

## Automated evidence already complete

The candidate has passed all of the following before physical testing:

1. UEFI El Torito ISO boot in QEMU/OVMF.
2. Approved splash -> kernel -> full three-window GUI transition.
3. ISO-level `/EFI/BOOT/BOOTX64.EFI` tree present.
4. ISO-level complete `/FRAMES` boot/GUI payload present.
5. ISO-level files are byte-identical to the certified EFI payload.
6. Fresh GPT/FAT32 removable image constructed only from the ISO-level files.
7. That fresh image booted through virtual xHCI USB mass storage to the same full GUI.
8. `FRAMES_FULL_INTERACTIVE_DESKTOP_OK` and `FRAMES_INTEGRATED_GUI_OK` present.
9. `FRAMES_DESKTOP_CERT_FAIL` absent.

## Safety boundary

- Physical destructive writes are NOT certified by this image.
- Internal NVMe/SATA/system media must remain outside destructive-write certification scope.
- `promotion_allowed` remains false.
- Frames 1.0 remains NOT promoted.

## Before boot

1. Verify the ISO with `verify-certified-iso.ps1` or another SHA-256 tool.
2. Write the exact ISO to sacrificial/removable test media using a trusted imaging/extraction method.
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

## Minimum physical evidence

Capture at least one photo of the approved splash and one clear photo of the final desktop. If boot fails, preserve the first clean failure screen as evidence.

## Pass condition

The physical milestone can pass only when this exact ISO hash boots on the real UEFI machine and the required desktop, pointer, and keyboard observations pass without crossing the write-safety boundary.
