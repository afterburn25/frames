# Frames — Canonical Project State

> Authoritative cross-chat handoff for active Frames engineering.
> Repository/evidence overrides chat summaries and prior claims.

Last updated: 2026-08-16

## Project identity / safety

- Frames is an independent OS using Nexus.
- Boot chain: UEFI -> BOOTX64.EFI -> FramesKernel.fkrn.
- Evidence model is fail-closed: exact source/hash, QEMU/OVMF first, then real hardware for physical claims.
- Frames 1.0 is NOT promoted.
- Physical destructive writes, installation, persistent internal-media modification, and release promotion remain blocked.
- User-facing physical-test artifacts must be Rufus-compatible UEFI ISOs. Raw IMG is CI-only.
- Independent workflows/lanes should run in parallel whenever practical.

## Certified reconstruction foundation — Frames 0.9.98 v108 r9

Fresh unchanged certification:
- workflow `.github/workflows/main.yml`
- run `31831716862`, attempt 2: PASS
- source commit `7333a6670a38c9180e7d72c2a3df444409c36164`
- runtime kit SHA-256 `61b0fc25513719fce554729724c7848647de9cffe54434d4ab5f7ba8af42a36a`
- nested source ZIP SHA-256 `5f8c13adac6d34e64bd47d9463a3e261cd0b51bb5ddb500aa9f7b87c2914a52d`
- exact certified base `kernel/main.nx` SHA-256 `ffc5721eca68844357dbdca63b0edf266e7e210f9d162eecde8cae0067f210a8`
- evidence artifact `9257820749`
- evidence ZIP SHA-256 `b7589b75190186b3886e76e8e571bbee1d58884e8a5516338ba59c994427ce74`

Active branch: `v108-physical-input-bringup`.
All current physical-input work reconstructs exact certified v108. v109-v116 transforms are excluded from this bring-up train.

## Authoritative physical result — r10 on user's ASUS laptop

Exact tested ISO:
- `Frames-0.9.98-v108-Physical-Input-Repair-r10-Rufus-UEFI.iso`
- SHA-256 `ef9d3cd24724acf4cf3bfb75708393c1b8de3a2f5fefeba7e0281acda125cde7`
- size `18,745,344 bytes`
- Rufus mode: ISO Image mode

### Touchpad — FIRST REAL PHYSICAL POINTER SUCCESS

The user's built-in touchpad physically moved the Frames cursor smoothly in the intended direction.

Representative physical telemetry from the supplied photo:
- `PS2 E PK = 1, 704`
- `P2 O A K = 6101, 6101, 0`
- `P2 R PH PK = 6101, 4, 704`
- `P2 SY R1 R2 = 1121, 18, 0`
- `SRC X Y = 2, 922, 131`

Physical conclusions:
- i8042/AUX transport: PASS on this laptop.
- r10 six-byte recognizer locked at `PH=4` on real hardware.
- hundreds of touchpad packets were accepted.
- Generic Pointer source became `SRC=2`.
- real cursor direction/control: PASS.
- movement smoothness: physically usable, but sensitivity is too low.
- some initial/small movements require repeating.
- physical click/tap behavior is NOT yet proven.

Do not reduce this to a VM claim: this is the first user-observed real-hardware Frames pointer movement.
Do not overstate it either: touchpad tuning and physical button/click proof remain pending.

### External USB mouse — STILL PHYSICAL FAIL at r10

User observed no USB mouse cursor motion.

Representative physical telemetry:
- `USB H R P = 0, 0, 16`
- `USB S T X E = 6, 8, 1, 1`
- `USB D L T C R = 0, 18, 1, 1, 1`

Interpretation:
- the full 18-byte device descriptor is now valid on physical hardware;
- the blocker moved beyond address/full-device-descriptor completion;
- r10 still exhausted an artificial 8-attempt/8-slot scan boundary;
- HID configuration/report delivery never became physically active.

Known separate USB topology gap:
- workflow `.github/workflows/frames-v108-usb-hub-topology-probe.yml`
- run `31929194248`
- direct xHCI mouse: VM supported
- mouse behind hub: `NO_HID_BEHIND_TOPOLOGY`

## r11 active repair — touchpad gain + click proof + expanded USB discovery

Primary patch:
- `tools/ci/patch_v108_physical_input_r11_touch_usb.py`
- creation commit `a137c3bc3882be7527ec78d3f70ed8ddbd460161`
- exact r10 input SHA `b2dee4fc2c1ca3ad68d4428febf564a2143948ee797ea74ee532ac87b2c14ab6`
- exact r11 output source SHA `4e6b4fd0f4c44020099e2c097615d3b6f03e8e123763fd803c90eb1d40f3b016`

