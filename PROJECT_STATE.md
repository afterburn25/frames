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

The previously produced physical-test ISO that showed the Frames dashboard/home shell is NOT a full desktop GUI.

It must be classified only as an integrated desktop-shell / GUI-infrastructure proof.

Do not call that artifact a full GUI, full desktop, finished desktop, or equivalent.

## Active milestone

**Full Interactive Desktop GUI**

Active branch:

`full-interactive-desktop-gui`

Current objective:

Produce a NEW physical-test ISO whose exact booted framebuffer visibly demonstrates a real desktop session, not the prior dashboard shell.

The candidate must visibly show, at minimum:

1. Multiple distinct native overlapping or spatially separated application windows.
2. Native title bars and window controls visibly present.
3. File Manager visibly open with application content.
4. Settings visibly open with application content.
5. Nexus or another real application visibly open with application content.
6. Desktop/taskbar visible.
7. Mouse cursor visible.
8. Window focus/move/resize/input code paths active.
9. Approved splash -> kernel -> desktop transition.
10. `FRAMES_FULL_INTERACTIVE_DESKTOP_OK` and `FRAMES_INTEGRATED_GUI_OK` in serial evidence.
11. No `FRAMES_DESKTOP_CERT_FAIL` in the certified path.

## Current full-GUI work state

The dedicated workflow exists:

`.github/workflows/frames-v116-full-interactive-desktop-gui.yml`

It is intentionally fail-closed:

- It reconstructs exact sealed v108 r9 source.
- It ports exact v109-v116 architecture transforms.
- It preserves the approved splash identity.
- It applies the full-interactive desktop integration.
- It boots the raw ESP in QEMU/OVMF.
- It captures an actual framebuffer.
- It validates the framebuffer for native window chrome.
- It does NOT create the physical ISO unless the raw framebuffer proof passes.
- It then boots the exact ISO itself and repeats the visible proof.
- It uploads the ISO only if all final gates pass.

Latest checked run before this state file:

- Run: `31923624297`
- Branch: `full-interactive-desktop-gui`
- Head at that run: `572ca27bad6a9da34af7aaf97a2969862a8a4154`
- Result: FAIL, correctly fail-closed.
- Build: PASS.
- Approved splash proof: PASS.
- Full interactive desktop serial path reached its expected markers.
- Actual framebuffer contained rich desktop content and two visible native window close-control components.
- Visual proof required at least three distinct visible native window controls, so the workflow rejected the candidate.
- ISO creation/upload steps were skipped.
- Therefore NO new full-GUI physical-test ISO was certified from that run.

Most recent active repair after that failed run:

- Commit: `8a730a580b98026189eac897d0dec9efde58c07e`
- Purpose: reposition/resize File Manager, Settings, and Nexus windows so at least three real native window title bars/controls remain visibly distinct in the final framebuffer.
- This repair must be tested through the same fail-closed workflow before any success claim.

## Approved splash identity

Approved splash asset SHA-256:

`70e9ca0c9e31b56b720f3cf0bd22c5eacc35b51797782ad0f03172c2038b9fbd`

Do not alter or substitute the approved splash in the current GUI milestone unless explicitly requested.

## Physical safety policy

- Physical destructive writes remain uncertified/blocked for this GUI physical-test path.
- A GUI test ISO must not weaken existing physical-write safety gates.
- `promotion_allowed` must remain false unless a separate explicit release-promotion certification authorizes promotion.

## Automatic progression rule

For Frames engineering, do not stop after reporting a build/test result.

- If a gate fails: diagnose, repair, rerun, and continue automatically.
- If a gate passes: verify evidence independently, then continue to the next already-defined milestone automatically.
- Stop only when user input/authorization is genuinely required, a safety boundary requires it, or no next milestone has been defined.

## New-chat startup rule

Before making Frames engineering changes in a new chat:

1. Read `PROJECT_STATE.md` from the repository.
2. Read `CONTINUITY_PROTOCOL.md`.
3. Inspect the current active branch/run/evidence named here.
4. Do not infer a new roadmap from older chat summaries if it conflicts with this state.
5. Update this file whenever the active milestone, certified baseline, decisive failure, or next action changes.
