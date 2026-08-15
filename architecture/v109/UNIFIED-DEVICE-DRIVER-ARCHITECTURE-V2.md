# Frames Unified Device & Driver Architecture v2

Target milestone: **Frames 0.9.99 — Unified Kernel Device & Driver Architecture Phase 1**.

This candidate is intentionally built from the sealed Frames 0.9.98 v108-r9 source while the new architecture is validated. The release identity is not promoted until external certification.

The kernel adds shared object models for bus topology, resource ownership, IRQ routing policy, deferred work, generic asynchronous I/O, DMA-map ownership, parent/child device relationships, lifecycle transitions, class-aware driver matching, USB host/root-hub objects, normalized input-source objects, completion objects, deadline/timer queues, driver probe scheduling, stable platform inventory, USB descriptor metadata, generic USB transfer requests, a USB enumeration state machine, HID class objects, and a normalized input-event ring.

The aggregate architecture manager requires all 20 component layers to pass their boot-time structural self-tests and chains that result to the pre-existing driver platform gate.

This phase does not replace or modify the physical xHCI, PS/2, NVMe, AHCI, network, display, or audio transaction paths. Existing physical-boot safety and media-write policy remain unchanged.
