# Frames v108 r55b Physical Handoff

Date: 2026-08-18

## r54 physical result — Intel EHCI root hub descriptor PASS

Authoritative physical telemetry:

- `R54 S E R C M V D = 1 1 1 9 64 32903 32776`
- EHCI ordinal 1, root port 1.
- USB device class 9 (hub).
- EP0 max packet size 64.
- VID 32903 / `0x8087` (Intel).
- PID 32776 / `0x8008`.
- built-in PS/2/Elantech input remains active.
- external USB mouse is still not a physical pointer-control PASS.

This physically proves the path is EHCI -> Intel internal USB2 hub/rate-matching hub -> downstream full-speed receiver. Direct EHCI mouse scheduling at the root device would therefore be incorrect.

## Failed unreleased r55

The first r55 hub-discovery implementation was never released for physical testing. GitHub run 32165130181 reached the Nexus build and was rejected with `NX4004: x64 backend supports at most 4 parameters (v155_ehci_control)`. This is recorded as `physical_r55=NOT_RELEASED_COMPILE_REJECTED_NX4004`; no physical r55 claim exists.

## r55b behavior

r55b preserves the r55 hub-discovery scope but adapts the EHCI control helper to the Nexus x64 four-parameter ABI. The EHCI ordinal and DMA page are carried in reserved controller-state slots instead of function parameters.

After the physically proven r54 Intel hub identity, r55b performs bounded hub discovery:

1. Assigns USB address 1 to the root Intel hub.
2. Reads the hub configuration descriptor header.
3. Sets only the hub's advertised configuration.
4. Reads the USB 2.0 hub descriptor.
5. Validates a bounded port count (1..15).
6. Powers hub downstream ports when the hub characteristics require software port power.
7. Waits for the hub's advertised power-good interval.
8. Reads each downstream port status.
9. Records connected/enabled counts, connected bitmap, first connected port and its hub-reported speed class.

Safety boundaries:

- EHCI interrupts remain disabled.
- EHCI periodic schedule remains disabled.
- The asynchronous schedule is enabled only for each bounded control transfer and disabled again afterward.
- No HID interrupt endpoint is scheduled.
- No USB storage transfer is introduced.
- Internal NVMe/SATA/system/ESP writes remain blocked.
- General writes remain blocked.

## r55b physical overlay

`R55 S N C E B F T`

- `S`: hub-discovery state (`1` = hub descriptor and downstream scan completed with >=1 connected port).
- `N`: hub downstream port count.
- `C`: number of connected downstream ports.
- `E`: number of enabled downstream ports.
- `B`: connected-port bitmap.
- `F`: first connected downstream port.
- `T`: first connected port speed code: `0` full, `1` low, `2` high, `3` unknown.

Additional machine-readable state records the selected hub configuration, raw first-port status, hub characteristics, powered-port count, successful power commands and change bitmap.

## Exact r55b certification identity

- repository: `afterburn25/frames`
- branch: `v108-usb-hub-topology-r1`
- successful certification run: `32165646136`
- successful run head: `143ca9bfcb23d21f08fefe8a8b61b061b64dbd47`
- exact patched kernel SHA-256: `038e9e9e930c8d9ae160925d474b13b2919681ed42e17f9584ebbe23f8f5faf2`
- exact ISO: `Frames-0.9.98-v108-r55b-EHCI-Intel-Hub-Discovery-4Param-Rufus-UEFI.iso`
- ISO SHA-256: `cbdfd2381be4c7111f86ee87ddf7bcf8ad4e49061a0ca710ec90a68cee8fbf1b`
- ISO size: `23,365,632 bytes`
- status: `PASS_VM_PENDING_PHYSICAL`
- physical handoff: `RUFUS_ISO_ONLY`

Artifacts:

- `Frames-v108-r55b-Rufus-Final`, artifact ID `9335516351`, ZIP SHA-256 `896889fd9904db7711f5fbe1282344e2c6749bf8d43944f9d2f877ea94850be3`
- `Frames-v108-r55b-Evidence`, artifact ID `9335515859`, ZIP SHA-256 `87ac39bce3d24d57c5a22e5559ff714609162e52eed19f406164204922e8df14`

Aggregate evidence status: PASS. All inherited interaction, USB direct/hub/multi/controller/control/keyboard, PS/2, pointer-smoothness, text/focus, flight-log, logging-fail-open, safety and model gates pass.

## Physical test

Boot the exact r55b Rufus ISO with the same receiver in the same physical USB port. Confirm the built-in touchpad remains normal. Leave the receiver attached, then photograph the complete panel with `R55 S N C E B F T` visible.

If `S=1` and `C>0`, the next bounded step is to reset/enumerate the identified downstream port and read the downstream device descriptor. No usable USB-mouse claim is authorized until the receiver itself is identified and its HID interrupt reports physically move the Frames pointer.
