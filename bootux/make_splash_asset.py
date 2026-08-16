#!/usr/bin/env python3
from pathlib import Path
from PIL import Image
import json, struct, sys

if len(sys.argv) != 3:
    raise SystemExit('usage: make_splash_asset.py INPUT_LOGO.png OUTPUT.FSP')
src=Path(sys.argv[1]); out=Path(sys.argv[2])
im=Image.open(src).convert('RGBA')
alpha=im.getchannel('A')
bbox=alpha.getbbox()
if bbox:
    im=im.crop(bbox)
max_w,max_h=360,180
scale=min(max_w/im.width,max_h/im.height,1.0)
if scale<1.0:
    im=im.resize((max(1,round(im.width*scale)),max(1,round(im.height*scale))),Image.Resampling.LANCZOS)
header=struct.pack('<8sIIII',b'FSPL1\0\0\0',im.width,im.height,im.width*4,1)
out.parent.mkdir(parents=True,exist_ok=True)
out.write_bytes(header+im.tobytes('raw','RGBA'))
meta={'format':'Frames Splash Asset v1','width':im.width,'height':im.height,'stride':im.width*4,'flags':1,'bytes':out.stat().st_size,'source':src.name}
print(json.dumps(meta,sort_keys=True))
