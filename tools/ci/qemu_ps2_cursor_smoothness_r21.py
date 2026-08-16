#!/usr/bin/env python3
from pathlib import Path

# r21 enlarges the opaque INPUT V108 LIVE telemetry surface to about 544 px
# high. Keep the complete diagnostic surface out of pointer-locality metrics;
# the telemetry panel is independently verified by the interaction/model gates.
base=Path(__file__).with_name('qemu_ps2_cursor_smoothness.py')
s=base.read_text()
old='OVERLAY_X=850; OVERLAY_Y=205'
new='OVERLAY_X=840; OVERLAY_Y=552'
if s.count(old)!=1:
    raise SystemExit(f'unexpected base smoothness mask anchor: {s.count(old)}')
s=s.replace(old,new,1)
ns={'__name__':'__main__','__file__':str(base)}
exec(compile(s,str(base),'exec'),ns,ns)
