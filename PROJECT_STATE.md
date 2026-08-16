# Frames — Canonical Project State

> Authoritative cross-chat handoff for active Frames engineering.
> Repository/evidence overrides chat summaries and prior claims.

Last updated: 2026-08-16

## Project identity / safety
- Frames is an independent OS using Nexus.
- Boot: UEFI -> BOOTX64.EFI -> FramesKernel.fkrn.
- Evidence: fail-closed, exact-source/hash, QEMU/OVMF-first, then physical confirmation for hardware claims.
- Frames 1.0 is NOT promoted.
- Physical destructive writes remain uncertified and blocked.
- Installation/persistent internal-media modification remain locked.
- User-facing physical-test artifacts must be Rufus-compatible UEFI ISOs; raw IMG is CI-only.

## Fresh certified foundation — Frames 0.9.98 v108 r9
- workflow `.github/workflows/main.yml`
- fresh run `31831716862`, attempt 2: PASS
- source commit `7333a6670a38c9180e7d72c2a3df444409c36164`
- runtime kit SHA-256 `61b0fc25513719fce554729724c7848647de9cffe54434d4ab5f7ba8af42a36a`
- nested source SHA-256 `5f8c13adac6d34e64bd47d9463a3e261cd0b51bb5ddb500aa9f7b87c2914a52d`
- exact certified `kernel/main.nx` SHA-256 `ffc5721eca68844357dbdca63b0edf266e7e210f9d162eecde8cae0067f210a8`
- evidence artifact `9257820749`
- evidence ZIP SHA-256 `b7589b75190186b3886e76e8e571bbee1d58884e8a5516338ba59c994427ce74`

Active branch: `v108-physical-input-bringup`.
All current physical-input work is reconstructed from the exact certified v108 source; v109-v116 transforms are excluded.

## Authoritative real-hardware result from r6
The user's laptop booted the stable r6 Rufus diagnostic ISO and supplied baseline, USB-movement and touchpad-movement photos.

### External USB mouse — physical FAIL before HID
Observed unchanged while moving USB mouse:
- `USB H R P = 0, 0, 16`
- `USB S T C = 5, 8, 0, 0`
- no USB live-report increase
- no pointer-coordinate movement from USB

Meaning:
- stage 5: first 8 bytes of USB device descriptor obtained;
- 8 scan attempts exhausted;
- class still 0;
- failure occurs after descriptor-8, before full descriptor/HID discovery.

A separate QEMU topology probe also proves v108 lacks USB-hub traversal:
- workflow `.github/workflows/frames-v108-usb-hub-topology-probe.yml`
- run `31929194248`
- direct xHCI mouse: supported
- mouse behind hub: `NO_HID_BEHIND_TOPOLOGY`

The laptop's first known blocker, however, is the earlier physical stage-5 transition.

### Built-in touchpad — physical PS/2/AUX ingress PROVEN
Before touchpad motion: internal pointer around `396,290` with essentially no live packet count.
After motion, physical panel approximately showed:
- `PS2 E PK = 1, 21`
- `P2 O A K = 1410, 1410, 0`
- `P2 R PH PK = 1410, 0, 21`
- `P2 SY R1 R2 = 245, 1047, 71`
- `P2 B0 B1 B2 = 45, 16, 49`
- `SRC = 2`
- internal pointer moved to about `1194,0`

Therefore on the real laptop:
- i8042/PS2 bytes arrive;
- they classify as AUX;
- Frames decodes some packets;
- source becomes PS2;
- internal GUI pointer coordinates change from real touchpad motion.

Touchpad is not an I2C-only dead end on this machine. Remaining physical questions are visible cursor behavior and motion quality. High reject counts indicate later packet synchronization tuning may still be needed.

### r6 framebuffer observation
The earlier full-screen repaint problem is fixed. During physical touchpad motion only the diagnostic box flickers/refreshes. That is expected telemetry redraw.

## r7 result — VM PASS, superseded before physical handoff
r7 added:
- EP0 current transfer-ring dequeue pointer before second xHCI Address Device command;
- xHCI completion-code telemetry;
- cursor-only background save/restore and motion presentation.

Exact final r7 source SHA-256:
`d458aa61d92ff33bcf7e529354deec7cd345d5d96188c95b08842853fa3e3e2b`

Workflow run `31931069383`: build, USB VM input, PS2 VM input, read-only safety and final seal all PASS.

