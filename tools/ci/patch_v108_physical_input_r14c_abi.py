# r14e workflow trigger: corrected packed-pointer ABI is sealed below.
# The generated source output remains byte-for-byte fc1dec191b3ccf90e096d2b21d15f9fd1fae2c2e69fc0ae6be2da27f9ee347e4.
from pathlib import Path
import hashlib,sys
p=Path(sys.argv[1]); raw=p.read_bytes(); expected='45f9baa577e2736019fa63a06ba2e5b42d9a5a9d3c19c5745017ca831c5605be'
actual=hashlib.sha256(raw).hexdigest()
if actual!=expected: raise SystemExit(f'unexpected r14b source hash {actual}')
s=raw.decode()
old='''fn v108_input_pointer_draw(surface:u64,state:u64,input_state:u64,x:u64,y:u64) -> u64 {\n    if surface==0 || state==0 || input_state==0 { return 0; } let py=v108_test_y(state);'''
new='''fn v108_input_pointer_draw(surface:u64,state:u64,input_state:u64,pos:u64) -> u64 {\n    if surface==0 || state==0 || input_state==0 { return 0; } let x=pos/65536; let y=pos%65536; let py=v108_test_y(state);'''
if s.count(old)!=1: raise SystemExit('pointer ABI signature anchor')
s=s.replace(old,new,1)
repls=[
('v108_input_pointer_draw(surface,state,input_state,cx,cy);','v108_input_pointer_draw(surface,state,input_state,(cx*65536)+cy);'),
('v108_input_pointer_draw(surface,state,input_state,cx,cy)==0','v108_input_pointer_draw(surface,state,input_state,(cx*65536)+cy)==0'),
('v108_input_pointer_draw(surface,state,input_state,newx,newy);','v108_input_pointer_draw(surface,state,input_state,(newx*65536)+newy);'),
]
for a,b in repls:
    if s.count(a)!=1: raise SystemExit(f'pointer ABI call anchor {a}')
    s=s.replace(a,b,1)
p.write_text(s)
out=hashlib.sha256(p.read_bytes()).hexdigest(); print(out)
if out!='fc1dec191b3ccf90e096d2b21d15f9fd1fae2c2e69fc0ae6be2da27f9ee347e4': raise SystemExit(f'unexpected r14c source hash {out}')
