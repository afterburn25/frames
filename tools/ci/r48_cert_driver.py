#!/usr/bin/env python3
from pathlib import Path
import traceback
here=Path(__file__).parent
# Retarget the proven r45 certification generator directly to r48.  The r48
# patch chains r47->r46->r45, so all inherited USB, PS/2, GUI, logging and
# internal-media safety gates stay active while the new scheduler boundary is
# certified.
base=here/'r45_cert_driver.py'
src=base.read_text()

def one(old,new,label):
    global src
    n=src.count(old)
    if n!=1: raise SystemExit(f'r48 cert anchor {label} count {n}')
    src=src.replace(old,new,1)

def alln(old,new,count,label):
    global src
    n=src.count(old)
    if n!=count: raise SystemExit(f'r48 cert anchor {label} count {n}, expected {count}')
    src=src.replace(old,new)

one("'patch_v108_r45_touchpad_button_isolation_xhci_dcs.py'","'patch_v108_r48_xhci_scheduler_wake.py'",'patch target')
one('kernel-r45.nx','kernel-r48.nx','kernel evidence target')
one('b22fbc974398bdf6f13302fc1c05589966bad81edb72e83f0ca56b16f60b9b1b','0e9a059bcec8ee0a1b7204b39585618418d51fce1ed4daccae67e2c2f877b984','exact kernel identity target')
one("'Frames-0.9.98-v108-r45-Touchpad-Button-Isolation-xHCI-DCS-Rufus-UEFI.iso'","'Frames-0.9.98-v108-r48-xHCI-Scheduler-Wake-MMIO-Barrier-Rufus-UEFI.iso'",'ISO target')
one("'R45-SHA.txt'","'R48-SHA.txt'",'SHA evidence target')
one("'R25K-R45.patch'","'R25K-R48.patch'",'patch evidence target')
one("'FRAMES_V108_R45'","'FRAMES_V108_R48'",'ISO label target')
one('R45-AGGREGATE.json','R48-AGGREGATE.json','aggregate target')
one("'frames-0.9.98-v108-r45-touchpad-button-isolation-xhci-dcs'","'frames-0.9.98-v108-r48-xhci-scheduler-wake-mmio-barrier'",'profile target')
one("'Frames 0.9.98 v108 r45 — Touchpad Button Isolation + xHCI DCS Proof'","'Frames 0.9.98 v108 r48 — xHCI Scheduler Wake + DMA/MMIO Ordering Barrier'",'cert title target')
one('R45 PASS_VM_PENDING_PHYSICAL','R48 PASS_VM_PENDING_PHYSICAL','PASS target')
alln('R45-FAILURE.txt','R48-FAILURE.txt',2,'failure target')
one('r45 exact kernel identity mismatch','r48 exact kernel identity mismatch','identity label')

old_hist="'physical_r44':'PHYSICAL_USB_NO_EVENT_DMA_TOUCHPAD_FALSE_RIGHT_INPUT_LOCK','physical_r44_telemetry':'R44_A1_T0_D0_V0_M0_Q0_B0','physical_r45':'PENDING'"
new_hist="'physical_r44':'PHYSICAL_USB_NO_EVENT_DMA_TOUCHPAD_FALSE_RIGHT_INPUT_LOCK','physical_r44_telemetry':'R44_A1_T0_D0_V0_M0_Q0_B0','physical_r45':'PHYSICAL_TOUCHPAD_NORMAL_USB_ARMED_NO_DEQUEUE_EVENT_DMA_CYCLE_MATCH','physical_r45_telemetry':'R45_A1_D0_C1_H1_V0_M0_B0','physical_r46':'PHYSICAL_TOUCHPAD_STABLE_USB_CONTEXT_ACCEPTED_NO_REPORT_DIRECT_ROOT','physical_r46_telemetry':'R46_S1_I5_T7_B0_M8_A8_E8_USB_R0_HUB_ZERO','physical_r47':'PHYSICAL_TRB_HANDOFF_AND_DOORBELL_PATH_OK_MFINDEX_STATIC_NO_DEQUEUE_EVENT_DMA','physical_r47_telemetry':'R47_H1_F1_M0_R0_Q0_V0_B0','physical_r48':'PENDING'"
one(old_hist,new_hist,'physical r45-r47 evidence and r48 pending')

