# Frames — Canonical Project State

> Authoritative cross-chat handoff for active Frames engineering.
> Repository/evidence overrides chat summaries and prior claims.

Last updated: 2026-08-18

## Current physical-input checkpoint — r50 physical result -> r51 candidate

### r50 physical result — DEVICE CONFIGURED / MOUSE EP 0x82 NOT HALTED / FULL-SPEED / NO INTERRUPT REPORT
Exact tested r50 ISO:
- `Frames-0.9.98-v108-r50-USB-Device-Endpoint-Status-Proof-Rufus-UEFI.iso`
- SHA-256 `f37e7e7669b5ebd99a0cf0cbc1474508244a112ac1c97d7772c84c53de947662`
- size `23,339,008 bytes`

Observed on the user's ASUS/Intel 8086:8c31 laptop:
- the external USB mouse still did not produce a live Frames USB report (`USB H R P = 1 0 2`);
- PS/2/Elantech telemetry remained active;
- authoritative r50 row: `R50 C I E H X S P = 1 0 130 0 0 1 1`.

r50 interpretation:
- `C=1`: device `GET_CONFIGURATION` reports configuration 1;
- `I=0`: HID `GET_INTERFACE` reports alternate setting 0;
- `E=130`: the selected interrupt-IN endpoint is `0x82`;
- `H=0`: the physical device reports the selected endpoint is not halted;
- `X=0`: no clear-halt recovery was needed;
- `S=1`: Frames' selected device speed is full-speed;
- `P=1`: live xHCI PORTSC independently reports full-speed.

The r50 source-selection path confirms endpoint `0x82` belongs to the selected boot-mouse HID interface; it is not an accidental keyboard endpoint. The earlier pre-test note expecting `0x81` was too narrow and is superseded by this source + physical proof.

Engineering conclusion: EP0 communication, device configuration, HID alternate setting, mouse endpoint identity, endpoint halt state, physical root-port identity, link state, xHCI endpoint context, TRB ownership handoff, doorbell ordering and scheduler movement have all been physically narrowed away as leading causes. The unresolved failure is specifically that the xHCI interrupt-IN path never produces a usable mouse report on this hardware.

The historical r40 label that called the 248a:10ab receiver low-speed is also superseded for the tested path: r49/r50 independently prove live xHCI speed ID 1/full-speed.

### r51 — Intel EHCI Route Probe — NEXT AUTHORIZED PHYSICAL BOOT
r51 invokes the standing alternative-path rule instead of continuing small xHCI timing changes. This Lynx Point system has two EHCI USB2 companion controllers, while the current Frames bring-up path routes USB2 ports to xHCI and halts the companions after takeover.

r51 performs one tightly bounded alternate-path experiment:
1. Require exact Intel xHCI `8086:8c31`.
2. Require exact receiver `248a:10ab` (decimal 9354/4267).
3. Require selected xHCI root port 2, full-speed, and mouse endpoint `0x82`/130.
4. Verify port 2 is routable and currently owned by xHCI in Intel USB2PRM/XUSB2PR.
5. Clear only the port-2 XUSB2PR routing bit, leaving every other USB2 route bit unchanged.
6. Passively scan the two known EHCI companions and identify which EHCI PORTSC now reports a connected port.
7. Once the reroute is proven, suppress stale xHCI HID polling/recovery for that receiver.

r51 does NOT enable storage writes, internal-media writes, installation, persistent system modification, continuous EP0 GET_REPORT polling, or broad USB rerouting. It is a route/visibility proof, not yet a claim that the EHCI HID interrupt driver is complete.

Authoritative r51 certification identity:
- repository `afterburn25/frames`
- branch `v108-usb-hub-topology-r1`
- successful certification/head commit `3df8e801a52340c212043b63b63d181b497f8632`
- workflow `.github/workflows/frames-v108-r51-intel-ehci-route-probe-cert.yml`
- GitHub Actions run `32108714504`: PASS
- exact r51 patched source SHA-256 `25f02ab7852059b40c9387f0a139b8407a0e99dbc25038a917594a5f9526975a`

Exact next physical-test ISO:
- `Frames-0.9.98-v108-r51-Intel-EHCI-Route-Probe-Rufus-UEFI.iso`
- SHA-256 `50c9145a9d59b32668b3a0a1240a29df7522fdc369ca86fc823653b6f4ea1b1b`
- size `23,343,104 bytes`
- status `PASS_VM_PENDING_PHYSICAL`
- physical handoff `RUFUS_ISO_ONLY`

Artifacts:
- `Frames-v108-r51-Rufus-Final`, artifact ID `9314190338`, ZIP SHA-256 `e18fcad8d548dfbbcf678c1f884ce605acb22a834bcf240d4c49ce5bd000932c`
- `Frames-v108-r51-Evidence`, artifact ID `9314189712`, ZIP SHA-256 `dce4ab7a24ee5015dd84ce42389a6c10bde57380bf7ff0a510e389edf4d05979`

