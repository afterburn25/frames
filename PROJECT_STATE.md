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

## Freshly certified working foundation — Frames 0.9.98 v108 r9

On 2026-08-16 the authoritative Frames 0.9.98 v108 r9 workflow was re-run from the unchanged sealed source and passed end-to-end.

Authoritative workflow:
- `.github/workflows/main.yml`
- `Frames 0.9.98 Integrated Secure Online Services Certification v108 r9`
- GitHub run `31831716862`, attempt 2: PASS
- source commit used by the authoritative workflow: `7333a6670a38c9180e7d72c2a3df444409c36164`

Exact sealed identity:
- Frames version: `0.9.98`
- source revision: `v108-train`
- runtime kit: `Frames-0.9.98-Runtime-Certification-Kit-v108-r9.zip`
- runtime kit SHA-256: `61b0fc25513719fce554729724c7848647de9cffe54434d4ab5f7ba8af42a36a`
- nested source: `Frames-0.9.98-Source-v108.zip`
- source SHA-256: `5f8c13adac6d34e64bd47d9463a3e261cd0b51bb5ddb500aa9f7b87c2914a52d`
- workflow revision: `v108-integrated-secure-online-services-r9`
- train: `0.9.92-0.9.98`

Fresh rerun evidence:
- artifact ID: `9257820749`
- artifact name: `frames-0.9.98-integrated-secure-online-services-evidence-v108`
- artifact ZIP SHA-256: `b7589b75190186b3886e76e8e571bbee1d58884e8a5516338ba59c994427ce74`
- `FINAL-SECURE-ONLINE-SERVICES-CERTIFICATION.json`: PASS
- `FINAL-MANIFEST-VERIFY.json`: PASS with zero mismatches
- `RUNTIME-EVIDENCE.json`: PASS
- integrated QEMU connected + secure-online desktop gate: PASS
- Developer Preview / HelixFS / FAPP regression gate: PASS
- SDK tooling regression gate: PASS
- aggregate evidence and final enforcement: PASS

Important limits preserved by the v108 certification:
- physical boot approved: false
- physical media writes unlocked: false
- live external TLS certified: false
- certificate signature verification certified: false
- physical network hardware certified: false
- Frames 1.0 promoted: false

## Later architecture work

Frames 0.9.106 / architecture v116 remains separately certified architecture work. It is NOT the foundation for the next physical input repair unless explicitly reintroduced later.

The recent full-GUI v116 physical image is rejected as physical-interaction evidence because the user's real machine rendered the desktop but USB mouse and touch produced no visible movement.

Do not use that v116 GUI result to claim physical input functionality.

## Active milestone

**Physical Input Bring-Up from exact certified Frames 0.9.98 v108 r9**

The user explicitly requested that input work restart only after automatically certifying through `0.9.98 v108`.

Next input work must therefore reconstruct the exact sealed v108 source directly and must NOT apply v109-v116 transforms before the physical input problem is understood.

Work USB mouse and built-in touchpad in tandem:

1. identify the physical touchpad transport: PS/2-compatible, USB HID, I2C-HID/absolute, or other;
2. USB/xHCI enumeration across multiple connected devices/ports;
3. live HID report acquisition after boot;
4. PS/2 AUX packet acquisition and phase synchronization where available;
5. Generic Pointer/Core event generation;
6. actual GUI cursor-coordinate change;
7. pointer buttons;
8. keyboard/focus only after pointer movement is proven;
9. add I2C-HID/absolute touchpad support if the hardware proves that transport is required.

## Physical-input evidence standard

No marker based only on initialization/readiness/focus switching counts as live input proof.

Before another physical boot is requested, automated testing should prove as much of the following as possible:
- actual emulated USB HID reports are received;
- actual emulated PS/2 packets are received;
- those reports/packets create Generic Pointer/Core events;
- cursor coordinates actually change in the running GUI;
- before/after framebuffer captures differ at the cursor location;
- diagnostic telemetry can distinguish enumeration, report, decode, core-event and GUI-delivery failures on real hardware.

Physical hardware remains the final authority for the laptop touchpad and USB mouse.

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
