#!/usr/bin/env python3
# r60 certification trigger after workflow registration
from pathlib import Path
import traceback
here=Path(__file__).parent
base=here/'r59h_cert_driver.py'
src=base.read_text()

def one(old,new,label):
    global src
    n=src.count(old)
    if n!=1: raise SystemExit(f'r60 cert anchor {label} count {n}')
    src=src.replace(old,new,1)
def alln(old,new,count,label):
    global src
    n=src.count(old)
    if n!=count: raise SystemExit(f'r60 cert anchor {label} count {n}, expected {count}')
    src=src.replace(old,new)

one("'patch_v108_r59h_linux_split_schedule_repair.py'","'patch_v108_r60_reference_ehci_boot_mouse.py'",'patch target')
one('kernel-r59h.nx','kernel-r60.nx','kernel evidence target')
one('ee129f22dca19ba7d1d7a1cc41a7b90bfcba0dc472ad7493c38ca2a1537c094e','dc1d8d0590965f6d499eba0fe2d010287d6052d2c7ceab73dff41120fadcc04d','exact r60 identity target')
one("'Frames-0.9.98-v108-r59h-Linux-Split-Schedule-Repair-Rufus-UEFI.iso'","'Frames-0.9.98-v108-r60-Reference-EHCI-Boot-Mouse-Rufus-UEFI.iso'",'ISO target')
one("'R59H-SHA.txt'","'R60-SHA.txt'",'SHA evidence target')
one("'R25K-R59H.patch'","'R25K-R60.patch'",'patch evidence target')
one("'FRAMES_V108_R59H'","'FRAMES_V108_R60'",'ISO label target')
one('R59H-AGGREGATE.json','R60-AGGREGATE.json','aggregate target')
one("'frames-0.9.98-v108-r59h-linux-split-schedule-repair'","'frames-0.9.98-v108-r60-reference-ehci-boot-mouse'",'profile target')
one("'Frames 0.9.98 v108 r59h — Linux-Derived EHCI Split Schedule Repair'","'Frames 0.9.98 v108 r60 — Reference-Driven EHCI Boot Mouse Integration'",'cert title target')
one('R59H PASS_VM_PENDING_PHYSICAL','R60 PASS_VM_PENDING_PHYSICAL','PASS target')
alln('R59H-FAILURE.txt','R60-FAILURE.txt',2,'failure target')
one('r59h exact kernel identity mismatch','r60 exact kernel identity mismatch','identity label')
one("'physical_r59h':'PENDING'","'physical_r59h':'PENDING','physical_r60':'PENDING'",'r60 physical pending')

oldgeom="    req('let info2=1090586113' in r59gfn and 'let info2=1090591745' not in r59gfn,'r59h Linux-derived C-mask 0x06 repair missing')"
newgeom="    req('let info2=1090591745' in r59gfn and 'let info2=1090586113' not in r59gfn,'r60 default TT new-scheduler C-mask 0x1c missing')"
one(oldgeom,newgeom,'default Linux split geometry')

# r59b through r59g were intentionally raw-diagnostic builds and therefore
# banned input_push() inside the EHCI slice. r60 is the first bounded input
# integration build, so relax only that inherited ban while retaining every
# storage-write prohibition and adding explicit r60 pointer-delivery gates.
relaxed=0
for name in ('r59b_cert_driver.py','r59c_cert_driver.py','r59d_cert_driver.py','r59_cert_driver.py','r59e_cert_driver.py','r59f_cert_driver.py','r59g_cert_driver.py'):
    p=here/name
    t=p.read_text()
    n=t.count(",'input_push('")
    if n:
        t=t.replace(",'input_push('","")
        p.write_text(t)
        relaxed+=n
if relaxed<7: raise SystemExit(f'r60 inherited diagnostic input-delivery gates relaxed {relaxed}, expected >=7')

p=here/'r59f_cert_driver.py'; t=p.read_text()
old="    req('33+(11*256)+65536+(mif*4294967296)' in r59ffn,'r59f HID report-protocol SET_PROTOCOL missing')"
new="    req(('33+(11*256)+65536+(mif*4294967296)' in r59ffn) or ('33+(11*256)+(mif*4294967296)' in r59ffn),'r59f/r60 HID protocol selection missing')"
if t.count(old)==1: t=t.replace(old,new,1)
elif t.count(new)!=1: raise SystemExit('r60 inherited SET_PROTOCOL gate anchor missing')
old="    req('volatile_read8(dma+576)!=1' in r59ffn,'r59f report-protocol verification gate missing')"
new="    req(('volatile_read8(dma+576)!=1' in r59ffn) or ('volatile_read8(dma+576)!=0' in r59ffn),'r59f/r60 GET_PROTOCOL verification gate missing')"
if t.count(old)==1: t=t.replace(old,new,1)
elif t.count(new)!=1: raise SystemExit('r60 inherited GET_PROTOCOL gate anchor missing')
p.write_text(t)

