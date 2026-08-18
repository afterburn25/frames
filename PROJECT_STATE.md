# Frames — Canonical Project State

> Authoritative cross-chat handoff for active Frames engineering.
> Repository/evidence overrides chat summaries and prior claims.

Last updated: 2026-08-18

## Current physical-input checkpoint — r46 physical result -> r47 candidate

### r46 physical result — USB CONTEXT ACCEPTED / NO REPORT / DIRECT ROOT
Exact tested r46 ISO:
- `Frames-0.9.98-v108-r46-xHCI-Periodic-Endpoint-Context-Proof-Rufus-UEFI.iso`
- SHA-256 `17f2e400c31a69f20cdb4508b55bfc791a88fdfc63175812cacefdb560980b86`
- size `23,330,816 bytes`

Observed on the user's ASUS laptop:
- external USB mouse still did not produce usable pointer control;
- `USB H R P = 1 0 2`, so HID configuration remains present but no live USB report reached Frames;
- authoritative r46 output-endpoint-context row: `R46 S I T B M A E = 1 5 7 0 8 8 8`;
- HUB telemetry remained zero for the selected receiver, establishing the active receiver path as direct-root rather than a hub/TT child;
- PS/2/touchpad telemetry remained active and no return of the r44 false-right/input-lock regression was reported.

r46 interpretation:
- `S=1`: hardware Output Endpoint Context is Running;
- `I=5`: accepted periodic interval exponent is 5;
- `T=7`: accepted endpoint type is Interrupt IN;
- `B=0`: Max Burst is 0;
- `M=8`: Max Packet Size is 8 bytes;
- `A=8`: Average TRB Length is 8 bytes;
- `E=8`: Max ESIT Payload is 8 bytes.

Engineering conclusion: Intel accepted a coherent low-speed boot-HID periodic endpoint context exactly as intended, but no report arrived. Combined with r45 (`A1 D0 C1 H1 V0 M0 B0`), endpoint-context construction, producer/DCS disagreement, HID parsing, GUI delivery, and hub transaction-translator scheduling are no longer leading explanations. The failure is now at or after the transfer-TRB ownership/doorbell transaction boundary.

### r47 — xHCI Ordered HID Handoff + Doorbell Flush — NEXT AUTHORIZED PHYSICAL BOOT
r47 is derived from exact r46 and preserves the physically recovered r45 touchpad behavior and the r46 accepted endpoint context. It does not add Stop Endpoint, Reset Endpoint, Set TR Dequeue, EP0 GET_REPORT polling, endpoint reconfiguration, destructive writes, or a new HID decoder.

r47 changes the normal interrupt-IN submission boundary only:
1. Build the HID Normal TRB with the opposite/non-owned cycle state first.
2. Read back parameter, status and inactive control fields before release.
3. Flip the cycle bit to the real producer cycle last and read back the final owned TRB.
4. Ring the exact endpoint doorbell.
5. Immediately read the same doorbell MMIO location to flush the posted write.
6. Record MFINDEX movement and the hardware slot route string passively.

This ordering follows the same core discipline used by mature xHCI implementations: make transfer memory visible before ownership/doorbell handoff and flush the posted endpoint doorbell write.

Authoritative r47 certification identity:
- repository `afterburn25/frames`
- branch `v108-usb-hub-topology-r1`
- certification/head commit `6cd780868bfeca093aae5cf8b8ee48632c14e57b`
- workflow `.github/workflows/frames-v108-r47-xhci-ordered-handoff-doorbell-flush-cert.yml`
- GitHub Actions run `32101328442`: PASS
- exact r47 patched source SHA-256 `5037199d0ea3bde3a050ac648d2f91ef2c92e225ae303113b683cf7e453b90fa`

Exact next physical-test ISO:
- `Frames-0.9.98-v108-r47-xHCI-Ordered-Handoff-Doorbell-Flush-Rufus-UEFI.iso`
- SHA-256 `b3bbcf010ff790aa18851ffb0f1439cf5db7ec297db6e71d332d106ead251783`
- size `23,332,864 bytes`
- status `PASS_VM_PENDING_PHYSICAL`
- physical handoff `RUFUS_ISO_ONLY`

Artifacts:
- `Frames-v108-r47-Rufus-Final`, artifact ID `9311747014`, ZIP SHA-256 `0bde29756db787f313bcf4a007e99a0923726b7e25062267f0e8044155c1ec0d`
- `Frames-v108-r47-Evidence`, artifact ID `9311746466`, ZIP SHA-256 `4e30473c92c8265b85c5b20dd5046da26b5ee5ea45a97e1c088662a095e4abd8`

Automated r47 evidence status:
- aggregate: PASS
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
- physical r47: PENDING

