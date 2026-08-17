# Frames v108 r30b physical USB result — 2026-08-17

Status: **FAIL_USB_PHYSICAL**. Do not promote.

Observed on the ASUS physical-test laptop:

- USB mouse: no response.
- USB keyboard: no response.
- Touchpad/desktop remain usable.
- Moving the touchpad can still spuriously open the desktop right-click/context menu.
- Deliberate physical right click does not open the menu.
- Physical telemetry rows `X2A`, `X2F`, `XPWR`, `XRTY`, `XENU`, `FREC`, `EP0A`, and `EP0F` did not provide evidence of successful HID/MSC enumeration.

Source review after this test identified a USB-state architecture fault: `v108_log_msc_retain_v125` reused and zeroed the same `xhci_state` page used by the primary HID scan. A fallback MSC/log rescan could therefore destroy primary controller state/telemetry. The same function also reinitialized the physical controller after the primary scan.

The next physical candidate must isolate fallback MSC scan state, preserve primary controller evidence, and keep the known-good desktop behavior only as a regression gate. USB remains the sole development priority.
