#!/usr/bin/env python3
from pathlib import Path
import json, sys

if len(sys.argv) < 2:
    raise SystemExit('usage: verify_splash_frame.py FRAME.ppm [FRAME2.ppm ...]')

def read_ppm(path: Path):
    data=path.read_bytes()
    if not data.startswith(b'P6'):
        raise ValueError('not P6')
    i=2; toks=[]
    while len(toks)<3:
        while i<len(data) and data[i] in b' \t\r\n': i+=1
        if i<len(data) and data[i]==35:
            while i<len(data) and data[i] not in b'\r\n': i+=1
            continue
        j=i
        while j<len(data) and data[j] not in b' \t\r\n': j+=1
        toks.append(int(data[i:j])); i=j
    while i<len(data) and data[i] in b' \t\r\n': i+=1
    w,h,maxv=toks
    if maxv!=255: raise ValueError('unsupported max value')
    pix=data[i:i+w*h*3]
    if len(pix)!=w*h*3: raise ValueError('truncated pixels')
    return w,h,pix

def dist(p,c):
    return abs(p[0]-c[0])+abs(p[1]-c[1])+abs(p[2]-c[2])

bg=(8,17,31); accent=(62,142,255)
rows=[]; winner=None
for arg in sys.argv[1:]:
    p=Path(arg)
    try:
        w,h,pix=read_ppm(p)
        def rgb(x,y):
            k=(y*w+x)*3; return (pix[k],pix[k+1],pix[k+2])
        step=max(1,min(w,h)//220)
        total=bg_hits=accent_hits=center_nonbg=corner_bg=corner_total=0
        x0,x1=w//4,(3*w)//4; y0,y1=h//4,(3*h)//4
        corner=max(8,min(w,h)//16)
        for y in range(0,h,step):
            for x in range(0,w,step):
                q=rgb(x,y); total+=1
                if dist(q,bg)<=18: bg_hits+=1
                if dist(q,accent)<=45: accent_hits+=1
                if x0<=x<x1 and y0<=y<y1 and dist(q,bg)>45: center_nonbg+=1
                if (x<corner or x>=w-corner) and (y<corner or y>=h-corner):
                    corner_total+=1
                    if dist(q,bg)<=18: corner_bg+=1
        bg_ratio=bg_hits/max(1,total)
        corner_ratio=corner_bg/max(1,corner_total)
        passed=(w>=640 and h>=400 and bg_ratio>=0.35 and corner_ratio>=0.80 and center_nonbg>=80 and accent_hits>=8)
        row={'file':p.name,'width':w,'height':h,'bg_ratio':round(bg_ratio,4),'corner_bg_ratio':round(corner_ratio,4),'center_nonbg':center_nonbg,'accent_hits':accent_hits,'pass':passed}
        rows.append(row)
        if passed and winner is None: winner=row
    except Exception as e:
        rows.append({'file':p.name,'pass':False,'error':str(e)})
out={'status':'PASS' if winner else 'FAIL','profile':'frames-boot-splash-phase1-framebuffer-proof','winner':winner,'frames':rows}
print(json.dumps(out,indent=2))
if not winner:
    raise SystemExit(1)
