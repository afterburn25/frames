# Frames v108 r55c Physical Handoff

Date: 2026-08-18

## r55b physical result

Authoritative panel telemetry:

- `R55 S N C E B F T = 3 0 0 0 0 0 0`
- built-in touchpad path remained active.
- hub enumeration did not begin.
- r55b state 3 combined two possibilities: second DMA-page allocation failure or initial hub `SET_ADDRESS` control failure.
- therefore r55b is not a physical hub-enumeration PASS and no external USB mouse PASS is claimed.

The prior r54 physical proof remains authoritative:

- `R54 S E R C M V D = 1 1 1 9 64 32903 32776`
- EHCI root device is Intel hub `8087:8008`, class 9, EP0 MPS 64.

## r55c repair / diagnostic split

r55c removes the r55b ambiguity and reduces DMA pressure:

1. Reuses the exact DMA page retained by the successful r54 root descriptor transaction (`xhci_state+3848`).
2. Does not allocate a second EHCI DMA page.
3. Runs an 8-byte `GET_DESCRIPTOR(Device)` at address 0 through the generic four-parameter EHCI control helper.
4. Validates descriptor type 1 and EP0 MPS 64.
5. Only after a successful preflight does it issue hub `SET_ADDRESS(1)`.
6. Continues the existing bounded hub configuration / hub descriptor / downstream status scan only after the address stage succeeds.

Visible row remains the seven discovery values but carries the unique revision label:

`R5C S N C E B F T`

Failure-state encoding:

- `S=30`: the physically proven r54 DMA page was unexpectedly unavailable.
- `S=22..26`: generic EHCI address-0 descriptor preflight failed; subtract 20 to obtain helper return code.
- `S=29`: preflight transfer completed but returned an invalid 8-byte device descriptor / EP0 MPS.
- `S=32..36`: `SET_ADDRESS(1)` failed; subtract 30 to obtain helper return code.
- `S=1` with `C>0`: hub enumeration and downstream connected-port discovery succeeded.

Safety boundaries remain unchanged:

- EHCI interrupts disabled.
- EHCI periodic schedule disabled.
- asynchronous schedule enabled only during each bounded control transfer and disabled afterward.
- no HID interrupt endpoint schedule.
- no USB storage write path.
- internal NVMe/SATA/system/ESP writes blocked.
- general writes blocked.

## Exact r55c certification identity

- repository: `afterburn25/frames`
- branch: `v108-usb-hub-topology-r1`
- GitHub Actions run: `32167573921` — PASS
- run head: `9e0049dd6a2083c1bfb5f0f0c679f760a2aeef1a`
- exact patched kernel SHA-256: `8341c00a24f8dad89dec417dcaa93c1ff648344652cd6fda4ef47afd459f4595`
- exact ISO: `Frames-0.9.98-v108-r55c-EHCI-Hub-Address-Preflight-Rufus-UEFI.iso`
- ISO SHA-256: `7f757897278cc571f45a5532fe5089ed130ab8f4172437159fcd3c9b863ec085`
- ISO size: `23,365,632 bytes`
- status: `PASS_VM_PENDING_PHYSICAL`
- physical handoff: `RUFUS_ISO_ONLY`

Artifacts:

- `Frames-v108-r55c-Rufus-Final`, ID `9336176653`, ZIP digest `sha256:0eb4aeb5271974da41a541c680ea5b6e07cbacf58a8187334cae3fb3977142f3`
- `Frames-v108-r55c-Evidence`, ID `9336176298`, ZIP digest `sha256:0d6c9c258f4c18e2c83b4c7bbcb0a78cf9b16a8a413f92c2304f08ff01256e14`

Aggregate evidence status PASS. Interaction, USB direct/hub/multi/controller/control/keyboard, PS/2, pointer smoothness, text/focus, ISO logging, logging fail-open, safety and model gates all PASS.

## Physical test

Boot the exact r55c Rufus ISO with the receiver left in the same USB port. Confirm the built-in touchpad remains stable and photograph the complete panel with `R5C S N C E B F T` visible.

Interpretation is immediate from `S`:

- `1` with `C>0`: proceed to downstream port reset and receiver device descriptor.
- `22..26`: repair the generic EHCI control helper according to helper rc `S-20`.
- `29`: descriptor/preflight data integrity repair.
- `32..36`: repair the no-data `SET_ADDRESS` transaction according to helper rc `S-30`.
- `30`: investigate loss/corruption of the r54 retained DMA page.
