#!/usr/bin/env python3
from pathlib import Path
import traceback
here=Path(__file__).parent
base=here/'r39_cert_driver.py'
src=base.read_text()

def one(old,new,label):
    global src
    n=src.count(old)
    if n!=1: raise SystemExit(f'r39b cert anchor {label} count {n}')
    src=src.replace(old,new,1)

def alln(old,new,count,label):
    global src
    n=src.count(old)
    if n!=count: raise SystemExit(f'r39b cert anchor {label} count {n}, expected {count}')
    src=src.replace(old,new)

one("'patch_v108_r39_g750jm_hid_idle_disabled_wifi_ro.py'","'patch_v108_r39b_g750jm_hid_idle_1s_wifi_ro.py'",'patch target')
one('kernel-r39.nx','kernel-r39b.nx','kernel evidence target')
alln('ba873c5bcfb810faa6210f440832ad359c5e91c012541fc2431c2bd1acb3a8d1','7ca4e51896453e0bcaa131d7f4497e64e95556cb96941c599fa4151eb71bbea5',2,'exact kernel identity')
one("'Frames-0.9.98-v108-r39-G750JM-HID-Idle-Disabled-Recovery-WiFi-Discovery-Rufus-UEFI.iso'","'Frames-0.9.98-v108-r39b-G750JM-HID-Idle-1s-WiFi-Discovery-Rufus-UEFI.iso'",'ISO target')
one("'R39-SHA.txt'","'R39B-SHA.txt'",'SHA evidence target')
one("'R25K-R39.patch'","'R25K-R39B.patch'",'patch evidence target')
one("'FRAMES_V108_R39'","'FRAMES_V108_R39B'",'ISO label target')
one('R39-AGGREGATE.json','R39B-AGGREGATE.json','aggregate target')
one("'frames-0.9.98-v108-r39-g750jm-hid-idle-disabled-recovery-wifi-discovery'","'frames-0.9.98-v108-r39b-g750jm-hid-idle-1s-wifi-discovery'",'profile target')
one("'Frames 0.9.98 v108 r39 — G750JM HID Idle + Disabled Recovery + WiFi Discovery'","'Frames 0.9.98 v108 r39b — G750JM HID Idle 1s + Disabled Recovery + WiFi Discovery'",'cert title target')
one('R39 PASS_VM_PENDING_PHYSICAL','R39B PASS_VM_PENDING_PHYSICAL','PASS target')
alln('R39-FAILURE.txt','R39B-FAILURE.txt',2,'failure target')
one("'physical_r39':'PENDING'","'physical_r39':'REJECTED_CI_LOG_STARVATION_32MS_SET_IDLE','physical_r39b':'PENDING'",'physical/CI history target')
one("let idle_setup=2593+(2048*65536)+(interface_num*4294967296)","let idle_setup=2593+(64000*65536)+(interface_num*4294967296)",'one-second SET_IDLE model gate')

ns={'__name__':'__main__','__file__':str(base)}
try:
    exec(compile(src,str(base),'exec'),ns,ns)
except BaseException:
    out=Path('evidence'); out.mkdir(parents=True,exist_ok=True)
    (out/'R39B-FAILURE.txt').write_text(traceback.format_exc())
    raise
