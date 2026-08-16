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
old_sig='fn xhci_address_hub_child_v113(xhci_state:u64,phys_state:u64,parent_slot:u64,parent_root_port:u64,parent_speed:u64,child_port:u64,child_speed:u64) -> u64 {'
new_sig='''fn xhci_address_hub_child_v113(xhci_state:u64,phys_state:u64,parent_info:u64,child_info:u64) -> u64 {\n    let parent_slot=parent_info%256; let parent_root_port=(parent_info/256)%256; let parent_speed=(parent_info/65536)%256;\n    let child_port=child_info%256; let child_speed=(child_info/256)%256;'''
if s.count(old_sig)!=1: raise SystemExit('child address signature anchor')
s=s.replace(old_sig,new_sig,1)
old_call='xhci_address_hub_child_v113(xhci_state,phys_state,parent_slot,parent_root,parent_speed,p,speed)'
new_call='xhci_address_hub_child_v113(xhci_state,phys_state,parent_slot+(parent_root*256)+(parent_speed*65536),p+(speed*256))'
if s.count(old_call)!=1: raise SystemExit('child address call anchor')
s=s.replace(old_call,new_call,1)
p.write_text(s)
out=hashlib.sha256(p.read_bytes()).hexdigest()
print(out)
