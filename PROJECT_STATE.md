# Frames — Canonical Project State

> Authoritative cross-chat handoff for active Frames engineering.
> Repository/evidence overrides chat summaries and prior claims.

Last updated: 2026-08-16

## Project identity / safety
- Frames is an independent OS using Nexus.
- Boot: UEFI -> BOOTX64.EFI -> FramesKernel.fkrn.
- Evidence model: fail-closed, exact-source/hash, QEMU/OVMF-first, then physical confirmation for hardware claims.
- Frames 1.0 is NOT promoted.
- Physical destructive writes remain uncertified and blocked.
- Installation/persistent internal-media modification remain locked.
- User-facing physical-test artifacts must be Rufus-compatible UEFI ISOs; raw IMG is CI-only.

## Certified reconstruction foundation — Frames 0.9.98 v108 r9
- workflow `.github/workflows/main.yml`
- fresh run `31831716862`, attempt 2: PASS
- source commit `7333a6670a38c9180e7d72c2a3df444409c36164`
- runtime kit SHA-256 `61b0fc25513719fce554729724c7848647de9cffe54434d4ab5f7ba8af42a36a`
- nested source SHA-256 `5f8c13adac6d34e64bd47d9463a3e261cd0b51bb5ddb500aa9f7b87c2914a52d`
- exact certified `kernel/main.nx` SHA-256 `ffc5721eca68844357dbdca63b0edf266e7e210f9d162eecde8cae0067f210a8`
- evidence artifact `9257820749`
- evidence ZIP SHA-256 `b7589b75190186b3886e76e8e571bbee1d58884e8a5516338ba59c994427ce74`

Active branch: `v108-physical-input-bringup`.
All physical-input work is reconstructed from this exact certified v108 source; v109-v116 architecture transforms are intentionally excluded from this bring-up train.

## Latest authoritative physical result — r8 on user's laptop
Exact tested ISO:
- `Frames-0.9.98-v108-Physical-Input-Repair-r8-Rufus-UEFI.iso`
- SHA-256 `042b73cbd926b75b33102b1b1a8d5f26efcc00840409f74d38bcadfa88d12f44`
- size `18,728,960 bytes`
- Rufus mode: ISO Image mode
- r8 VM certification run `31931560447`: PASS

The user's physical r8 photo supersedes the earlier r6-only diagnosis.

### Built-in touchpad / PS2-AUX — transport and visible cursor movement PROVEN, control quality FAIL
Physical r8 telemetry after touchpad movement approximately:
- `PS2 E PK = 1, 30`
- `P2 O A K = 3066, 3066, 0`
- `P2 R PH PK = 3066, 0, 30`
- `P2 SY R1 R2 = 529, 2279, 192`
- `P2 B0 B1 B2 = 222, 68, 0`
- `SRC X Y = 2, 1895, 72`

Observed behavior: the visible cursor moves, but skips/jumps to apparently random positions and cannot be controlled reliably by direction.

Authoritative conclusions:
- i8042/AUX ingress is working physically;
- Frames receives thousands of AUX bytes;
- some packets decode and drive the real visible cursor;
- `SRC=2` confirms PS2 is the active pointer source;
- the cursor-render path itself is now working;
- the immediate blocker is protocol/framing/motion-quality handling, not transport or cursor visibility;
- 3066 raw AUX bytes but only 30 accepted packets plus very large reject/sync counters is inconsistent with a clean locked standard 3-byte stream and explains the random jumps.

Current repair strategy: protocol probe/normalization plus a sliding packet parser that requires consecutive valid packets and rejects implausible single-packet deltas before emitting motion. Synaptics detection/relative-mode normalization is included; standard PS/2 remains the fallback.

### External USB mouse — physical FAIL after successful second Address Device command
Physical r8 telemetry:
- `USB H R P = 0, 0, 16`
- `USB S T C E = 5, 8, 0, 1`

Observed behavior: external USB mouse does not move the cursor at all.

Interpretation from exact r8 source:
- stage 5 = descriptor-8 was obtained and execution reached the later address/full-descriptor transition;
- 8 scan attempts exhausted;
- class remains 0 because full device descriptor/HID discovery never completes;
- r8 field `E` is `xhci_state+488`, the xHCI command-completion code;
- `E=1` means the second Address Device command completed successfully on the user's real controller;
- therefore the r7 EP0 dequeue/address repair moved the physical failure forward;
- the current first USB blocker is the following 18-byte full device-descriptor control transfer, not the second Address Device command.

