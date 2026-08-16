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

## Authoritative physical input result — USB FAIL / PS2 TOUCHPAD INGRESS PROVEN

The user's real laptop booted the stable r6 Rufus diagnostic ISO and supplied three close-up telemetry photos: settled baseline, USB-mouse movement, and built-in-touchpad movement.

### External USB mouse — FAIL before HID

Baseline and USB-movement photos remained effectively unchanged:
- `USB H R P = 0, 0, 16`
- `USB S T C = 5, 8, 0, 0`
- no USB live-report count increase;
- no internal pointer-coordinate movement attributable to USB.

Interpretation:
- stage 5 means the first 8 bytes of the USB device descriptor were obtained;
- 8 scan tries were exhausted;
- device class remained unknown (`0`) because enumeration never reached the full-descriptor/HID-discovery stage;
- therefore the immediate USB blocker is the xHCI transition after descriptor-8, before full device descriptor/HID discovery.

The previously discovered USB-hub traversal gap remains real, but the physical telemetry now points to this earlier stage-5 address/descriptor transition as the first physical blocker to repair.

### Built-in touchpad / PS2-AUX — LIVE HARDWARE PATH PROVEN

Before touchpad movement the panel showed essentially no live PS2 packet traffic and internal pointer coordinates around `X=396, Y=290`.

After moving the built-in touchpad, the physical panel showed approximately:
- `PS2 E PK = 1, 21`
- `P2 O A K = 1410, 1410, 0`
- `P2 R PH PK = 1410, 0, 21`
- `P2 SY R1 R2 = 245, 1047, 71`
- last candidate bytes `P2 B0 B1 B2 = 45, 16, 49`
- `SRC = 2`
- internal pointer coordinates changed to approximately `X=1194, Y=0`.

This proves on the real laptop:
- i8042/PS2 input bytes are arriving;
- the bytes are AUX-classified;
- Frames decodes at least some packets;
- the pointer source becomes PS2 (`SRC=2`);
- the internal GUI pointer coordinates change in response to real touchpad motion.

Therefore the built-in touchpad is NOT an I2C-only dead end on this laptop. The immediate remaining touchpad work is visible cursor presentation plus motion-quality/packet-rejection tuning, not basic transport discovery.

The large reject counters also show that packet synchronization/quality can still be improved after visible cursor movement is restored.

### Framebuffer behavior

The old full-screen repaint behavior is gone in r6. During touchpad activity, only the diagnostic box flickers/refreshes. That is expected because r6 intentionally redraws the telemetry panel while suppressing normal desktop/window-manager repaints.

This validates the r6 stabilization change. The next repair can safely add cursor-only redraw without re-enabling full-desktop repainting.

## Confirmed USB topology gap

Workflow `.github/workflows/frames-v108-usb-hub-topology-probe.yml` corrected run `31929194248`:
- direct xHCI USB mouse: `SUPPORTED`;
- USB mouse behind a USB hub: `NO_HID_BEHIND_TOPOLOGY`.

Conclusion: v108 still lacks USB-hub traversal. This remains a required USB capability, but the current laptop first stalls earlier at physical stage 5.

## Superseded stable r6 diagnostic

Stable r6 was the diagnostic ISO that produced the decisive physical telemetry above:
- `Frames-0.9.98-v108-Stable-Physical-Input-Diagnostic-r6-Rufus-UEFI.iso`
- SHA-256 `4aa3ddfbe70668f0d362fcb9c8ea04c77a96977b417eed090c7bfc8f4177fd22`
- size `18,722,816 bytes`
- Rufus mode: ISO Image mode
- immutable re-cert run `31929841882`: PASS

Do not ask the user to retest r6; it has already served its diagnostic purpose.

## Active repair — r7 physical cursor + xHCI descriptor/address transition

Active patch:
- `tools/ci/patch_v108_physical_input_r7.py`
- exact source input: r6 kernel SHA-256 `de8cd41f707268bc0d7bb2ff5ef925ba0e8981650703afdb065b1a62a1d6cca1`
- exact r7 kernel output SHA-256 `b94070bfe399162a8bb5bef1694c92100716d500d9e85737896901ef3f5aa8e7`

Touchpad/cursor repair:
- retain stable diagnostic mode;
- save/restore only the small cursor backing rectangle;
- update only old/new cursor rectangles plus telemetry;
- do not call normal `appearance_render(process)` or `wm_render_all` in the physical-input loop;
- emit `FRAMES_V108_PHYSICAL_CURSOR_VISIBLE_OK` after actual pointer-coordinate movement is rendered.

USB repair:
- after the descriptor-8 control transfer, update EP0's input-context dequeue pointer to the current software control-ring enqueue position before the second Address Device command;
- preserve the updated EP0 max-packet size;
- expose the xHCI command-completion/error code on the physical telemetry panel as the fourth USB stage value.

Rationale: mature xHCI stacks refresh EP0's dequeue/enqueue position before the later Address Device transition. The physical stage-5 result directly targets this transition.

Certification workflow:
- `.github/workflows/frames-v108-physical-input-r7-rufus.yml`
- active run `31930792343`
- independent USB, PS2, and read-only safety lanes run in parallel after build;
- final ISO is not released unless all required lanes pass.

## Physical artifact delivery policy

- Every user-facing Frames physical-test artifact must be a Rufus-compatible UEFI `.iso`.
- Raw `.img` may be used internally by CI/QEMU only.
- Every delivered ISO must have an exact SHA-256 and be boot-tested in QEMU/OVMF first.
- State the validated Rufus mode for every artifact; do not make the user guess.

## Safety policy

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
