# Frames — Canonical Project State

> Authoritative cross-chat handoff for active Frames engineering.
> Repository/evidence overrides chat summaries and prior claims.

Last updated: 2026-08-18

## Current physical-input checkpoint — r44 physical failure -> r45 candidate

### r44 physical result — USB FAIL + TOUCHPAD FALSE-RIGHT / INPUT LOCK
Exact tested r44 ISO:
- `Frames-0.9.98-v108-r44-HID-Transfer-Ring-Forensic-Rufus-UEFI.iso`
- SHA-256 `e91158d6219de81c15207286a62c2ba27bb6d15f02e8ebecc97da0a0ee59c73a`
- size `23,330,816 bytes`

Observed on the user's ASUS laptop:
- external USB mouse: FAIL — still no cursor control;
- built-in touchpad: initially moved;
- while moving the touchpad, a right-click context menu was triggered without an intentional right click;
- after that event the pointer/input path locked and mouse control was lost;
- photographed r44 row: `R44 A T D V M Q B = 1 0 0 0 0 0 0`.

r44 USB interpretation:
- `A=1`: the interrupt TD is armed/pending;
- `T=0`: submitted HID transfer TRB is ring index 0;
- `D=0`: hardware endpoint dequeue telemetry did not advance from index 0;
- `V=0`: no direct Transfer Event was observed;
- `M=0`: no Transfer Event matched the submitted TRB;
- `Q=0`: no matching endpoint event arrived through the event mailbox;
- `B=0`: the HID DMA report buffer remained zero.

Engineering conclusion for USB: r44 did not show evidence that the physical mouse transfer was being serviced. The failure is upstream of HID decode and GUI delivery: no report DMA and no correlated completion event were observed while the TD remained armed.

Engineering conclusion for touchpad: source inspection found a concrete regression introduced in the later Elantech recovery train. `ps2_elan4_buttons_v111` had been broadened from button synchronization on packet classes 1/2 to `typ>=1 && typ<=3`, while class-3 packets were also restored as motion packets. On this physical stream, class-3 motion payload upper bits can therefore be interpreted as button bits and synthesize a right click. r45 corrects that by preserving class-3 motion while preventing class-3 motion packets from mutating button state.

Do not describe the r44 incident as proof that the whole OS crashed; the physical evidence establishes an input-path lock/loss of pointer control.

### r45 — Touchpad Button Isolation + xHCI DCS Proof — NEXT AUTHORIZED PHYSICAL BOOT
r45 is derived from exact r44 and makes two narrowly scoped changes:
1. **Touchpad button isolation:** class-3 Elantech packets remain eligible for motion delivery, but only packet classes 1/2 may update left/right button state. This directly addresses the r44 false-right-click-on-motion path.
2. **Passive xHCI cycle-state proof:** r45 adds the software producer cycle and hardware endpoint DCS to the physical overlay. It does not force a cycle value, reset the endpoint, rewrite the dequeue pointer, add a new HID doorbell, or reintroduce the rejected r43 EP0 `GET_REPORT` fallback.

Authoritative r45 certification identity:
- branch `v108-usb-hub-topology-r1`
- certification commit `fd181048f9d18a974dace237fc0d8d65e0939749`
- workflow `.github/workflows/frames-v108-r45-touchpad-button-xhci-dcs-cert.yml`
- GitHub Actions run `32097000392`: PASS
- exact r45 patched source SHA-256 `b22fbc974398bdf6f13302fc1c05589966bad81edb72e83f0ca56b16f60b9b1b`
- compiled `FramesKernel.fkrn` SHA-256 `798f1e20e7673317f8a94470c85430424cb27c34d1660ec9c74df92ca62aa20f`

Exact next physical-test ISO:
- `Frames-0.9.98-v108-r45-Touchpad-Button-Isolation-xHCI-DCS-Rufus-UEFI.iso`
- SHA-256 `a14751dc74f4daee0bfcf1e1002d2cc838cc9dd9d93e3efaf5a75b4b5968e0c6`
- size `23,330,816 bytes`
- status `PASS_VM_PENDING_PHYSICAL`
- physical handoff `RUFUS_ISO_ONLY`

Artifacts:
- `Frames-v108-r45-Rufus-Final`, artifact ID `9310375178`, ZIP SHA-256 `bcb229e6ffe223f4cace5b22feef5cbbcf89169e7cde60384d82cfbdd678df63`
- `Frames-v108-r45-Evidence`, artifact ID `9310374692`, ZIP SHA-256 `aa65d409e9a9a06e955589f0581511873222ede7344bc91e1e805cf036e248b8`

Automated r45 evidence status:
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
- physical r45: PENDING

The successful r45 run followed two automatic CI repairs. The first inherited an obsolete r37 assertion requiring class-3 packets to mutate button state; that historical assertion was compatibility-adapted without undoing the r45 fix. The second attempt showed PS/2 delivery PASS but the smoothness readiness marker was split by concurrent SMP serial output (`FRAMES_V108_PS2_ENA` + interleaved worker text + `BLE_OK`); the readiness check was hardened to tolerate that serial interleaving while retaining the independent PS/2 runtime gate. The final run passed the complete certification chain.

