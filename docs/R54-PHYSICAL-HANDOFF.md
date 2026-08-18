# Frames v108 r54 Physical Handoff

Date: 2026-08-18

## r53 physical result — EHCI retained/enabled root path PASS

Authoritative real-hardware telemetry from the ASUS / Intel 8086:8c31 target:

- `R53 S E P D O U H = 1 1 1 1 0 0 0`
- classifier state `S=1`
- EHCI ordinal `E=1`
- EHCI root port `P=1`
- Port Enable/Disable `D=1`
- Port Owner `O=0`
- PCI UHCI controller count `U=0`
- PCI OHCI controller count `H=0`

This physically proves the r53 bounded EHCI reset completed with the root path retained and enabled by EHCI. No UHCI/OHCI companion handoff exists on this machine.

The external USB mouse still has not produced usable Frames pointer motion, so r53 is not a physical USB-mouse PASS. The result narrows the next problem to enumeration/transactions beneath the EHCI-retained path.

## Why r54 exists

The r53 result is consistent with the EHCI root port exposing a high-speed USB 2.0 hub/rate-matching path while the full-speed receiver exists downstream. r54 therefore does not jump directly to a mouse interrupt queue. It performs one bounded address-0 EHCI control transfer to identify the device currently exposed at the enabled EHCI root port.

## r54 operation

r54 performs one `GET_DESCRIPTOR(Device, 0)` request for 18 bytes at USB address 0 using one EHCI asynchronous QH and a three-qTD SETUP/DATA/STATUS chain.

Safety boundaries:

1. r54 runs only after r53 state 1 (`PED=1`, `Owner=0`).
2. EHCI interrupts remain disabled.
3. The periodic schedule remains disabled.
4. Only the asynchronous schedule is enabled for the single bounded control transfer.
5. The asynchronous schedule is disabled immediately after completion or timeout.
6. r54 does not issue SET_ADDRESS.
7. r54 does not issue SET_CONFIGURATION.
8. r54 does not install a periodic HID interrupt queue.
9. r54 does not perform USB-storage, NVMe, SATA, ESP, or other general write operations.
10. Internal NVMe/SATA/system/ESP media remain read-only.

The descriptor probe records:

- descriptor class
- endpoint-0 maximum packet size
- USB vendor ID
- USB product ID
- qTD completion/error state
- remaining DATA bytes
- EHCI 64-bit addressing capability
- DMA upper segment
- live post-transfer PORTSC

## r54 physical overlay

`R54 S E R C M V D`

- `S` = r54 probe state
  - `1`: descriptor transfer completed and a valid 18-byte device descriptor was parsed
  - `2`: EHCI controller/root lookup failure
  - `3`: DMA, addressing, busmaster, or descriptor-setup failure
  - `4`: EHCI asynchronous schedule failed to arm
  - `5`: transfer timeout
  - `6`: SETUP/DATA/STATUS qTD error or halt
  - `7`: malformed or incomplete device descriptor
  - `8`: root port changed, disconnected, disabled, or changed ownership
  - `9`: probe armed/in progress
- `E` = EHCI ordinal
- `R` = EHCI root-port number
- `C` = USB `bDeviceClass`
- `M` = USB endpoint-0 `bMaxPacketSize0`
- `V` = USB vendor ID in decimal
- `D` = USB product ID in decimal

A successful hub-class result (`S=1`, `C=9`) would confirm that the next controlled step is hub enumeration and downstream-port discovery before attempting the receiver's interrupt endpoint. A successful non-hub descriptor will be handled according to the actual class/VID/PID observed; no identity is assumed in advance.

## Exact r54 certification identity

- repository: `afterburn25/frames`
- branch: `v108-usb-hub-topology-r1`
- successful certification run: `32162655986`
- successful run head: `8808021e33e1cb80103a6d08970130448b227cb5`
- exact patched kernel SHA-256: `ebcf7baf18422cc72804eec9e18a317ed5daf1baee65330528be66c07d599c19`
- exact ISO: `Frames-0.9.98-v108-r54-EHCI-Root-Descriptor-Probe-Rufus-UEFI.iso`
- ISO SHA-256: `773f3d19e3c9a0cd0f2e24561d58141a6f84a5933421efe757b5ed1fd4cfe329`
- ISO size: `23,355,392 bytes`
- status: `PASS_VM_PENDING_PHYSICAL`
- physical handoff: `RUFUS_ISO_ONLY`

Artifacts:

- `Frames-v108-r54-Rufus-Final`, artifact ID `9334378663`, artifact ZIP SHA-256 `d7ce205b0f916ce25645e37ed28360a57293f0bb7e0a30a050e19e801309e7a3`
- `Frames-v108-r54-Evidence`, artifact ID `9334378217`, artifact ZIP SHA-256 `c05513c92bc050c01e1084d36d0d6b784aa5e50cda41a67861b5faaa76636403`

Aggregate evidence status: PASS.

All inherited gates pass: interaction, USB direct, USB hub, USB multi-device/controller, USB control, USB keyboard, PS/2 delivery, pointer smoothness, text editing, focus persistence, ISO-native logging, logging fail-open, internal-media safety, and model/source contract.

## Physical test

Use the exact r54 Rufus ISO with the receiver in the same USB port used for r52/r53.

1. Boot r54.
2. Confirm the built-in touchpad remains usable.
3. Leave the receiver attached in the same physical USB port.
4. Move/click the external mouse for 10–15 seconds; mouse motion is not required for this descriptor-stage PASS.
5. Photograph the complete diagnostic panel with `R54 S E R C M V D` clearly visible.

Physical r54 remains PENDING until that telemetry is observed. Do not claim physical USB-mouse control until the external mouse actually moves the Frames pointer.
