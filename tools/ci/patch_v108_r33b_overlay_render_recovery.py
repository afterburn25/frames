#!/usr/bin/env python3
from pathlib import Path
import hashlib,subprocess,sys
if len(sys.argv)!=2: raise SystemExit('usage: patch_v108_r33b_overlay_render_recovery.py <kernel/main.nx>')
p=Path(sys.argv[1]); base=Path(__file__).with_name('patch_v108_r33_ehci_ownership_recovery.py')
subprocess.run([sys.executable,str(base),str(p)],check=True,stdout=subprocess.DEVNULL)
s=p.read_text(); BASE='d81cf6d3a6ff53c57d18748e1fcf7da49f03f9b580f26e59b21a01a08a1495cf'
if hashlib.sha256(s.encode()).hexdigest()!=BASE: raise SystemExit('r33 base mismatch')

def span(text,name):
 st=text.index('fn '+name); op=text.index('{',st); d=0
 for i in range(op,len(text)):
  if text[i]=='{': d+=1
  elif text[i]=='}':
   d-=1
   if d==0:return st,i+1
 raise RuntimeError(name)
def label_fn(name,text):
 out=f'fn {name}(surface:u64,x:u64,y:u64,color:u64) -> u64 {{'
 for i,ch in enumerate(text): out+=f' if gui_draw_char_scaled(surface,((x+{i*6})*65536)+y,({ord(ch)}*65536)+1,color)==0 {{ return 0; }}'
 return out+' return 1; }'
a,b=span(s,'v108_text_r32_v132'); s=s[:a]+label_fn('v108_text_r32_v132','R33 EH N CB CA BS H X')+s[b:]
if s.count('(410*65536)+760')==0: raise SystemExit('r33b overlay-height anchor missing')
s=s.replace('(410*65536)+760','(410*65536)+742')
a,b=span(s,'v108_input_overlay_draw'); ov=s[a:b]
old='''    v108_text_r32_v132(surface,px+10,py+694,white); if xhci!=0 { v108_draw_small_u64(surface,((px+130)*65536)+(py+694),volatile_read64(xhci+2288),amber); v108_draw_small_u64(surface,((px+202)*65536)+(py+694),volatile_read64(xhci+2296),green); v108_draw_small_u64(surface,((px+274)*65536)+(py+694),volatile_read64(xhci+2304),white); }
    v108_text_r33_v133(surface,px+10,py+712,white); if xhci!=0 { v108_draw_small_u64(surface,((px+130)*65536)+(py+712),volatile_read64(xhci+2312),white); v108_draw_small_u64(surface,((px+178)*65536)+(py+712),volatile_read64(xhci+2320),amber); v108_draw_small_u64(surface,((px+226)*65536)+(py+712),volatile_read64(xhci+2328),green); v108_draw_small_u64(surface,((px+274)*65536)+(py+712),volatile_read64(xhci+2344),red); v108_draw_small_u64(surface,((px+322)*65536)+(py+712),volatile_read64(xhci+2352),green); v108_draw_small_u64(surface,((px+370)*65536)+(py+712),volatile_read64(xhci+2368),green); }
    return 1;'''
new='''    v108_text_r32_v132(surface,px+10,py+694,white); if xhci!=0 { v108_draw_small_u64(surface,((px+130)*65536)+(py+694),volatile_read64(xhci+2312),white); v108_draw_small_u64(surface,((px+178)*65536)+(py+694),volatile_read64(xhci+2320),amber); v108_draw_small_u64(surface,((px+226)*65536)+(py+694),volatile_read64(xhci+2328),green); v108_draw_small_u64(surface,((px+274)*65536)+(py+694),volatile_read64(xhci+2344),red); v108_draw_small_u64(surface,((px+322)*65536)+(py+694),volatile_read64(xhci+2352),green); v108_draw_small_u64(surface,((px+370)*65536)+(py+694),volatile_read64(xhci+2368),green); }
    return 1;'''
if ov.count(old)!=1: raise SystemExit(f'r33b overlay row anchor {ov.count(old)}')
ov=ov.replace(old,new,1); s=s[:a]+ov+s[b:]
ov=s[span(s,'v108_input_overlay_draw')[0]:span(s,'v108_input_overlay_draw')[1]]
if 'v108_text_r33_v133(surface' in ov: raise SystemExit('r33b extra telemetry row still rendered')
if 'volatile_read64(xhci+2368)' not in ov: raise SystemExit('r33b merged telemetry missing')
if s.count('{')!=s.count('}'): raise SystemExit('brace imbalance')
expected='78081f168b3612b0f36d81b7dacca130a0f1ef0808385db81ae7a8178c130bb4'
actual=hashlib.sha256(s.encode()).hexdigest()
if actual!=expected: raise SystemExit(f'r33b identity mismatch {actual}')
p.write_text(s); print(actual)