old_row="    req('volatile_read64(xhci+808)' in s and 'volatile_read64(xhci+2824)' in s and 'volatile_read64(xhci+3344)' in s and 'volatile_read64(xhci+3352)' in s and 'volatile_read64(xhci+3320)' in s and 'volatile_read64(xhci+3328)' in s and 'volatile_read64(xhci+3280)' in s,'r45 physical DCS row missing')"
new_row="""    req('volatile_read64(xhci+3416)' in s and 'volatile_read64(xhci+3424)' in s and 'volatile_read64(xhci+3464)' in s and 'volatile_read64(xhci+3472)' in s and 'volatile_read64(xhci+3480)' in s and 'volatile_read64(xhci+3504)' in s and 'volatile_read64(xhci+3320)' in s,'r48 physical scheduler row missing')"""
one(old_row,new_row,'r48 physical row gate')

old_passive="    req('volatile_write32' not in f45 and 'v136_xhci_command_endpoint' not in f45 and 'xhci_control' not in f45 and 'pit_wait' not in f45,'r45 DCS snapshot became active rather than passive')"
new_passive=old_passive+"""
    req('volatile_read32(ep)' in f45 and 'volatile_read32(ep+4)' in f45 and 'volatile_read32(ep+16)' in f45,'r48 lost r46 accepted output endpoint-context proof')
    req('volatile_write64(xhci_state+3360,ep_state)' in f45 and 'volatile_write64(xhci_state+3408,ep_esit)' in f45,'r48 lost r46 endpoint-context telemetry')
    req('volatile_read32(runtime)%16384' in f45 and 'volatile_write64(xhci_state+3448,mf_moved)' in f45,'r48 lost r47 MFINDEX forensic snapshot')
    req('route=slot0%1048576' in f45 and 'volatile_write64(xhci_state+3456,route)' in f45,'r48 lost r47 direct-root route proof')
    arm=s[s.index('fn xhci_hid_arm_continuous'):s.index('fn xhci_hid_poll_continuous')]
    req('volatile_write32(trb+12,inactive)' in arm and 'volatile_read32(trb+12)!=inactive' in arm,'r48 lost non-owned TRB construction/readback')
    req('volatile_write32(trb+12,control)' in arm and 'volatile_read32(trb+12)!=control' in arm,'r48 lost final ownership handoff/readback')
    req('cpuid_eax(0,0)' in arm,'r48 DMA/MMIO serializing barrier missing')
    req('sts_flush=volatile_read32(op+4)' in arm and 'volatile_read32(db)' not in arm,'r48 safe USBSTS posted-write flush missing')
    req('mf_after=volatile_read32(runtime)%16384' in arm and 'spins<2000000' in arm,'r48 bounded MFINDEX scheduler proof missing')
    req('live_cmd=set_flag(live_cmd,1)' in arm and 'volatile_write32(db,dci)' in arm,'r48 bounded scheduler wake/re-ring missing')
    req('volatile_write64(xhci_state+3464,moved)' in arm and 'volatile_write64(xhci_state+3472,cmd_after%2)' in arm and 'volatile_write64(xhci_state+3480,sts_after%2)' in arm and 'volatile_write64(xhci_state+3504,wake)' in arm,'r48 scheduler telemetry missing')
    req('v136_xhci_command_endpoint' not in arm and 'xhci_control' not in arm and 'pit_wait' not in arm and 'v135_hid_control_fallback' not in arm,'r48 scheduler arm introduced forbidden recovery')
    req('if typ==1 || typ==2 {' in buttons and 'return ps2_elan4_motion_v112(input_state,a,b);' in s,'r48 regressed physically recovered touchpad contract')
"""
one(old_passive,new_passive,'r48 scheduler/order model gates')

ns={'__name__':'__main__','__file__':str(base)}
try:
    exec(compile(src,str(base),'exec'),ns,ns)
except BaseException:
    out=Path('evidence'); out.mkdir(parents=True,exist_ok=True)
    (out/'R48-FAILURE.txt').write_text(traceback.format_exc())
    raise
