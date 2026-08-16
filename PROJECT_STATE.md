# Frames — Canonical Project State

> Authoritative cross-chat handoff for active Frames engineering.
> Repository/evidence overrides chat summaries and prior claims.

Last updated: 2026-08-16

## Project identity / safety
- Frames is an independent OS using Nexus.
- Boot chain: UEFI -> BOOTX64.EFI -> FramesKernel.fkrn.
- Evidence is fail-closed: exact source/hash, QEMU/OVMF first, then real hardware for physical claims.
- VM PASS is never described as physical PASS.
- Generated/mockup images are never Frames runtime evidence.
- Frames 1.0 is NOT promoted.
- Physical destructive writes, installation, persistent internal-media modification, and release promotion remain blocked.
- User-facing physical-test artifacts must be Rufus-compatible UEFI ISOs; raw IMG is CI-only.
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

All current physical-input work reconstructs this exact v108 source. v109-v116 architecture transforms are intentionally excluded from this bring-up train.

## Authoritative real-hardware input results
### Touchpad
The user's ASUS gaming laptop is a circa-2014 Core i7 / GTX 860M generation system. Physical telemetry strongly supports a legacy PS/2-compatible ELAN/Synaptics-style path rather than I2C-HID for this machine.

r9 physical result:
- i8042/AUX transport active, roughly 2208 AUX bytes seen;
- zero accepted motion packets;
- showed protocol/framing rather than electrical/transport failure.

r10 physical breakthrough:
- six-byte Elantech-v4-like recognizer locked with `PH=4`;
- hundreds of packets accepted;
- `SRC=2` touchpad path active;
- cursor physically moved smoothly in the requested direction;
- sensitivity was too low.

r11 physical result:
- sensitivity substantially improved and cursor remained controllable;
- intermittent stalls remain: telemetry continues changing during some finger motion while cursor temporarily does not move;
- this is the active touchpad responsiveness/latency issue, not a complete touchpad failure.

### External USB mouse
r11 physical result:
- external USB mouse still produced no cursor movement;
- descriptor/config telemetry advanced farther than earlier revisions but no live HID report reached the GUI.

Known software gap identified by VM topology probe:
- direct xHCI USB mouse worked;
- mouse behind a USB hub failed because Frames did not traverse hubs.

That gap has now been implemented and VM-certified in r13, but physical USB remains PENDING until the user's laptop proves it.

### Keyboard
Physical keyboard validation is PENDING. The user's laptop keyboard itself is known to behave erratically at times (including spontaneous/repeating letters), so Frames diagnostics must distinguish make/break events, repeats/stuck keys, and actual text delivery instead of assuming all odd input is an OS bug.

## r12b combined touchpad-latency + keyboard + interactive test UI — VM PASS
Corrected source chain:
- r12 intermediate SHA `70e01c31e669679ec8de986cddfb361a3686681ce109740c16a7e50bb1a90be3`
- r12b source SHA `92782808bd0cda553f6f84116dc8761cefc561c2c025c464cbfe7830b72df81b`
- repair `tools/ci/patch_v108_physical_input_r12b_pollfix.py`

r12/r12b adds:
- Elantech-v4 motion-packet handling in addition to head packets;
- burst/drain PS/2 polling to reduce event backlog/latency;
- reduced diagnostic redraw pressure;
- PS/2 keyboard make/break decode;
- basic Shift/Caps/text mapping;
- repeat/stuck-key telemetry/suppression;
- real `INPUT TEST` UI with text box, `CLICK TEST`, and `CLEAR` controls.

Authoritative r12b workflow:
- `.github/workflows/frames-v108-physical-input-r12b-rufus.yml`
- run `31964885466`: PASS
- head `b0b9378552f5ca711d781daae77dfab23a214b5a`
- all build, USB, PS/2, smoothness, interactive, model, safety, and final jobs PASS.

Exact r12b ISO:
- `Frames-0.9.98-v108-Physical-Input-Repair-r12b-Rufus-UEFI.iso`
- SHA-256 `3b08bf72557735c1b8ac36c1cafbf0d00345d38774b75b2a8587bdcf0996d7e6`
- size `18,786,304 bytes`
- Rufus: ISO Image mode

Interactive VM evidence:
- keyboard text marker PASS;
- click-test marker PASS;
- textbox framebuffer visibly changed and contained typed text;
- physical keyboard/click remain unclaimed until hardware test.

## r13 USB-hub + r12b combined input candidate — NEXT AUTHORIZED PHYSICAL BOOT
USB hub implementation branch:
- `v108-usb-hub-topology-r1`

Hub repair provenance:
- hub-r2 pre-ABI-repair source SHA `8ebec9c4ed641be22eccf3294a9f478093189d4ad36c454605b1b273dd662cd6`
- hub-r3 exact source SHA `7bc6594c05e71d821a07275a7ded816869681fa2d328e64f18dee0ebd0f02ce9`
- ABI repair `tools/ci/patch_v108_usb_hub_topology_r3_abi.py`
- Nexus x64 4-parameter ABI compile probe run `31967066233`: PASS

