# Frames — Canonical Project State

> Authoritative cross-chat handoff for active Frames engineering.
> Repository/evidence overrides chat summaries and prior claims.

Last updated: 2026-08-18

## Current physical-input checkpoint — r49 physical result -> r50 candidate

### r49 physical result — ROOT PORT/SLOT MATCH / LIVE U0 DEVICE / NO USB REPORT
Exact tested r49 ISO:
- `Frames-0.9.98-v108-r49-xHCI-Root-Port-Slot-Transaction-Proof-Rufus-UEFI.iso`
- SHA-256 `89eb877f330d91203760b55cfa75502721c445b9c51074623474e42199f26321`
- size `23,336,960 bytes`

Observed on the user's ASUS/Intel 8086:8c31 laptop:
- external USB mouse still did not produce usable pointer control;
- built-in PS/2/Elantech touchpad path remained active;
- authoritative physical row: `R49 P R C E L S A = 2 2 1 1 0 1 1`.

r49 interpretation:
- `P=2`: Frames selected root port 2;
- `R=2`: hardware Slot Context also identifies root-hub port 2;
- `C=1`: PORTSC Current Connect Status is connected;
- `E=1`: root port is enabled;
- `L=0`: link state is U0/active;
- `S=1`: xHCI PORTSC speed ID 1, which is full-speed and is coherent with Frames' full/low-speed interval conversion;
- `A=1`: hardware-assigned USB device address is non-zero.

Engineering conclusion: Frames and Intel xHCI agree on the exact live physical port/device identity. Combined with r46-r48 evidence, the following are no longer leading explanations: endpoint-context construction, producer/DCS mismatch, HID decode/GUI delivery, hub-TT scheduling, TRB ownership handoff, endpoint-doorbell ordering, xHC Run state, MFINDEX scheduler movement, or root-port/Slot Context identity. The remaining investigation belongs at the USB device/endpoint response boundary.

### r50 — USB Device Endpoint Status Proof — NEXT AUTHORIZED PHYSICAL BOOT
r50 is derived from exact r49 and preserves the physically accepted r45 touchpad button isolation plus the proven r48 scheduler/handoff behavior.

r50 performs one bounded EP0 state proof before the interrupt TD is armed:
1. `GET_CONFIGURATION` to prove the device's active configuration.
2. `GET_INTERFACE` to prove the HID alternate setting.
3. endpoint `GET_STATUS` for the selected interrupt endpoint.
4. Only if the device itself reports `ENDPOINT_HALT`, issue standard `CLEAR_FEATURE(ENDPOINT_HALT)` exactly once and verify the result.
5. Record Frames' internal speed ID beside live PORTSC speed ID.

r50 does NOT reintroduce the rejected continuous EP0 `GET_REPORT` fallback from r43.

Authoritative r50 certification identity:
- repository `afterburn25/frames`
- branch `v108-usb-hub-topology-r1`
- certification commit `7766815629a9bb9e611972e1a63b3e0e38bd73b5`
- workflow `.github/workflows/frames-v108-r50-usb-device-endpoint-status-cert.yml`
- GitHub Actions run `32106407042`: PASS
- exact r50 patched source SHA-256 `30d8239eb1c91a5b70246744d856e1a7aae77360baeaa024033fb135070fd6f1`

Exact next physical-test ISO:
- `Frames-0.9.98-v108-r50-USB-Device-Endpoint-Status-Proof-Rufus-UEFI.iso`
- SHA-256 `f37e7e7669b5ebd99a0cf0cbc1474508244a112ac1c97d7772c84c53de947662`
- size `23,339,008 bytes`
- status `PASS_VM_PENDING_PHYSICAL`
- physical handoff `RUFUS_ISO_ONLY`

