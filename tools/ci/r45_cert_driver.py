#!/usr/bin/env python3
from pathlib import Path
import traceback
here=Path(__file__).parent
base=here/'r44_cert_driver.py'
src=base.read_text()

def one(old,new,label):
    global src
    n=src.count(old)
    if n!=1: raise SystemExit(f'r45 cert anchor {label} count {n}')
    src=src.replace(old,new,1)

def alln(old,new,count,label):
    global src
    n=src.count(old)
    if n!=count: raise SystemExit(f'r45 cert anchor {label} count {n}, expected {count}')
    src=src.replace(old,new)

one("'patch_v108_r44_hid_ring_forensic.py'","'patch_v108_r45_touchpad_button_isolation_xhci_dcs.py'",'patch target')
one('kernel-r44.nx','kernel-r45.nx','kernel evidence target')
alln('5fca6164e902f9720bef0d789ca46d2af480b065f32e1a6f61990476066962c1','b22fbc974398bdf6f13302fc1c05589966bad81edb72e83f0ca56b16f60b9b1b',2,'exact kernel identity')
one("'Frames-0.9.98-v108-r44-HID-Transfer-Ring-Forensic-Rufus-UEFI.iso'","'Frames-0.9.98-v108-r45-Touchpad-Button-Isolation-xHCI-DCS-Rufus-UEFI.iso'",'ISO target')
one("'R44-SHA.txt'","'R45-SHA.txt'",'SHA evidence target')
one("'R25K-R44.patch'","'R25K-R45.patch'",'patch evidence target')
one("'FRAMES_V108_R44'","'FRAMES_V108_R45'",'ISO label target')
one('R44-AGGREGATE.json','R45-AGGREGATE.json','aggregate target')
one("'frames-0.9.98-v108-r44-hid-transfer-ring-forensic'","'frames-0.9.98-v108-r45-touchpad-button-isolation-xhci-dcs'",'profile target')
one("'Frames 0.9.98 v108 r44 — HID Transfer-Ring Forensic'","'Frames 0.9.98 v108 r45 — Touchpad Button Isolation + xHCI DCS Proof'",'cert title target')
one('R44 PASS_VM_PENDING_PHYSICAL','R45 PASS_VM_PENDING_PHYSICAL','PASS target')
alln('R44-FAILURE.txt','R45-FAILURE.txt',2,'failure target')
one('r44 exact kernel identity mismatch','r45 exact kernel identity mismatch','identity label')
one("'physical_r44':'PENDING'","'physical_r44':'PHYSICAL_USB_NO_EVENT_DMA_TOUCHPAD_FALSE_RIGHT_INPUT_LOCK','physical_r44_telemetry':'R44_A1_T0_D0_V0_M0_Q0_B0','physical_r45':'PENDING'",'physical history target')

old_row="    req('volatile_read64(xhci+808)' in s and 'volatile_read64(xhci+3272)' in s and 'volatile_read64(xhci+2824)' in s and 'volatile_read64(xhci+3320)' in s and 'volatile_read64(xhci+3328)' in s and 'volatile_read64(xhci+3336)' in s and 'volatile_read64(xhci+3280)' in s,'r44 physical forensic row missing')"
new_row="""    req('volatile_read64(xhci+808)' in s and 'volatile_read64(xhci+2824)' in s and 'volatile_read64(xhci+3344)' in s and 'volatile_read64(xhci+3352)' in s and 'volatile_read64(xhci+3320)' in s and 'volatile_read64(xhci+3328)' in s and 'volatile_read64(xhci+3280)' in s,'r45 physical DCS row missing')
    buttons=s[s.index('fn ps2_elan4_buttons_v111'):s.index('fn ps2_signed_scale_v112')]
    req('if typ==1 || typ==2 {' in buttons and 'if typ>=1 && typ<=3 {' not in buttons,'r45 typ3 can still mutate touchpad buttons')
    req('if typ==3 {' in buttons and 'return ps2_elan4_motion_v112(input_state,a,b);' in s,'r45 lost typ3 observation or motion delivery')
    f45=s[s.index('fn v144_hid_forensic_snapshot'):s.index('fn v136_xhci_endpoint_snapshot')]
    req('volatile_read64(xhci_state+800)' in f45 and 'volatile_read64(xhci_state+2832)' in f45 and 'volatile_write64(xhci_state+3344,sw_cycle)' in f45 and 'volatile_write64(xhci_state+3352,hw_dcs)' in f45,'r45 software-cycle/hardware-DCS proof missing')
    req('volatile_write32' not in f45 and 'v136_xhci_command_endpoint' not in f45 and 'xhci_control' not in f45 and 'pit_wait' not in f45,'r45 DCS snapshot became active rather than passive')"""
one(old_row,new_row,'r45 model row and touchpad isolation gates')

ns={'__name__':'__main__','__file__':str(base)}
try:
    exec(compile(src,str(base),'exec'),ns,ns)
except BaseException:
    out=Path('evidence'); out.mkdir(parents=True,exist_ok=True)
    (out/'R45-FAILURE.txt').write_text(traceback.format_exc())
    raise
