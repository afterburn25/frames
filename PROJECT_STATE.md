# Frames — Canonical Project State

> Authoritative cross-chat handoff for active Frames engineering.
> Repository/evidence overrides chat summaries and prior claims.

Last updated: 2026-08-16

## Project identity / safety
- Frames is an independent operating system, not Windows- or Linux-based.
- Native systems language/toolchain: Nexus.
- Boot chain: UEFI -> BOOTX64.EFI -> FramesKernel.fkrn.
- Native application formats: FEX/FAPP.
- Evidence is fail-closed: exact source/hash, QEMU/OVMF first, then real hardware for physical claims.
- VM PASS is never described as physical PASS.
- Frames 1.0 is NOT promoted.
- Physical destructive writes, installation, persistent internal-media modification, and release promotion remain blocked.
- User-facing physical-test artifacts must be Rufus-compatible UEFI ISOs; raw IMG is CI-only.
- Independent workflows/lanes should run in parallel whenever practical.

## Certified reconstruction foundation — Frames 0.9.98 v108 r9
Fresh unchanged certification:
- workflow `.github/workflows/main.yml`
- run `31831716862`, attempt 2: PASS
- source commit `7333a6670a38c9180e7d72c2a3df444409c36164`
- runtime kit SHA-256 `61b0fc25513719fce554729724c7848647de9cffe54434d4ab5f7ba8af42a36a`
- nested source ZIP SHA-256 `5f8c13adac6d34e64bd47d9463a3e261cd0b51bb5ddb500aa9f7b87c2914a52d`
- exact certified base `kernel/main.nx` SHA-256 `ffc5721eca68844357dbdca63b0edf266e7e210f9d162eecde8cae0067f210a8`
- evidence artifact `9257820749`
- evidence ZIP SHA-256 `b7589b75190186b3886e76e8e571bbee1d58884e8a5516338ba59c994427ce74`

All current physical-input work reconstructs this exact v108 source. v109-v116 architecture transforms remain intentionally excluded from this physical-input bring-up train.

## Authoritative r13 physical result — user's ASUS laptop
Exact tested ISO:
- `Frames-0.9.98-v108-Physical-Input-Repair-r13-USB-Hub-Rufus-UEFI.iso`
- SHA-256 `ceb2201bd641e8f950929730e1dd6a0db8c7049aa29f0a133533e38fd55900a6`
- size `18,796,544 bytes`

Observed physical result:
- external USB mouse: FAIL — USB telemetry active but no visible cursor control;
- built-in touchpad: PARTIAL/FAIL — cursor is controllable and buttons work, but movement can jump back to earlier trail positions, especially during vertical motion and near the Input Test box;
- physical left click: PASS at the interactive UI;
- right click: untestable in r13 because no right-click target existed;
- keyboard: PARTIAL PASS — characters reached the text box, but this laptop keyboard has known hardware faults, so individual missed/repeated characters are not automatically attributed to Frames.

Physical interpretation:
- the PS/2/AUX -> Generic Pointer -> GUI path is real and active, but r13 introduced/retained a movement discontinuity;
- the GUI cursor/compositor path is proven by the touchpad, so the external USB mouse failure is upstream of visible pointer rendering;
- physical USB mouse remains unresolved and physical hardware remains authoritative.

## r14 corrective repair — VM certified, not physically tested
r14 source SHA-256:
- `2401b3a460430da6b008716e65f7be10dfb8e289da48b12045e1e1b920ed6caf`

r14 changes:
- quarantines r13/r12 typ-3 Elantech relative synthesis associated with physical jump-back discontinuities;
- preserves/restores hub parent control context while scanning sibling children;
- skips a boot-keyboard hub child and continues to the mouse child;
- adds a real right-click context-menu test and right-click counter;
- preserves existing boot, keyboard, left-click, GUI and read-only safety behavior.

Workflow:
- `.github/workflows/frames-v108-physical-input-r14-realhw-cert.yml`
- run `31969028082`: PASS
- all nine automated lanes PASS: USB direct, USB hub, USB multi-child hub, PS/2, quantitative smoothness, interactive UI, right-click, source model and read-only safety.

r14 was intentionally NOT sent as the next physical boot after the user requested text-editing UX before the next hands-on test.

## r15 text-editing + physical-input candidate — NEXT AUTHORIZED PHYSICAL BOOT
Exact r15 source SHA-256:
- `fa0f42f558f0004f7663f79b49c3049c57c896203cf18646b1ec6f999824f941`

r15 adds to the exact r14 source:
- pointer changes to an I-beam while hovering over the Input Test text box;
- visible blinking insertion caret while the text box has focus;
- click-to-position caret placement;
- Left Arrow and Right Arrow caret navigation;
- Home/End caret positioning support;
- Delete-at-caret;
- Backspace-before-caret;
- insertion at the caret rather than append-only text entry;
- dedicated live markers/counters for I-beam, caret, blink, Left, Right and Delete paths.

