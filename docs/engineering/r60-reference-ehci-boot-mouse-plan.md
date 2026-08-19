# Frames v108 r60 — Reference-Driven EHCI Boot Mouse Configuration

Date: 2026-08-19

## Why r60 exists

The r59 diagnostic sequence narrowed the physical failure to one full-speed HID mouse endpoint behind the Intel Lynx Point EHCI transaction-translator path. r60 stops speculative C-mask/protocol tuning and rebuilds the last mile from the physical evidence plus mature EHCI scheduling behavior.

## Physically established topology

- Host platform: Intel 8-Series/C220 / Lynx Point.
- xHCI: `8086:8c31`.
- Two EHCI companions are present and can be started.
- The working alternate path is the second EHCI controller.
- Intel high-speed rate-matching hub: `8087:8008`, USB address 1.
- Receiver: `248a:10ab`, full-speed, USB address 2, downstream hub port 2.
- Composite boot-HID receiver:
  - keyboard interrupt-IN endpoint `0x81`;
  - mouse interrupt-IN endpoint `0x82`;
  - mouse interface 0;
  - mouse max packet 8 bytes;
  - mouse `bInterval = 4` frames.

Key accepted physical rows:
- `R56 S E N C B F T = 1 2 8 1 2 2 0`
- `R57 S P M V D R E = 1 2 8 9354 4267 1 130`
- `R58 S P K M I L C = 1 2 129 130 0 8 2`
- r59e/r59f physically proved the periodic QH is fetched and its qTD is active without a QH-level error.

## Cross-reference result

Linux EHCI constructs full-speed interrupt QHs behind a transaction translator with:
- endpoint speed = full-speed (`EPS=0`);
- device address + endpoint number in QH endpoint characteristics;
- max packet in QH endpoint characteristics;
- TT hub address and downstream TT port in endpoint capabilities;
- `Mult = 1` for TT traffic;
- reload/Nak count left zero for interrupt traffic;
- a periodic S-mask/C-mask selected by the TT scheduler.

The default Linux `USB_EHCI_TT_NEWSCHED` path is enabled by default and, for a Start-Split in microframe 0, considers Complete-Splits in microframes 2 through 4. That corresponds to `S-mask = 0x01`, `C-mask = 0x1c`.

Therefore r59h's experimental `C-mask = 0x06` is not retained as the r60 reference configuration. r60 restores the default new-scheduler geometry `0x1c`.

Linux also normally marks the final qTD with IOC. Frames still polls rather than enabling EHCI interrupts, but r60 sets IOC in the qTD so the descriptor itself matches the ordinary final-qTD construction more closely.

## r60 exact target configuration

For the physically identified mouse path:

- EHCI controller: ordinal 2 / second discovered EHCI.
- TT hub address: 1.
- TT downstream port: 2.
- USB device address: 2.
- endpoint: 2 IN (`0x82`).
- endpoint speed: full-speed.
- max packet: 8.
- interval: 4 frames.
- S-mask: `0x01`.
- C-mask: `0x1c`.
- Mult: 1.
- qTD PID: IN.
- CERR: 3.
- qTD length: 8.
- qTD Active: 1.
- IOC: 1.
- HID protocol: boot protocol (`SET_PROTOCOL(0)`), verified by `GET_PROTOCOL` returning 0.

## Important r60 behavioral change

r59 was intentionally diagnostics-only. r60 is the first bounded EHCI candidate allowed to deliver a successfully completed boot-mouse packet into Frames' already-existing Generic Pointer queue:

- report byte 0 -> input kind 4 (buttons),
- report byte 1 -> input kind 5 (X),
- report byte 2 -> input kind 6 (Y).

The same input kinds are already consumed by the GUI pointer path. r60 therefore can produce actual cursor movement if the EHCI interrupt-IN transaction completes.

r60 also observes the live QH overlay token (`QH + 24`) in addition to qTD memory. This follows the EHCI QH overlay model and removes the r59 diagnostic blind spot where only the qTD memory token was being treated as the live execution state.

## Safety scope

r60 remains read-only with respect to storage. It does not enable installation, NVMe/SATA writes, filesystem writes, or persistent internal-media modification. The only newly authorized side effect is bounded delivery of buttons/X/Y events to the existing in-memory Generic Pointer input queue.

## Physical success criterion

Physical PASS requires the external USB mouse to move the Frames cursor and produce changing r60 completion/delivery/raw-report telemetry. CI/VM PASS alone is not a physical mouse PASS.
