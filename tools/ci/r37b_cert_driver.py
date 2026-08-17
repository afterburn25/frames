#!/usr/bin/env python3
from pathlib import Path
import traceback
here=Path(__file__).parent
base=here/'r37_cert_driver.py'
src=base.read_text()

def one(old,new,label):
 global src
 n=src.count(old)
 if n!=1: raise SystemExit(f'r37b cert anchor {label} count {n}')
 src=src.replace(old,new,1)

one("'patch_v108_r37_g750jm_xhci_ring_ps2.py'","'patch_v108_r37b_stable_diag.py'",'patch target')
one("\"kernel-r37.nx\"","\"kernel-r37b.nx\"",'kernel evidence target')
one("03f446845e111e35b8cff6b216c5fee2d214dc0a4d6e25898f8a03b891c0c511","2cb422d2c7d00cdbb1da3eee4ee696c9ae0723b3f28669bf80efe256d14de650",'exact kernel identity')
one("'Frames-0.9.98-v108-r37-G750JM-xHCI-Ring-Elantech-Recovery-Rufus-UEFI.iso'","'Frames-0.9.98-v108-r37b-G750JM-xHCI-Ring-Elantech-Stable-Diagnostics-Rufus-UEFI.iso'",'ISO target')
one("'R37-SHA.txt'","'R37B-SHA.txt'",'SHA evidence target')
one("'R25K-R37.patch'","'R25K-R37B.patch'",'patch evidence target')
one("'FRAMES_V108_R37'","'FRAMES_V108_R37B'",'ISO label target')
one("\"(ROOT/'evidence/R37-AGGREGATE.json')\"","\"(ROOT/'evidence/R37B-AGGREGATE.json')\"",'aggregate target')
one("'frames-0.9.98-v108-r37-g750jm-xhci-ring-elantech-recovery'","'frames-0.9.98-v108-r37b-g750jm-xhci-ring-elantech-stable-diagnostics'",'profile target')
one("'Frames 0.9.98 v108 r37 — G750JM xHCI Ring + Elantech Recovery'","'Frames 0.9.98 v108 r37b — G750JM xHCI Ring + Elantech Stable Diagnostics'",'cert title target')
one("\"print('R37 PASS_VM_PENDING_PHYSICAL',iso_sha)\"","\"print('R37B PASS_VM_PENDING_PHYSICAL',iso_sha)\"",'PASS target')
one('alln("R36-FAILURE.txt","R37-FAILURE.txt",3,\'failure evidence\')','alln("R36-FAILURE.txt","R37B-FAILURE.txt",3,\'failure evidence\')','failure target')
one("'physical_r36_telemetry':'R36_S1_I5_D5_M8_K562_E0','physical_r37':'PENDING'","'physical_r36_telemetry':'R36_S1_I5_D5_M8_K562_E0','physical_r37':'NOT_TESTED','physical_r37b':'PENDING'",'physical history target')
one("req('dnow-last_r37_draw>=1000000000' in s,'r37 diagnostic redraw throttle missing')","req('dnow-last_r37_draw>=2000000000' in s,'r37b endpoint-row redraw throttle missing')",'redraw throttle gate')
needle="    req('last_r36_k' not in s,'r37 stale per-kick telemetry redraw state remains')"
insert=needle+"""
    req('fn v108_input_overlay_r37_draw_v137' in s and 'fn v108_input_overlay_r37_present_v137' in s,'r37b compact endpoint row presenter missing')
    req('var r37_telemetry_redraw:u64=0' in s and 'v108_input_overlay_r37_present_v137(process,state,input_state,xhci)' in s,'r37b isolated endpoint telemetry scheduling missing')
    req('if usb_now!=last_usb_r { last_usb_r=usb_now; telemetry_redraw=1; }' not in s,'r37b USB report churn can still repaint full diagnostics panel')
    req('(410*65536)+28' in s and '(py+726)' in s,'r37b compact row geometry missing')
"""
one(needle,insert,'stable diagnostic model gates')

ns={'__name__':'__main__','__file__':str(base)}
try:
 exec(compile(src,str(base),'exec'),ns,ns)
except BaseException:
 out=Path('evidence'); out.mkdir(parents=True,exist_ok=True)
 (out/'R37B-FAILURE.txt').write_text(traceback.format_exc())
 raise
