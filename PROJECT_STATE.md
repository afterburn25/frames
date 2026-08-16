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

## Physical history — r8
Exact tested r8 ISO:
- `Frames-0.9.98-v108-Physical-Input-Repair-r8-Rufus-UEFI.iso`
- SHA-256 `042b73cbd926b75b33102b1b1a8d5f26efcc00840409f74d38bcadfa88d12f44`
- size `18,728,960 bytes`
- Rufus mode: ISO Image mode

Physical r8 touchpad result:
- thousands of i8042/AUX bytes reached Frames;
- some standard-three-byte candidates were accepted;
- visible cursor moved, proving the cursor-render path;
- movement jumped randomly and was not controllable;
- representative telemetry: `PS2 E PK=1,30`, `P2 O A K=3066,3066,0`, `SRC X Y=2,1895,72` with very high reject/sync counters.

Physical r8 USB result:
- no cursor movement;
- representative telemetry `USB S T C E=5,8,0,1`;
- repaired second xHCI Address Device command completed successfully (`E=1`), moving the first physical blocker to the following full-device-descriptor stage.

Known later USB topology gap still exists:
- `.github/workflows/frames-v108-usb-hub-topology-probe.yml`
- run `31929194248`
- direct xHCI mouse supported in VM;
- mouse behind hub: `NO_HID_BEHIND_TOPOLOGY`.

## r9 kernel / VM certification
Patch:
- `tools/ci/patch_v108_physical_input_r9_protocol.py`
- exact r9 output source SHA `5b2384f8e128b1ec6922f34c14478918c3388179937c2000dd12135fefcf682c`

r9 added:
- Synaptics-style protocol probe / attempted relative normalization;
- safer sliding standard-PS2 three-byte parser;
- two-consecutive-valid-packet lock before motion emission;
- implausible single-packet delta rejection;
- USB full 18-byte descriptor retries;
- `USB S T X E` telemetry where `X` is xHCI transfer completion and `E` is command completion.

r9c VM recertification:
- workflow `.github/workflows/frames-v108-physical-input-r9c-smoothness.yml`
- run `31958797777`: PASS
- exact ISO `Frames-0.9.98-v108-Physical-Input-Repair-r9-Rufus-UEFI.iso`
- ISO SHA-256 `afad163240b6db6d95a694235456ee8a1fdfb322805c6ce6b0d4c23df08b8a85`
- size `18,733,056 bytes`
- Rufus mode: ISO Image mode
- USB stable input VM: PASS
- standard PS2 stable input VM: PASS
- quantitative 42-step standard PS2 cursor smoothness VM: PASS
- read-only safety: PASS

The standard-PS2 smoothness gate is mandatory for future touchpad handoffs. It proves the reference parser/render path behaves smoothly under controlled QEMU input; it does NOT prove the user's physical touchpad protocol is decoded correctly.

## Latest authoritative physical result — r9 on user's laptop: FAIL
Exact physically tested r9 ISO:
- `Frames-0.9.98-v108-Physical-Input-Repair-r9-Rufus-UEFI.iso`
- SHA-256 `afad163240b6db6d95a694235456ee8a1fdfb322805c6ce6b0d4c23df08b8a85`

Observed behavior:
- built-in touchpad: cursor does not move at all, but telemetry changes continuously while the pad is moved;
- external USB mouse: no visible behavior.

Representative r9 physical telemetry from photo:
- `USB H R P = 0, 0, 16`
- `USB S T X E = 5, 8, 1, 1`
- `PS2 E PK = 1, 0`
- `P2 O A K ≈ 2208, 2208, 0`
- `P2 R PH PK ≈ 2208, 0, 0`
- `P2 SY R1 R2 ≈ 0, 4054, 241`
- `P2 B0 B1 B2 = 16, 0, 0`
- `SRC X Y = 0, 396, 290`

Authoritative r9 touchpad conclusion:
- physical i8042/AUX transport remains proven;
- roughly 2208 AUX bytes reached Frames during the test;
- r9 accepted zero motion packets and therefore emitted no pointer source (`SRC=0`);
- cursor remained at the initial position;
- the stricter standard-three-byte parser prevented random jumps but is incompatible with / unable to lock onto the user's actual touchpad stream;
- this is a physical protocol/framing problem, not lack of touchpad electrical/transport activity.

