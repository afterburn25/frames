#!/usr/bin/env python3
from pathlib import Path
import struct, sys

p=Path(sys.argv[1])
b=p.read_bytes()
if len(b)<512:
    raise SystemExit('PTRLOG.BIN too small')
magic,version,count,dropped,recsize,pages,ustg,eflr,ecc,upor,uvid,core,p2pk,usbr,auxn,tsc=struct.unpack_from('<16Q',b,0)
if magic!=15821226413937222 or version!=58 or recsize!=32:
    raise SystemExit(f'bad r58 header magic/version/record-size: {magic:x} {version} {recsize}')
print(f'Frames r58 Physical Input Flight Recorder')
print(f'records={count} dropped={dropped} pages={pages}')
print(f'usb_stage={ustg} usb_fail_stage={eflr} usb_completion={ecc} port={upor} vid=0x{uvid:04x}')
print(f'core_events={core} ps2_packets={p2pk} usb_reports={usbr} aux_bytes={auxn} save_tsc={tsc}')
print('')
print('index tsc kind a b')
kind_names={1:'PS2_RAW',2:'PS2_PKT',3:'GP_REL',4:'USB_REPORT',5:'SAVE_BEGIN'}
max_records=min(count,(len(b)-512)//32)
for i in range(max_records):
    off=512+i*32
    t,k,a,v=struct.unpack_from('<4Q',b,off)
    print(f'{i:05d} {t:016x} {kind_names.get(k,str(k)):10s} {a:016x} {v:016x}')
