# Frames — Canonical Project State

> Authoritative cross-chat handoff for active Frames engineering.
> Repository/evidence overrides chat summaries and prior claims.

Last updated: 2026-08-18

## Current physical-input checkpoint — r45 physical result -> r46 candidate

### r45 physical result — TOUCHPAD PASS / USB FAIL / CYCLE STATE MATCH
Exact tested r45 ISO:
- `Frames-0.9.98-v108-r45-Touchpad-Button-Isolation-xHCI-DCS-Rufus-UEFI.iso`
- SHA-256 `a14751dc74f4daee0bfcf1e1002d2cc838cc9dd9d93e3efaf5a75b4b5968e0c6`
- size `23,330,816 bytes`

Observed on the user's ASUS laptop:
- built-in touchpad returned to normal physical operation;
- the r44 false-right-click-on-motion regression did not recur in the accepted r45 evidence;
- external USB mouse still did not control the pointer;
- sustained USB mouse movement was performed before the final accepted photograph;
- authoritative photographed row: `R45 A D C H V M B = 1 0 1 1 0 0 0`.

r45 interpretation:
- `A=1`: the HID interrupt TD is armed/pending;
- `D=0`: hardware endpoint dequeue ring index did not advance;
- `C=1`: Frames transfer-ring producer cycle is 1;
- `H=1`: hardware endpoint DCS is 1;
- `V=0`: no direct xHCI Transfer Event was observed;
- `M=0`: no Transfer Event matched the submitted HID TRB;
- `B=0`: the HID DMA report buffer remained zero.

Engineering conclusion: the software producer cycle and hardware DCS agree, so the cycle-state mismatch hypothesis is not supported. The physical USB failure remains upstream of HID decode and GUI delivery: while the TD is armed, Intel xHCI does not visibly advance the HID dequeue pointer, produce a Transfer Event, or DMA-write mouse report bytes.

The r45 touchpad repair is physically accepted for the r44 regression: class-3 Elantech packets continue to provide motion but no longer mutate button state.

### r46 — xHCI Periodic Endpoint Context Proof — NEXT AUTHORIZED PHYSICAL BOOT
r46 is derived from exact r45 and is intentionally passive. It does not change the recovered touchpad parser, add a HID doorbell, reset/stop the endpoint, rewrite TR Dequeue, force a cycle state, alter HID report decoding, or reintroduce the rejected EP0 `GET_REPORT` fallback.

r46 reads the hardware Output Endpoint Context accepted by the controller after Configure Endpoint and exposes the periodic endpoint fields needed to determine whether the Intel controller accepted Frames' schedule exactly as requested.

Authoritative r46 certification identity:
- repository `afterburn25/frames`
- branch `v108-usb-hub-topology-r1`
- certification/head commit `b66ac172bd551aae6bb570189d61eb0d9e5376dc`
- workflow `.github/workflows/frames-v108-r46-xhci-periodic-context-proof-cert.yml`
- GitHub Actions run `32099628435`: PASS
- exact r46 patched source SHA-256 `8ddc1a93fa4a19e72d0a6a40058d8681ed2ef42b48bcd0ff4644ba8e25c2caf1`

Exact next physical-test ISO:
- `Frames-0.9.98-v108-r46-xHCI-Periodic-Endpoint-Context-Proof-Rufus-UEFI.iso`
- SHA-256 `17f2e400c31a69f20cdb4508b55bfc791a88fdfc63175812cacefdb560980b86`
- size `23,330,816 bytes`
- status `PASS_VM_PENDING_PHYSICAL`
- physical handoff `RUFUS_ISO_ONLY`

Artifacts:
- `Frames-v108-r46-Rufus-Final`, artifact ID `9311196363`, ZIP SHA-256 `000be7f824203da0e27d46a13f7bf2932469bed8e20c4b798c01651b987accbb`
- `Frames-v108-r46-Evidence`, artifact ID `9311195930`, ZIP SHA-256 `3f3bcb258ba296ef1c9fa66cdcf4332e84c9be23e44b1a1b11abc8229a069703`

Automated r46 evidence status:
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
- physical r46: PENDING

