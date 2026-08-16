#!/usr/bin/env python3
from PIL import Image
from pathlib import Path
import json, sys

if len(sys.argv)!=2:
    raise SystemExit('usage: verify_full_desktop_frame.py FRAMEBUFFER.ppm')
p=Path(sys.argv[1])
im=Image.open(p).convert('RGB'); w,h=im.size
px=im.load()
if w<1024 or h<700:
    raise SystemExit(f'frame too small: {w}x{h}')

# Native wm_render_window close button color = 0xFFEE6B5B. Real window chrome
# therefore gives us a fail-closed visual proof independent of serial markers.
target=(238,107,91)
mask=set()
for y in range(h):
    for x in range(w):
        r,g,b=px[x,y]
        if abs(r-target[0])<=2 and abs(g-target[1])<=2 and abs(b-target[2])<=2:
            mask.add((x,y))

components=[]
while mask:
    seed=mask.pop(); stack=[seed]; xs=[]; ys=[]
    while stack:
        x,y=stack.pop(); xs.append(x); ys.append(y)
        for nx,ny in ((x-1,y),(x+1,y),(x,y-1),(x,y+1)):
            if (nx,ny) in mask:
                mask.remove((nx,ny)); stack.append((nx,ny))
    area=len(xs); bbox=[min(xs),min(ys),max(xs),max(ys)]
    if area>=100 and bbox[2]-bbox[0]>=9 and bbox[3]-bbox[1]>=9:
        components.append({'area':area,'bbox':bbox,'center':[(bbox[0]+bbox[2])//2,(bbox[1]+bbox[3])//2]})

# Require three independently located real title-bar close buttons. The former
# dashboard proof has none, so this is the primary visible full-desktop gate.
centers=[c['center'] for c in components]
distinct=[]
for c in centers:
    if all(abs(c[0]-d[0])>30 or abs(c[1]-d[1])>24 for d in distinct):
        distinct.append(c)
window_chrome_ok=len(distinct)>=3

# Require a populated taskbar and nontrivial central desktop content. Color
# diversity is deliberately secondary to native-window chrome because mature
# dark themes can use a small, consistent palette.
def diversity(box,step=4):
    x0,y0,x1,y1=box; colors=set(); samples=0
    for y in range(y0,y1,step):
        for x in range(x0,x1,step):
            r,g,b=px[x,y]; colors.add((r//16,g//16,b//16)); samples+=1
    return len(colors),samples
bottom_div,_=diversity((0,int(h*.88),w,h),4)
center_div,_=diversity((int(w*.12),int(h*.08),int(w*.94),int(h*.84)),5)
taskbar_ok=bottom_div>=12
content_ok=center_div>=15

# Check that the frame has content on both left and right halves, which catches
# accidentally rendered single-window or blank-desktop results.
def nonflat_score(box,step=6):
    x0,y0,x1,y1=box; vals=[]
    for y in range(y0,y1,step):
        for x in range(x0,x1,step):
            r,g,b=px[x,y]; vals.append(r+g+b)
    if not vals:return 0
    mean=sum(vals)/len(vals)
    return sum(abs(v-mean)>24 for v in vals)/len(vals)
left_score=nonflat_score((0,0,w//2,int(h*.86)))
right_score=nonflat_score((w//2,0,w,int(h*.86)))
balanced_ok=left_score>.08 and right_score>.08

status='PASS' if all((window_chrome_ok,taskbar_ok,content_ok,balanced_ok)) else 'FAIL'
out={
    'status':status,'frame':str(p.name),'width':w,'height':h,
    'native_window_close_components':components,
    'distinct_window_controls':len(distinct),
    'bottom_quantized_color_diversity':bottom_div,
    'center_quantized_color_diversity':center_div,
    'left_nonflat_score':round(left_score,4),'right_nonflat_score':round(right_score,4),
    'checks':{'multiple_native_windows':window_chrome_ok,'taskbar_region':taskbar_ok,'rich_center_content':content_ok,'balanced_desktop_content':balanced_ok}
}
print(json.dumps(out,indent=2))
if status!='PASS':
    raise SystemExit(1)
