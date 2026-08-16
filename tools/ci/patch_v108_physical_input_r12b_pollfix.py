from pathlib import Path
import hashlib,sys
p=Path(sys.argv[1]); raw=p.read_bytes(); expected='70e01c31e669679ec8de986cddfb361a3686681ce109740c16a7e50bb1a90be3'
actual=hashlib.sha256(raw).hexdigest()
if actual!=expected: raise SystemExit(f'unexpected flawed r12 hash {actual}')
s=raw.decode(); sig='fn ps2_poll_fallback(input_state:u64) -> u64 {'
starts=[]; pos=0
while True:
 i=s.find(sig,pos)
 if i<0: break
 starts.append(i); pos=i+1
if len(starts)!=2: raise SystemExit(f'expected two fallback functions, got {len(starts)}')
def span(st):
 op=s.index('{',st); d=0
 for j in range(op,len(s)):
  if s[j]=='{': d+=1
  elif s[j]=='}':
   d-=1
   if d==0:return st,j+1
 raise SystemExit('unclosed')
spans=[span(x) for x in starts]
first=s[spans[0][0]:spans[0][1]]
expected_wrapper='''fn ps2_poll_fallback(input_state:u64) -> u64 {\n    let n=ps2_poll_fallback_burst_v112(input_state,16); if n!=0 { unsafe { volatile_write64(input_state+56,1); } return 1; } return 0;\n}'''
if first!=expected_wrapper: raise SystemExit('first fallback is not r12 wrapper')
burst='''fn ps2_poll_fallback_burst_v112(input_state:u64,limit:u64) -> u64 {\n    if input_state==0 || volatile_read64(input_state+32)!=1 { return 0; } var n:u64=0;\n    while n<limit {\n        let status=io_read8(100); if status%2==0 { return n; } let data=io_read8(96);\n        unsafe { volatile_write64(input_state+3224,volatile_read64(input_state+3224)+1); volatile_write64(input_state+3248,status); volatile_write64(input_state+3256,data); }\n        if (status/32)%2!=0 { unsafe { volatile_write64(input_state+3232,volatile_read64(input_state+3232)+1); } ps2_mouse_decode_v108(input_state,data); }\n        else { unsafe { volatile_write64(input_state+3240,volatile_read64(input_state+3240)+1); } ps2_keyboard_decode_v112(input_state,data); }\n        n=n+1;\n    }\n    unsafe { volatile_write64(input_state+56,1); } return n;\n}\n'''
a,b=spans[1]; s=s[:a]+s[b:]
a=spans[0][0]; s=s[:a]+burst+s[a:]
s=s.replace('}\n\n\n\nfn serial_marker_acpi_reset_ready','}\n\n\nfn serial_marker_acpi_reset_ready',1)
p.write_text(s)
out=hashlib.sha256(p.read_bytes()).hexdigest(); print(out)
if out!='92782808bd0cda553f6f84116dc8761cefc561c2c025c464cbfe7830b72df81b': raise SystemExit(f'unexpected repaired r12b hash {out}')
