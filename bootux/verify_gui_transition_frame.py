#!/usr/bin/env python3
from pathlib import Path
import json, sys

if len(sys.argv)!=3:
    raise SystemExit('usage: verify_gui_transition_frame.py SPLASH.ppm GUI.ppm')

def ppm(path):
    b=Path(path).read_bytes()
    if not b.startswith(b'P6'):
        raise ValueError(f'{path}: not P6 PPM')
    i=2; vals=[]
    while len(vals)<3:
        while i<len(b) and b[i] in b' \t\r\n': i+=1
        if i<len(b) and b[i]==35:
            while i<len(b) and b[i] not in b'\r\n': i+=1
            continue
        j=i
        while j<len(b) and b[j] not in b' \t\r\n': j+=1
        vals.append(int(b[i:j])); i=j
    while i<len(b) and b[i] in b' \t\r\n': i+=1
    w,h,maxv=vals
    if maxv!=255: raise ValueError('unsupported max value')
    pix=b[i:i+w*h*3]
    if len(pix)!=w*h*3: raise ValueError('truncated PPM')
    return w,h,pix

sw,sh,sp=ppm(sys.argv[1]); gw,gh,gp=ppm(sys.argv[2])
if (sw,sh)!=(gw,gh):
    out={'status':'FAIL','reason':'resolution_changed','splash':[sw,sh],'gui':[gw,gh]}
    print(json.dumps(out,indent=2)); raise SystemExit(1)

pixels=sw*sh
step=max(1,pixels//250000)
diff=0; gui_unique=set(); gui_non_splash_bg=0
bg=(8,17,31)
for n in range(0,pixels,step):
    k=n*3
    a=sp[k:k+3]; b=gp[k:k+3]
    if a!=b: diff+=1
    rgb=(b[0],b[1],b[2]); gui_unique.add((rgb[0]//8,rgb[1]//8,rgb[2]//8))
    if abs(rgb[0]-bg[0])+abs(rgb[1]-bg[1])+abs(rgb[2]-bg[2])>45: gui_non_splash_bg+=1
count=(pixels+step-1)//step
diff_ratio=diff/max(1,count)
nonbg_ratio=gui_non_splash_bg/max(1,count)
passed=(sw>=640 and sh>=400 and diff_ratio>=0.10 and nonbg_ratio>=0.08 and len(gui_unique)>=20)
out={'status':'PASS' if passed else 'FAIL','profile':'frames-splash-kernel-gui-frame-transition','width':sw,'height':sh,'sample_count':count,'changed_ratio':round(diff_ratio,5),'gui_non_splash_bg_ratio':round(nonbg_ratio,5),'quantized_unique_colors':len(gui_unique)}
print(json.dumps(out,indent=2))
if not passed: raise SystemExit(1)
