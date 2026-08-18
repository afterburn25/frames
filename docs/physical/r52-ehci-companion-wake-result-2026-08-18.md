# Frames v108 r52 physical result — Intel EHCI Companion Wake Proof

Date: 2026-08-18

User-reported physical telemetry from the exact r52 USB/EHCI diagnostic build:

`R52 W E P C R F V = 1 1 1 1 2 2 6147`

Decoded against `patch_v108_r52_intel_ehci_companion_wake.py`:
- `W=1`: bounded EHCI wake/route probe succeeded; a routed receiver was visible while the EHCI fabric was running.
- `E=1`: the receiver appeared on EHCI companion/controller ordinal 1.
- `P=1`: it appeared on EHCI root port 1.
- `C=1`: EHCI PORTSC Current Connect Status is asserted.
- `R=2`: both discovered EHCI controllers reached Running (`HCHalted=0`).
- `F=2`: both EHCI controllers reported CONFIGFLAG asserted.
- `V=6147` decimal = `0x1803`: the physical EHCI port is connected and powered, but Port Enable is still clear in this pre-reset state.

Physical engineering conclusion:
- r51 had already proven the Intel USB2 route bit could move away from xHCI but found no EHCI CCS while the companions were halted.
- r52 proves the alternate USB2 path is real and alive: waking the EHCI companions exposes the receiver on EHCI #1 port #1.
- This is not yet physical USB mouse PASS because no usable external pointer report has been delivered.
- The next discriminator is a bounded EHCI port reset / companion classification step. Standard EHCI determines high-speed ownership at reset; a non-high-speed device may be handed to a USB1 companion path.

Authoritative physical telemetry token:
`R52_W1_E1_P1_C1_R2_F2_V6147`
