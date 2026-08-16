# Frames — Canonical Project State

> Authoritative cross-chat handoff for active Frames engineering.
> Repository/evidence overrides chat summaries and prior claims.

Last updated: 2026-08-16

## Project identity / safety
- Frames is an independent OS using Nexus.
- Boot: UEFI -> BOOTX64.EFI -> FramesKernel.fkrn.
- Evidence model is fail-closed: exact source/hash, QEMU/OVMF first, then physical confirmation for hardware claims.
- Frames 1.0 is NOT promoted.
- Physical destructive writes remain uncertified and blocked.
- Installation/persistent internal-media modification remain locked.
- User-facing physical-test artifacts must be Rufus-compatible UEFI ISOs; raw IMG is CI-only.

## Certified reconstruction foundation — Frames 0.9.98 v108
- workflow `.github/workflows/main.yml`
- fresh certification run `31831716862`, attempt 2: PASS
- source commit `7333a6670a38c9180e7d72c2a3df444409c36164`
- runtime kit SHA-256 `61b0fc25513719fce554729724c7848647de9cffe54434d4ab5f7ba8af42a36a`
- nested source SHA-256 `5f8c13adac6d34e64bd47d9463a3e261cd0b51bb5ddb500aa9f7b87c2914a52d`
- exact certified base `kernel/main.nx` SHA-256 `ffc5721eca68844357dbdca63b0edf266e7e210f9d162eecde8cae0067f210a8`
- evidence artifact `9257820749`
- evidence ZIP SHA-256 `b7589b75190186b3886e76e8e571bbee1d58884e8a5516338ba59c994427ce74`

Active branch: `v108-physical-input-bringup`.
All current physical-input work reconstructs this exact certified v108 source; v109-v116 architecture transforms are intentionally excluded from this bring-up train.

## Latest authoritative physical result — r8 on user's laptop
Exact tested r8 ISO:
- `Frames-0.9.98-v108-Physical-Input-Repair-r8-Rufus-UEFI.iso`
- SHA-256 `042b73cbd926b75b33102b1b1a8d5f26efcc00840409f74d38bcadfa88d12f44`
- size `18,728,960 bytes`
- Rufus mode: ISO Image mode

### Built-in touchpad / PS2-AUX
Physical r8 telemetry after movement approximately:
- `PS2 E PK = 1, 30`
- `P2 O A K = 3066, 3066, 0`
- `P2 R PH PK = 3066, 0, 30`
- `P2 SY R1 R2 = 529, 2279, 192`
- `P2 B0 B1 B2 = 222, 68, 0`
- `SRC X Y = 2, 1895, 72`

Observed behavior: visible cursor moves, but skips/jumps to random positions and cannot be controlled reliably by direction.

Authoritative conclusion:
- i8042/AUX transport is physically working;
- thousands of AUX bytes reach Frames;
- some packets decode and drive the real visible cursor;
- `SRC=2` proves PS2 is the active pointer source;
- cursor rendering itself works;
- the blocker is packet protocol/framing/motion quality, not transport or visibility;
- 3066 raw AUX bytes with only 30 accepted packets plus very high sync/reject counts explains the uncontrolled jumps.

### External USB mouse
Physical r8 telemetry:
- `USB H R P = 0, 0, 16`
- `USB S T C E = 5, 8, 0, 1`

Observed behavior: external USB mouse does not move the cursor.

Exact-source interpretation:
- descriptor-8 was obtained;
- the repaired second xHCI Address Device command completed successfully (`E=1`);
- class remains 0 because full device descriptor/HID discovery does not complete;
- the current first physical USB blocker is the following 18-byte full device-descriptor control transfer, not Address Device.

Known later topology gap still exists:
- workflow `.github/workflows/frames-v108-usb-hub-topology-probe.yml`
- run `31929194248`
- direct xHCI mouse supported in VM;
- mouse behind hub: `NO_HID_BEHIND_TOPOLOGY`.

## r9 kernel repair
Patch:
- `tools/ci/patch_v108_physical_input_r9_protocol.py`
- patch commit `a144066f3acd2affc3eafa33c37532ca16e5dbbf`
- finalized hash-lock commit `a1765d2a9cfc2d716fb04e581115179f9860d229`
- r8 input source SHA `b0e7893dea8306b44ea044b5e712fb4568223b5bdd599b9d369f19e523bad037`
- exact r9 output source SHA `5b2384f8e128b1ec6922f34c14478918c3388179937c2000dd12135fefcf682c`

### r9 touchpad changes
- stop streaming before protocol probe;
- perform Synaptics-style four-SETRES + status probe;
- request Synaptics relative-mode normalization when signature is detected;
- preserve standard PS/2 as fallback;
- replace blind three-byte phase reset with a sliding three-byte window;
- validate header bit 3, overflow and sign consistency;
- reject single-packet motion magnitude above 80;
- slide one byte on invalid candidates instead of discarding the stream;
- require two consecutive valid packets before emitting motion.

### r9 USB changes
- retain repaired EP0 dequeue/current transfer-ring pointer before second Address Device;
- retry full 18-byte device-descriptor GET up to three times;
- record descriptor attempt count, returned length/type and config count;
- physical telemetry changes to `USB S T X E`;
- `X` = xHCI transfer completion code (`xhci_state+504`), directly diagnosing the full-descriptor control transfer;
- `E` = xHCI command completion code (`xhci_state+488`).

## r9c VM certification — PASS, including quantitative cursor smoothness
Workflow:
- `.github/workflows/frames-v108-physical-input-r9c-smoothness.yml`
- commit `2e8996269e2d36293d98ea4e1da6461c05f55d52`
- run `31958797777`: PASS

