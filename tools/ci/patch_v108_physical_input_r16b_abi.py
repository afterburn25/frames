from pathlib import Path
import hashlib,sys
p=Path(sys.argv[1]); raw=p.read_bytes(); actual=hashlib.sha256(raw).hexdigest(); expected='8fd8fcf0be5160bed4524e1dc6e45cac659ab7a5fc9c2f1fbb9c14de32e00ffd'
if actual!=expected: raise SystemExit(f'unexpected r16 source hash {actual}')
s=raw.decode()

def fn_span(text,name):
    start=text.index(name); op=text.index('{',start); depth=0
    for j in range(op,len(text)):
        if text[j]=='{': depth+=1
        elif text[j]=='}':
            depth-=1
            if depth==0: return start,j+1
    raise RuntimeError(name)

old_sig='fn v108_xhci_scan_pointer_v116(hardware_state:u64,phys_state:u64,xhci_state:u64,pml4:u64,input_state:u64) -> u64 {'
new_sig='fn v108_xhci_scan_pointer_v116(hardware_state:u64,phys_state:u64,xhci_state:u64,pml4:u64) -> u64 {'
if s.count(old_sig)!=1: raise SystemExit('r16 selector signature mismatch')
a,b=fn_span(s,old_sig)
fn=s[a:b].replace(old_sig,new_sig,1).replace(' || input_state==0','')
for old,new in [('input_state+3192','xhci_state+1056'),('input_state+3200','xhci_state+1064'),('input_state+3208','xhci_state+1072'),('input_state+3216','xhci_state+1080')]: fn=fn.replace(old,new)
if 'input_state' in fn: raise SystemExit('selector still references fifth parameter')
s=s[:a]+fn+s[b:]
old_call='v108_xhci_scan_pointer_v116(hardware_state,phys_state,xhci_state,kernel_pml4,input_state)'
if s.count(old_call)!=1: raise SystemExit('r16 selector call mismatch')
s=s.replace(old_call,'v108_xhci_scan_pointer_v116(hardware_state,phys_state,xhci_state,kernel_pml4)',1)

old_repaint='fn v108_desktop_interaction_repaint_v116(process:u64,state:u64,input_state:u64,xhci:u64,cursor:u64) -> u64 {'
new_repaint='fn v108_desktop_interaction_repaint_v116(process:u64,state:u64,input_state:u64,xhci:u64) -> u64 {'
if s.count(old_repaint)!=1: raise SystemExit('r16 repaint signature mismatch')
a,b=fn_span(s,old_repaint)
fn=s[a:b].replace(old_repaint,new_repaint,1)
needle='if process==0 || state==0 || input_state==0 || cursor==0 { return 0; }'
replacement='if process==0 || state==0 || input_state==0 { return 0; } let cursor=volatile_read64(process+640); if cursor==0 { return 0; }'
if fn.count(needle)!=1: raise SystemExit('r16 repaint cursor precondition mismatch')
fn=fn.replace(needle,replacement,1)
s=s[:a]+fn+s[b:]
old_call='v108_desktop_interaction_repaint_v116(process,state,input_state,xhci,cursor)'
if s.count(old_call)!=2: raise SystemExit(f'r16 repaint call mismatch {s.count(old_call)}')
s=s.replace(old_call,'v108_desktop_interaction_repaint_v116(process,state,input_state,xhci)')

p.write_text(s)
out=hashlib.sha256(p.read_bytes()).hexdigest(); print(out)
if out!='6d2a3b1ce3acbe35635dfd18d650e1d6c2fec2c1eaffceb264904cdaf8e8feb2': raise SystemExit(f'unexpected r16b source hash {out}')
