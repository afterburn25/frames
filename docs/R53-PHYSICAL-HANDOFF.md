# Frames v108 r53 Physical Handoff

Date: 2026-08-18

## r52 physical result — EHCI companion wake/visibility PASS

Authoritative physical telemetry on the ASUS / Intel 8086:8c31 target:

- `R52 W E P C R F V = 1 1 1 1 2 2 6147`
- Intel XUSB2PR port-2 route was successfully moved away from xHCI.
- Both EHCI controllers reached running state (`R=2`).
- Both EHCI CONFIGFLAGs were asserted (`F=2`).
- EHCI companion 1, root port 1, physically sees the receiver (`E=1 P=1 C=1`).
- raw EHCI PORTSC is `6147` / `0x1803`.
- built-in PS/2/Elantech touchpad remained active.
- external USB mouse still did not produce usable Frames pointer input.

r52 therefore physically passes the bounded EHCI companion wake/visibility gate, but is NOT a physical USB mouse PASS.

## Why r53 exists

`PORTSC=0x1803` is a connected/powered pre-reset state with Port Enable still clear. r53 performs a bounded EHCI root-port reset and classifies the post-reset ownership state before any host-controller transfer schedule is introduced.

The purpose is to determine whether the receiver is retained by EHCI or handed to a USB1 companion host controller, and to inventory UHCI/OHCI PCI controllers if a companion handoff occurs.

## r53 behavior and safety boundaries

r53 preserves the exact Intel/device guard:

- xHCI `8086:8c31`
- receiver `248a:10ab` / decimal `9354:4267`
- original xHCI root port 2
- full-speed device
- HID mouse endpoint `0x82` / decimal 130

r53:

1. moves only the exact XUSB2PR port-2 route bit;
2. wakes the two existing EHCI controllers with interrupts disabled;
3. keeps EHCI periodic schedule, asynchronous schedule, and IAAD disabled;
4. asserts CONFIGFLAG and powers ports where supported;
5. finds the receiver on EHCI companion 1 / port 1;
6. performs one bounded EHCI port reset with read/write-clear PORTSC bits sanitized before writes;
7. reads post-reset Port Enable and Port Owner;
8. if the device is not EHCI-enabled and the controller advertises companions, performs one bounded Port Owner handoff write and re-reads the result;
9. inventories PCI UHCI and OHCI host-controller programming interfaces;
10. does NOT program EHCI/UHCI/OHCI transfer descriptors, queues, periodic lists, asynchronous lists, HID transactions, storage transfers, or any internal-media write path.

Internal NVMe/SATA/system/ESP writes remain blocked. Frames 1.0 remains unpromoted.

## r53 physical overlay

`R53 S E P D O U H`

- `S` = classifier state:
  - `1`: EHCI retained/enabled the device (`PED=1`, Owner=0)
  - `2`: device handed to a USB1 companion (`PED=0`, Owner=1)
  - `3`: non-EHCI device but EHCI reports no companion controllers (`PED=0`, Owner=0, N_CC=0)
  - `4`: post-reset classification inconsistency
  - `5`: no running/visible EHCI port, disconnect, or reset timeout
  - `6`: exact hardware/device guard mismatch
- `E` = EHCI companion ordinal
- `P` = EHCI root-port number
- `D` = post-reset Port Enable/Disable bit
- `O` = post-reset Port Owner bit
- `U` = PCI UHCI controller count
- `H` = PCI OHCI controller count

Additional machine-readable telemetry records raw post-reset PORTSC, EHCI `N_CC`, and line-state bits.

## Exact r53 certification identity

- repository: `afterburn25/frames`
- branch: `v108-usb-hub-topology-r1`
- successful full certification run: `32159235260`
- successful run head: `6e11cb0d89a6d58340c65a934470a613d6b33de0`
- exact sealed patched kernel SHA-256: `815287063aae3e8d2ab56dbd4514de4cafdcd4ee763ff355f65b0867468d05d6`
- exact ISO: `Frames-0.9.98-v108-r53-EHCI-Port-Reset-Companion-Classifier-Rufus-UEFI.iso`
- ISO SHA-256: `c820023321a0adccf21b1b4e1b3623e991affcdfd17a22d4c3590cf9a6200a56`
- ISO size: `23,347,200 bytes`
- status: `PASS_VM_PENDING_PHYSICAL`
- physical handoff: `RUFUS_ISO_ONLY`

Artifacts:

- `Frames-v108-r53-Rufus-Final-Minimal`, artifact ID `9333185709`, ZIP SHA-256 `ecbfd13e6572eacc429698d07ddac11a101e014404a8886684ce07f5ea60a99b`
- `Frames-v108-r53-Evidence-Minimal`, artifact ID `9333185228`, ZIP SHA-256 `d6a05ee32b7b78280d6b792f1d61ea035f7a15363c7db50f515637b67d6564cf`

Aggregate evidence status: PASS.

All inherited certification gates pass: interaction, USB direct, USB hub, USB multi-device/controller, USB control, USB keyboard, PS/2 delivery, quantitative pointer smoothness, text editing, focus persistence, ISO-native logging, logging fail-open, internal-media safety, and model/source contract.

Physical r53 remains PENDING. No USB mouse physical-pass claim is authorized until usable real-hardware pointer control is observed.

## Physical test

Boot the exact r53 Rufus ISO with the same receiver in the same physical USB port. Confirm the touchpad still behaves normally, move/click the external mouse for 10–15 seconds, and photograph the complete diagnostic panel with `R53 S E P D O U H` visible.

If `S=2`, the next engineering step is the identified USB1 companion host-controller path (UHCI when `U>0`, OHCI when `H>0`) rather than another xHCI/EHCI timing revision. If `S=1`, the next bounded step belongs to EHCI transaction scheduling. Other states remain diagnostic and fail closed.
