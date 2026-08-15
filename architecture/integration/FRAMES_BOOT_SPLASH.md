# Frames Full-Product Boot Splash Integration

Target: Frames v116 full-product integration on the v101 product shell.

## UX contract
- Use the existing Frames `F` loader mark as the initial splash mark for this test train.
- Switch to splash rendering as soon as GOP/framebuffer is available.
- Dark full-screen background, centered Frames mark/wordmark, single progress bar near the lower third.
- Do not expose primitive stage/status text on the framebuffer during the normal path.
- Preserve every detailed boot/handoff breadcrumb on serial/evidence output.
- Fall back to the existing text loader if GOP/framebuffer splash setup is unavailable.

## Progress contract
The bar is milestone driven, never timer driven:
1. 8%  - loader initialized / boot medium opened
2. 20% - FramesKernel.fkrn located and SHA-256 verified
3. 32% - System.fex/FEX payload located and verified
4. 45% - kernel/System executable memory prepared
5. 58% - ACPI/framebuffer/boot-module/memory-map handoff structures prepared
6. 70% - immediately before ExitBootServices
7. 80% - ExitBootServices succeeded / firmware ownership released
8. 88% - first FramesKernel entry breadcrumb reached
9. 94% - early kernel/platform/scheduler initialization complete
10. 98% - System/FEX and compositor/desktop startup initiated
11. 100% - desktop-ready handoff; desktop takes framebuffer ownership

If a stage stalls, the bar must remain at the last successfully completed milestone.

## Diagnostic breadcrumbs
Serial/evidence markers must include at minimum:
- FRAMES_HANDOFF_PRE_EBS
- FRAMES_HANDOFF_POST_EBS
- FRAMES_KERNEL_ENTRY
- FRAMES_KERNEL_EARLY_MEMORY_OK
- FRAMES_KERNEL_PLATFORM_OK
- FRAMES_KERNEL_SCHEDULER_OK
- FRAMES_SYSTEM_LAUNCH_BEGIN
- FRAMES_SYSTEM_LAUNCH_OK
- FRAMES_COMPOSITOR_BEGIN
- FRAMES_DESKTOP_READY

The framebuffer splash and serial breadcrumb stream are deliberately separate: the user sees a polished loading experience while CI/physical debugging retains exact stage evidence.
