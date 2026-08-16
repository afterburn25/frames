from pathlib import Path
import hashlib,sys
p=Path(sys.argv[1]); raw=p.read_bytes(); actual=hashlib.sha256(raw).hexdigest(); expected='8fd8fcf0be5160bed4524e1dc6e45cac659ab7a5fc9c2f1fbb9c14de32e00ffd'
if actual!=expected: raise SystemExit(f'unexpected r16 source hash {actual}')
s=raw.decode()
old_sig='fn v108_xhci_scan_pointer_v116(hardware_state:u64,phys_state:u64,xhci_state:u64,pml4:u64,input_state:u64) -> u64 {'
new_sig='fn v108_xhci_scan_pointer_v116(hardware_state:u64,phys_state:u64,xhci_state:u64,pml4:u64) -> u64 {'
if s.count(old_sig)!=1: raise SystemExit('r16 selector signature mismatch')
start=s.index(old_sig); op=s.index('{',start); depth=0; end=0
for j in range(op,len(s)):
    if s[j]=='{': depth+=1
    elif s[j]=='}':
        depth-=1
        if depth==0:
            end=j+1; break
if end==0: raise SystemExit('selector function span not found')
fn=s[start:end].replace(old_sig,new_sig,1)
fn=fn.replace(' || input_state==0','')
for old,new in [('input_state+3192','xhci_state+1056'),('input_state+3200','xhci_state+1064'),('input_state+3208','xhci_state+1072'),('input_state+3216','xhci_state+1080')]:
    fn=fn.replace(old,new)
if 'input_state' in fn: raise SystemExit('selector still references fifth parameter')
s=s[:start]+fn+s[end:]
old_call='v108_xhci_scan_pointer_v116(hardware_state,phys_state,xhci_state,kernel_pml4,input_state)'
new_call='v108_xhci_scan_pointer_v116(hardware_state,phys_state,xhci_state,kernel_pml4)'
if s.count(old_call)!=1: raise SystemExit('r16 selector call mismatch')
s=s.replace(old_call,new_call,1)
p.write_text(s)
out=hashlib.sha256(p.read_bytes()).hexdigest(); print(out)
if out!='a756177ca28ddb370e0995bd899bb6be1f9550421b55631cffa3cb94aac8ac05': raise SystemExit(f'unexpected r16b source hash {out}')
