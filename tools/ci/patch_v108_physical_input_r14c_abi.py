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
if s.count('v108_input_pointer_draw(surface,state,input_state,cx,cy);')!=2: raise SystemExit('cx/cy pointer ABI call anchors')
s=s.replace('v108_input_pointer_draw(surface,state,input_state,cx,cy);','v108_input_pointer_draw(surface,state,input_state,(cx*65536)+cy);')
if s.count('v108_input_pointer_draw(surface,state,input_state,newx,newy);')!=1: raise SystemExit('newx/newy pointer ABI call anchor')
s=s.replace('v108_input_pointer_draw(surface,state,input_state,newx,newy);','v108_input_pointer_draw(surface,state,input_state,(newx*65536)+newy);',1)
p.write_text(s)
out=hashlib.sha256(p.read_bytes()).hexdigest(); print(out)
if out!='a59b20a3247389f7977c788756314f16fc6ac27a4dadc21dfad226f73b2eea76': raise SystemExit(f'unexpected r14c source hash {out}')