r47 physical overlay is `R47 H F M R Q V B`:
- `H` = two-phase HID TRB memory readback/handoff was exact;
- `F` = endpoint-doorbell MMIO readback flush executed;
- `M` = xHCI MFINDEX advanced after the transfer was armed;
- `R` = hardware Slot Context route string (`0` means direct-root);
- `Q` = hardware HID endpoint dequeue ring index;
- `V` = direct Transfer Events observed;
- `B` = first four bytes in the HID DMA report buffer, packed little-endian.

Physical r47 interpretation:
- usable external USB pointer control is the only physical USB PASS;
- `H=1 F=1 M=1 R=0` proves the TRB handoff readback, doorbell flush, xHCI scheduler clock, and direct-root topology are all present;
- if `Q/V/B` then move/change, diagnose completion/HID delivery from that evidence;
- if `H=1 F=1 M=1 R=0 Q=0 V=0 B=0` after sustained mouse movement, stop tuning endpoint context/doorbell timing and move to device-side transaction proof, endpoint halt/status/configuration verification, or an alternate USB2-controller transaction path.

Physical test order for r47:
1. Exercise the built-in touchpad first and confirm normal behavior.
2. Move the external USB mouse continuously for 10–15 seconds and click its buttons.
3. Photograph the complete panel, especially `R47 H F M R Q V B`, `USB H R P`, and the inherited r42/r46 information.
4. Do not infer physical USB success from telemetry alone.

## Project identity / safety
- Frames is an independent operating system, not Windows- or Linux-based.
- Native systems language/toolchain: Nexus.
- Boot chain: UEFI -> BOOTX64.EFI -> FramesKernel.fkrn.
- Native application formats: FEX/FAPP.
- Evidence is fail-closed: exact source/hash, QEMU/OVMF first, then real hardware for physical claims.
- VM PASS is never described as physical PASS.
- Frames 1.0 is NOT promoted.
- Physical destructive writes, installation, persistent internal-media modification, and release promotion remain blocked.
- Internal NVMe/SATA/system/ESP media remain read-only in this train.
- User-facing physical-test artifacts must be Rufus-compatible UEFI ISOs; raw IMG is CI-only.
- Independent workflows/lanes should run in parallel whenever practical.

## Certified reconstruction foundation — Frames 0.9.98 v108 r9
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
- **r13:** external USB mouse failed; touchpad physically controlled GUI but had jump-back discontinuities; left-click physically passed.
- **r35b:** EP0 fallback timed out and regressed touchpad behavior; `R35_F1_K1_M1_Q270_R78_E12`.
- **r36:** physical USB endpoint ran without useful events; touchpad flicker; `R36_S1_I5_D5_M8_K562_E0`.
- **r37b:** touchpad recovered; USB HID stopped with completion 26; `R37_S1_Q0_C1_K3_F2_E26`.
- **r38:** endpoint disabled/no transfer event; `R38_S0_Q0_A0_T0_V255_E0`.
- **r39b:** endpoint Running with Set Idle success but no transfer; Broadcom BCM4352 Wi-Fi identified; `R39_S1_Q0_I1_R0_C0_E0`.
- **r40:** exact external receiver identified as low-speed VID 9354 / PID 4267; babble observed; `R40_S1_I1_H2_V9354_P4267_E3`.
- **r41b:** control path healthy, descriptor 142, interrupt length 8, but TD stopped E26; `R41B_G1_P0_D142_L8_B0_E26`.
- **r42:** false endpoint-stop removed; endpoint Running but no USB report; `R42_G1_P0_D142_L8_B0_E0_USB_R0`.
- **r43:** rejected physical regression; EP0 fallback returned zero report bytes/status 11 and killed touchpad movement; `R43_C1_K1_M1_N76_A0_E11`.
- **r44:** USB no event/DMA; touchpad motion synthesized false right-click then pointer input locked; `R44_A1_T0_D0_V0_M0_Q0_B0`.
- **r45:** touchpad physically returned to normal; USB remained armed with no dequeue/event/DMA and cycle states matched; `R45_A1_D0_C1_H1_V0_M0_B0`.
- **r46:** hardware accepted Running interrupt-IN periodic context `S1 I5 T7 B0 M8 A8 E8`, direct-root path, but `USB_R0`.
- **r47:** VM/safety certified ordered TRB ownership + endpoint-doorbell flush candidate; physical pending.

## Claim policy
- The r45 touchpad class-3 button isolation repair is physically accepted for the r44 regression unless later physical evidence supersedes it.
- External USB mouse physical input remains unresolved through r46. r47 is a VM-certified physical candidate, not a claimed physical USB fix.
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
