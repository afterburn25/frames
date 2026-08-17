#!/usr/bin/env python3
from pathlib import Path

base=Path(__file__).with_name('r25_cert_driver.py')
s=base.read_text()
repls={
    "R25_SHA='068ed900f8942ecec797e2f5fa5e79f95fce51ef817b2e3336af05d643528674'":"R25_SHA='9224366a0d53bab0815d8c04f17017fc20858dc2a196f41cf159bf85ac24f395'",
    "patch_v108_r25_flightrec_usbwrite.py":"patch_v108_r25c_bracefix.py",
    "'FRAMES_FLIGHT_RECORDER_R25_READY','FRAMES_CONTROLLED_USB_LOG_R25_ARMED','fn v108_msc_snapshot_v125'":"'fn serial_marker_flight_recorder_r25','fn serial_marker_controlled_usb_log_r25','fn v108_msc_snapshot_v125'",
    "'XENU ST FL VID PID MSC LOG','FREC Q DROP ARM W ERR'":"'fn v108_text_xenu_v125','fn v108_text_frec_v125'",
}
for old,new in repls.items():
    if s.count(old)!=1:
        raise SystemExit(f'r25 v4 anchor mismatch for {old!r}: {s.count(old)}')
    s=s.replace(old,new,1)
ns={'__name__':'__main__','__file__':str(base)}
exec(compile(s,str(base),'exec'),ns,ns)
