#!/usr/bin/env python3
import argparse, hashlib, json, pathlib, socket, subprocess, time
from PIL import Image

WHITE=(244,247,251)
CURSOR_PATTERN=[(1,1),(1,2),(1,3),(1,4),(1,5),(3,5),(4,5),(1,6),(1,7),(1,8),(5,8),(6,8),(1,9),(1,10),(1,11),(1,12),(1,13)]
OVERLAY_X=840
OVERLAY_Y=242

def sha256(path):
    h=hashlib.sha256()
    with open(path,'rb') as f:
        for b in iter(lambda:f.read(1024*1024),b''): h.update(b)
    return h.hexdigest()

def locate_cursor(im,cx=396,cy=290,radius=80):
    cand=[]
    for y in range(max(0,cy-radius),min(im.height-16,cy+radius)+1):
        for x in range(max(0,cx-radius),min(im.width-8,cx+radius)+1):
            if all(im.getpixel((x+dx,y+dy))==WHITE for dx,dy in CURSOR_PATTERN):
                wc=sum(1 for yy in range(y,y+16) for xx in range(x,x+8) if im.getpixel((xx,yy))==WHITE)
                cand.append((abs(x-cx)+abs(y-cy),abs(wc-17),x,y,wc))
    if not cand:return None
    cand.sort(); return (cand[0][2],cand[0][3])

def frame_delta(a,b):
    pts=[]
    for y in range(a.height):
        for x in range(a.width):
            if x>=OVERLAY_X and y<OVERLAY_Y: continue
            if a.getpixel((x,y))!=b.getpixel((x,y)): pts.append((x,y))
    if not pts:return 0,None
    return len(pts),[min(x for x,y in pts),min(y for x,y in pts),max(x for x,y in pts),max(y for x,y in pts)]

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--ovmf',required=True); ap.add_argument('--iso',required=True); ap.add_argument('--lane',choices=['usb','ps2'],required=True)
    ap.add_argument('--out',required=True); ap.add_argument('--expected-iso-sha',required=True)
    a=ap.parse_args(); out=pathlib.Path(a.out); out.mkdir(parents=True,exist_ok=True)
    result={'status':'FAIL','lane':a.lane,'iso_sha256':sha256(a.iso),'gate':'r10_stable_input_visual'}
    if result['iso_sha256']!=a.expected_iso_sha: raise SystemExit('unexpected ISO SHA '+result['iso_sha256'])
    q=out/'qmp.sock'; ser=out/'serial.log'; err=(out/'qemu.stderr').open('wb')
    cmd=['qemu-system-x86_64','-machine','q35','-m','768M','-smp','2','-cpu','max','-accel','tcg,thread=single','-display','none','-no-reboot','-no-shutdown','-nic','none','-serial',f'file:{ser}','-qmp',f'unix:{q},server=on,wait=off','-drive',f'if=pflash,format=raw,readonly=on,file={a.ovmf}','-cdrom',a.iso,'-boot','d']
    if a.lane=='usb': cmd += ['-device','qemu-xhci,id=xhci','-device','usb-mouse,bus=xhci.0,id=usbmouse']
    (out/'qemu-command.json').write_text(json.dumps(cmd,indent=2)+'\n')
    p=subprocess.Popen(cmd,stdout=subprocess.DEVNULL,stderr=err)
    try:
        for _ in range(500):
            if q.exists():break
            time.sleep(.05)
        if not q.exists():raise RuntimeError('qmp timeout')
        s=socket.socket(socket.AF_UNIX,socket.SOCK_STREAM); s.connect(str(q)); f=s.makefile('rwb',0); json.loads(f.readline())
        def call(name,args=None):
            o={'execute':name}
            if args is not None:o['arguments']=args
            f.write((json.dumps(o)+'\n').encode())
            while True:
                r=json.loads(f.readline())
                if 'return' in r:return r['return']
                if 'error' in r:raise RuntimeError(r['error'])
        call('qmp_capabilities'); mice=call('query-mice'); (out/'query-mice.json').write_text(json.dumps(mice,indent=2)+'\n')
        if a.lane=='usb': idx=next((m['index'] for m in mice if ('usb' in m['name'].lower() or 'hid' in m['name'].lower()) and 'ps/2' not in m['name'].lower()),None)
        else: idx=next((m['index'] for m in mice if 'ps/2' in m['name'].lower() or 'ps2' in m['name'].lower()),None)
        if idx is None:raise RuntimeError('pointer frontend missing')
        call('human-monitor-command',{'command-line':f'mouse_set {idx}'})
        ready=['FRAMES_V108_INPUT_TEST_RUNTIME_READY','FRAMES_V108_STABLE_INPUT_DIAG_OK']
        if a.lane=='ps2':ready.append('FRAMES_V108_PS2_ENABLE_OK')
        for _ in range(800):
            t=ser.read_text(errors='ignore') if ser.exists() else ''
            if all(m in t for m in ready):break
            time.sleep(.1)
        else:raise RuntimeError('runtime marker timeout')
        def capture(name):
            ppm=out/(name+'.ppm'); png=out/(name+'.png'); call('screendump',{'filename':str(ppm)})
            im=Image.open(ppm).convert('RGB'); im.save(png); ppm.unlink(); return im
        time.sleep(.3); before=capture('BEFORE'); pos0=locate_cursor(before)
        if pos0 is None:raise RuntimeError('initial cursor not found')
        time.sleep(.25); stable=capture('STABLE'); posS=locate_cursor(stable,pos0[0],pos0[1],4)
        idle_changed,_=frame_delta(before,stable)
        if posS!=pos0 or idle_changed>4:raise RuntimeError(f'baseline not stable pos={pos0}->{posS}, pixels={idle_changed}')
        req=['FRAMES_V108_PHYSICAL_CURSOR_VISIBLE_OK'] + (['FRAMES_V108_USB_LIVE_REPORT_OK','FRAMES_V108_USB_GUI_CURSOR_OK'] if a.lane=='usb' else ['FRAMES_V108_PS2_PACKET_OK','FRAMES_V108_PS2_GUI_CURSOR_OK'])
        markers=False
        for _ in range(24):
            call('input-send-event',{'events':[{'type':'rel','data':{'axis':'x','value':4}},{'type':'rel','data':{'axis':'y','value':2}}]})
            time.sleep(.08); t=ser.read_text(errors='ignore')
            if all(m in t for m in req):markers=True; break
        if not markers:raise RuntimeError('required live-input markers not reached')
        time.sleep(.15); after=capture('AFTER'); pos1=locate_cursor(after,pos0[0]+8,pos0[1]+4,120)
        if pos1 is None:raise RuntimeError('moved cursor not found')
        changed,bbox=frame_delta(stable,after); dx=pos1[0]-pos0[0]; dy=pos1[1]-pos0[1]
        result.update(markers=True,initial_cursor=list(pos0),final_cursor=list(pos1),dx=dx,dy=dy,changed_pixels_outside_overlay=changed,changed_bbox=bbox,idle_changed_pixels=idle_changed)
        if not (dx>0 and dy>0 and abs(dx)<=96 and abs(dy)<=96):raise RuntimeError('cursor displacement invalid')
        if not (20<=changed<=2000):raise RuntimeError('movement redraw not localized')
        result['status']='PASS'; call('quit')
    except Exception as e:
        result['error']=str(e); raise
    finally:
        try:p.wait(timeout=5)
        except Exception:p.kill(); p.wait()
        err.close(); (out/'RUNTIME.json').write_text(json.dumps(result,indent=2)+'\n')

if __name__=='__main__':main()