r7 ISO:
- SHA-256 `745236c199f88b15234ac7aa1bcd3a807c4cb960124aae90873733a62a101d35`
- size `18,728,960`

Independent screenshot inspection then found a static ghost cursor caused by existing desktop compose code reading cursor fields with wrong offsets (`+16/+24` instead of `+8/+16`). r7 was therefore NOT handed to the user for physical testing.

## Active physical candidate — r8 single-cursor + r7 USB repair
r8 fixes the ghost cursor while retaining the r7 xHCI repair.

Patch:
- `tools/ci/patch_v108_physical_input_r8_cursor_offsets.py`
- r7 input SHA `d458aa61d92ff33bcf7e529354deec7cd345d5d96188c95b08842853fa3e3e2b`
- exact r8 `kernel/main.nx` SHA `b0e7893dea8306b44ea044b5e712fb4568223b5bdd599b9d369f19e523bad037`

r8 cursor repair:
- fixes all eight incorrect cursor structure reads;
- canonical cursor fields are `+8 = X`, `+16 = Y`, `+24 = width`;
- performs one clean desktop redraw at input-runtime startup with the cursor temporarily hidden;
- restores cursor pointer, captures clean backing pixels and draws one correctly positioned cursor;
- subsequent movement redraws only old/new 8x16 cursor rectangles plus telemetry;
- continuous full-desktop repaint remains disabled.

r7 USB repair retained in r8:
- after descriptor-8, EP0 input-context dequeue uses the current software transfer-ring enqueue pointer before second Address Device;
- updated EP0 max-packet size retained;
- telemetry fourth USB stage value exposes xHCI command completion/error code.

### r8 certification
Authoritative successful workflow:
- `.github/workflows/frames-v108-physical-input-r8b-rufus.yml`
- run `31931560447`: PASS

Parallel required lanes:
- build/package: PASS
- USB VM live input + single-cursor visual gate: PASS
- PS2 VM live input + single-cursor visual gate: PASS
- read-only safety: PASS
- final seal: PASS

Exact r8 payload:
- `BOOTX64.EFI` SHA-256 `69942fa4f886c949b1375abc0fdc9198af86234b690646f9ec9ea29ccae69f04`
- `FramesKernel.fkrn` SHA-256 `61db147e58337dee9c559774772f70890df2422bebf61f99f8d43d5fcbbb8267`
- source `kernel/main.nx` SHA-256 `b0e7893dea8306b44ea044b5e712fb4568223b5bdd599b9d369f19e523bad037`

Exact r8 physical-test ISO:
- `Frames-0.9.98-v108-Physical-Input-Repair-r8-Rufus-UEFI.iso`
- SHA-256 `042b73cbd926b75b33102b1b1a8d5f26efcc00840409f74d38bcadfa88d12f44`
- size `18,728,960 bytes`
- Rufus mode: **ISO Image mode**
- final artifact ID `9259478279`
- final artifact ZIP SHA-256 `12bf34630a71f207f4edced9314f540817e30bc55820924595f78977c407dcb7`

Independent local artifact verification:
- final ZIP manifest: PASS
- USB evidence manifest: PASS
- PS2 evidence manifest: PASS
- exact ISO SHA/size: PASS
- read-only safety status: PASS

VM visual evidence:
- PS2 lane: PASS, one cursor only, initial cursor at about `396,290`, moved to about `404,294`, 395 framebuffer pixels changed, legacy ghost absent before and after.
- USB lane: PASS, one cursor only, initial cursor at about `396,290`, moved to about `404,294`, 235 framebuffer pixels changed, legacy ghost absent before and after.
- no full-screen repaint in either lane.

This is VM evidence only. It does NOT claim the user's physical USB mouse or touchpad visible cursor is fixed yet.

## Next physical test — r8
Use only exact ISO SHA:
`042b73cbd926b75b33102b1b1a8d5f26efcc00840409f74d38bcadfa88d12f44`

Rufus: **ISO Image mode**.

Physical test order:
1. boot r8 and wait for the input telemetry panel;
2. move built-in touchpad slowly right/left/up/down;
3. check whether the single visible cursor now moves; diagnostic box flicker is acceptable, full-screen repaint is not;
4. then move external USB mouse;
5. if USB still fails, photograph the `USB S T C E` row; the fourth `E` value is the xHCI completion/error code;
6. if touchpad moves but is jumpy/erratic, report that behavior; packet-quality tuning is the next touchpad task.

Physical destructive writes remain blocked during this test.

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
