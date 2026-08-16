from pathlib import Path
import hashlib,sys
p=Path(sys.argv[1]); raw=p.read_bytes(); expected='8ebec9c4ed641be22eccf3294a9f478093189d4ad36c454605b1b273dd662cd6'
actual=hashlib.sha256(raw).hexdigest()
if actual!=expected: raise SystemExit(f'unexpected hub-r2 hash {actual}')
s=raw.decode()
old='''fn usb_setup_value_v113(reqtype:u64,request:u64,value:u64,index:u64,length:u64) -> u64 {\n    return (reqtype%256)+((request%256)*256)+((value%65536)*65536)+((index%65536)*4294967296)+((length%65536)*281474976710656);\n}'''
new='''fn usb_setup_value_v113(reqtype:u64,request:u64,value:u64,index_length:u64) -> u64 {\n    let index=index_length/65536; let length=index_length%65536;\n    return (reqtype%256)+((request%256)*256)+((value%65536)*65536)+((index%65536)*4294967296)+((length%65536)*281474976710656);\n}'''
if s.count(old)!=1: raise SystemExit('setup helper anchor')
s=s.replace(old,new,1)
repls={
'usb_setup_value_v113(128,6,512,0,9)':'usb_setup_value_v113(128,6,512,9)',
'usb_setup_value_v113(0,9,config,0,0)':'usb_setup_value_v113(0,9,config,0)',
'usb_setup_value_v113(160,6,10496,0,9)':'usb_setup_value_v113(160,6,10496,9)',
'usb_setup_value_v113(163,0,0,port,4)':'usb_setup_value_v113(163,0,0,(port*65536)+4)',
'usb_setup_value_v113(35,3,feature,port,0)':'usb_setup_value_v113(35,3,feature,port*65536)',
}
for a,b in repls.items():
    if s.count(a)!=1: raise SystemExit('call anchor '+a)
    s=s.replace(a,b,1)
p.write_text(s)
out=hashlib.sha256(p.read_bytes()).hexdigest()
print(out)
