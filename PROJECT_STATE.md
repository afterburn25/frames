# Frames — Canonical Project State

> Authoritative cross-chat handoff for active Frames engineering.
> Repository/evidence overrides chat summaries and prior claims.

Last updated: 2026-08-18

## Current physical-input checkpoint — r43 regression -> r44 candidate

### r43 physical result — REJECTED / USB FAIL + TOUCHPAD REGRESSION
Exact tested r43 ISO:
- `Frames-0.9.98-v108-r43-HID-Control-Fallback-Live-Rufus-UEFI.iso`
- SHA-256 `29ed77ee22390f2b374ed8591293275a02c03cf6447c2a80b4187b1710eb881f`
- size `23,328,768 bytes`

Observed physical result on the user's ASUS laptop:
- external USB mouse: FAIL — no cursor control;
- built-in touchpad: FAIL/REGRESSION — touchpad movement stopped in r43;
- photographed fallback row: `R43 C K M N A E = 1 1 1 76 0 11`.

Physical interpretation:
- `C=1`: class-control fallback prepared;
- `K=1`: keyboard HID interface ready;
- `M=1`: mouse HID interface ready;
- `N=76`: fallback polling path executed repeatedly;
- `A=0`: zero GET_REPORT payload bytes were returned;
- `E=11`: fallback ended in status/error 11;
- the simultaneous touchpad loss reproduces the older EP0/control-fallback regression pattern rather than solving USB report delivery.

Engineering conclusion: r43 is rejected as a physical regression. Do not continue tuning the live EP0/class-control GET_REPORT route. The next revision returns to the exact r42 interrupt-IN runtime behavior and adds passive transfer-ring/event-ring/DMA forensics only.

### r44 — HID Transfer-Ring Forensic — NEXT AUTHORIZED PHYSICAL BOOT
r44 is derived from exact r42 behavior, not r43. It does not integrate `v135_hid_control_fallback_prepare` or `v135_hid_control_fallback_poll`, so the r43 live EP0 polling path is removed. r44 preserves the r42 persistent interrupt-IN policy and recovered PS/2/touchpad service while adding non-blocking diagnostic telemetry around the existing xHCI transfer.

r44 does not add a new Stop Endpoint cycle, endpoint reset, Set TR Dequeue, control GET_REPORT, delay loop, or extra HID doorbell. Its purpose is to determine whether the controller consumes the submitted interrupt TRB, DMA-writes report bytes, emits a Transfer Event, and whether that event points back to the submitted TRB.

Authoritative r44 certification identity:
- branch `v108-usb-hub-topology-r1`
- certification commit `bc593c831d5b75adcb87666a77e545ace22b49c6`
- workflow `.github/workflows/frames-v108-r44-hid-ring-forensic-cert.yml`
- GitHub Actions run `32095264934`: PASS
- exact r44 patched source SHA-256 `5fca6164e902f9720bef0d789ca46d2af480b065f32e1a6f61990476066962c1`

Exact next physical-test ISO:
- `Frames-0.9.98-v108-r44-HID-Transfer-Ring-Forensic-Rufus-UEFI.iso`
- SHA-256 `e91158d6219de81c15207286a62c2ba27bb6d15f02e8ebecc97da0a0ee59c73a`
- size `23,330,816 bytes`
- status `PASS_VM_PENDING_PHYSICAL`
- physical handoff `RUFUS_ISO_ONLY`

Artifacts:
- `Frames-v108-r44-Rufus-Final`, artifact ID `9309798612`, ZIP SHA-256 `10ce727fa6e1dc5efcceb8a51056813d8ba4869f2c041935b40d3e55b608a3af`
- `Frames-v108-r44-Evidence`, artifact ID `9309798235`, ZIP SHA-256 `eb3472658b031e419a339195c77917475d091d490541db2a5d1eabe310bba4c5`

Automated r44 evidence status:
- interaction: PASS
- USB direct: PASS
- USB hub: PASS
- USB multi-child: PASS
- USB multi-controller: PASS
- USB keyboard: PASS
- PS/2 delivery: PASS
- quantitative pointer smoothness: PASS
- text edit: PASS
- focus persistence: PASS
- controlled USB flight log: PASS
- logging fail-open behavior: PASS
- internal-media read-only safety sentinel: PASS
- model/source contract: PASS
- physical r44: PENDING