A separate known topology gap remains:
- workflow `.github/workflows/frames-v108-usb-hub-topology-probe.yml`
- corrected run `31929194248`
- direct xHCI mouse: supported in VM
- mouse behind hub: `NO_HID_BEHIND_TOPOLOGY`
This hub traversal gap remains required later, but the user's current machine first fails earlier at the full descriptor transfer.

## Stable framebuffer behavior
The previous full-screen repaint bug is fixed. Physical touchpad activity may flicker/update the telemetry panel, but the whole desktop no longer repaints continuously.

r8 also fixed the old static ghost cursor:
- one clean desktop redraw at input-runtime startup with cursor hidden;
- canonical cursor fields restored (`+8=X`, `+16=Y`, `+24=width`);
- subsequent pointer movement updates only old/new cursor rectangles plus telemetry.

## Active repair — r9 protocol lock + USB full-descriptor diagnostics/retry
Primary patch:
- `tools/ci/patch_v108_physical_input_r9_protocol.py`
- patch creation commit `a144066f3acd2affc3eafa33c37532ca16e5dbbf`
- finalized hash-lock commit `a1765d2a9cfc2d716fb04e581115179f9860d229`
- exact input r8 `kernel/main.nx` SHA-256 `b0e7893dea8306b44ea044b5e712fb4568223b5bdd599b9d369f19e523bad037`
- exact finalized r9 output SHA-256 `5b2384f8e128b1ec6922f34c14478918c3388179937c2000dd12135fefcf682c`

### r9 PS2/touchpad changes
- stop PS2 streaming before protocol probe;
- perform Synaptics-style four-SETRES + status probe;
- if Synaptics signature is seen, request relative-mode normalization;
- restore defaults/streaming;
- replace blind phase reset with a three-byte sliding window;
- validate bit-3 header, overflow and sign consistency;
- reject a candidate if either single-packet magnitude exceeds 80;
- on invalid candidate slide by one byte rather than discarding the whole stream;
- require two consecutive valid packets before emitting pointer movement;
- preserve standard 3-byte PS/2 behavior as fallback.

Goal: stop vendor/interleaved/noisy bytes from being interpreted as huge X/Y movements while retaining real relative motion.

### r9 USB changes
- retain the r7 physical EP0 dequeue/address repair;
- retry the 18-byte full device descriptor GET up to 3 times;
- record full-descriptor attempt count, returned descriptor length/type and config count;
- change physical USB telemetry row from `USB S T C E` to `USB S T X E`;
- `X` now displays the xHCI transfer completion code (`xhci_state+504`), which directly diagnoses the full-descriptor control transfer;
- `E` retains the command-completion code (`xhci_state+488`).

### r9 certification state
Initial workflow `.github/workflows/frames-v108-physical-input-r9-rufus.yml`:
- run `31958178899`: FAIL before build due provisional output-hash mismatch;
- transform completed its anchor/replacement checks and CI revealed finalized output SHA `5b2384f8...`;
- no ISO was produced.

The transform hash was then corrected without changing repair semantics.
A stale-hash second run of the original workflow also failed as expected and is not authoritative.

Authoritative rerun workflow:
- `.github/workflows/frames-v108-physical-input-r9b-rufus.yml`
- creation commit `576f776f1b24cea7a7cd1104e09358b2c7bdb016`
- active run `31958310396`
- exact r9 source SHA required: `5b2384f8e128b1ec6922f34c14478918c3388179937c2000dd12135fefcf682c`
- after build, USB VM input, PS2 VM input and read-only safety run independently; final ISO seal requires all lanes PASS.

Do not hand r9 to the user unless this exact run or a later repaired run passes and the exact final artifact/framebuffers are independently inspected.

## Physical artifact delivery policy
- Every user-facing physical-test artifact must be a Rufus-compatible UEFI `.iso`.
- Raw `.img` is internal CI/QEMU only.
- Every delivered ISO must have exact SHA-256/size and QEMU/OVMF evidence first.
- State Rufus mode explicitly.
- VM success never proves a real-hardware USB/touchpad fix; physical hardware remains authority.

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
