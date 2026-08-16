# Frames — Canonical Project State

> This file is the authoritative cross-chat handoff for active Frames engineering.
> Repository/evidence overrides chat summaries or prior claims.

Last updated: 2026-08-16

## Project identity

- Frames is an independent operating system, not Windows- or Linux-based.
- Native systems language/toolchain: Nexus.
- Boot chain: UEFI -> BOOTX64.EFI -> FramesKernel.fkrn.
- Native application formats: FEX/FAPP.
- Evidence model: fail-closed, exact-source/hash based, QEMU/OVMF-first, then real-hardware confirmation for hardware claims.
- Frames 1.0 is NOT promoted.

## Fresh certified foundation — Frames 0.9.98 v108 r9

The unchanged authoritative v108 r9 certification was freshly rerun on 2026-08-16 and passed end-to-end.

- workflow: `.github/workflows/main.yml`
- run `31831716862`, attempt 2: PASS
- workflow source commit `7333a6670a38c9180e7d72c2a3df444409c36164`
- runtime kit SHA-256 `61b0fc25513719fce554729724c7848647de9cffe54434d4ab5f7ba8af42a36a`
- nested source SHA-256 `5f8c13adac6d34e64bd47d9463a3e261cd0b51bb5ddb500aa9f7b87c2914a52d`
- exact certified `kernel/main.nx` SHA-256 `ffc5721eca68844357dbdca63b0edf266e7e210f9d162eecde8cae0067f210a8`
- fresh evidence artifact `9257820749`
- evidence ZIP SHA-256 `b7589b75190186b3886e76e8e571bbee1d58884e8a5516338ba59c994427ce74`

Active input branch: `v108-physical-input-bringup`.

All current input work is reconstructed from the exact certified v108 source. v109-v116 transforms are intentionally excluded from this bring-up train.

## Authoritative physical input result — FAIL

The user's real laptop booted the previous v108 Rufus physical-input candidate successfully, but physical input failed.

Observed on real hardware:
- external USB mouse: no cursor movement;
- built-in touchpad: no cursor movement;
- visible USB/PS2 input counters did not advance during normal movement;
- moving the built-in touchpad repeatedly triggered framebuffer/screen refresh behavior;
- therefore physical interactive input is NOT certified.

This physical result overrides prior QEMU input passes. Do not call USB mouse or touchpad physically working until a later real-machine test proves it.

The prior Rufus r4 candidate is superseded and must not be handed to the user again.

## Discovered VM visual-proof flaw

Post-failure evidence review found that earlier QEMU "after input" screenshots could catch the desktop in a mostly cleared/partial repaint state while the old verifier still passed because it only required changed framebuffer bytes/pixels.

Therefore:
- old changed-pixel-only visual evidence is insufficient;
- input activity must not be allowed to masquerade as success by clearing/repainting the desktop;
- the current diagnostic train adds a strong visual-stability gate and suppresses normal desktop repainting during hardware-input diagnosis.

## Confirmed USB topology gap

Workflow `.github/workflows/frames-v108-usb-hub-topology-probe.yml` tested the exact v108 input candidate with direct and hub-attached QEMU USB mice.

Corrected topology run `31929194248`:
- direct xHCI USB mouse: `SUPPORTED`;
- USB mouse behind a USB hub: `NO_HID_BEHIND_TOPOLOGY`;
- runtime reached, but no HID live report and no GUI cursor delivery behind the hub.

Conclusion: the current v108 USB stack does not traverse USB hubs. This is a confirmed implementation gap. It may explain the user's physical USB failure if the real port/device is behind a hub, but that is not yet physically proven.

## Deep physical telemetry

`tools/ci/patch_v108_physical_deep_telemetry.py` adds live stage telemetry without changing destructive-write paths.

USB stage telemetry:
- stage 1: scan started;
- stage 2: connected root port selected/reset;
- stage 3: slot enabled;
- stage 4: default address step passed;
- stage 5: first descriptor read passed;
- stage 6: full device descriptor passed;
- stage 7: boot HID discovered;
- stage 8: HID configured.

It also exposes scan tries, selected root port, device class, report activity and source/cursor state.

PS/2 telemetry exposes:
- total i8042 bytes read;
- AUX-classified versus non-AUX bytes;
- decoder/raw counts and packet phase;
- sync/header/sign reject counters;
- last candidate packet bytes;
- decoded packet/source/cursor state.

This is diagnostic telemetry only; it does not itself prove hardware support.

## Current physical-test candidate — stable r6

The next allowed real-machine test uses the stable hardware-input diagnostic runtime. Normal desktop/window-manager repaints are suppressed during input testing; only the hardware telemetry panel is updated. This prevents the physical screen-refresh behavior from obscuring the input diagnosis.

Source identity:
- stable diagnostic kernel SHA-256 `de8cd41f707268bc0d7bb2ff5ef925ba0e8981650703afdb065b1a62a1d6cca1`
- derived deterministically from deep-r5 kernel SHA-256 `d0421388cd288a7073ca750915b1b51ceeee62acfe524a6785f855e42f9b1e7f`
- stable runtime patch: `tools/ci/patch_v108_stable_input_diag_runtime.py`

