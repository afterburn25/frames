#!/usr/bin/env python3
from pathlib import Path
import traceback
here=Path(__file__).parent
base=here/'r59e_cert_driver.py'
src=base.read_text()

def one(old,new,label):
    global src
    n=src.count(old)
    if n!=1: raise SystemExit(f'r59f cert anchor {label} count {n}')
    src=src.replace(old,new,1)
def alln(old,new,count,label):
    global src
    n=src.count(old)
    if n!=count: raise SystemExit(f'r59f cert anchor {label} count {n}, expected {count}')
    src=src.replace(old,new)

one("'patch_v108_r59e_ehci_periodic_execution_forensics.py'","'patch_v108_r59f_hid_report_protocol_periodic.py'",'patch target')
one('kernel-r59e.nx','kernel-r59f.nx','kernel evidence target')
one('a582d1f5f8464da49f06b67c9ced5fbf755bbde3106b9cae97991f1ff6f406fa','51103efecc88695f2f75cb786d273d7379c5628424e9f1f391853bdb5e81198e','exact r59f identity target')
one("'Frames-0.9.98-v108-r59e-EHCI-Periodic-Execution-Forensics-Rufus-UEFI.iso'","'Frames-0.9.98-v108-r59f-HID-Report-Protocol-Periodic-Rufus-UEFI.iso'",'ISO target')
one("'R59E-SHA.txt'","'R59F-SHA.txt'",'SHA evidence target')
one("'R25K-R59E.patch'","'R25K-R59F.patch'",'patch evidence target')
one("'FRAMES_V108_R59E'","'FRAMES_V108_R59F'",'ISO label target')
one('R59E-AGGREGATE.json','R59F-AGGREGATE.json','aggregate target')
one("'frames-0.9.98-v108-r59e-ehci-periodic-execution-forensics'","'frames-0.9.98-v108-r59f-hid-report-protocol-periodic'",'profile target')
one("'Frames 0.9.98 v108 r59e — EHCI Periodic Execution Forensics'","'Frames 0.9.98 v108 r59f — HID Report Protocol Periodic Repair'",'cert title target')
one('R59E PASS_VM_PENDING_PHYSICAL','R59F PASS_VM_PENDING_PHYSICAL','PASS target')
alln('R59E-FAILURE.txt','R59F-FAILURE.txt',2,'failure target')
one('r59e exact kernel identity mismatch','r59f exact kernel identity mismatch','identity label')
one("'physical_r59d':'PHYSICAL_PERIODIC_SCHEDULE_ARMED_QTD_NO_COMPLETION','physical_r59d_telemetry':'R5D_S1_N0_C0_B0_X0_Y0_W0','physical_r59e':'PENDING'",
    "'physical_r59d':'PHYSICAL_PERIODIC_SCHEDULE_ARMED_QTD_NO_COMPLETION','physical_r59d_telemetry':'R5D_S1_N0_C0_B0_X0_Y0_W0','physical_r59e':'PHYSICAL_QH_FETCHED_QTD_ACTIVE_NO_ERROR','physical_r59e_telemetry':'R5E_S1_N0_F12324_Q1_A1_E0_P1','physical_r59f':'PENDING'",
    'physical r59e result + r59f pending')
anchor="    req('R5E' not in s,'r59e textual label unexpectedly embedded as raw string')"
extra=anchor+"""
    r59ffn=s[s.index('fn v159_ehci_mouse_periodic_arm'):s.index('fn v135_hid_control_fallback_prepare')]
    req('33+(11*256)+65536+(mif*4294967296)' in r59ffn,'r59f HID report-protocol SET_PROTOCOL missing')
    req('161+(3*256)+(mif*4294967296)+(1*281474976710656)' in r59ffn,'r59f GET_PROTOCOL verification request missing')
    req('volatile_read8(dma+576)!=1' in r59ffn,'r59f report-protocol verification gate missing')
    req('volatile_read32(qh+12)' in r59ffn and 'cur==(qtd%4294967296)' in r59ffn,'r59f inherited QH current-qTD proof missing')
    req('volatile_read32(op+12)%16384' in r59ffn and 'volatile_read32(op+4)/16384' in r59ffn,'r59f inherited EHCI periodic forensics missing')
    req('volatile_write64(xhci_state+4064,volatile_read64(xhci_state+4064)+1)' in r59ffn,'r59f completion counter lost')
    low59f=r59ffn.lower(); req(all(x not in low59f for x in ['write(10)','nvme_submit_write','ahci_write','fat_write','block_write','input_push(']),'r59f exceeds diagnostic/read-only scope')
    req('R5F' not in s,'r59f textual label unexpectedly embedded as raw string')
"""
one(anchor,extra,'r59f report protocol model gates')

ns={'__name__':'__main__','__file__':str(base)}
try:
    exec(compile(src,str(base),'exec'),ns,ns)
except BaseException:
    out=Path('evidence'); out.mkdir(parents=True,exist_ok=True)
    (out/'R59F-FAILURE.txt').write_text(traceback.format_exc())
    raise