r45 physical overlay is `R45 A D C H V M B`:
- `A` = interrupt TD armed/pending;
- `D` = hardware endpoint dequeue ring index;
- `C` = Frames software transfer-ring producer cycle;
- `H` = hardware endpoint dequeue-cycle-state (DCS);
- `V` = direct Transfer Events observed for the polling path;
- `M` = direct Transfer Events whose event parameter matches the submitted HID TRB;
- `B` = first four bytes currently present in the HID DMA report buffer, packed little-endian.

Interpretation guide for physical r45 evidence:
- `C != H`: strong evidence of a software-producer/hardware-consumer cycle-state disagreement; diagnose transfer-ring synchronization before changing HID decode.
- `C == H`, `A=1`, and `D/V/M/B` remain unchanged/zero while the USB mouse is moved: the cycle-state hypothesis is not supported; focus next on periodic endpoint scheduling/context/device transaction service rather than GUI/input decode or event correlation.
- `D` advances but `V=0`: hardware consumed transfer-ring work but completion-event delivery/routing is failing.
- `B` becomes nonzero while `V/M=0`: DMA reached the report buffer but event delivery/correlation is broken.
- `V>0` and `M=0`: Transfer Events are arriving but correlate to a different TRB/ring state.
- `V>0` and `M>0` while visible USB input still fails: move diagnosis downstream into completion decode, HID report parsing, or Generic Pointer delivery.

Physical test order for r45:
1. Exercise the built-in touchpad extensively first. Confirm movement does not synthesize a right-click menu and does not lock the input path.
2. Then move the external USB mouse continuously for at least 10–15 seconds.
3. Photograph the complete diagnostic panel with special attention to `R45 A D C H V M B`.
4. Physical USB PASS still requires usable external USB pointer control; telemetry alone does not promote it.

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

## Key physical-input history
- **r13:** external USB mouse failed; built-in touchpad physically controlled the GUI but had jump-back discontinuities; left-click physically passed. Exact r13 ISO SHA-256 `ceb2201bd641e8f950929730e1dd6a0db8c7049aa29f0a133533e38fd55900a6`.
- **r14:** VM-certified corrective repair; quarantined the earlier type-3 discontinuity path and added right-click testing. Not physically booted before text-edit UX work continued.
- **r15:** VM-certified text-editing candidate with I-beam, insertion caret, navigation, Delete/Backspace and right-click context-menu checks. Historical exact ISO SHA-256 `c9e5177a5595a7fee0910e3a177f258dd57e70a321cb1977118939e15716dd1c`.
- **r35b:** physical USB EP0 fallback timed out and regressed touchpad behavior; telemetry `R35_F1_K1_M1_Q270_R78_E12`.
- **r36:** physical USB endpoint ran without useful events; touchpad flicker; telemetry `R36_S1_I5_D5_M8_K562_E0`.
- **r37b:** touchpad recovered; USB HID stopped with event/completion 26; telemetry `R37_S1_Q0_C1_K3_F2_E26`.
- **r38:** USB endpoint disabled/no transfer event; telemetry `R38_S0_Q0_A0_T0_V255_E0`.
- **r39b:** endpoint running with Set Idle success but no transfer; Broadcom BCM4352 Wi-Fi board identity discovered; telemetry `R39_S1_Q0_I1_R0_C0_E0_WIFI_14E4_43B1_B3D0F0`.
- **r40:** exact external receiver identified as low-speed VID 9354 / PID 4267; babble condition observed; telemetry `R40_S1_I1_H2_V9354_P4267_E3_W40_V5348_D17329_SV6715_SD8483_R3`.
- **r41b:** control path healthy, report descriptor length 142, interrupt length 8, but interrupt TD stopped with E26; telemetry `R41B_G1_P0_D142_L8_B0_E26`.
- **r42:** false endpoint-stop condition removed; endpoint remained running but no USB report reached Frames; telemetry `R42_G1_P0_D142_L8_B0_E0_USB_R0`.
- **r43:** rejected physical regression. Live EP0/class-control fallback ran but returned zero report bytes/status 11 and killed touchpad movement; telemetry `R43_C1_K1_M1_N76_A0_E11`.
- **r44:** USB still had no event/DMA progress; touchpad initially worked, then motion synthesized a false right-click menu and pointer input locked; telemetry `R44_A1_T0_D0_V0_M0_Q0_B0`.
- **r45:** next physical candidate. VM certified; touchpad class-3 button-state mutation removed while motion retained; passive software-cycle/hardware-DCS proof added.

## Claim policy
- Touchpad physical movement/control is proven on this laptop, but later revisions have exposed parser/button-state regressions. r45 specifically repairs the r44 false-right-on-motion source path and is pending physical confirmation.
- External USB mouse physical input remains unresolved through r44. r45 is diagnostic plus a touchpad repair; it is not a claimed physical USB fix until the user demonstrates usable USB pointer control.
- Keyboard text has been physically partially delivered, but the laptop keyboard itself has known hardware faults, so individual missed/repeated keys are not automatically attributed to Frames.
- Right-click, I-beam, caret blink and caret editing remain VM-certified; physical confirmation is evidence-dependent.
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
