from pathlib import Path
import hashlib,sys,re
p=Path(sys.argv[1]); raw=p.read_bytes()
expected='8ebec9c4ed641be22eccf3294a9f478093189d4ad36c454605b1b273dd662cd6'
actual=hashlib.sha256(raw).hexdigest()
if actual!=expected: raise SystemExit(f'unexpected hub-r2 input {actual}')
s=raw.decode()
old='''fn usb_setup_value_v113(reqtype:u64,request:u64,value:u64,index:u64,length:u64) -> u64 {\n    return (reqtype%256)+((request%256)*256)+((value%65536)*65536)+((index%65536)*4294967296)+((length%65536)*281474976710656);\n}'''
new='''fn usb_setup_value_v113(reqtype:u64,request:u64,value:u64,index:u64) -> u64 {\n    return (reqtype%256)+((request%256)*256)+((value%65536)*65536)+((index%65536)*4294967296);\n}\nfn usb_setup_length_v113(setup:u64,length:u64) -> u64 {\n    return setup+((length%65536)*281474976710656);\n}'''
if s.count(old)!=1: raise SystemExit('setup helper anchor mismatch')
s=s.replace(old,new,1)
repls={
'usb_setup_value_v113(128,6,512,0,9)':'usb_setup_length_v113(usb_setup_value_v113(128,6,512,0),9)',
'usb_setup_value_v113(0,9,config,0,0)':'usb_setup_length_v113(usb_setup_value_v113(0,9,config,0),0)',
'usb_setup_value_v113(160,6,10496,0,9)':'usb_setup_length_v113(usb_setup_value_v113(160,6,10496,0),9)',
'usb_setup_value_v113(163,0,0,port,4)':'usb_setup_length_v113(usb_setup_value_v113(163,0,0,port),4)',
'usb_setup_value_v113(35,3,feature,port,0)':'usb_setup_length_v113(usb_setup_value_v113(35,3,feature,port),0)',
}
for a,b in repls.items():
    if a not in s: raise SystemExit(f'missing setup call {a}')
    s=s.replace(a,b)
old_sig='fn xhci_address_hub_child_v113(xhci_state:u64,phys_state:u64,parent_slot:u64,parent_root_port:u64,parent_speed:u64,child_port:u64,child_speed:u64) -> u64 {\n    if child_port==0 || child_port>15 || child_speed==0 || child_speed>3 { return 0; }'
new_sig='fn xhci_address_hub_child_v113(xhci_state:u64,phys_state:u64,child_port:u64,child_speed:u64) -> u64 {\n    if child_port==0 || child_port>15 || child_speed==0 || child_speed>3 { return 0; }\n    let parent_slot=volatile_read64(xhci_state+136); let parent_root_port=volatile_read64(xhci_state+112); let parent_speed=volatile_read64(xhci_state+184); if parent_slot==0 || parent_root_port==0 { return 0; }'
if s.count(old_sig)!=1: raise SystemExit('child signature anchor mismatch')
s=s.replace(old_sig,new_sig,1)
old_call='xhci_address_hub_child_v113(xhci_state,phys_state,parent_slot,parent_root,parent_speed,p,speed)'
if s.count(old_call)!=1: raise SystemExit('child call anchor mismatch')
s=s.replace(old_call,'xhci_address_hub_child_v113(xhci_state,phys_state,p,speed)',1)
# Fail closed if either repaired helper still exceeds the Nexus x64 four-parameter ABI.
for name in ('usb_setup_value_v113','xhci_address_hub_child_v113'):
    m=re.search(r'fn '+name+r'\(([^)]*)\)',s)
    if not m: raise SystemExit(f'missing {name}')
    params=[x for x in m.group(1).split(',') if x.strip()]
    if len(params)>4: raise SystemExit(f'{name} still has {len(params)} params')
p.write_text(s)
out=hashlib.sha256(p.read_bytes()).hexdigest(); print(out)
