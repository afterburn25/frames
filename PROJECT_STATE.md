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

## Freshly certified foundation — Frames 0.9.98 v108 r9

On 2026-08-16 the unchanged authoritative Frames 0.9.98 v108 r9 workflow was re-run and passed end-to-end.

Authoritative workflow / identity:
- `.github/workflows/main.yml`
- `Frames 0.9.98 Integrated Secure Online Services Certification v108 r9`
- GitHub run `31831716862`, attempt 2: PASS
- workflow source commit `7333a6670a38c9180e7d72c2a3df444409c36164`
- Frames `0.9.98`, source revision `v108-train`
- runtime kit SHA-256 `61b0fc25513719fce554729724c7848647de9cffe54434d4ab5f7ba8af42a36a`
- nested source SHA-256 `5f8c13adac6d34e64bd47d9463a3e261cd0b51bb5ddb500aa9f7b87c2914a52d`
- exact certified `kernel/main.nx` SHA-256 `ffc5721eca68844357dbdca63b0edf266e7e210f9d162eecde8cae0067f210a8`
- fresh evidence artifact ID `9257820749`
- fresh evidence ZIP SHA-256 `b7589b75190186b3886e76e8e571bbee1d58884e8a5516338ba59c994427ce74`
- final certification, manifest verification, runtime evidence, connected/secure-online desktop, Developer Preview/HelixFS/FAPP, SDK and final enforcement: PASS

## Active hardware branch

`v108-physical-input-bringup`

All physical-input work is reconstructed directly from the exact certified v108 source. v109-v116 transforms are intentionally excluded from this bring-up train.

The old Pointer Diagnostics source kit is not accepted as a canonical base; provenance audit run `31926038311` proved it had unrelated source/toolchain drift. Only the required input fixes were re-applied to the sealed v108 source.

## v108 live-input VM evidence

The v108 branch now contains a combined input repair derived directly from the certified source.

Combined live-input certification:
- workflow `.github/workflows/frames-v108-combined-live-input-cert.yml`
- run `31926756188`: PASS
- USB HID live report -> input path -> GUI cursor: VM PASS
- PS/2 packet -> input path -> GUI cursor: VM PASS

Physical removable-media candidate:
- `Frames-0.9.98-v108-Physical-Input-Test-r2.img`
- SHA-256 `6918d228725f0cb3185e17f974119b4abf8c8413af1173369fc8d0594f30bab7`
- size `67,108,864 bytes`
- source build/certification run `31927431251`: PASS
- candidate artifact ID `9258264525`
- candidate artifact ZIP SHA-256 `7cceea42332b665c0b3551e6d5f9c761f6950015fc2c244fae2c51f24a260710`
- xHCI USB-storage boot + USB mouse live-input lane: PASS
- xHCI USB-storage boot + PS/2 live-input lane: PASS

## Corrected visual input certification — PASS

The prior r3 visual workflow failed only because its telemetry-panel color threshold was too strict; live-input markers and framebuffer movement were already present. The verifier was corrected without changing the candidate image.

Corrected certification:
- workflow `.github/workflows/frames-v108-physical-input-visual-cert-r4.yml`
- run `31927881454`: PASS
- exact candidate SHA checked before each lane
- USB lane: PASS, 1280x800, runtime markers present, 69 framebuffer pixels changed, desktop preserved
- PS/2 lane: PASS, 1280x800, runtime markers present, 65 framebuffer pixels changed, desktop preserved
- final artifact ID `9258388697`
- final artifact ZIP SHA-256 `a7f5d267567099d903588ba051d3751f3180e453eb1ba403c1827fec0ae383ac`
- `FINAL-VISUAL-CERTIFICATION.json`: PASS

This is VM evidence only. It does not claim the user's physical mouse/touchpad works yet.

## Physical Boot Safety Gate — PASS

A separate fail-closed gate now permits another **read-only diagnostic physical boot** of the exact candidate above.

Workflow:
- `.github/workflows/frames-v108-physical-boot-safety-gate.yml`
- run `31927897926`: PASS

