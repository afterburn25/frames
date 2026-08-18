#!/usr/bin/env python3
from pathlib import Path
import traceback
here=Path(__file__).parent
base=here/'r48_cert_driver.py'
src=base.read_text()

def one(old,new,label):
    global src
    n=src.count(old)
    if n!=1: raise SystemExit(f'r49 cert anchor {label} count {n}')
    src=src.replace(old,new,1)

def alln(old,new,count,label):
    global src
    n=src.count(old)
    if n!=count: raise SystemExit(f'r49 cert anchor {label} count {n}, expected {count}')
    src=src.replace(old,new)

one("'patch_v108_r48_xhci_scheduler_wake.py'","'patch_v108_r49_xhci_root_port_slot_proof.py'",'patch target')
one('kernel-r48.nx','kernel-r49.nx','kernel evidence target')
one('0e9a059bcec8ee0a1b7204b39585618418d51fce1ed4daccae67e2c2f877b984','8fb90cb36157c9efaec61983105de52834d62e912f4bd709de97ec0deee4991a','exact kernel identity target')
one("'Frames-0.9.98-v108-r48-xHCI-Scheduler-Wake-MMIO-Barrier-Rufus-UEFI.iso'","'Frames-0.9.98-v108-r49-xHCI-Root-Port-Slot-Transaction-Proof-Rufus-UEFI.iso'",'ISO target')
one("'R48-SHA.txt'","'R49-SHA.txt'",'SHA evidence target')
one("'R25K-R48.patch'","'R25K-R49.patch'",'patch evidence target')
one("'FRAMES_V108_R48'","'FRAMES_V108_R49'",'ISO label target')
one('R48-AGGREGATE.json','R49-AGGREGATE.json','aggregate target')
one("'frames-0.9.98-v108-r48-xhci-scheduler-wake-mmio-barrier'","'frames-0.9.98-v108-r49-xhci-root-port-slot-transaction-proof'",'profile target')
one("'Frames 0.9.98 v108 r48 — xHCI Scheduler Wake + DMA/MMIO Ordering Barrier'","'Frames 0.9.98 v108 r49 — xHCI Root-Port + Slot Transaction Proof'",'cert title target')
one('R48 PASS_VM_PENDING_PHYSICAL','R49 PASS_VM_PENDING_PHYSICAL','PASS target')
alln('R48-FAILURE.txt','R49-FAILURE.txt',2,'failure target')
one('r48 exact kernel identity mismatch','r49 exact kernel identity mismatch','identity label')

old_hist="'physical_r44':'PHYSICAL_USB_NO_EVENT_DMA_TOUCHPAD_FALSE_RIGHT_INPUT_LOCK','physical_r44_telemetry':'R44_A1_T0_D0_V0_M0_Q0_B0','physical_r45':'PHYSICAL_TOUCHPAD_NORMAL_USB_ARMED_NO_DEQUEUE_EVENT_DMA_CYCLE_MATCH','physical_r45_telemetry':'R45_A1_D0_C1_H1_V0_M0_B0','physical_r46':'PHYSICAL_TOUCHPAD_STABLE_USB_CONTEXT_ACCEPTED_NO_REPORT_DIRECT_ROOT','physical_r46_telemetry':'R46_S1_I5_T7_B0_M8_A8_E8_USB_R0_HUB_ZERO','physical_r47':'PHYSICAL_TRB_HANDOFF_AND_DOORBELL_PATH_OK_MFINDEX_STATIC_NO_DEQUEUE_EVENT_DMA','physical_r47_telemetry':'R47_H1_F1_M0_R0_Q0_V0_B0','physical_r48':'PENDING'"
new_hist="'physical_r44':'PHYSICAL_USB_NO_EVENT_DMA_TOUCHPAD_FALSE_RIGHT_INPUT_LOCK','physical_r44_telemetry':'R44_A1_T0_D0_V0_M0_Q0_B0','physical_r45':'PHYSICAL_TOUCHPAD_NORMAL_USB_ARMED_NO_DEQUEUE_EVENT_DMA_CYCLE_MATCH','physical_r45_telemetry':'R45_A1_D0_C1_H1_V0_M0_B0','physical_r46':'PHYSICAL_TOUCHPAD_STABLE_USB_CONTEXT_ACCEPTED_NO_REPORT_DIRECT_ROOT','physical_r46_telemetry':'R46_S1_I5_T7_B0_M8_A8_E8_USB_R0_HUB_ZERO','physical_r47':'PHYSICAL_TRB_HANDOFF_AND_DOORBELL_PATH_OK_MFINDEX_STATIC_NO_DEQUEUE_EVENT_DMA','physical_r47_telemetry':'R47_H1_F1_M0_R0_Q0_V0_B0','physical_r48':'PHYSICAL_SCHEDULER_RUNNING_TRB_HANDOFF_FLUSH_OK_NO_TRANSFER_EVENT','physical_r48_telemetry':'R48_T1_F1_M1_U1_H0_W0_V0','physical_r49':'PENDING'"
one(old_hist,new_hist,'physical r48 evidence and r49 pending')

old_row="""    req('volatile_read64(xhci+3416)' in s and 'volatile_read64(xhci+3424)' in s and 'volatile_read64(xhci+3464)' in s and 'volatile_read64(xhci+3472)' in s and 'volatile_read64(xhci+3480)' in s and 'volatile_read64(xhci+3504)' in s and 'volatile_read64(xhci+3320)' in s,'r48 physical scheduler row missing')"""
new_row="""    req('volatile_read64(xhci+3544)' in s and 'volatile_read64(xhci+3552)' in s and 'volatile_read64(xhci+3560)' in s and 'volatile_read64(xhci+3568)' in s and 'volatile_read64(xhci+3576)' in s and 'volatile_read64(xhci+3584)' in s and 'volatile_read64(xhci+3592)' in s,'r49 physical root-port/slot row missing')"""
one(old_row,new_row,'r49 physical row gate')

anchor="    req('if typ==1 || typ==2 {' in buttons and 'return ps2_elan4_motion_v112(input_state,a,b);' in s,'r48 regressed physically recovered touchpad contract')"
extra=anchor.replace('r48','r49')+"""
    req('hw_root=(slot1/65536)%256' in f45 and 'dev_addr=slot3%256' in f45 and 'slot_state=(slot3/134217728)%32' in f45,'r49 hardware Slot Context identity proof missing')
    req('portsc=volatile_read32(port)' in f45 and 'ccs=portsc%2' in f45 and 'ped=(portsc/2)%2' in f45 and 'pls=(portsc/32)%16' in f45 and 'pspeed=(portsc/1024)%16' in f45,'r49 live PORTSC transaction-path proof missing')
    req('volatile_write64(xhci_state+3544,sw_port)' in f45 and 'volatile_write64(xhci_state+3552,hw_root)' in f45 and 'volatile_write64(xhci_state+3608,portsc)' in f45,'r49 root-port evidence storage missing')
    req('volatile_write32(port' not in f45 and 'xhci_control' not in f45 and 'v136_xhci_command_endpoint' not in f45 and 'pit_wait' not in f45,'r49 root-port proof became active')
"""
one(anchor,extra,'r49 root-port/slot model gates')

ns={'__name__':'__main__','__file__':str(base)}
try:
    exec(compile(src,str(base),'exec'),ns,ns)
except BaseException:
    out=Path('evidence'); out.mkdir(parents=True,exist_ok=True)
    (out/'R49-FAILURE.txt').write_text(traceback.format_exc())
    raise
