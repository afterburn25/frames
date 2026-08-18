#!/usr/bin/env python3
from pathlib import Path
import traceback
here=Path(__file__).parent
base=here/'r59b_cert_driver.py'
src=base.read_text()

def one(old,new,label):
    global src
    n=src.count(old)
    if n!=1: raise SystemExit(f'r59c cert anchor {label} count {n}')
    src=src.replace(old,new,1)
def alln(old,new,count,label):
    global src
    n=src.count(old)
    if n!=count: raise SystemExit(f'r59c cert anchor {label} count {n}, expected {count}')
    src=src.replace(old,new)

one("'patch_v108_r59b_ehci_periodic_frame_reuse.py'","'patch_v108_r59c_ehci_periodic_reserved_fallback.py'",'patch target')
one('kernel-r59b.nx','kernel-r59c.nx','kernel evidence target')
one('1a5d41c5693b4e01c16eb724b4894748bb5682cbe4c61b05b7934dc1f2c8d033','e1218ffe017749b252b6e939534f9d191bccbc68433f6a478f8f19c1506cb66c','exact r59c identity target')
one("'Frames-0.9.98-v108-r59b-EHCI-Periodic-Frame-Reuse-Rufus-UEFI.iso'","'Frames-0.9.98-v108-r59c-EHCI-Reserved-Page-Fallback-Rufus-UEFI.iso'",'ISO target')
one("'R59B-SHA.txt'","'R59C-SHA.txt'",'SHA evidence target')
one("'R25K-R59B.patch'","'R25K-R59C.patch'",'patch evidence target')
one("'FRAMES_V108_R59B'","'FRAMES_V108_R59C'",'ISO label target')
one('R59B-AGGREGATE.json','R59C-AGGREGATE.json','aggregate target')
one("'frames-0.9.98-v108-r59b-ehci-periodic-frame-reuse'","'frames-0.9.98-v108-r59c-ehci-reserved-page-fallback'",'profile target')
one("'Frames 0.9.98 v108 r59b — EHCI Periodic Frame Reuse Repair'","'Frames 0.9.98 v108 r59c — EHCI Reserved Page Fallback Repair'",'cert title target')
one('R59B PASS_VM_PENDING_PHYSICAL','R59C PASS_VM_PENDING_PHYSICAL','PASS target')
alln('R59B-FAILURE.txt','R59C-FAILURE.txt',2,'failure target')
one('r59b exact kernel identity mismatch','r59c exact kernel identity mismatch','identity label')
one("'physical_r58':'PHYSICAL_COMPOSITE_HID_MOUSE_ENDPOINT_DISCOVERED','physical_r58_telemetry':'R58_S1_P2_K129_M130_I0_L8_C2','physical_r59':'PHYSICAL_PERIODIC_FRAME_ALLOC_EXHAUSTED','physical_r59_telemetry':'R59_S14_N0_C0_B0_X0_Y0_W0','physical_r59b':'PENDING'",
    "'physical_r58':'PHYSICAL_COMPOSITE_HID_MOUSE_ENDPOINT_DISCOVERED','physical_r58_telemetry':'R58_S1_P2_K129_M130_I0_L8_C2','physical_r59':'PHYSICAL_PERIODIC_FRAME_ALLOC_EXHAUSTED','physical_r59_telemetry':'R59_S14_N0_C0_B0_X0_Y0_W0','physical_r59b':'PHYSICAL_PERIODIC_RESERVED_PAGE3_UNAVAILABLE','physical_r59b_telemetry':'R5B_S14_N0_C0_B0_X0_Y0_W0','physical_r59c':'PENDING'",
    'physical r59b result + r59c pending')
anchor="    req('R5B' not in s,'r59b textual label unexpectedly embedded as raw string')"
extra=anchor+"""
    r59cfn=s[s.index('fn v159_ehci_mouse_periodic_arm'):s.index('fn v135_hid_control_fallback_prepare')]
    req('volatile_read64(phys_state+48)' in r59cfn and 'volatile_read64(phys_state+40)' in r59cfn and 'volatile_read64(phys_state+32)' in r59cfn,'r59c three reserved-page probes missing')
    req('rslot=48' in r59cfn and 'rslot=40' in r59cfn and 'rslot=32' in r59cfn,'r59c reserved-page priority ladder missing')
    req('dma_record(ledger,frame,4)' in r59cfn,'r59c DMA-ledger ownership registration missing')
    req('volatile_write64(xhci_state+4056,26)' in r59cfn and 'volatile_write64(xhci_state+4056,27)' in r59cfn,'r59c ledger failure diagnostics missing')
    req('volatile_write64(phys_state+48,0)' in r59cfn and 'volatile_write64(phys_state+40,0)' in r59cfn and 'volatile_write64(phys_state+32,0)' in r59cfn,'r59c reserved ownership transfer missing')
    req('alloc_dma_page(phys_state,4)' in r59cfn,'r59c fresh-allocation fallback missing')
    req('volatile_write32(op+20,flo)' in r59cfn and 'cmd=set_flag(cmd,16)' in r59cfn,'r59c periodic schedule path lost')
    low59c=r59cfn.lower(); req(all(x not in low59c for x in ['write(10)','nvme_submit_write','ahci_write','fat_write','block_write','input_push(']),'r59c exceeds raw diagnostic/safety scope')
    req('R5C' not in s,'r59c textual label unexpectedly embedded as raw string')
"""
one(anchor,extra,'r59c reserved fallback model gates')

ns={'__name__':'__main__','__file__':str(base)}
try:
    exec(compile(src,str(base),'exec'),ns,ns)
except BaseException:
    out=Path('evidence'); out.mkdir(parents=True,exist_ok=True)
    (out/'R59C-FAILURE.txt').write_text(traceback.format_exc())
    raise
