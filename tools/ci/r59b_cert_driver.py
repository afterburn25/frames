#!/usr/bin/env python3
from pathlib import Path
import traceback
here=Path(__file__).parent
base=here/'r59_cert_driver.py'
src=base.read_text()

def one(old,new,label):
    global src
    n=src.count(old)
    if n!=1: raise SystemExit(f'r59b cert anchor {label} count {n}')
    src=src.replace(old,new,1)
def alln(old,new,count,label):
    global src
    n=src.count(old)
    if n!=count: raise SystemExit(f'r59b cert anchor {label} count {n}, expected {count}')
    src=src.replace(old,new)

one("'patch_v108_r59_ehci_mouse_periodic_report_probe.py'","'patch_v108_r59b_ehci_periodic_frame_reuse.py'",'patch target')
one('kernel-r59.nx','kernel-r59b.nx','kernel evidence target')
one('38544595b9ce8c1d7775319247b9d544adadf16b2526d6ca9dbfb41fa0f7a9b7','1a5d41c5693b4e01c16eb724b4894748bb5682cbe4c61b05b7934dc1f2c8d033','exact r59b identity target')
one("'Frames-0.9.98-v108-r59-EHCI-Mouse-Periodic-Report-Probe-Rufus-UEFI.iso'","'Frames-0.9.98-v108-r59b-EHCI-Periodic-Frame-Reuse-Rufus-UEFI.iso'",'ISO target')
one("'R59-SHA.txt'","'R59B-SHA.txt'",'SHA evidence target')
one("'R25K-R59.patch'","'R25K-R59B.patch'",'patch evidence target')
one("'FRAMES_V108_R59'","'FRAMES_V108_R59B'",'ISO label target')
one('R59-AGGREGATE.json','R59B-AGGREGATE.json','aggregate target')
one("'frames-0.9.98-v108-r59-ehci-mouse-periodic-report-probe'","'frames-0.9.98-v108-r59b-ehci-periodic-frame-reuse'",'profile target')
one("'Frames 0.9.98 v108 r59 — EHCI Mouse Periodic Report Probe'","'Frames 0.9.98 v108 r59b — EHCI Periodic Frame Reuse Repair'",'cert title target')
one('R59 PASS_VM_PENDING_PHYSICAL','R59B PASS_VM_PENDING_PHYSICAL','PASS target')
alln('R59-FAILURE.txt','R59B-FAILURE.txt',2,'failure target')
one('r59 exact kernel identity mismatch','r59b exact kernel identity mismatch','identity label')
one("'physical_r58':'PHYSICAL_COMPOSITE_HID_MOUSE_ENDPOINT_DISCOVERED','physical_r58_telemetry':'R58_S1_P2_K129_M130_I0_L8_C2','physical_r59':'PENDING'",
    "'physical_r58':'PHYSICAL_COMPOSITE_HID_MOUSE_ENDPOINT_DISCOVERED','physical_r58_telemetry':'R58_S1_P2_K129_M130_I0_L8_C2','physical_r59':'PHYSICAL_PERIODIC_FRAME_ALLOC_EXHAUSTED','physical_r59_telemetry':'R59_S14_N0_C0_B0_X0_Y0_W0','physical_r59b':'PENDING'",
    'physical r59 result + r59b pending')
anchor="    req('R59' not in s,'r59 textual label unexpectedly embedded as raw string')"
extra=anchor+"""
    r59bfn=s[s.index('fn v159_ehci_mouse_periodic_arm'):s.index('fn v135_hid_control_fallback_prepare')]
    req('volatile_read64(phys_state+48)' in r59bfn,'r59b reserved physical page lookup missing')
    req('dma_record(ledger,frame,4)' in r59bfn,'r59b reserved page DMA-ledger registration missing')
    req('volatile_write64(phys_state+48,0)' in r59bfn,'r59b reserved-page ownership transfer missing')
    req('alloc_dma_page(phys_state,4)' in r59bfn,'r59b safe fresh-allocation fallback missing')
    req('volatile_write32(op+20,flo)' in r59bfn and 'cmd=set_flag(cmd,16)' in r59bfn,'r59b periodic schedule path lost')
    low59b=r59bfn.lower(); req(all(x not in low59b for x in ['write(10)','nvme_submit_write','ahci_write','fat_write','block_write','input_push(']),'r59b exceeds raw diagnostic/safety scope')
    req('R5B' not in s,'r59b textual label unexpectedly embedded as raw string')
"""
one(anchor,extra,'r59b frame reuse model gates')

ns={'__name__':'__main__','__file__':str(base)}
try:
    exec(compile(src,str(base),'exec'),ns,ns)
except BaseException:
    out=Path('evidence'); out.mkdir(parents=True,exist_ok=True)
    (out/'R59B-FAILURE.txt').write_text(traceback.format_exc())
    raise