r46 physical overlay is `R46 S I T B M A E`:
- `S` = hardware Output Endpoint Context state;
- `I` = hardware-accepted xHCI interval exponent;
- `T` = hardware-accepted endpoint type;
- `B` = hardware-accepted Max Burst;
- `M` = hardware-accepted Max Packet Size;
- `A` = hardware-accepted Average TRB Length;
- `E` = hardware-accepted Max ESIT Payload.

Physical r46 interpretation:
- a sane running low/full-speed HID interrupt-IN context should show `S=1`, interrupt-IN endpoint type `T=7`, `B=0`, and packet/payload values consistent with the selected mouse descriptor;
- `I` should match the interval Frames calculated from the descriptor;
- `M`, `A`, and `E` should be internally consistent for the selected boot-mouse interrupt endpoint;
- if the hardware output context differs from the values Frames requested, the next repair belongs in Configure Endpoint / periodic scheduling context construction;
- if the output context is accepted exactly yet USB still shows no dequeue/event/DMA progress, move the next diagnosis beyond context construction into Intel periodic transaction service, slot/topology/TT scheduling, or device transaction issuance.

Physical test order for r46:
1. Confirm the built-in touchpad still behaves normally; do not accept any return of the r44 false-right-click/input-lock regression.
2. Move the external USB mouse continuously for at least 10–15 seconds and click its buttons.
3. Photograph the complete panel with special attention to `R46 S I T B M A E` and the inherited USB/r42 rows.
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
- **r39b:** endpoint running with Set Idle success but no transfer; Broadcom BCM4352 Wi-Fi identified; `R39_S1_Q0_I1_R0_C0_E0`.
- **r40:** external receiver identified as low-speed VID 9354 / PID 4267; babble observed.
- **r41b:** control path healthy, report descriptor 142 bytes, interrupt length 8, TD stopped with E26.
- **r42:** false endpoint-stop removed; endpoint stayed running but no USB report reached Frames; `R42_G1_P0_D142_L8_B0_E0_USB_R0`.
- **r43:** rejected regression; EP0/class-control polling returned no report bytes/status 11 and touchpad failed; `R43_C1_K1_M1_N76_A0_E11`.
- **r44:** no USB event/DMA progress; touchpad motion synthesized a false right-click and pointer input locked; `R44_A1_T0_D0_V0_M0_Q0_B0`.
- **r45:** touchpad physically returned to normal; external USB still failed; cycle states matched while dequeue/event/DMA stayed idle; `R45_A1_D0_C1_H1_V0_M0_B0`.
- **r46:** VM-certified passive Output Endpoint Context proof; physical test pending.

## Claim policy
- Touchpad physical movement/control and the r45 button-isolation repair are accepted on this laptop from the current evidence.
- External USB mouse physical input remains unresolved through r45.
- r46 is diagnostic and is not a claimed physical USB fix until the user demonstrates usable USB pointer control.
- Keyboard text has been physically partially delivered, but the laptop keyboard itself has known hardware faults, so individual missed/repeated keys are not automatically attributed to Frames.
- Frames 1.0 remains NOT promoted.
- Physical destructive writes remain BLOCKED.

## Automatic progression — standing project rule
- Failure -> diagnose -> repair -> rerun automatically.
- Pass -> independently verify -> update this file -> continue automatically.
- Do not wait for the user to say `continue`, `next`, or otherwise re-authorize routine engineering progression.
- Continue fixes/builds/CI automatically until the next genuine physical-hardware test, required user information, explicit authorization boundary, or safety boundary is reached.
- After the user supplies the physical result, immediately resume the diagnose -> repair -> CI -> next-physical-candidate loop without asking them to tell us to continue.
- Independent workflows/lanes should run in parallel whenever practical.

## New-chat startup
1. Read `PROJECT_STATE.md`.
2. Read `CONTINUITY_PROTOCOL.md`.
3. Inspect the active branch/run/evidence named here.
4. Repository/evidence overrides older chat/project summaries.
5. Do not silently pivot to another roadmap or claim level.
6. Preserve the automatic-progression rule above.
