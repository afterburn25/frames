# Frames v108 r32 physical USB result — 2026-08-17

Status: **FAIL_USB_PHYSICAL**. Do not promote.

Observed on the ASUS physical-test laptop:

- External USB input still does not work.
- New `R32 USB B A W` telemetry shows the xHCI connected-root census remained `1 -> 1` through the bounded settle window, with the wait window exhausted/stable.
- `XPWR` shows the xHCI root-port set powered while only one root connection remains visible.
- Intel USB2/USB3 routing telemetry remains applied.
- The visible root device continues to be the Rufus/SanDisk boot-side device rather than external HID.
- r32 right-click/text-focus regressions were not re-certified physically in this report and remain pending physical confirmation.

Interpretation:

The r32 settle experiment rules out a simple post-reset device-arrival delay. Repeated incremental timing changes should stop. The next candidate switches to controller-ownership recovery: explicitly request EHCI OS ownership, quiesce released EHCI companions, reassert Intel xHCI routing before and after xHCI initialization, and then re-census xHCI. If USB HID is stranded behind legacy EHCI ownership/routing, this should move it onto the existing xHCI path; otherwise the new EHCI telemetry will justify a direct EHCI HID fallback rather than more xHCI trial-and-error.
