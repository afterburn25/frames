# Frames — Canonical Project State

> This file is the authoritative cross-chat handoff for active Frames engineering.
> When chat memory, summaries, prior messages, or assumptions disagree with this file and current repository/evidence, the repository/evidence wins.

Last updated: 2026-08-16

## Project identity

- Frames is an independent operating system, not Windows-based and not Linux-based.
- Native systems language/toolchain: Nexus.
- Boot chain: UEFI -> BOOTX64.EFI -> FramesKernel.fkrn.
- Native application formats: FEX/FAPP.
- Evidence model: fail-closed, exact-source/hash based, QEMU/OVMF-first.
- Frames 1.0 is NOT promoted.

## Current architecture baseline

- Frames 0.9.106 / architecture v116 is the current certified architecture baseline for active GUI/boot work.
- v109-v116 transforms are preserved/hash-checked before product-integration changes.
- Frames 0.9.98 v108 r9 remains the sealed reconstruction source used by current integration workflows.

## GUI classification correction

The older dashboard/home-shell physical-test ISO is NOT a full desktop GUI. It is only an integrated desktop-shell / GUI-infrastructure proof and is superseded.

## Completed milestone — Full Interactive Desktop GUI

Branch: `full-interactive-desktop-gui`

Certified GUI commit: `8a730a580b98026189eac897d0dec9efde58c07e`

Workflow: `.github/workflows/frames-v116-full-interactive-desktop-gui.yml`

Successful run: `31923853583`

Result: **PASS** after independent artifact inspection.

The actual QEMU framebuffer visibly proves a real multi-window desktop:

- three distinct native window-manager title bars/controls;
- File Manager visibly open with content;
- Settings visibly open with Appearance/Themes/Wallpaper/Fonts/Cursor/Lock Screen content;
- separate Nexus/terminal-style window;
- desktop icons/background;
- bottom taskbar/dock;
- visible mouse cursor;
- splash -> kernel -> full desktop transition at 1280x800.

Required runtime markers include `FRAMES_FULL_GUI_WINDOWS_OK`, `FRAMES_FULL_GUI_INPUT_OK`, `FRAMES_FULL_GUI_FILEMAN_OK`, `FRAMES_FULL_GUI_SETTINGS_OK`, `FRAMES_FULL_INTERACTIVE_DESKTOP_OK`, `FRAMES_INTEGRATED_GUI_OK`, and `FRAMES_GUI_PHYSICAL_TEST_READY`. `FRAMES_DESKTOP_CERT_FAIL` is absent.

## Superseded full-GUI ISO

The first full-GUI ISO remains valid QEMU evidence but is superseded for physical testing:

- filename: `Frames-0.9.106-v116-Full-Interactive-Desktop-GUI-UEFI.iso`
- SHA-256: `abeead78504b6562ee6ecef47027c95803594dd21527cfc3120205a5ef9b7068`
- size: `67,160,064 bytes`
- run: `31923853583`

Reason for supersession: it booted correctly through El Torito/OVMF but did not expose a duplicate ISO-level `/EFI/BOOT` tree for broad extraction-based USB authoring.

## Current physical-test candidate — USB-compatible full GUI

Branch: `physical-hardware-full-gui-validation`

Physical-media compatibility workflow: `.github/workflows/frames-v116-full-gui-physical-media-compatibility.yml`

Successful media compatibility run: `31924483046`

Candidate ISO:

`Frames-0.9.106-v116-Full-Interactive-Desktop-GUI-USB-Compatible-UEFI.iso`

SHA-256:

`7d1c212ad71778a84579e91c2e12ebafe3801a8bcd8a0a0856e506d47ebe20c7`

Exact size:

`67,401,728 bytes`

ISO artifact:

- artifact ID: `9257407968`
- artifact ZIP SHA-256: `1097752e9b03e8619728d26e07365a3e3b5897db7a956818e698680e2f533cee`

Media-compat evidence:

- artifact ID: `9257408367`
- artifact ZIP SHA-256: `e13cff8e729613547afab7895e65d66563c2bd96ac2881f53edb90f348bd15b1`
- independent ZIP integrity PASS
- every `EVIDENCE-FILES-SHA256.txt` entry PASS
- `FINAL-PHYSICAL-MEDIA-CERTIFICATION.json`: PASS