r13 hub implementation adds first-tier USB hub traversal:
- hub class recognition;
- hub descriptor/configuration path;
- downstream port power/status/reset handling;
- xHCI child slot route/context setup;
- child device descriptor/finalize-address flow;
- child boot-HID discovery/configuration;
- runtime markers `FRAMES_USB_HUB_FOUND`, `FRAMES_USB_HUB_CHILD_FOUND`, `FRAMES_USB_HUB_CHILD_HID_OK`.

Authoritative combined r13 workflow:
- `.github/workflows/frames-v108-usb-hub-topology-r3-cert.yml`
- run `31967222521`: PASS
- head `b28115ea45df0e18b1c19f62294c5314982fd52b`
- exact-source reconstruction: PASS
- destructive-write surface audit: PASS
- build/Rufus packaging: PASS
- VM USB direct mouse: PASS
- VM USB mouse behind hub: PASS
- VM PS/2 input: PASS
- VM quantitative PS/2 smoothness: PASS
- VM clickable controls + keyboard text: PASS
- source/model gate: PASS
- read-only NVMe sentinel: PASS
- final seal: PASS

Independent hub evidence check:
- hub `TOPOLOGY.json`: PASS
- exact ISO SHA in hub evidence `ceb2201bd641e8f950929730e1dd6a0db8c7049aa29f0a133533e38fd55900a6`
- hub found: true
- hub child found: true
- hub child HID: true
- live USB report: true
- GUI cursor: true
- serial markers for all of the above present;
- evidence manifest hashes independently matched after normalizing GitHub artifact directory prefix.

Independent interactive evidence check:
- `r12_interactive_pointer_keyboard_ui`: PASS on the same r13 ISO SHA;
- keyboard text marker true;
- click marker true;
- textbox visual change true;
- actual final framebuffer inspected: `INPUT TEST` panel visible, text `ABC` visible, `CLICK TEST` count `1` visible.

Independent safety check:
- read-only sentinel before/after SHA identical: `83ee47245398adee79bd9c0a8bc57b821e92aba10f5f9ade8a5d1fae4d8c4302`.

Exact r13 physical-test ISO:
- `Frames-0.9.98-v108-Physical-Input-Repair-r13-USB-Hub-Rufus-UEFI.iso`
- SHA-256 `ceb2201bd641e8f950929730e1dd6a0db8c7049aa29f0a133533e38fd55900a6`
- size `18,796,544 bytes`
- Rufus: ISO Image mode
- final artifact ID `9268854072`
- final artifact ZIP digest `d124bb91a5cd215f1a600ab27a1c97d7ed557e005e062817688ab3a69eb616b6`

## r13 physical test order
Use only exact ISO SHA `ceb2201bd641e8f950929730e1dd6a0db8c7049aa29f0a133533e38fd55900a6`.

1. Boot in UEFI mode and wait for the input test desktop.
2. Touchpad: test small and long movements in all directions; note whether the r11 intermittent cursor stalls are reduced/eliminated.
3. Click: physically press/click the touchpad while over `CLICK TEST`; confirm click count changes.
4. Text box: click `TEXT BOX`, type a short known sequence such as `ABC123`; observe typed text and keyboard make/break/repeat counters.
5. Because the physical keyboard is known to be flaky, report both what was intentionally typed and any spontaneous/repeated characters separately.
6. External USB mouse: move it in all directions and test a button click. This is the first physical candidate containing VM-certified USB-hub traversal.
7. If any path fails, photograph the complete `INPUT V108 LIVE` panel plus `INPUT TEST` panel.

Physical PASS is not inferred from VM PASS. The user's real-machine result is authoritative.

## Claim policy
- Touchpad: physically proven to move and be controllable since r10/r11, but intermittent stalls remain pending r13 physical retest.
- USB hub traversal: VM-certified in r13; physical external USB mouse remains PENDING.
- Keyboard/text/click UI: VM-certified in r12b/r13; physical keyboard and physical click behavior remain PENDING.
- Frames 1.0 remains NOT promoted.
- Physical destructive writes remain BLOCKED.

## Automatic progression
- Run independent workflows/lanes in parallel whenever practical.
- Failure -> diagnose -> repair -> rerun automatically.
- Pass -> independently verify -> update this file -> continue automatically.
- Stop only for genuine physical hardware/user action, required user information, authorization, or safety boundary.

## New-chat startup
1. Read `PROJECT_STATE.md`.
2. Read `CONTINUITY_PROTOCOL.md`.
3. Inspect the active branch/run/evidence named here.
4. Repository/evidence overrides older chat/project summaries.
5. Do not silently pivot to another roadmap or claim level.