Authoritative r9 USB conclusion:
- both displayed xHCI completion fields are `1`, i.e. success-class completion values in this exact diagnostic implementation;
- Frames still remains at stage 5/class 0 and produces no HID reports;
- current investigation therefore targets descriptor DMA/content/residual/settle handling after the successful address command rather than assuming the xHCI command itself failed.

## Active physical-input repair — r10 hardware decode / descriptor diagnostics
Primary patch:
- `tools/ci/patch_v108_physical_input_r10_hwdecode.py`
- created on `v108-physical-input-bringup`
- exact input r9 source SHA `5b2384f8e128b1ec6922f34c14478918c3388179937c2000dd12135fefcf682c`
- exact CI-produced r10 source SHA `b2dee4fc2c1ca3ad68d4428febf564a2143948ee797ea74ee532ac87b2c14ab6`

### r10 touchpad changes
r10 does not assume the laptop is definitely Elantech. It adds a guarded six-byte auto-detection path while preserving the known-good standard PS2 path.

- rolling six-byte AUX window;
- repeated-signature requirement before switching away from unknown/standard mode;
- Elantech-v4-like status/head/motion frame recognizer based on six-byte signatures;
- absolute X/Y extraction for recognized head packets;
- absolute-to-bounded-relative conversion for the diagnostic cursor;
- maximum converted step bounded at 40 px;
- implausible absolute jumps above 512 units rejected;
- standard three-byte PS2 remains fallback/reference behavior;
- kernel-side decoder self-test (`ps2_elan4_selftest_v110`) is executed by input backend preparation;
- expanded on-screen telemetry includes protocol mode and the full recent six-byte window:
  - `P2 R PH PK`: PH protocol mode (`0` unknown, `1` standard PS2, `4` Elantech-v4-like lock in r10);
  - `P2 A0 A1 A2` and `P2 B0 B1 B2`: recent six-byte frame/window;
  - `SRC X Y`: accepted input source and cursor coordinates.

This is a hypothesis-testing decoder. Do NOT claim the user's touchpad is Elantech until physical telemetry shows the r10 recognizer locking consistently and real cursor behavior is controllable.

### r10 USB changes
- retain r7/r9 EP0/address repair and descriptor retry logic;
- add a bounded post-address settle delay before full descriptor transfer;
- record xHCI transfer residual length at `xhci_state+576`;
- expanded row `USB D L T C R`:
  - D = transfer residual;
  - L = descriptor length byte returned;
  - T = descriptor type byte returned;
  - C = configuration count;
  - R = descriptor attempt count;
- retain `USB S T X E` completion telemetry.

Goal: if real hardware still stops at stage 5, the next photo can distinguish no DMA payload, short/residual transfer, malformed descriptor data, or later validation failure.

## r10 VM build and source-run evidence
Primary workflow:
- `.github/workflows/frames-v108-physical-input-r10-rufus.yml`
- authoritative source run `31960209876`
- head commit `ada1040e7f1526c936ed0833d889759592383a04`

Substantive results on the exact r10 candidate:
- exact certified-v108 reconstruction through r10: PASS
- destructive-write surface audit: PASS
- build/package Rufus UEFI ISO: PASS
- decoder-model/source seal: PASS
- USB stable live-input visual gate: PASS
- PS2 stable live-input visual gate: PASS
- read-only NVMe sentinel gate: PASS

The smoothness job in source run `31960209876` did NOT execute its test: its workspace order downloaded the candidate and then checkout deleted the `candidate/` directory. That job is an infrastructure failure only and is not accepted as smoothness evidence.

Exact source-run candidate:
- candidate artifact ID `9267039522`
- candidate artifact ZIP SHA-256 `5cf2980143140c689ea7b8d38aae39190db46c17a6aedaac1211219b8f0a722b`
- exact ISO SHA-256 `ef9d3cd24724acf4cf3bfb75708393c1b8de3a2f5fefeba7e0281acda125cde7`
- exact ISO size `18,745,344 bytes`

Independent local check of source-run PS2 evidence:
- `status=PASS`
- initial cursor `396,290`
- final cursor `400,292`
- actual movement `+4,+2`
- changed pixels outside telemetry `112`
- idle changed pixels `0`
- actual framebuffer inspected; desktop remains intact and cursor is singular/localized.

