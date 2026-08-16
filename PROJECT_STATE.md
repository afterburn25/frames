# Frames — Canonical Project State

> This file is the authoritative cross-chat handoff for active Frames engineering.
> When chat memory, summaries, prior messages, or assumptions disagree with this file and current repository/evidence, the repository/evidence wins.

Last updated: 2026-08-16

## Project identity

- Frames is an independent operating system, not Windows-based and not Linux-based.
- Native systems language/toolchain: Nexus.
- Boot chain: UEFI -> BOOTX64.EFI -> FramesKernel.fkrn.
- Native application formats: FEX/FAPP.
- Evidence model: fail-closed, exact-source/hash based, QEMU/OVMF-first, no promotion from a merely green workflow.
- Frames 1.0 is NOT promoted.

## Current architecture baseline

- Frames 0.9.106 / architecture v116 is the current certified architecture baseline for the active GUI/boot work.
- v109-v116 architecture transforms are preserved and hash-checked before product-integration changes.
- Historical Frames 0.9.98 v108 r9 remains the sealed source reconstruction baseline used by the current integration workflows.

## Important correction to prior GUI claims

The earlier physical-test ISO that showed the Frames dashboard/home shell is NOT a full desktop GUI.

It is classified only as an integrated desktop-shell / GUI-infrastructure proof and is superseded for GUI physical testing by the independently verified full-interactive desktop candidate below.

Do not call the older dashboard artifact a full GUI, full desktop, finished desktop, or equivalent.

## Completed milestone — Full Interactive Desktop GUI VM/ISO gate

Branch:

`full-interactive-desktop-gui`

Certified candidate commit:

`8a730a580b98026189eac897d0dec9efde58c07e`

Workflow:

`.github/workflows/frames-v116-full-interactive-desktop-gui.yml`

Successful run:

`31923853583`

Result: **PASS** after independent artifact inspection.

The exact candidate visibly demonstrates a real multi-window desktop session rather than the prior dashboard shell.

Verified user-visible framebuffer properties:

1. Three distinct native window-manager title-bar close-control components are visibly present.
2. File Manager is visibly open with file/folder content.
3. Settings is visibly open with Appearance/Themes/Wallpaper/Fonts/Cursor/Lock Screen content.
4. A separate Nexus/terminal-style application window is visibly open.
5. Desktop icons and background are visible.
6. Bottom taskbar/dock is visible.
7. Mouse cursor is visible.
8. The image contains rich content on both left and right desktop regions.
9. Approved splash -> kernel -> full desktop transition is visually proven at 1280x800.
10. Raw-ESP and exact-ISO framebuffer verifiers both PASS.

Raw/ISO visual verifier metrics:

- `distinct_window_controls = 3`
- `bottom_quantized_color_diversity = 45`
- `center_quantized_color_diversity = 17`
- `left_nonflat_score = 0.8708`
- `right_nonflat_score = 0.8422`
- splash-to-GUI `changed_ratio = 1.0`
- splash-to-GUI `quantized_unique_colors = 176`

Required runtime evidence is present on both raw ESP and exact ISO boots:

- `FRAMES_KERNEL_START`
- `FRAMES_USB_MIGRATION_RUNTIME_V9_OK`
- `FRAMES_DESKTOP_PHASE12_OK`
- `FRAMES_APPEARANCE_SYSTEM_OK`
- `FRAMES_FULL_GUI_WINDOWS_OK`
- `FRAMES_FULL_GUI_INPUT_OK`
- `FRAMES_FULL_GUI_FILEMAN_OK`
- `FRAMES_FULL_GUI_SETTINGS_OK`
- `FRAMES_FULL_INTERACTIVE_DESKTOP_OK`
- `FRAMES_INTEGRATED_GUI_OK`
- `FRAMES_GUI_PHYSICAL_TEST_READY`

`FRAMES_DESKTOP_CERT_FAIL` is absent from both certified boot paths.

## Exact physical-test ISO identity

Filename:

`Frames-0.9.106-v116-Full-Interactive-Desktop-GUI-UEFI.iso`

SHA-256:

`abeead78504b6562ee6ecef47027c95803594dd21527cfc3120205a5ef9b7068`

Exact size:

`67,160,064 bytes`

GitHub ISO artifact:

- Artifact ID: `9257223855`
- Artifact ZIP SHA-256: `3e0abb11d5dd609e870cd60e3932e3e608db0413b3705684a35a9f59a533c546`

Evidence artifact:

- Artifact ID: `9257223971`
- Artifact ZIP SHA-256: `78e2af46737817e98fab44044fae3b77fb820be9c5e7da2c91a43c2378fd6dd7`
- all entries in `EVIDENCE-FILES-SHA256.txt` independently verify PASS.

Final certification file:

`FINAL-FULL-INTERACTIVE-DESKTOP-GUI-CERTIFICATION.json`

Final certification status: **PASS**.

Certification scope:

- `physical_test_allowed: true`
- `physical_destructive_writes_certified: false`
- `promotion_allowed: false`

The ISO has an El Torito UEFI boot image and was booted from CD/DVD media in QEMU/OVMF. The ISO build still emits an xorriso compatibility warning that the ISO filesystem itself does not expose a duplicate `/EFI/BOOT` tree; this does not invalidate the proven OVMF DVD boot, but it should be addressed before claiming broad production USB-authoring compatibility.

## Approved splash identity

Approved splash asset SHA-256:

`70e9ca0c9e31b56b720f3cf0bd22c5eacc35b51797782ad0f03172c2038b9fbd`

The successful full-GUI candidate preserves this exact splash.

## Active milestone

**Physical Hardware Full-GUI Boot Validation**

Current objective:

Boot the exact certified ISO SHA-256 `abeead78504b6562ee6ecef47027c95803594dd21527cfc3120205a5ef9b7068` on the user's physical UEFI test machine and verify that real hardware reaches the same splash -> kernel -> full multi-window desktop path.

Physical validation should confirm at minimum:

1. UEFI media is detected and launches Frames.
2. Approved splash is displayed.
3. Boot reaches the multi-window desktop rather than the old dashboard shell.
4. File Manager, Settings, and Nexus/terminal-style window are visibly present.
5. Mouse cursor is visible and real pointer movement can be tested.
6. Keyboard focus/input can be tested.
7. No destructive internal-disk write operation is authorized by this test image.

This milestone requires a real physical boot performed by the user; QEMU cannot substitute for that evidence.

## Physical safety policy

- Physical destructive writes remain uncertified/blocked for this GUI physical-test path.
- The GUI test ISO must not weaken existing physical-write safety gates.
- `promotion_allowed` remains false.
- Frames 1.0 remains NOT promoted.

## Automatic progression rule

For Frames engineering, do not stop after reporting a build/test result.

- If a gate fails: diagnose, repair, rerun, and continue automatically.
- If a gate passes: verify evidence independently, update this file, then continue to the next already-defined milestone automatically.
- Stop only when user input/authorization is genuinely required, a safety boundary requires it, or the next action requires physical hardware that ChatGPT cannot operate.

## New-chat startup rule

Before making Frames engineering changes in a new chat:

1. Read `PROJECT_STATE.md` from the repository.
2. Read `CONTINUITY_PROTOCOL.md`.
3. Inspect the current active branch/run/evidence named here.
4. Do not infer a new roadmap from older chat summaries if it conflicts with this state.
5. Update this file whenever the active milestone, certified baseline, decisive failure, approved artifact, or next action changes.