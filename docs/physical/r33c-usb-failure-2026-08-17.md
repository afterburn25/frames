# Frames v108 r33c physical USB result — 2026-08-17

Status: **FAIL_USB_PHYSICAL_LATE_REROUTE_NO_HID**. Do not promote r33c.

Observed on the ASUS physical-test laptop:

- External USB input still does not work.
- The r33c diagnostic panel remains live and PS/2/touchpad activity is present.
- `XPWR PPC N B W A C` still shows the controller-init census at approximately `0 21 21 0 21 1`: 21 xHCI root ports are visible/powered and only one connection was present at the original init/power sample.
- The new r33 ownership row `R33 EH N CB CA BS H X` is decisive. The first value overlaps the final label glyph in this revision, but the row is consistent with `N=2, CB=0, CA=0, BS=0, H=2, X=5`: two EHCI companions were processed and halted, no devices remained connected on EHCI before/after release, BIOS ownership was cleared, and the post-reroute xHCI connected-root census increased to five.
- `X2A` / `X2F` still show no second distinct root HID enumeration/progression, and neither the external USB mouse nor external USB keyboard produces usable input.

Interpretation:

r33c changes the failure boundary. The machine is no longer best explained by USB HID being stranded behind BIOS-owned EHCI. EHCI ownership recovery appears to succeed, and repeating Intel USB2 routing after xHCI startup exposes additional root connections (`1 -> 5`). The failure is now between that late reroute and xHCI device enumeration/HID configuration.

The existing r33 path only settles/re-counts after the late route change. It does not rebuild the xHCI controller/rings after the newly routed USB2 ports become visible. The next candidate should therefore perform a bounded xHCI reinitialization only when the late reroute increases the connected-root census, then power/settle the newly routed ports and scan them with explicit before/post/reinit telemetry. Direct EHCI HID fallback is not the next experiment because the physical evidence shows zero EHCI-connected devices after ownership recovery while xHCI gains the connections.