## r10 quantitative smoothness final recert — PASS
Workflow:
- `.github/workflows/frames-v108-r10-smoothness-final-recert.yml`
- creation commit `7578a3a44109e6b8a7908f4adbd5485b296df580`
- run `31960415886`: PASS

This workflow does NOT rebuild a different kernel/ISO. It downloads and hash-verifies the immutable source-run candidate artifact `9267039522`, verifies the existing source-run USB/PS2/decoder/read-only PASS evidence, reruns the 42-step PS2 smoothness test with the corrected checkout/download order, and seals the same exact ISO only if everything passes.

Verified source evidence artifact:
- ID `9267076216`
- ZIP SHA-256 `5de5bdec6d15c91e166a1adf17014ec2a5f8fcb46cdbbf1bf5d5193e9ef3fa24`

Smoothness recert artifact:
- ID `9267089226`
- ZIP SHA-256 `bbfbd5e8c1a3d3ef2584aa8a511ace744eaedf0be8212780e53dc4944ec52838`
- exact ISO SHA inside smoothness evidence `ef9d3cd24724acf4cf3bfb75708393c1b8de3a2f5fefeba7e0281acda125cde7`
- gate `ps2_cursor_smoothness_v1`: PASS
- pre-input idle change: `0 px`
- 42 requested steps all matched direction/magnitude;
- 1-pixel micro steps remained exactly 1 px;
- 3-pixel vertical steps remained exactly 3 px;
- ramp `1,2,3,4,5` matched exactly in both directions;
- maximum single-step jump `5 px`;
- maximum cross-axis drift `0 px`;
- final return error `0,0`;
- post-test idle cursor remained stationary;
- maximum changed pixels outside telemetry per step `115`.

Independent local verification:
- final artifact manifest: PASS after normalizing artifact-directory prefix;
- smoothness evidence manifest: PASS after normalizing artifact-directory prefix;
- exact contained ISO SHA/size independently recomputed and matched recorded identity.

## Exact r10 physical-test artifact — NEXT AUTHORIZED BOOT
Final recertified artifact:
- name `Frames-v108-r10-Rufus-Final-Recertified`
- artifact ID `9267091554`
- artifact ZIP SHA-256 `19b535952b83a87e5bac67981e5e709a7fd4fc45c85ee6ca4444410a9e11218e`

Exact contained ISO:
- `Frames-0.9.98-v108-Physical-Input-Repair-r10-Rufus-UEFI.iso`
- SHA-256 `ef9d3cd24724acf4cf3bfb75708393c1b8de3a2f5fefeba7e0281acda125cde7`
- size `18,745,344 bytes`
- Rufus mode: ISO Image mode

Final certification record:
- VM USB live input: PASS
- VM PS2 live input: PASS
- VM quantitative standard-PS2 cursor smoothness: PASS
- r10 decoder model/selftest: PASS
- read-only safety: PASS
- physical touchpad: PENDING
- physical USB: PENDING
- physical destructive writes: BLOCKED

## Claim policy — touchpad
Do NOT call the touchpad physically fixed until BOTH are true:
1. the exact candidate passes the GitHub quantitative smoothness gate; and
2. the user's real laptop demonstrates controllable right/left/up/down movement without random jumps or idle drift.

r10 satisfies condition 1 only. Condition 2 is still pending physical hardware.

## Next physical test — r10 exact ISO
Use only ISO SHA:
`ef9d3cd24724acf4cf3bfb75708393c1b8de3a2f5fefeba7e0281acda125cde7`

Rufus: ISO Image mode.

Test order:
1. boot and wait for `INPUT V108 LIVE` panel;
2. do not move anything initially; photograph panel if practical;
3. move touchpad slowly right, left, down and up;
4. observe whether the visible cursor follows direction smoothly and whether `PH` changes to a stable protocol mode;
5. stop touching the pad for several seconds and confirm cursor does not wander;
6. photograph the expanded `P2 A0 A1 A2`, `P2 B0 B1 B2`, `P2 R PH PK`, and `SRC X Y` rows after touchpad movement;
7. move external USB mouse;
8. if USB still fails, photograph both `USB S T X E` and `USB D L T C R` rows;
9. do not interpret VM PASS as physical PASS; physical hardware result remains authoritative.

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