r9c intentionally reuses the exact r9 candidate built in source run `31958310396` rather than rebuilding a different ISO.
Exact candidate identity:
- candidate artifact ID `9266559750`
- candidate artifact ZIP SHA-256 `d78b35b959a366705567a44fe58d31090d6dec83537cd5341f5089f80404b9da`
- ISO `Frames-0.9.98-v108-Physical-Input-Repair-r9-Rufus-UEFI.iso`
- ISO SHA-256 `afad163240b6db6d95a694235456ee8a1fdfb322805c6ce6b0d4c23df08b8a85`
- ISO size `18,733,056 bytes`
- exact r9 source SHA `5b2384f8e128b1ec6922f34c14478918c3388179937c2000dd12135fefcf682c`

r9c required lanes:
- USB stable-frame live input: PASS
- PS2 stable-frame live input: PASS
- quantitative PS2 cursor smoothness: PASS
- verified read-only safety: PASS
- final seal: PASS

Stable input evidence on exact ISO:
- PS2 cursor `396,290 -> 400,292`, requested positive X/Y; PASS
- USB cursor `396,290 -> 400,292`, requested positive X/Y; PASS
- both lanes changed only 112 framebuffer pixels outside telemetry overlay;
- no legacy ghost cursor.

### Quantitative PS2 cursor smoothness gate
Host verifier: `tools/ci/qemu_ps2_cursor_smoothness.py`
Smoothness evidence artifact:
- ID `9266688388`
- ZIP SHA-256 `03df77c54284b9eb51bd5cea9d68aa452639e2fba567896a38271506868d0c2e`

Measured result: PASS across 42 controlled rendered-cursor steps.
- pre-input cursor: `396,290`
- measurement origin after two-packet lock warm-up: `398,290`
- final cursor after full round trip: `398,290`
- round-trip error: `0,0`
- maximum changed pixels outside telemetry overlay per motion step: `115`
- maximum single-step jump: `5 px`
- maximum cross-axis drift: `0 px`
- pre-input idle framebuffer change: `0 px`
- three post-test idle samples all remained exactly `398,290`

Exact step behavior:
- 8 one-pixel right requests -> eight `1 px` right movements
- 8 one-pixel left requests -> eight `1 px` left movements
- 8 three-pixel down requests -> eight `3 px` down movements
- 8 three-pixel up requests -> eight `3 px` up movements
- ramp right requested `1,2,3,4,5` -> actual `1,2,3,4,5`
- ramp left requested `5,4,3,2,1` -> actual `5,4,3,2,1`

This VM gate is now a mandatory prerequisite for future touchpad-fix claims. A build may not be called touchpad-fixed merely because the cursor moves.

## Exact r9c final artifact
Final artifact:
- name `Frames-v108-r9c-Rufus-Final`
- ID `9266690953`
- artifact ZIP SHA-256 `7c04ad1add8084a3906074e68079036c4aa80f7d98a17eb4c61764f00562bd53`

Exact contained ISO:
- `Frames-0.9.98-v108-Physical-Input-Repair-r9-Rufus-UEFI.iso`
- SHA-256 `afad163240b6db6d95a694235456ee8a1fdfb322805c6ce6b0d4c23df08b8a85`
- size `18,733,056 bytes`
- Rufus mode: ISO Image mode

Certification status inside final artifact:
- exact r9 candidate reused: PASS
- VM USB stable input: PASS
- VM PS2 stable input: PASS
- VM PS2 cursor smoothness: PASS
- read-only safety: PASS
- physical touchpad smoothness: PENDING USER HARDWARE
- physical USB full descriptor: PENDING USER HARDWARE
- physical destructive writes: BLOCKED

## Claim policy — touchpad
Do NOT call the touchpad physically fixed until BOTH are true:
1. the exact candidate passes the GitHub quantitative smoothness gate; and
2. the user's real laptop demonstrates controllable right/left/up/down movement without random jumps or idle drift.

VM smoothness PASS proves the standard PS/2 parser/render path is mathematically smooth under controlled input. It does not prove the laptop's real touchpad protocol stream is normalized correctly.

## Next physical test — r9c exact ISO
Use only ISO SHA:
`afad163240b6db6d95a694235456ee8a1fdfb322805c6ce6b0d4c23df08b8a85`

Rufus: ISO Image mode.

Test order:
1. boot and wait for `INPUT V108 LIVE` panel;
2. move touchpad slowly right, left, down and up;
3. judge whether the visible cursor follows direction smoothly without random jumps;
4. stop touching the pad for several seconds and confirm cursor does not wander;
5. move external USB mouse;
6. if USB still fails, photograph the `USB S T X E` row — `X` is now the transfer completion code for the full descriptor transfer and `E` remains the command completion code;
7. if touchpad is still erratic, photograph `PS2 E PK`, `P2 O A K`, `P2 R PH PK`, `P2 SY R1 R2`, `P2 B0 B1 B2`, and `SRC X Y` after deliberate movement.

Physical destructive writes remain blocked.

## Automatic progression
- run independent workflows/lanes in parallel whenever practical;
- failure -> diagnose -> repair -> rerun automatically;
- pass -> independently verify -> update this file -> continue automatically;
- stop only for genuine physical hardware/user action or a safety/authorization boundary.

## New-chat startup
1. Read `PROJECT_STATE.md`.
2. Read `CONTINUITY_PROTOCOL.md`.
3. Inspect the active branch/run/evidence named here.
4. Repository/evidence overrides older chat summaries.
5. Update this file whenever milestone, decisive failure, artifact identity, safety boundary or next action changes.