Primary r15 workflow:
- `.github/workflows/frames-v108-physical-input-r15-textedit-cert.yml`
- run `31969530813`
- exact r15 ISO built successfully;
- runtime/safety lanes PASS: USB direct, USB hub, USB hub keyboard-then-mouse, PS/2, quantitative smoothness, interactive UI, right-click, live text-edit, and read-only NVMe sentinel;
- initial model lane failed only because it searched for literal marker strings even though Nexus serial markers are encoded as `serial_putc` calls; live text-edit runtime had already emitted the markers and passed.

Corrected independent finalizer:
- `.github/workflows/frames-v108-physical-input-r15-finalize-r2.yml`
- run `31969738151`: PASS
- reuses the exact candidate from run `31969530813` rather than rebuilding/substituting it;
- re-verifies all successful runtime/safety evidence;
- corrected source-model contract: PASS;
- final artifact: `Frames-v108-r15-Rufus-Final-r2`
- artifact ID `9269447513`
- artifact ZIP digest `sha256:ef4665ff74ea7e97078f2eb162fc8f1e11082985cc714b40df94d89f1f39e694`

Exact next physical-test ISO:
- `Frames-0.9.98-v108-Physical-Input-Repair-r15-TextEdit-Rufus-UEFI.iso`
- SHA-256 `c9e5177a5595a7fee0910e3a177f258dd57e70a321cb1977118939e15716dd1c`
- size `18,817,024 bytes`
- Rufus mode: **ISO Image mode**
- status: `PASS_VM_PENDING_PHYSICAL`

Automated r15 evidence status:
- VM USB direct mouse: PASS
- VM USB hub child HID: PASS
- VM USB hub keyboard then mouse: PASS
- VM PS/2 pointer: PASS
- VM quantitative PS/2 smoothness: PASS
- VM keyboard text + clickable Input Test UI: PASS
- VM right-click context menu: PASS
- VM I-beam hover: PASS
- VM insertion caret: PASS
- VM caret blink: PASS
- VM Left/Right/Delete text editing: PASS
- read-only internal-media sentinel: PASS
- destructive writes: BLOCKED
- physical r15: PENDING

## r15 physical test order
Use only ISO SHA-256 `c9e5177a5595a7fee0910e3a177f258dd57e70a321cb1977118939e15716dd1c`.

1. Write with Rufus in **ISO Image mode** and boot the laptop in UEFI mode.
2. Touchpad: move slowly and quickly in all four directions, especially repeated up/down strokes and movement across/around the Input Test box. Report any jump-back, stale trail point, stall or reversal.
3. External USB mouse: move it in all directions. If it still cannot control the cursor, photograph the full `INPUT V108 LIVE` panel after moving it for several seconds.
4. Left click: verify normal controls still work.
5. Right click: right-click in the Input Test area and verify the visible `RIGHT CLICK OK` context popover/counter appears.
6. Hover over the text box without clicking: verify the normal pointer changes to an I-beam.
7. Click inside the text box: verify a visible insertion caret appears and visibly blinks.
8. Type a known short string such as `ABCD1234`.
9. Press Left and Right several times and verify the blinking caret visibly moves through the text.
10. Place the caret inside the string and press Delete; verify the character at the caret is removed and the remaining text closes the gap.
11. Press Backspace with the caret inside the string; verify the character before the caret is removed.
12. Because the laptop keyboard is known to be flaky, report intended keystrokes separately from spontaneous/repeating hardware behavior.
13. If any path fails or behaves oddly, photograph both the complete `INPUT V108 LIVE` panel and `INPUT TEST` panel.

No r14 physical boot is required; r15 supersedes r14 as the next physical candidate.

## Claim policy
- Touchpad physical movement/control: proven since r10/r11, but r13 jump-back regression requires r15 confirmation.
- External USB mouse: physical FAIL through r13; r15 is the next physical attempt after VM-certified multi-child hub repair.
- Keyboard text: physical partial delivery proven at r13, but laptop keyboard hardware is unreliable.
- Right-click, I-beam, caret blink and caret editing: VM-certified in r14/r15; physical confirmation pending r15.
- Frames 1.0 remains NOT promoted.
- Physical destructive writes remain BLOCKED.

## Automatic progression — standing project rule
- Failure -> diagnose -> repair -> rerun automatically.
- Pass -> independently verify -> update this file -> continue automatically.
- Do not wait for the user to say `continue`, `next`, or otherwise re-authorize routine engineering progression.
- Continue fixes/builds/CI automatically until the next genuine physical-hardware test, required user information, explicit authorization boundary, or safety boundary is reached.
- After the user supplies the physical result, immediately resume the diagnose -> repair -> CI -> next-physical-candidate loop without asking them to tell us to continue.
- Independent workflows/lanes should run in parallel whenever practical.

## Safety policy
- Physical destructive writes remain uncertified and blocked.
- Internal NVMe/SATA/system media remain outside destructive-write certification scope.
- `promotion_allowed` remains false.
- Frames 1.0 remains NOT promoted.

## New-chat startup
1. Read `PROJECT_STATE.md`.
2. Read `CONTINUITY_PROTOCOL.md`.
3. Inspect the active branch/run/evidence named here.
4. Repository/evidence overrides older chat/project summaries.
5. Do not silently pivot to another roadmap or claim level.
6. Preserve the automatic-progression rule above.