Artifacts:
- `Frames-v108-r50-Rufus-Final`, artifact ID `9313412628`, ZIP SHA-256 `7ee72f47d4c176f5aa5a0527b67ca077c781bd8dd5cf804b1d6e676fc012a411`
- `Frames-v108-r50-Evidence`, artifact ID `9313412195`, ZIP SHA-256 `46c2698190a69396f414d0c4876eeb9ab35a0b7178334912f1aa4972e4f1b9a9`

Automated r50 evidence status:
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
- physical r50: PENDING

The first r50 certification attempt failed only because its new structural assertions inspected the inherited `v144_hid_forensic_snapshot` slice instead of the generated `xhci_configure_boot_hid` function. The r50 kernel source identity had already independently passed. The harness scope was corrected and run `32106407042` then passed the full inherited gate chain and sealed Rufus handoff.

r50 physical overlay is `R50 C I E H X S P`:
- `C` = device `GET_CONFIGURATION` value;
- `I` = HID `GET_INTERFACE` alternate setting;
- `E` = selected USB endpoint address;
- `H` = device endpoint-halt status before any recovery;
- `X` = clear-halt result (`0` not needed, `1` cleared+verified, `2` attempted but not verified);
- `S` = Frames internal speed ID;
- `P` = live PORTSC speed ID.

Expected healthy baseline for the current receiver is approximately `C=1 I=0 E=129 H=0 X=0 S=1 P=1`. Physical USB PASS still requires actual usable external USB pointer control; telemetry alone is not a PASS.

Physical test order for r50:
1. Confirm the built-in touchpad still behaves normally and does not reproduce r44/r43 regressions.
2. Move the external USB mouse continuously for at least 10–15 seconds and click several times.
3. Photograph the complete panel, especially `R50 C I E H X S P`, `USB H R P`, and the inherited USB diagnostic rows.
4. If `C/I/E/H/S/P` are all sane and the device is not halted yet no report appears, move the next diagnosis below host scheduling into actual endpoint/device transaction response or an alternate Intel USB2 transaction path.

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
- **r40:** external receiver identified as VID 9354 / PID 4267; earlier speed interpretation was low-speed; later direct PORTSC proof at r49 establishes live speed ID 1/full-speed on the tested path; babble was observed at r40.
- **r41b:** control path healthy, descriptor 142, interrupt length 8, but TD stopped E26; `R41B_G1_P0_D142_L8_B0_E26`.
- **r42:** false endpoint-stop removed; endpoint Running but no USB report; `R42_G1_P0_D142_L8_B0_E0_USB_R0`.
- **r43:** rejected physical regression; EP0 fallback returned zero report bytes/status 11 and killed touchpad movement; `R43_C1_K1_M1_N76_A0_E11`.
- **r44:** USB no event/DMA; touchpad motion synthesized false right-click then pointer input locked; `R44_A1_T0_D0_V0_M0_Q0_B0`.
- **r45:** touchpad physically returned to normal; USB remained armed with no dequeue/event/DMA and cycle states matched; `R45_A1_D0_C1_H1_V0_M0_B0`.
- **r46:** hardware accepted Running interrupt-IN periodic context `S1 I5 T7 B0 M8 A8 E8`, direct-root path, but `USB_R0`.
- **r47:** physical ordered TRB handoff and doorbell flush passed, but initial MFINDEX proof was static and no dequeue/event/DMA occurred; `R47_H1_F1_M0_R0_Q0_V0_B0`.
- **r48:** scheduler movement physically proven with controller Running/not halted, but still no Transfer Event; `R48_T1_F1_M1_U1_H0_W0_V0`.
- **r49:** Frames root port and hardware Slot Context matched; live port connected/enabled/U0/full-speed/addressed; still no report; `R49_P2_R2_C1_E1_L0_S1_A1`.
- **r50:** VM/safety certified bounded device endpoint-state proof; physical pending.

## Claim policy
- The r45 touchpad class-3 button isolation repair is physically accepted for the r44 regression unless later physical evidence supersedes it.
- External USB mouse physical input remains unresolved through r49. r50 is a VM-certified physical candidate, not a claimed physical USB fix.
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