Exact Rufus ISO:
- `Frames-0.9.98-v108-Stable-Physical-Input-Diagnostic-r6-Rufus-UEFI.iso`
- SHA-256 `4aa3ddfbe70668f0d362fcb9c8ea04c77a96977b417eed090c7bfc8f4177fd22`
- size `18,722,816 bytes`
- Rufus mode: **ISO Image mode**

Build / certification:
- source/build workflow `.github/workflows/frames-v108-stable-physical-input-rufus-r6.yml`
- source build run `31929714354`
- candidate artifact `9258923697`
- candidate artifact ZIP SHA-256 `1f70bae5d74be9ca25c0b8af7942e4ea3d34f9082dbfe38fa8fde016e00b8edc`
- exact immutable re-cert workflow `.github/workflows/frames-v108-stable-physical-input-rufus-r6b-cert.yml`
- re-cert run `31929841882`: PASS
- final artifact `9258971873`
- final artifact ZIP SHA-256 `8dcf43f1bd41339be693db3f557970cff501cbac5242e6ba0cad11e446b1e2d8`
- `FINAL-STABLE-INPUT-DIAGNOSTIC.json`: PASS

Independent verification after GitHub run:
- all final/USB/PS2/read-only evidence ZIP integrity: PASS;
- all SHA-256 manifests: PASS;
- USB `RUNTIME.json`: PASS, exact ISO verified, live input markers present;
- PS/2 `RUNTIME.json`: PASS, exact ISO verified, live input markers present;
- USB visual stability: PASS, 122 changed pixels, 99.988% frame unchanged, non-dark content retention 100%;
- PS/2 visual stability: PASS, 263 changed pixels, 99.974% frame unchanged, non-dark content retention 100%;
- both actual AFTER framebuffers retain the complete desktop and change only a tiny diagnostic area;
- read-only safety: PASS with internal NVMe sentinel read-only;
- physical destructive writes certified: false;
- promotion allowed: false.

These are VM/OVMF results only. Physical hardware input remains unverified.

## Next physical boot procedure

Use only the exact stable r6 ISO SHA above.

1. Write with Rufus using **ISO Image mode**.
2. Boot in UEFI mode and wait for the diagnostic desktop/panel to settle.
3. Before moving any pointing device, take a close-up photo of the top-right `INPUT V108 LIVE` telemetry panel.
4. Do not touch the built-in touchpad. Move only the external USB mouse for 10-15 seconds in multiple directions. Take a second close-up photo of the telemetry panel.
5. Stop the USB mouse. Move only the built-in touchpad for 10-15 seconds right/left/up/down. Take a third close-up photo of the telemetry panel.
6. Do not infer success merely from a screen refresh; the counters/stages are the authority for this diagnostic.

Interpretation targets:

USB:
- stage reaches 6 with device class 9 -> a USB hub was reached; hub traversal becomes the immediate repair;
- stage stalls below 6 -> root-port/address/descriptor bring-up failure;
- stage 7/8 or HID configured but report counter stays zero -> HID endpoint/report polling issue;
- live report/source/cursor-state counters change -> transport reached Frames, even though normal cursor repaint is intentionally suppressed in this diagnostic build.

Touchpad / PS2:
- total i8042 bytes increase but AUX count does not -> byte classification/routing failure;
- AUX/raw counts increase but packet count stays static and reject counters rise -> packet synchronization/decoder failure;
- i8042/AUX counts do not change at all during touchpad movement -> the touchpad likely is not reaching Frames through the PS/2/AUX transport, and I2C-HID/Precision Touchpad bring-up becomes the next transport target;
- decoded packet/source/cursor-state counters change -> PS/2 transport is functioning internally, even though normal cursor repaint is intentionally suppressed.

## Touchpad transport limitation

Exact-v108 audit proved:
- PS/2/AUX support exists;
- USB HID support exists;
- I2C-HID / absolute digitizer / Precision Touchpad support is not implemented yet.

Do not claim the built-in touchpad is supported until the physical telemetry identifies its transport and movement reaches the pointer path.

## Physical artifact delivery policy

- Every user-facing Frames physical-test artifact must be a **Rufus-compatible UEFI `.iso`**.
- Raw `.img` may be used internally by CI/QEMU only.
- Every delivered ISO must have an exact SHA-256 and be boot-tested in QEMU/OVMF first.
- State the validated Rufus mode for every artifact; do not make the user guess.

## Safety policy

- The stable r6 ISO is authorized only for a read-only diagnostic physical boot.
- Physical destructive writes remain uncertified and blocked.
- Installation, persistent internal-media modification and release promotion remain locked.
- Frames 1.0 remains NOT promoted.

## Automatic progression

- Run independent workflows/lanes in parallel whenever practical.
- Failure -> diagnose -> repair -> rerun automatically.
- Pass -> independently verify -> update this file -> continue automatically.
- Do not stop merely to report routine intermediate results.
- Stop only when real physical hardware/user action is genuinely required or a safety boundary requires authorization.

## New-chat startup

1. Read `PROJECT_STATE.md`.
2. Read `CONTINUITY_PROTOCOL.md`.
3. Inspect the active branch/run/evidence named here.
4. Repository/evidence overrides older chat summaries.
5. Update this file whenever the milestone, decisive failure, artifact identity, safety boundary or next action changes.
