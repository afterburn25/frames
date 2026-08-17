# Frames v108 r31b physical USB/input result — 2026-08-17

Status: **FAIL_USB_PHYSICAL_INPUT_REGRESSIONS**. Do not promote r31b.

Exact tested candidate:

- Frames `0.9.98` / v108 r31b
- ISO: `Frames-0.9.98-v108-r31b-USB-State-Isolation-Controller-Order-Recovery-Rufus-UEFI.iso`
- ISO SHA-256: `8cad32d19daa7945297628b1a46289e02e0eeb04f2962b8ac22946b4b754ca64`
- ISO label: `FRAMES_V108_R31B`

Observed on the ASUS physical-test laptop:

- External USB mouse still produces no usable input.
- External USB keyboard still produces no usable input.
- Touchpad movement still controls the pointer.
- Moving the touchpad can falsely activate/open the desktop right-click/context menu.
- Deliberate physical right click does not open the context menu.
- The INPUT TEST text box can no longer be focused/clicked for keyboard testing.

Physical telemetry visible in the diagnostic overlay included:

- `XPWR PPC N B W A C`: approximately `0 21 21 0 21 1` — 21 root ports reported/powered, only one root connection visible at the sampled census.
- `XPRI S F C P R O`: approximately `9 0 1 16 0 1` — primary xHCI reached the running/controller-order proof state without an init error, but only one connection was observed.
- `XPRT M C E P S`: approximately `21 1 0 21 4785` — 21 max ports, one connected, zero enabled before reset sample, 21 powered.
- `X2A` / `X2F`: remained zero, providing no evidence that a second distinct root-port HID device was enumerated.
- Hub-path telemetry remained zero; no successful downstream-hub HID discovery was demonstrated.
- `TEST F C L` remained zero, consistent with the observed inability to focus the text box.

Source diagnosis after the physical result:

1. `ps2_elan4_buttons_v111` allowed Elantech motion packet class `typ==3` to update the right-button state. With one-packet acceptance, motion could therefore manufacture a right-button down edge and open the context menu.
2. `v108_input_test_click_v112` rejected a text-box click when either the current or previous button state contained right-button state, so the false/stale right edge could prevent focus recovery.
3. The primary xHCI controller was reaching its fully started state, but the immediate post-reset/root-power connection census observed only one root device. The next candidate therefore needs a bounded physical settle/re-census before scanning rather than treating the first instantaneous count as final.

r32 response:

- Add a bounded post-controller/root-power USB connection settle/re-census window with physical before/after telemetry.
- Prevent Elantech motion packets from mutating right-button state; accept right-button changes only from button-bearing packet classes.
- Allow a released stale right state to stop blocking a subsequent legitimate text-box left click.
- Keep USB HID recovery as the primary physical objective while certifying the right-click/text-focus regressions as required side fixes.