Independent lanes:
- UEFI/GPT/FAT removable-media structure: PASS
- `/EFI/BOOT/BOOTX64.EFI` present and verified
- `/FRAMES/FramesKernel.fkrn` present and verified
- input-overlay write-surface audit: PASS, zero write-path hits
- QEMU boot with the Frames USB forced read-only: PASS
- QEMU boot with an internal NVMe sentinel also forced read-only: PASS
- no read-only write errors observed
- input diagnostic runtime reached while all guest-visible block devices were read-only

Final safety artifact:
- artifact ID `9258389041`
- artifact ZIP SHA-256 `44909732424e1866344a4e70af1faf3be05b0ffb94df3ca34b20ec5c874e1b97`
- `PHYSICAL-BOOT-SAFETY.json`: PASS
- `physical_boot_test_allowed: true`
- `physical_destructive_writes_certified: false`
- `promotion_allowed: false`

## Physical boot status

**Read-only diagnostic physical boot: UNLOCKED for the exact v108 r2 image only.**

This does NOT unlock installation, persistent writes, internal-disk modification, or release promotion.

Physical hardware remains the final authority. The next physical test must use exact SHA-256:

`6918d228725f0cb3185e17f974119b4abf8c8413af1173369fc8d0594f30bab7`

Test order:
1. boot the exact image in UEFI mode from sacrificial/removable USB;
2. move the external USB mouse for 10-15 seconds without touching the built-in touchpad;
3. observe whether the cursor moves and whether USB live-report / GUI-delivery telemetry changes;
4. then move the built-in touchpad slowly right and down;
5. observe whether the cursor moves and whether PS/2/AUX telemetry changes;
6. photograph the diagnostic screen if either path fails.

## Physical artifact delivery policy

- From this point forward, every Frames physical-test artifact delivered to the user must be a **Rufus-compatible UEFI ISO**.
- Raw `.img` files may still be used internally by CI, QEMU, provenance checks, or as intermediate build artifacts, but they are not the normal user-facing physical-test deliverable.
- The Rufus ISO must preserve the exact certified EFI/kernel payload, have an exact SHA-256 identity, and be boot-tested in QEMU/OVMF before being handed to the user.
- Prefer a hybrid/removable-media-compatible ISO layout with `/EFI/BOOT/BOOTX64.EFI` and the required `/FRAMES` payload exposed so Rufus can write it reliably.
- If Rufus offers ISO mode or DD mode, the certified instructions for that exact artifact must state which mode was validated; do not make the user guess.

## Touchpad transport limitation

Exact-v108 transport audit proved:
- PS/2/AUX support exists and is the first built-in touchpad path being tested;
- USB HID support exists;
- I2C-HID / absolute digitizer / Precision Touchpad support is not implemented yet.

Therefore a physical touchpad that exposes only I2C-HID may still fail even if the PS/2 VM lane passes. That result must trigger I2C-HID bring-up rather than being mislabeled as a working touchpad.

## Later architecture / GUI work

Frames 0.9.106 / architecture v116 remains separately certified architecture work, but it is not the current physical-input foundation.

The earlier v116 GUI physical image is rejected as physical-interaction evidence because the real test machine rendered the desktop but produced no USB mouse or touch movement. Do not use that result to claim physical interactivity.

## Safety policy

- Physical destructive writes remain uncertified and blocked.
- Internal NVMe/SATA/system media remain outside destructive-write certification scope.
- `promotion_allowed` remains false.
- Frames 1.0 remains NOT promoted.

## Automatic progression

- Run independent workflows/lanes in parallel whenever practical.
- Failure -> diagnose -> repair -> rerun automatically.
- Pass -> independently verify -> update this file -> continue automatically.
- Do not stop merely to report routine intermediate results.
- Stop only where real physical hardware/user action is genuinely required or a safety boundary requires authorization.

## New-chat startup

1. Read `PROJECT_STATE.md`.
2. Read `CONTINUITY_PROTOCOL.md`.
3. Inspect the active branch/run/evidence named here.
4. Repository/evidence overrides older chat summaries.
5. Update this file whenever the milestone, decisive failure, artifact identity, safety boundary or next action changes.