p=here/'r59_cert_driver.py'; t=p.read_text()
old="    req('token=527744' in r59fn and 'volatile_write32(qtd+8,527744)' in r59fn,'r59 8-byte interrupt-IN qTD arm/rearm missing')"
new="    req((('token=527744' in r59fn and 'volatile_write32(qtd+8,527744)' in r59fn) or ('token=560512' in r59fn and 'volatile_write32(qtd+8,560512)' in r59fn)),'r59/r60 8-byte interrupt-IN qTD arm/rearm missing')"
if t.count(old)==1: t=t.replace(old,new,1)
elif t.count(new)!=1: raise SystemExit('r60 inherited qTD token gate anchor missing')
old="    req('r59_redraw=v159_ehci_mouse_periodic_tick(xhci)' in s and 'var telemetry_redraw:u64=r59_redraw' in s,'r59 live desktop polling/redraw hook missing')"
new="    req((('r59_redraw=v159_ehci_mouse_periodic_tick(xhci)' in s) or ('r59_redraw=v159_ehci_mouse_periodic_tick(xhci,input_state)' in s)) and 'var telemetry_redraw:u64=r59_redraw' in s,'r59/r60 live desktop polling/redraw hook missing')"
if t.count(old)==1: t=t.replace(old,new,1)
elif t.count(new)!=1: raise SystemExit('r60 inherited live polling gate anchor missing')
p.write_text(t)

# r59e's forensic contract was written for the earlier diagnostic-only layout.
# r60 deliberately replaces FRINDEX/packed-qTD display storage with the live
# QH overlay token plus completed report telemetry. Widen only those inherited
# witnesses; keep the QH current-qTD, PSS, completion, DMA and safety checks.
p=here/'r59e_cert_driver.py'; t=p.read_text()
adapters=[
("    req('volatile_read32(op+12)%16384' in r59efn,'r59e FRINDEX observation missing')",
 "    req(('volatile_read32(op+12)%16384' in r59efn) or ('volatile_read32(qh+24)' in r59efn),'r59e/r60 live EHCI execution observation missing')"),
("    req('volatile_write64(xhci_state+4072,qmatch)' in r59efn,'r59e QH/qTD match telemetry missing')",
 "    req(('volatile_write64(xhci_state+4072,qmatch)' in r59efn) or ('cur==(qtd%4294967296)' in r59efn and 'volatile_write64(xhci_state+4072,volatile_read64(xhci_state+4072)+1)' in r59efn),'r59e/r60 QH/qTD execution telemetry missing')"),
("    req('volatile_write64(xhci_state+4080,tok)' in r59efn,'r59e qTD token telemetry missing')",
 "    req(('volatile_write64(xhci_state+4080,tok)' in r59efn) or ('volatile_write64(xhci_state+4080,raw)' in r59efn and 'volatile_write64(xhci_state+4088,otok)' in r59efn),'r59e/r60 transfer-token/report telemetry missing')"),
("    req('volatile_write64(xhci_state+4088,fri+(pss*16384))' in r59efn,'r59e FRINDEX/PSS packed telemetry missing')",
 "    req(('volatile_write64(xhci_state+4088,fri+(pss*16384))' in r59efn) or ('volatile_write64(xhci_state+4088,actual)' in r59efn and 'volatile_read32(op+4)/16384' in r59efn),'r59e/r60 execution-state telemetry missing')")]
for old,new in adapters:
    if t.count(old)==1: t=t.replace(old,new,1)
    elif t.count(new)!=1: raise SystemExit('r60 inherited r59e telemetry gate anchor missing')
p.write_text(t)

ns={'__name__':'__main__','__file__':str(base)}
try:
    exec(compile(src,str(base),'exec'),ns,ns)
    final_src=Path('evidence/kernel-r60.nx').read_text()
    r60fn=final_src[final_src.index('fn v159_ehci_mouse_periodic_arm'):final_src.index('fn v135_hid_control_fallback_prepare')]
    checks=[
        ('let info2=1090591745' in r60fn and 'let info2=1090586113' not in r60fn,'r60 TT new-scheduler geometry missing'),
        ('let token=560512' in r60fn and 'volatile_write32(qtd+8,560512)' in r60fn,'r60 IOC interrupt-IN qTD missing'),
        ('33+(11*256)+(mif*4294967296)' in r60fn and 'volatile_read8(dma+576)!=0' in r60fn,'r60 HID boot protocol selection/verification missing'),
        ('volatile_read32(qh+24)' in r60fn,'r60 QH overlay-token observation missing'),
        ('v159_ehci_mouse_periodic_tick(xhci_state:u64,input_state:u64)' in r60fn,'r60 input-aware periodic tick missing'),
        ('input_push(input_state,4,0,buttons)' in r60fn and 'input_push(input_state,5,0,dx)' in r60fn and 'input_push(input_state,6,0,dy)' in r60fn,'r60 Generic Pointer delivery missing'),
        (all(x not in r60fn.lower() for x in ['write(10)','nvme_submit_write','ahci_write','fat_write','block_write']),'r60 exceeds read-only input-integration scope'),
    ]
    for ok,msg in checks:
        if not ok: raise SystemExit(msg)
except BaseException:
    out=Path('evidence'); out.mkdir(parents=True,exist_ok=True)
    (out/'R60-FAILURE.txt').write_text(traceback.format_exc())
    raise
