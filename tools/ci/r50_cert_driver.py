#!/usr/bin/env python3
from pathlib import Path
import traceback
here=Path(__file__).parent
base=here/'r49_cert_driver.py'
src=base.read_text()

def one(old,new,label):
    global src
    n=src.count(old)
    if n!=1: raise SystemExit(f'r50 cert anchor {label} count {n}')
    src=src.replace(old,new,1)

def alln(old,new,count,label):
    global src
    n=src.count(old)
    if n!=count: raise SystemExit(f'r50 cert anchor {label} count {n}, expected {count}')
    src=src.replace(old,new)

one("'patch_v108_r49_xhci_root_port_slot_proof.py'","'patch_v108_r50_device_endpoint_status_proof.py'",'patch target')
one('kernel-r49.nx','kernel-r50.nx','kernel evidence target')
one('8fb90cb36157c9efaec61983105de52834d62e912f4bd709de97ec0deee4991a','30d8239eb1c91a5b70246744d856e1a7aae77360baeaa024033fb135070fd6f1','exact kernel identity target')
one("'Frames-0.9.98-v108-r49-xHCI-Root-Port-Slot-Transaction-Proof-Rufus-UEFI.iso'","'Frames-0.9.98-v108-r50-USB-Device-Endpoint-Status-Proof-Rufus-UEFI.iso'",'ISO target')
one("'R49-SHA.txt'","'R50-SHA.txt'",'SHA evidence target')
one("'R25K-R49.patch'","'R25K-R50.patch'",'patch evidence target')
one("'FRAMES_V108_R49'","'FRAMES_V108_R50'",'ISO label target')
one('R49-AGGREGATE.json','R50-AGGREGATE.json','aggregate target')
one("'frames-0.9.98-v108-r49-xhci-root-port-slot-transaction-proof'","'frames-0.9.98-v108-r50-usb-device-endpoint-status-proof'",'profile target')
one("'Frames 0.9.98 v108 r49 — xHCI Root-Port + Slot Transaction Proof'","'Frames 0.9.98 v108 r50 — USB Device Endpoint Status Proof'",'cert title target')
one('R49 PASS_VM_PENDING_PHYSICAL','R50 PASS_VM_PENDING_PHYSICAL','PASS target')
alln('R49-FAILURE.txt','R50-FAILURE.txt',2,'failure target')
one('r49 exact kernel identity mismatch','r50 exact kernel identity mismatch','identity label')

old_hist="'physical_r48':'PHYSICAL_SCHEDULER_RUNNING_TRB_HANDOFF_FLUSH_OK_NO_TRANSFER_EVENT','physical_r48_telemetry':'R48_T1_F1_M1_U1_H0_W0_V0','physical_r49':'PENDING'"
new_hist="'physical_r48':'PHYSICAL_SCHEDULER_RUNNING_TRB_HANDOFF_FLUSH_OK_NO_TRANSFER_EVENT','physical_r48_telemetry':'R48_T1_F1_M1_U1_H0_W0_V0','physical_r49':'PHYSICAL_ROOT_PORT_SLOT_MATCH_CONNECTED_ENABLED_U0_FULLSPEED_ADDR1_NO_REPORT','physical_r49_telemetry':'R49_P2_R2_C1_E1_L0_S1_A1','physical_r50':'PENDING'"
one(old_hist,new_hist,'physical r49 evidence and r50 pending')

old_row="""    req('volatile_read64(xhci+3544)' in s and 'volatile_read64(xhci+3552)' in s and 'volatile_read64(xhci+3560)' in s and 'volatile_read64(xhci+3568)' in s and 'volatile_read64(xhci+3576)' in s and 'volatile_read64(xhci+3584)' in s and 'volatile_read64(xhci+3592)' in s,'r49 physical root-port/slot row missing')"""
new_row="""    req('volatile_read64(xhci+3624)' in s and 'volatile_read64(xhci+3632)' in s and 'volatile_read64(xhci+3640)' in s and 'volatile_read64(xhci+3648)' in s and 'volatile_read64(xhci+3656)' in s and 'volatile_read64(xhci+3672)' in s and 'volatile_read64(xhci+3680)' in s,'r50 physical device-status row missing')"""
one(old_row,new_row,'r50 physical row gate')

gate_anchor="    req('volatile_write32(port' not in f45 and 'xhci_control' not in f45 and 'v136_xhci_command_endpoint' not in f45 and 'pit_wait' not in f45,'r49 root-port proof became active')"
gate_extra=gate_anchor+"""
    cfg50=s[s.index('fn xhci_configure_boot_hid'):s.index('fn xhci_hid_arm_continuous')]
    req('usb_setup_value_v113(128,8,0,0)' in cfg50,'r50 GET_CONFIGURATION proof missing')
    req('usb_setup_value_v113(129,10,0,interface_num)' in cfg50,'r50 GET_INTERFACE proof missing')
    req('usb_setup_value_v113(130,0,0,ep_addr)' in cfg50,'r50 endpoint GET_STATUS proof missing')
    req('usb_setup_value_v113(2,1,0,ep_addr)' in cfg50 and 'if halt_before==1' in cfg50,'r50 bounded clear-halt recovery missing')
    req('volatile_write64(xhci_state+3624,cfg_val)' in cfg50 and 'volatile_write64(xhci_state+3680,port_speed)' in cfg50,'r50 device-status telemetry missing')
    req('v135_hid_control_fallback_poll' not in cfg50,'r50 reintroduced continuous GET_REPORT fallback')
"""
one(gate_anchor,gate_extra,'r50 device endpoint-status model gates')

ns={'__name__':'__main__','__file__':str(base)}
try:
    exec(compile(src,str(base),'exec'),ns,ns)
except BaseException:
    out=Path('evidence'); out.mkdir(parents=True,exist_ok=True)
    (out/'R50-FAILURE.txt').write_text(traceback.format_exc())
    raise
