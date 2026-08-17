# Frames v108 r26 physical USB failure — 2026-08-17

Physical ASUS laptop evidence from r26 ISO-native Flight Recorder build:

- Rufus ISO boot path works and desktop/touchpad remain operational.
- USB mouse and USB keyboard remain nonfunctional.
- Returned `FRAMES.LOG` is byte-for-byte pristine; no runtime sector was written.
- Touchpad motion can spuriously activate the context menu; deliberate physical right-click does nothing.
- Telemetry photo shows meaningful `XINI` state but `XEVT`, `EP0A`, `EP0F`, `XRST`, `XPRT`, `XENU`, and `FREC` effectively zero.
- Therefore the immediate priority is native physical USB controller recovery before further unrelated feature work.

## r27 priority order

1. Controller ownership and Intel routing handoff.
2. xHC halted/run/reset state, CRCR/DCBAAP/ERST/ERDP validity.
3. Root-port census, reset, enable, protocol/speed mapping.
4. Enable Slot and Address Device.
5. EP0 control transfers and descriptors.
6. Hubs / multiple simultaneous slots and endpoints.
7. HID mouse + keyboard.
8. USB Mass Storage read path.
9. ISO-native `FRAMES.LOG` bounded write / flush / readback.
10. Keep internal NVMe/SATA/ESP read-only.

## Regression baseline

Preserve the working r24/r26 desktop behavior (pointer motion, left click, full-window drag, text/focus, no full-desktop repaint). The right-click defect remains recorded but does not outrank USB controller recovery.
