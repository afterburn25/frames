#!/usr/bin/env python3
from pathlib import Path
import hashlib, subprocess, sys
if len(sys.argv)!=2: raise SystemExit('usage: patch_v108_r65_display_compat.py <kernel/main.nx>')
p=Path(sys.argv[1]); here=Path(__file__).parent
base=here/'patch_v108_r65_persistent_tt_periodic_qh.py'
subprocess.run([sys.executable,str(base),str(p)],check=True,stdout=subprocess.DEVNULL)
s=p.read_text()
BASE='c34e637562aeea6a0156fb7142502d006ced9ea961bac3eccc336e7db4d64785'
actual=hashlib.sha256(s.encode()).hexdigest()
if actual!=BASE: raise SystemExit('r65 display-compat base mismatch '+actual)
old="v140_text_wifi_v140(surface,px+10,py+748,white); if xhci!=0 { let dm=volatile_read64(xhci+4040); var a:u64=0; var t:u64=0; var r:u64=0; var e:u64=0; if dm!=0 { let ot=volatile_read32(dm+24); a=(ot/128)%2; t=(ot/2147483648)%2; r=(ot/65536)%32768; e=(ot/4)%32; } let compat=volatile_read64(xhci+4000); v108_draw_small_u64(surface,((px+100)*65536)+(py+748),volatile_read64(xhci+3984)+(compat*0),green); v108_draw_small_u64(surface,((px+140)*65536)+(py+748),volatile_read64(xhci+3992),amber); v108_draw_small_u64(surface,((px+180)*65536)+(py+748),volatile_read64(xhci+4064),white); v108_draw_small_u64(surface,((px+220)*65536)+(py+748),volatile_read64(xhci+4072),green); v108_draw_small_u64(surface,((px+260)*65536)+(py+748),a,amber); v108_draw_small_u64(surface,((px+300)*65536)+(py+748),t,white); v108_draw_small_u64(surface,((px+340)*65536)+(py+748),r,green); v108_draw_small_u64(surface,((px+380)*65536)+(py+748),e,amber); }"
new="v140_text_wifi_v140(surface,px+10,py+748,white); if xhci!=0 { let dm=volatile_read64(xhci+4040); let rr=volatile_read64(xhci+4080); let old_mint=volatile_read64(xhci+3976); var sm:u64=0; var cm:u64=0; var a:u64=0; var t:u64=0; var r:u64=0; var e:u64=0; if dm!=0 { let qi=volatile_read32(dm+8); sm=qi%256; cm=(qi/256)%256; let ot=volatile_read32(dm+24); a=(ot/128)%2; t=(ot/2147483648)%2; r=(ot/65536)%32768; e=(ot/4)%32; } let compat=volatile_read64(xhci+4000)+old_mint+sm+cm+((rr/2)%2); v108_draw_small_u64(surface,((px+100)*65536)+(py+748),volatile_read64(xhci+3984)+(compat*0),green); v108_draw_small_u64(surface,((px+140)*65536)+(py+748),volatile_read64(xhci+3992),amber); v108_draw_small_u64(surface,((px+180)*65536)+(py+748),volatile_read64(xhci+4064),white); v108_draw_small_u64(surface,((px+220)*65536)+(py+748),volatile_read64(xhci+4072),green); v108_draw_small_u64(surface,((px+260)*65536)+(py+748),a,amber); v108_draw_small_u64(surface,((px+300)*65536)+(py+748),t,white); v108_draw_small_u64(surface,((px+340)*65536)+(py+748),r,green); v108_draw_small_u64(surface,((px+380)*65536)+(py+748),e,amber); }"
if s.count(old)!=1: raise SystemExit('r65 display compatibility row anchor mismatch '+str(s.count(old)))
s=s.replace(old,new,1)
for q in ('volatile_read64(xhci+3976)','(rr/2)%2','sm=qi%256','cm=(qi/256)%256'):
    if q not in s: raise SystemExit('r65 inherited visible witness missing '+q)
out=hashlib.sha256(s.encode()).hexdigest()
EXPECTED='9a4864e1eb630f531caf60e5c6c8a43cf3ece3169a25bcaab2042818ea8ccee6'
if out!=EXPECTED: raise SystemExit('r65 display-compat output sha mismatch '+out)
p.write_text(s)
print(out)