The USB-compatible ISO preserves the exact certified EFI/GUI payload, exposes ISO-level `/EFI/BOOT/BOOTX64.EFI` and complete `/FRAMES` boot/GUI files, removes the prior missing-`/EFI/BOOT` compatibility warning, and boots in QEMU/OVMF to the same full three-window desktop.

## Extracted USB boot proof

Workflow: `.github/workflows/frames-v116-full-gui-extracted-usb-proof.yml`

Initial run `31924578354` failed before QEMU because `cp -a` attempted to preserve Unix ownership on FAT32. This was a harness-only failure and was repaired.

Repair commit: `caba0a2af1f6b32805d2319a340a14bc9e58704d`

Successful run: `31924646428`

Result: **PASS**.

The workflow:

1. downloads exact ISO SHA-256 `7d1c212a...e20c7`;
2. extracts only the ISO filesystem tree;
3. creates a fresh 128 MiB GPT disk with FAT32 EFI System Partition;
4. copies only exposed `/EFI` and `/FRAMES` files to that removable image;
5. attaches it to QEMU through xHCI + USB mass storage;
6. boots OVMF from that USB device;
7. proves approved splash -> kernel -> same full multi-window desktop.

Extracted-USB evidence artifact:

- artifact ID: `9257455438`
- artifact ZIP SHA-256: `bba4f4bb95bdcfde3a937363d19bd548e5e733257537e25c65a69d600a2c5ea5`
- independent ZIP integrity PASS
- every evidence manifest entry PASS
- `FINAL-EXTRACTED-USB-CERTIFICATION.json`: PASS
- `physical_test_allowed: true`
- `physical_destructive_writes_certified: false`
- `promotion_allowed: false`

This proves both DVD/El Torito boot and extraction-style UEFI USB boot in QEMU.

## Approved splash identity

Approved splash asset SHA-256:

`70e9ca0c9e31b56b720f3cf0bd22c5eacc35b51797782ad0f03172c2038b9fbd`

The current physical candidate preserves this exact splash.

## Active milestone

**Physical Hardware Full-GUI Boot Validation**

Current objective:

Boot exact ISO SHA-256 `7d1c212ad71778a84579e91c2e12ebafe3801a8bcd8a0a0856e506d47ebe20c7` on the user's physical UEFI test machine and verify real hardware reaches the approved splash -> kernel -> full multi-window desktop path.

Physical validation must confirm at minimum:

1. UEFI detects and launches the removable media.
2. Approved splash appears.
3. Full multi-window desktop appears rather than the old dashboard shell.
4. File Manager, Settings, and Nexus/terminal window are visible.
5. Mouse cursor is visible and real pointer movement works.
6. Pointer buttons can be exercised.
7. Keyboard focus/input works.
8. No unexpected freeze/panic/reboot/destructive-write prompt occurs.

This is now the only remaining gate that requires the user's physical machine; QEMU cannot substitute for real-hardware evidence.

## Physical safety policy

- Physical destructive writes remain uncertified/blocked.
- Internal NVMe/SATA/system media remain outside destructive-write certification scope.
- `promotion_allowed` remains false.
- Frames 1.0 remains NOT promoted.

## Automatic progression rule

For Frames engineering:

- Failure -> inspect evidence -> make narrow repair -> rerun automatically.
- Success -> independently verify -> update this file -> continue to next defined milestone automatically.
- Do not stop merely to report a routine failure or intermediate pass.
- Stop only when user input/authorization is genuinely required, a safety boundary requires it, or the next action requires physical hardware ChatGPT cannot operate.

## New-chat startup rule

Before Frames engineering changes in a new chat:

1. Read `PROJECT_STATE.md`.
2. Read `CONTINUITY_PROTOCOL.md`.
3. Inspect active branch/run/evidence named here.
4. Do not let older chat summaries override repository/evidence.
5. Update this file whenever active milestone, baseline, decisive failure, approved artifact, safety boundary, or next action changes.