r44 physical overlay adds `R44 A T D V M Q B`:
- `A` = interrupt TD armed/pending;
- `T` = submitted transfer TRB ring index;
- `D` = hardware endpoint dequeue ring index;
- `V` = direct Transfer Events observed for the polling path;
- `M` = direct Transfer Events whose event parameter matches the submitted TRB;
- `Q` = matching endpoint events recovered through the event mailbox;
- `B` = first four bytes currently present in the HID DMA report buffer, packed little-endian.

Interpretation guide for physical r44 evidence:
- `B` changes/nonzero while `V/M/Q` stay zero: device/controller DMA reached the report buffer but event delivery/correlation is broken;
- `D` advances while `V` stays zero: controller consumed the transfer ring but the completion event is being lost or routed elsewhere;
- `V>0` with `M=0`: Frames sees Transfer Events but they point to a different TRB than the submitted HID transfer, indicating ring/cycle/correlation trouble;
- `V>0` and `M>0` while `USB R` remains zero: the hardware event is seen and correlated, moving the failure downstream into completion decode/input delivery;
- `A=1` with no `D`, `V`, `M`, `Q`, or `B` progress: the TD remains armed but the controller/device is not servicing it, pointing toward endpoint scheduling/context rather than GUI/input decode.

VM PASS must not be described as a physical USB-input PASS. r44 remains diagnostic until tested on the ASUS laptop.

## Project identity / safety
- Frames is an independent operating system, not Windows- or Linux-based.
- Native systems language/toolchain: Nexus.
- Boot chain: UEFI -> BOOTX64.EFI -> FramesKernel.fkrn.
- Native application formats: FEX/FAPP.
- Evidence is fail-closed: exact source/hash, QEMU/OVMF first, then real hardware for physical claims.
- VM PASS is never described as physical PASS.
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

All current physical-input work reconstructs this exact v108 source. v109-v116 architecture transforms remain intentionally excluded from this physical-input bring-up train.

## Authoritative r13 physical result — user's ASUS laptop
Exact tested ISO:
- `Frames-0.9.98-v108-Physical-Input-Repair-r13-USB-Hub-Rufus-UEFI.iso`
- SHA-256 `ceb2201bd641e8f950929730e1dd6a0db8c7049aa29f0a133533e38fd55900a6`
- size `18,796,544 bytes`

Observed physical result:
- external USB mouse: FAIL — USB telemetry active but no visible cursor control;
- built-in touchpad: PARTIAL/FAIL — cursor is controllable and buttons work, but movement can jump back to earlier trail positions, especially during vertical motion and near the Input Test box;
- physical left click: PASS at the interactive UI;
- right click: untestable in r13 because no right-click target existed;
- keyboard: PARTIAL PASS — characters reached the text box, but this laptop keyboard has known hardware faults, so individual missed/repeated characters are not automatically attributed to Frames.

Physical interpretation:
- the PS/2/AUX -> Generic Pointer -> GUI path is real and active, but r13 introduced/retained a movement discontinuity;
- the GUI cursor/compositor path is proven by the touchpad, so the external USB mouse failure is upstream of visible pointer rendering;
- physical USB mouse remains unresolved and physical hardware remains authoritative.

## r14 corrective repair — VM certified, not physically tested
r14 source SHA-256:
- `2401b3a460430da6b008716e65f7be10dfb8e289da48b12045e1e1b920ed6caf`

r14 changes:
- quarantines r13/r12 typ-3 Elantech relative synthesis associated with physical jump-back discontinuities;
- preserves/restores hub parent control context while scanning sibling children;
- skips a boot-keyboard hub child and continues to the mouse child;
- adds a real right-click context-menu test and right-click counter;
- preserves existing boot, keyboard, left-click, GUI and read-only safety behavior.

Workflow:
- `.github/workflows/frames-v108-physical-input-r14-realhw-cert.yml`
- run `31969028082`: PASS
- all nine automated lanes PASS: USB direct, USB hub, USB multi-child hub, PS/2, quantitative smoothness, interactive UI, right-click, source model and read-only safety.

r14 was intentionally NOT sent as the next physical boot after the user requested text-editing UX before the next hands-on test.

## r15 text-editing + physical-input candidate — historical checkpoint
Exact r15 source SHA-256:
- `fa0f42f558f0004f7663f79b49c3049c57c896203cf18646b1ec6f999824f941`

