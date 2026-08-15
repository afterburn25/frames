# Frames 0.9.98 r56 — Linux-reference input architecture

r56 changes strategy from cursor filtering to subsystem boundaries.

USB target: separate PCI/xHCI controller discovery, controller initialization, root-port enumeration, USB device descriptor/configuration, HID interface binding, interrupt-IN streaming, and Generic Pointer delivery.

PS/2 target: separate i8042/AUX transport from protocol identification and packet decoding. Generic 3-byte PS/2 is a fallback protocol, not an assumption for laptop touchpads.

The first r56 physical gate records controller-probe readiness, xHCI state presence, discovered xHCI hardware, controller-init success, USB enumeration stage, scan attempts, selected port, and VID. This is diagnostic-only and must not replace the known working r50 physical pointer baseline.