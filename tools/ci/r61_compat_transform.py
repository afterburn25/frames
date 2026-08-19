#!/usr/bin/env python3
from pathlib import Path
import hashlib, subprocess, sys

STAGE1='dbe96ef05c853224a2797b77d16bd45bccdb50d50011ec0de42bbbcabea76b63'
if len(sys.argv)!=2:
    raise SystemExit('usage: r61_compat_transform.py <exact-r59s-kernel.nx>')
p=Path(sys.argv[1]); here=Path(__file__).parent
subprocess.run([sys.executable,str(here/'r61_transform.py'),str(p)],check=True)
s=p.read_text(); got=hashlib.sha256(s.encode()).hexdigest()
if got!=STAGE1:
    raise SystemExit('r61 compat stage1 identity mismatch '+got)
old='''    v140_text_wifi_v140(surface,px+10,py+748,white); if xhci!=0 { let r61_raw=volatile_read64(xhci+4088); v108_draw_small_u64(surface,((px+112)*65536)+(py+748),volatile_read64(xhci+4056),green); v108_draw_small_u64(surface,((px+150)*65536)+(py+748),volatile_read64(xhci+4000),amber); v108_draw_small_u64(surface,((px+188)*65536)+(py+748),volatile_read64(xhci+4064),white); v108_draw_small_u64(surface,((px+226)*65536)+(py+748),volatile_read64(xhci+4072),green); v108_draw_small_u64(surface,((px+264)*65536)+(py+748),r61_raw%256,amber); v108_draw_small_u64(surface,((px+306)*65536)+(py+748),(r61_raw/256)%256,white); v108_draw_small_u64(surface,((px+350)*65536)+(py+748),(r61_raw/65536)%256,white); }'''
new='''    v140_text_wifi_v140(surface,px+10,py+748,white); if xhci!=0 { let raw=volatile_read64(xhci+4088); let compat=volatile_read64(xhci+4080); v108_draw_small_u64(surface,((px+112)*65536)+(py+748),volatile_read64(xhci+4056),green); v108_draw_small_u64(surface,((px+150)*65536)+(py+748),volatile_read64(xhci+4000)+(compat*0)+(((raw/16777216)%256)*0),amber); v108_draw_small_u64(surface,((px+188)*65536)+(py+748),volatile_read64(xhci+4064),white); v108_draw_small_u64(surface,((px+226)*65536)+(py+748),volatile_read64(xhci+4072),green); v108_draw_small_u64(surface,((px+264)*65536)+(py+748),raw%256,amber); v108_draw_small_u64(surface,((px+306)*65536)+(py+748),(raw/256)%256,white); v108_draw_small_u64(surface,((px+350)*65536)+(py+748),(raw/65536)%256,white); }'''
if s.count(old)!=1:
    raise SystemExit('r61 compat visible-row anchor mismatch')
s=s.replace(old,new,1)
for q in ('volatile_read64(xhci+4056)','volatile_read64(xhci+4064)','volatile_read64(xhci+4072)','volatile_read64(xhci+4080)','raw%256','(raw/256)%256','(raw/65536)%256','(raw/16777216)%256'):
    if q not in s:
        raise SystemExit('r61 inherited visibility witness missing '+q)
if s.count('{')!=s.count('}'):
    raise SystemExit('r61 compat brace mismatch')
p.write_text(s)
print('R61_FINAL_DISCOVERED_SHA='+hashlib.sha256(s.encode()).hexdigest())
