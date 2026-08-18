#!/usr/bin/env python3
from pathlib import Path
import traceback
here=Path(__file__).parent
base=here/'r45_cert_driver.py'
src=base.read_text()

def one(old,new,label):
    global src
    n=src.count(old)
    if n!=1: raise SystemExit(f'r46 cert anchor {label} count {n}')
    src=src.replace(old,new,1)

def alln(old,new,count,label):
    global src
    n=src.count(old)
    if n!=count: raise SystemExit(f'r46 cert anchor {label} count {n}, expected {count}')
    src=src.replace(old,new)

# Retarget the already-green r45 certification generator to the passive r46
# endpoint-context proof. r46's patch itself chains through exact r45, so every
# inherited VM, interaction, logging, USB topology, PS/2 and safety gate remains.
one("'patch_v108_r45_touchpad_button_isolation_xhci_dcs.py'","'patch_v108_r46_xhci_periodic_context_proof.py'",'patch target')
one('kernel-r45.nx','kernel-r46.nx','kernel evidence target')
one('b22fbc974398bdf6f13302fc1c05589966bad81edb72e83f0ca56b16f60b9b1b','8ddc1a93fa4a19e72d0a6a40058d8681ed2ef42b48bcd0ff4644ba8e25c2caf1','exact kernel identity target')
one("'Frames-0.9.98-v108-r45-Touchpad-Button-Isolation-xHCI-DCS-Rufus-UEFI.iso'","'Frames-0.9.98-v108-r46-xHCI-Periodic-Endpoint-Context-Proof-Rufus-UEFI.iso'",'ISO target')
one("'R45-SHA.txt'","'R46-SHA.txt'",'SHA evidence target')
one("'R25K-R45.patch'","'R25K-R46.patch'",'patch evidence target')
one("'FRAMES_V108_R45'","'FRAMES_V108_R46'",'ISO label target')
one('R45-AGGREGATE.json','R46-AGGREGATE.json','aggregate target')
one("'frames-0.9.98-v108-r45-touchpad-button-isolation-xhci-dcs'","'frames-0.9.98-v108-r46-xhci-periodic-endpoint-context-proof'",'profile target')
one("'Frames 0.9.98 v108 r45 — Touchpad Button Isolation + xHCI DCS Proof'","'Frames 0.9.98 v108 r46 — xHCI Periodic Endpoint Context Proof'",'cert title target')
one('R45 PASS_VM_PENDING_PHYSICAL','R46 PASS_VM_PENDING_PHYSICAL','PASS target')
alln('R45-FAILURE.txt','R46-FAILURE.txt',2,'failure target')
one('r45 exact kernel identity mismatch','r46 exact kernel identity mismatch','identity label')

old_hist="'physical_r44':'PHYSICAL_USB_NO_EVENT_DMA_TOUCHPAD_FALSE_RIGHT_INPUT_LOCK','physical_r44_telemetry':'R44_A1_T0_D0_V0_M0_Q0_B0','physical_r45':'PENDING'"
new_hist="'physical_r44':'PHYSICAL_USB_NO_EVENT_DMA_TOUCHPAD_FALSE_RIGHT_INPUT_LOCK','physical_r44_telemetry':'R44_A1_T0_D0_V0_M0_Q0_B0','physical_r45':'PHYSICAL_TOUCHPAD_NORMAL_USB_ARMED_NO_DEQUEUE_EVENT_DMA_CYCLE_MATCH','physical_r45_telemetry':'R45_A1_D0_C1_H1_V0_M0_B0','physical_r46':'PENDING'"
one(old_hist,new_hist,'physical r45 evidence / r46 pending')

old_row="    req('volatile_read64(xhci+808)' in s and 'volatile_read64(xhci+2824)' in s and 'volatile_read64(xhci+3344)' in s and 'volatile_read64(xhci+3352)' in s and 'volatile_read64(xhci+3320)' in s and 'volatile_read64(xhci+3328)' in s and 'volatile_read64(xhci+3280)' in s,'r45 physical DCS row missing')"
new_row="    req('volatile_read64(xhci+3360)' in s and 'volatile_read64(xhci+3368)' in s and 'volatile_read64(xhci+3376)' in s and 'volatile_read64(xhci+3384)' in s and 'volatile_read64(xhci+3392)' in s and 'volatile_read64(xhci+3400)' in s and 'volatile_read64(xhci+3408)' in s,'r46 physical endpoint-context row missing')"
one(old_row,new_row,'r46 physical row gate')

old_passive="    req('volatile_write32' not in f45 and 'v136_xhci_command_endpoint' not in f45 and 'xhci_control' not in f45 and 'pit_wait' not in f45,'r45 DCS snapshot became active rather than passive')"
new_passive=old_passive+"""
    req('volatile_read32(ep)' in f45 and 'volatile_read32(ep+4)' in f45 and 'volatile_read32(ep+16)' in f45,'r46 output endpoint-context reads missing')
    req('volatile_write64(xhci_state+3360,ep_state)' in f45 and 'volatile_write64(xhci_state+3368,ep_interval)' in f45 and 'volatile_write64(xhci_state+3376,ep_type)' in f45 and 'volatile_write64(xhci_state+3384,ep_burst)' in f45 and 'volatile_write64(xhci_state+3392,ep_mps)' in f45 and 'volatile_write64(xhci_state+3400,ep_avg)' in f45 and 'volatile_write64(xhci_state+3408,ep_esit)' in f45,'r46 accepted periodic endpoint fields missing')
    req('if typ==1 || typ==2 {' in buttons and 'return ps2_elan4_motion_v112(input_state,a,b);' in s,'r46 regressed physically recovered touchpad contract')
"""
one(old_passive,new_passive,'r46 passive endpoint-context gates')

ns={'__name__':'__main__','__file__':str(base)}
try:
    exec(compile(src,str(base),'exec'),ns,ns)
except BaseException:
    out=Path('evidence'); out.mkdir(parents=True,exist_ok=True)
    (out/'R46-FAILURE.txt').write_text(traceback.format_exc())
    raise
