# Frames v108 r47 physical USB result — 2026-08-18

Physical target: ASUS laptop with Intel Lynx Point xHCI controller `8086:8c31` and Maxxter low-speed HID receiver `248a:10ab`.

Result: **USB HID physical FAIL; touchpad/desktop remained available.**

Observed r47 telemetry after boot and USB input exercise:

- `R47 H F M R Q V B = 1 1 0 0 0 0 0`
- `H=1`: software-built Normal TRB survived the two-phase controller-ownership handoff readback.
- `F=1`: r47 endpoint doorbell path executed.
- `M=0`: MFINDEX did not prove periodic-scheduler advancement after the HID TD was armed.
- `R=0`: selected HID is direct-root (`route string 0`), not hub/TT dependent.
- `Q=0`: hardware output endpoint dequeue remained at transfer-ring index 0.
- `V=0`: no direct Transfer Event was observed.
- `B=0`: first four HID DMA bytes remained zero.
- Existing r42 row remained consistent with a healthy control path and report descriptor discovery (`G=1`, protocol 0, report length 142, interrupt request length 8, babble 0, completion 0).

Interpretation:

The physical failure boundary is later than enumeration, HID selection, Configure Endpoint, Set Configuration/Protocol, and TRB publication. r46 already proved the controller accepted a Running interrupt-IN endpoint context (`S1 I5 T7 B0 M8 A8 E8`). r47 now proves the TD was published and the endpoint doorbell path executed, yet the controller did not advance the periodic transfer machinery.

Follow-up: r48 changes only this boundary. It adds a serializing CPU barrier before the endpoint doorbell, flushes posted MMIO through USBSTS instead of reading the doorbell register, waits boundedly for MFINDEX movement, and when the controller has no host-controller error, performs one bounded Run/wake + endpoint re-ring recovery. New physical row: `R48 T F M U H W V`.
