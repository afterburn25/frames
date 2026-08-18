# Frames v108 r52 Physical Handoff

Date: 2026-08-18

## Superseded physical checkpoint

r51 physical result on the ASUS / Intel 8086:8c31 target:

- telemetry: `R51 S B A E P C V = 4 1 0 0 0 0 0`
- Intel XUSB2PR port-2 route bit successfully changed from xHCI-owned (`B=1`) to EHCI-owned (`A=0`).
- Neither EHCI companion exposed a connected PORTSC while the companions remained in their inherited halted state.
- r51 is therefore not a physical USB mouse PASS.

## r52 certified candidate

r52 changes the experiment from passive EHCI visibility to bounded EHCI companion wake/visibility proof.

Safety boundaries:

- exact guard remains Intel xHCI `8086:8c31`, receiver `248a:10ab`, root port 2, full speed, endpoint `0x82`;
- only the exact Intel XUSB2PR port-2 route bit is changed;
- EHCI interrupts remain disabled;
- periodic schedule, asynchronous schedule, and IAAD remain disabled;
- no EHCI QH/qTD schedule, enumeration transfer, HID transfer, or storage transfer is implemented in r52;
- internal NVMe/SATA/ESP and general storage writes remain blocked.

r52 wakes both existing EHCI companions, asserts CONFIGFLAG, powers ports only when the controller advertises per-port power control, sets Run/Stop, waits for `HCHalted=0`, then rescans PORTSC.

Physical overlay: `R52 W E P C R F V`

- `W`: wake/route state: `1` route moved + EHCI running + connected port found; `2` exact guard mismatch; `3` route write/verification failed; `4` route moved + at least one EHCI running but no connected port found; `5` route moved but no companion reached running state.
- `E`: connected EHCI companion ordinal (1/2, or 0).
- `P`: connected EHCI root-port number.
- `C`: Current Connect Status.
- `R`: number of EHCI companions that reached running (`HCHalted=0`).
- `F`: number of EHCI companions with CONFIGFLAG asserted.
- `V`: raw connected-port PORTSC value.

## Certification identity

- branch: `v108-usb-hub-topology-r1`
- workflow commit: `3226afd43fa5e6237d684c5356d7e2bc780a46e6`
- workflow: `.github/workflows/frames-v108-r52-intel-ehci-companion-wake-cert.yml`
- GitHub Actions run: `32155535889` — PASS
- exact patched kernel SHA-256: `7f854b564c7ddee71382ebe616ec1dd70dad3ce679684b1babd1550ac40ffcf3`
- exact ISO: `Frames-0.9.98-v108-r52-Intel-EHCI-Companion-Wake-Proof-Rufus-UEFI.iso`
- ISO SHA-256: `1d449a580ffa1a5d382b4ea6b68eb52c40e83855d5622212b3ab01d0c47c8278`
- ISO size: `23,345,152 bytes`
- status: `PASS_VM_PENDING_PHYSICAL`
- physical handoff: `RUFUS_ISO_ONLY`
- evidence artifact: `Frames-v108-r52-Evidence`, ID `9331696683`, digest `sha256:2f5fb8abdbd283c7479f94def829e6924d0028283125c7c6d17d73c665fe6665`
- Rufus artifact: `Frames-v108-r52-Rufus-Final`, ID `9331697680`, digest `sha256:6f6e3a962d585d4af55f843f23eedcf4a1fb031448cd9ed63f47be850a944fa6`

All inherited VM gates passed: interaction, USB direct, USB hub, USB multi-device/controller, USB control, USB keyboard, PS/2 delivery, quantitative pointer smoothness, text editing, focus persistence, ISO-native logging, logging fail-open, safety sentinel, and model/source contract.

## Physical test

Boot the exact r52 ISO with Rufus and the same external receiver attached. Verify the touchpad remains normal, move/click the external mouse for 10–15 seconds, then photograph the complete diagnostic panel with `R52 W E P C R F V` visible.

A healthy companion-visibility proof is approximately `W=1`, `E=1|2`, `P>0`, `C=1`, `R>0`, `F>0`, `V!=0`. That is still not a physical USB mouse PASS; it authorizes the next bounded step: an EHCI HID interrupt-IN schedule on the identified companion/port.