Automated r51 evidence status:
- aggregate: PASS
- interaction: PASS
- USB direct: PASS
- USB hub: PASS
- USB multi-child/controller: PASS
- USB control/keyboard: PASS
- PS/2 delivery: PASS
- quantitative pointer smoothness: PASS
- text edit: PASS
- focus persistence: PASS
- controlled USB flight log: PASS
- logging fail-open: PASS
- internal-media read-only safety sentinel: PASS
- model/source contract: PASS
- physical r51: PENDING

The first r51 certification run `32108528273` failed only because the inherited r36 certifier required its original xHCI polling statement verbatim. r51 intentionally adds a guard that preserves that polling until a successful EHCI handoff, then suppresses stale xHCI access. The compatibility assertion was narrowed to accept either the original r36 contract or the r51 guarded equivalent; no runtime/safety gate was removed. Run `32108714504` then passed the full certification and sealed Rufus handoff.

r51 physical overlay is `R51 S B A E P C V`:
- `S` = route-probe state (`1` = route moved and EHCI connected port found; `2` = exact hardware/device guard mismatch; `3` = route write/verification failed; `4` = route moved but no EHCI connected port found);
- `B` = selected XUSB2PR port bit before reroute;
- `A` = selected XUSB2PR port bit after reroute;
- `E` = EHCI companion ordinal (`1` or `2` when found);
- `P` = EHCI root-port number;
- `C` = EHCI PORTSC Current Connect Status;
- `V` = raw EHCI PORTSC value.

A successful route proof should look approximately like `S=1 B=1 A=0 E=1|2 P=<port> C=1 V=<nonzero>`. This does not by itself count as physical USB mouse PASS; it proves the receiver can be handed from Lynx Point xHCI to a specific EHCI companion/port, which is the foundation for an EHCI HID interrupt path if needed.

Physical test order for r51:
1. Boot the exact r51 Rufus ISO with the same external receiver/mouse configuration.
2. Confirm the desktop and PS/2/touchpad path remain responsive.
3. Move/click the external USB mouse for 10–15 seconds.
4. Photograph the full diagnostic panel, especially `R51 S B A E P C V`, `USB H R P`, and `R33 EH N CB CA BS H X`.
5. If `S=1 ... C=1`, the next engineering step is to bring up a bounded EHCI HID interrupt-IN path on the identified companion/port rather than return to xHCI timing experiments.
6. If `S=4`, diagnose companion ownership/power/PORTSC visibility before implementing EHCI HID scheduling.

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
- **r40:** receiver VID/PID identified as 9354/4267 (`248a:10ab`); its historical low-speed interpretation is superseded by later full-speed PORTSC/device proof; babble E3 was observed.
- **r41b:** control path healthy, descriptor 142, interrupt length 8, but TD stopped E26; `R41B_G1_P0_D142_L8_B0_E26`.
- **r42:** false endpoint-stop removed; endpoint Running but no USB report; `R42_G1_P0_D142_L8_B0_E0_USB_R0`.
- **r43:** rejected physical regression; EP0 fallback returned zero report bytes/status 11 and killed touchpad movement; `R43_C1_K1_M1_N76_A0_E11`.
- **r44:** USB no event/DMA; touchpad motion synthesized false right-click then pointer input locked; `R44_A1_T0_D0_V0_M0_Q0_B0`.
- **r45:** touchpad physically returned to normal; USB remained armed with no dequeue/event/DMA and cycle states matched; `R45_A1_D0_C1_H1_V0_M0_B0`.
- **r46:** hardware accepted Running interrupt-IN context `S1 I5 T7 B0 M8 A8 E8`, direct-root path, but `USB_R0`.
- **r47:** ordered TRB handoff/doorbell flush physically executed but initial MFINDEX proof was static and no dequeue/event/DMA occurred; `R47_H1_F1_M0_R0_Q0_V0_B0`.
- **r48:** scheduler movement physically proven with controller Running/not halted; no Transfer Event; `R48_T1_F1_M1_U1_H0_W0_V0`.
- **r49:** root port and Slot Context matched; connected/enabled/U0/full-speed/addressed; no report; `R49_P2_R2_C1_E1_L0_S1_A1`.
- **r50:** EP0 device state healthy; config1/alt0/mouse endpoint0x82/not halted/full-speed; still no interrupt report; `R50_C1_I0_E130_H0_X0_S1_P1`.
- **r51:** VM/safety certified exact-device Intel EHCI route probe; physical pending.

## Claim policy
- The r45 touchpad class-3 button isolation repair is physically accepted for the r44 regression unless later physical evidence supersedes it.
- External USB mouse physical input remains unresolved through r50. r51 is a VM-certified alternate-path physical candidate, not a claimed physical USB fix.
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