r15 adds to the exact r14 source:
- pointer changes to an I-beam while hovering over the Input Test text box;
- visible blinking insertion caret while the text box has focus;
- click-to-position caret placement;
- Left Arrow and Right Arrow caret navigation;
- Home/End caret positioning support;
- Delete-at-caret;
- Backspace-before-caret;
- insertion at the caret rather than append-only text entry;
- dedicated live markers/counters for I-beam, caret, blink, Left, Right and Delete paths.

Primary r15 workflow:
- `.github/workflows/frames-v108-physical-input-r15-textedit-cert.yml`
- run `31969530813`
- exact r15 ISO built successfully;
- runtime/safety lanes PASS: USB direct, USB hub, USB hub keyboard-then-mouse, PS/2, quantitative smoothness, interactive UI, right-click, live text-edit, and read-only NVMe sentinel;
- initial model lane failed only because it searched for literal marker strings even though Nexus serial markers are encoded as `serial_putc` calls; live text-edit runtime had already emitted the markers and passed.

Corrected independent finalizer:
- `.github/workflows/frames-v108-physical-input-r15-finalize-r2.yml`
- run `31969738151`: PASS
- reuses the exact candidate from run `31969530813` rather than rebuilding/substituting it;
- re-verifies all successful runtime/safety evidence;
- corrected source-model contract: PASS;
- final artifact: `Frames-v108-r15-Rufus-Final-r2`
- artifact ID `9269447513`
- artifact ZIP digest `sha256:ef4665ff74ea7e97078f2eb162fc8f1e11082985cc714b40df94d89f1f39e694`

Exact historical r15 physical-test ISO:
- `Frames-0.9.98-v108-Physical-Input-Repair-r15-TextEdit-Rufus-UEFI.iso`
- SHA-256 `c9e5177a5595a7fee0910e3a177f258dd57e70a321cb1977118939e15716dd1c`
- size `18,817,024 bytes`
- Rufus mode: **ISO Image mode**
- status at that checkpoint: `PASS_VM_PENDING_PHYSICAL`

Automated r15 evidence status:
- VM USB direct mouse: PASS
- VM USB hub child HID: PASS
- VM USB hub keyboard then mouse: PASS
- VM PS/2 pointer: PASS
- VM quantitative PS/2 smoothness: PASS
- VM keyboard text + clickable Input Test UI: PASS
- VM right-click context menu: PASS
- VM I-beam hover: PASS
- VM insertion caret: PASS
- VM caret blink: PASS
- VM Left/Right/Delete text editing: PASS
- read-only internal-media sentinel: PASS
- destructive writes: BLOCKED

## Claim policy
- Touchpad physical movement/control: proven since r10/r11, but r43 introduced a physical touchpad regression through the live EP0 fallback. r44 removes that fallback and restores the r42 PS/2/touchpad path pending physical confirmation.
- External USB mouse: physical input remains unresolved through r43; r43 also regressed the touchpad. r44 is the next exact physical candidate and is diagnostic rather than a claimed USB fix.
- Keyboard text: physical partial delivery proven, but laptop keyboard hardware is unreliable.
- Right-click, I-beam, caret blink and caret editing: VM-certified; physical confirmation remains evidence-dependent.
- Frames 1.0 remains NOT promoted.
- Physical destructive writes remain BLOCKED.

## Automatic progression — standing project rule
- Failure -> diagnose -> repair -> rerun automatically.
- Pass -> independently verify -> update this file -> continue automatically.
- Do not wait for the user to say `continue`, `next`, or otherwise re-authorize routine engineering progression.
- Continue fixes/builds/CI automatically until the next genuine physical-hardware test, required user information, explicit authorization boundary, or safety boundary is reached.
- After the user supplies the physical result, immediately resume the diagnose -> repair -> CI -> next-physical-candidate loop without asking them to tell us to continue.
- Independent workflows/lanes should run in parallel whenever practical.

## Safety policy
- Physical destructive writes remain uncertified and blocked.
- Internal NVMe/SATA/system media remain outside destructive-write certification scope.
- `promotion_allowed` remains false.
- Frames 1.0 remains NOT promoted.

## New-chat startup
1. Read `PROJECT_STATE.md`.
2. Read `CONTINUITY_PROTOCOL.md`.
3. Inspect the active branch/run/evidence named here.
4. Repository/evidence overrides older chat/project summaries.
5. Do not silently pivot to another roadmap or claim level.
6. Preserve the automatic-progression rule above.