r11 changes:
- Elantech-like physical gain changes from approximately 1/8 to 1/4;
- maximum converted physical step increases from 40 px to 64 px while retaining implausible-jump rejection;
- left/right button transitions are extracted from all recognized Elantech-v4-like packet types, not only motion packets;
- hardware-button and GUI-button telemetry are separated;
- marker `FRAMES_V108_GUI_CLICK_OK` proves a button event reaches the GUI layer in VM;
- stable diagnostic runtime again calls desktop/appearance click handlers for kind-4 button events;
- xHCI `MaxSlots` diagnostic cap raised from 8 to 32;
- root-port HID scan cap raised from 8 to 32;
- configuration descriptor/header retries and interface/subclass/protocol/endpoint telemetry added.

The stale self-hash in `patch_v108_physical_input_r10_hwdecode.py` was corrected to the already-certified r10 output SHA. This changes no r10 output bytes; it only makes the patch script exit consistently with its actual sealed result.

## r11 certification — VM PASS, physical pending

Workflow:
- `.github/workflows/frames-v108-physical-input-r11-rufus.yml`
- run `31962777837`, attempt 2: PASS
- workflow head `569a0ac14a41f33160979d450bd8d1c2f8528ba5`

Parallel gates on the same exact r11 ISO:
- exact source reconstruction: PASS
- destructive-write surface audit: PASS, zero hits
- VM USB live input + localized cursor motion: PASS
- VM PS/2 live input + localized cursor motion: PASS
- VM quantitative standard-PS2 smoothness: PASS
- VM PS/2 button -> GUI click layer: PASS
- r11 source/model contract: PASS
- read-only internal NVMe sentinel: PASS, sentinel hash unchanged
- final aggregate seal: PASS

Independent inspection:
- USB runtime: cursor `396,290 -> 400,292`, changed pixels outside telemetry `112`, idle changed pixels `0`
- PS/2 runtime: cursor `396,290 -> 400,292`, changed pixels outside telemetry `112`, idle changed pixels `0`
- actual USB and PS/2 AFTER framebuffers inspected; desktop remains intact with a singular localized cursor
- click JSON: PASS with `gui_click_marker=true`
- smoothness JSON: PASS
- read-only safety result: PASS

Candidate artifact:
- `Frames-v108-r11-Candidate`
- artifact ID `9267709712`
- artifact ZIP SHA-256 `bb41a06c48234004a93a2bb06107835e15be956703b5769b8b0125b41e2b7e40`

Final artifact:
- `Frames-v108-r11-Rufus-Final`
- artifact ID `9267735713`
- artifact ZIP SHA-256 `5403a852857cde8842561e75d432e5d962735db1d272299db3c5615790cb6eb9`

### Exact next authorized physical-test ISO

- `Frames-0.9.98-v108-Physical-Input-Repair-r11-Rufus-UEFI.iso`
- SHA-256 `f4657955ce073fe244e647c77b690324f2da13a21645faf1893ddf8d0170c07d`
- size `18,753,536 bytes`
- Rufus mode: **ISO Image mode**

Physical r11 claims remain PENDING until user hardware confirms them.

## Next physical test — r11

1. Boot exact SHA `f4657955ce073fe244e647c77b690324f2da13a21645faf1893ddf8d0170c07d` using Rufus ISO Image mode.
2. Test touchpad motion in all directions, including small movements; judge whether sensitivity is materially improved and whether first motion registers reliably.
3. Stop moving and confirm no idle cursor drift.
4. Physically press the touchpad left button/clickpad and, if supported, right button. Also try a normal tap once, but keep button press and tap results separate.
5. Observe `BTN H HP G GP`:
   - H = hardware button state
   - HP = hardware left-press count
   - G = GUI button state
   - GP = GUI left-press count
6. Test external USB mouse.
7. If USB still fails, photograph `USB H R P`, `USB S T X E`, `USB D L T C R`, and new `USB G L I S P E` row.
8. Physical destructive writes remain blocked.

## Claim policy

- Touchpad physical movement is proven on r10.
- Touchpad sensitivity improvement is not proven until r11 physical test.
- Touchpad physical clicking is not proven until r11 physical `BTN` telemetry and observed behavior confirm it.
- USB mouse remains physically unproven/failing until the real machine produces HID reports/cursor movement.
- VM PASS never substitutes for physical PASS.

## Automatic progression

- Run independent workflows/lanes in parallel whenever practical.
- Failure -> diagnose -> repair -> rerun automatically.
- Pass -> independently verify -> update this file -> continue automatically.
- Stop only for genuine physical hardware/user action or a safety/authorization boundary.

## New-chat startup

1. Read `PROJECT_STATE.md`.
2. Read `CONTINUITY_PROTOCOL.md`.
3. Inspect active branch/run/evidence named here.
4. Repository/evidence overrides older chat summaries.
5. Resume from the exact pending physical or CI gate; do not fall back to the old v116/static-GUI narrative.
