#!/usr/bin/env python3
from pathlib import Path
import hashlib, sys

p=Path(sys.argv[1])
raw=p.read_bytes()
expected='b94070bfe399162a8bb5bef1694c92100716d500d9e85737896901ef3f5aa8e7'
actual=hashlib.sha256(raw).hexdigest()
if actual!=expected:
    raise SystemExit(f'unexpected r7 pre-compilefix kernel hash: {actual}')
s=raw.decode()

old='''fn v108_cursor_present(process:u64,oldx:u64,oldy:u64,newx:u64,newy:u64) -> u64 {
    let dirty=volatile_read64(process+624); let timing=volatile_read64(process+664); let present=volatile_read64(process+672); if dirty==0 || timing==0 || present==0 { return 0; }
    dirty_add(dirty,(oldx*65536)+oldy,(8*65536)+16,32); dirty_add(dirty,(newx*65536)+newy,(8*65536)+16,32);
    present_enqueue(present,(oldx*65536)+oldy,(8*65536)+16,32); present_enqueue(present,(newx*65536)+newy,(8*65536)+16,32);
    if present_flush(present,volatile_read64(process+616),timing)==0 { return 0; }
    return 1;
}'''
new='''fn v108_cursor_present(process:u64,oldpos:u64,newpos:u64) -> u64 {
    let oldx=oldpos/65536; let oldy=oldpos%65536; let newx=newpos/65536; let newy=newpos%65536;
    let dirty=volatile_read64(process+624); let timing=volatile_read64(process+664); let present=volatile_read64(process+672); if dirty==0 || timing==0 || present==0 { return 0; }
    dirty_add(dirty,oldpos,(8*65536)+16,32); dirty_add(dirty,newpos,(8*65536)+16,32);
    present_enqueue(present,oldpos,(8*65536)+16,32); present_enqueue(present,newpos,(8*65536)+16,32);
    if present_flush(present,volatile_read64(process+616),timing)==0 { return 0; }
    return 1;
}'''
if s.count(old)!=1:
    raise SystemExit(f'cursor-present helper anchor mismatch: {s.count(old)}')
s=s.replace(old,new,1)
oldcall='v108_cursor_present(process,oldx,oldy,newx,newy);'
newcall='v108_cursor_present(process,(oldx*65536)+oldy,(newx*65536)+newy);'
if s.count(oldcall)!=1:
    raise SystemExit(f'cursor-present call anchor mismatch: {s.count(oldcall)}')
s=s.replace(oldcall,newcall,1)
p.write_text(s)
out=hashlib.sha256(p.read_bytes()).hexdigest()
print(out)
expected_out='d458aa61d92ff33bcf7e529354deec7cd345d5d96188c95b08842853fa3e3e2b'
if out!=expected_out:
    raise SystemExit(f'unexpected r7 compilefix output hash: {out}')
