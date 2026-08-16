# Frames — Canonical Project State

> This file is the authoritative cross-chat handoff for active Frames engineering.
> When chat memory, summaries, prior messages, or assumptions disagree with this file and current repository/evidence, repository/evidence wins.

Last updated: 2026-08-16

## Project identity

- Frames is an independent operating system, not Windows- or Linux-based.
- Native systems language/toolchain: Nexus.
- Boot chain: UEFI -> BOOTX64.EFI -> FramesKernel.fkrn.
- Native application formats: FEX/FAPP.
- Evidence model: fail-closed, exact-source/hash based, QEMU/OVMF-first, then real-hardware confirmation for hardware claims.
- Frames 1.0 is NOT promoted.

## Current certified architecture baseline

- Frames 0.9.106 / architecture v116 remains the certified architecture baseline for the active GUI/input work.
- Frames 0.9.98 v108 r9 remains the sealed reconstruction source used by current integration workflows.
- v109-v116 transforms remain hash-checked before product integration changes.

## VM-rendered full GUI result

The full-interactive desktop renderer is real and remains VM-certified as a rendering/composition result:

- branch: `full-interactive-desktop-gui`
- GUI candidate commit: `8a730a580b98026189eac897d0dec9efde58c07e`
- workflow run: `31923853583`
- QEMU framebuffer visibly shows File Manager, Settings, Nexus/terminal-style window, native window chrome, desktop/taskbar and cursor.
- approved splash -> kernel -> rendered desktop passes in QEMU/OVMF.

This no longer qualifies as proof of **interactive** GUI input on physical hardware.

## Physical-media/USB packaging result

USB-compatible full-GUI ISO packaging remains technically valid:

- ISO: `Frames-0.9.106-v116-Full-Interactive-Desktop-GUI-USB-Compatible-UEFI.iso`
- SHA-256: `7d1c212ad71778a84579e91c2e12ebafe3801a8bcd8a0a0856e506d47ebe20c7`
- size: `67,401,728 bytes`
- media compatibility run: `31924483046` PASS
- extracted GPT/FAT32 xHCI USB boot run: `31924646428` PASS

Those passes prove boot/media/rendering in QEMU. They do NOT prove physical pointer/touch input.

## Decisive physical result — FAIL

On 2026-08-16 the user physically booted the current USB-compatible full-GUI candidate on the real UEFI test machine.

Observed:

- boot succeeded;
- desktop rendered;
- USB mouse produced no visible cursor movement;
- touch input produced no visible movement/interaction;
- the resulting desktop therefore behaved like a static/mock-style desktop rather than an interactive desktop.

Result: **Physical Hardware Full-GUI Boot Validation FAIL for interaction.**

Do not describe the current physical image as a proven full interactive GUI.

## Important certification correction — `FRAMES_FULL_GUI_INPUT_OK`

The current full-GUI patch emits `FRAMES_FULL_GUI_INPUT_OK` after exercising internal `gui_input_focus(...)` calls between existing windows. That marker proves an internal GUI focus path, not live hardware input.

Therefore:

- `FRAMES_FULL_GUI_INPUT_OK` is NOT accepted as physical mouse/touch proof;
- future interactive certification must require real hardware/backend activity and an observable cursor/event change;
- a rendered cursor by itself is not input proof.

## Relevant prior pointer engineering that must be carried forward

Do not restart pointer work from scratch.

Repository history contains a dedicated Frames 0.9.98 physical pointer train including:

- Pointer Diagnostics CI v2 with PS/2 and xHCI USB HID lanes;
- r46 USB startup handoff fix: avoids synchronous first-report/decode gating and lets continuous HID processing own live reports;
- r48-r55 physical PS/2/USB/protocol diagnostics;
- r55 physical protocol telemetry including USB enumeration stages and raw touchpad/AUX protocol bytes.

The full-GUI v116 path did not establish that these physical-input fixes were correctly ported into the live desktop path.

## Active milestone

**Physical Input Bring-Up for Full GUI**

Active development branch should be:

`physical-input-bringup`

Current objective:

Make the rendered full GUI genuinely interactive on physical hardware by proving and fixing the complete live chain:

1. physical device/controller enumeration;
2. USB HID mouse and/or PS/2/touch source activity;
3. live report/packet acquisition after boot;
4. decode/normalization into Generic Pointer/Core events;
5. GUI event delivery;
6. actual cursor coordinate change;
7. pointer buttons;
8. keyboard focus/input;
9. touch path separately identified and implemented if it is I2C-HID/absolute rather than USB/PS2.

The next physical candidate must include machine-readable/live on-screen telemetry sufficient to distinguish enumeration failure, report failure, decode failure, core-event failure and GUI-delivery failure.

## Next engineering actions

1. Reconstruct the exact v116 + full-GUI candidate in CI.
2. Inspect the live input functions and compare them with the r46/r55 physical-input train.
3. Port the proven r46 USB startup handoff semantics where still missing.
4. Integrate live physical input counters/telemetry into the full-GUI candidate without hiding the desktop.
5. Add a fail-closed QEMU regression requiring injected USB mouse events to change the actual Frames cursor coordinates, not merely focus state.
6. Build a new physical diagnostic/full-GUI ISO only after that regression passes.
7. Physical test remains required before restoring the phrase `full interactive GUI` for hardware.

## Safety policy

- Physical destructive writes remain uncertified and blocked.
- Internal NVMe/SATA/system media remain outside destructive-write certification scope.
- `promotion_allowed` remains false.
- Frames 1.0 remains NOT promoted.

## Automatic progression

- Failure -> diagnose -> repair -> rerun automatically.
- Pass -> independently verify -> update this file -> continue to the next defined milestone automatically.
- Do not stop merely to report routine intermediate results.
- Stop only where real physical hardware/user action is genuinely required or a safety boundary requires authorization.

## New-chat startup

1. Read `PROJECT_STATE.md`.
2. Read `CONTINUITY_PROTOCOL.md`.
3. Inspect the active branch/run/evidence named here.
4. Repository/evidence overrides older chat summaries.
5. Update this file whenever the milestone, decisive failure, artifact identity, safety boundary or next action changes.
