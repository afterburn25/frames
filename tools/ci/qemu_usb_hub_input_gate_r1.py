#!/usr/bin/env python3
import argparse, hashlib, json, pathlib, socket, subprocess, time

WHITE=(244,247,251)
CURSOR_PATTERN=[(1,1),(1,2),(1,3),(1,4),(1,5),(3,5),(4,5),(1,6),(1,7),(1,8),(5,8),(6,8),(1,9),(1,10),(1,11),(1,12),(1,13)]
OVERLAY_X=840
OVERLAY_Y=242

def sha256(path):
    h=hashlib.sha256()
    with open(path,'rb') as f:
        for b in iter(lambda:f.read(1024*1024),b''):
            h.update(b)
    return h.hexdigest()

def read_ppm(path):
    data=pathlib.Path(path).read_bytes()
    pos=0; toks=[]
    while len(toks)<4:
        while pos<len(data) and data[pos] in b' \t\r\n': pos+=1
        if pos<len(data) and data[pos]==35:
            while pos<len(data) and data[pos] not in b'\r\n': pos+=1
            continue
        st=pos
        while pos<len(data) and data[pos] not in b' \t\r\n': pos+=1
        toks.append(data[st:pos])
    if toks[0]!=b'P6': raise RuntimeError('unexpected screendump format')
    w=int(toks[1]); h=int(toks[2]); mx=int(toks[3])
    if mx!=255: raise RuntimeError('unexpected PPM maxval')
    need=w*h*3
    if len(data)<need: raise RuntimeError('truncated PPM')
    return (w,h,data[-need:])

def pixel(im,x,y):
    w,h,p=im
    i=(y*w+x)*3
    return (p[i],p[i+1],p[i+2])

def locate_cursor(im,cx=396,cy=290,radius=100):
    w,h,_=im; cand=[]
    for y in range(max(0,cy-radius),min(h-16,cy+radius)+1):
        for x in range(max(0,cx-radius),min(w-8,cx+radius)+1):
            if all(pixel(im,x+dx,y+dy)==WHITE for dx,dy in CURSOR_PATTERN):
                wc=sum(1 for yy in range(y,y+16) for xx in range(x,x+8) if pixel(im,xx,yy)==WHITE)
                cand.append((abs(x-cx)+abs(y-cy),abs(wc-17),x,y,wc))
    if not cand: return None
    cand.sort(); return (cand[0][2],cand[0][3])

def frame_delta(a,b):
    w,h,pa=a; wb,hb,pb=b
    if (w,h)!=(wb,hb): raise RuntimeError('frame size changed')
    n=0; minx=w; miny=h; maxx=-1; maxy=-1
    for y in range(h):
        row=y*w*3
        for x in range(w):
            if x>=OVERLAY_X and y<OVERLAY_Y: continue
            i=row+x*3
            if pa[i:i+3]!=pb[i:i+3]:
                n+=1; minx=min(minx,x); miny=min(miny,y); maxx=max(maxx,x); maxy=max(maxy,y)
    return n,(None if n==0 else [minx,miny,maxx,maxy])

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--ovmf',required=True)
    ap.add_argument('--iso',required=True)
    ap.add_argument('--out',required=True)
    ap.add_argument('--expected-iso-sha',required=True)
    ap.add_argument('--topology',choices=['direct','hub'],required=True)
    a=ap.parse_args()
    out=pathlib.Path(a.out); out.mkdir(parents=True,exist_ok=True)
    result={'status':'FAIL','gate':'usb_hub_input_visual_v2','topology':a.topology,'iso_sha256':sha256(a.iso),'child_hid_marker':False}
    if result['iso_sha256']!=a.expected_iso_sha:
        raise SystemExit('unexpected ISO SHA '+result['iso_sha256'])
    q=out/'qmp.sock'; ser=out/'serial.log'; err=(out/'qemu.stderr').open('wb')
    cmd=['qemu-system-x86_64','-machine','q35','-m','768M','-smp','2','-cpu','max','-accel','tcg,thread=single','-display','none','-no-reboot','-no-shutdown','-nic','none','-serial',f'file:{ser}','-qmp',f'unix:{q},server=on,wait=off','-drive',f'if=pflash,format=raw,readonly=on,file={a.ovmf}','-cdrom',a.iso,'-boot','d','-device','qemu-xhci,id=xhci']
    if a.topology=='direct':
        cmd += ['-device','usb-mouse,bus=xhci.0,port=1,id=usbmouse']
    else:
        cmd += ['-device','usb-hub,bus=xhci.0,port=1,id=hub','-device','usb-mouse,bus=hub.0,port=1,id=usbmouse']
    (out/'qemu-command.json').write_text(json.dumps(cmd,indent=2)+'\n')
    p=subprocess.Popen(cmd,stdout=subprocess.DEVNULL,stderr=err)
    try:
        for _ in range(600):
            if q.exists(): break
            if p.poll() is not None: raise RuntimeError('QEMU exited before QMP became ready')
            time.sleep(.05)
        if not q.exists(): raise RuntimeError('qmp timeout')
        s=socket.socket(socket.AF_UNIX,socket.SOCK_STREAM); s.connect(str(q)); f=s.makefile('rwb',0)
        json.loads(f.readline())
        def call(name,args=None):
            o={'execute':name}
            if args is not None: o['arguments']=args
            f.write((json.dumps(o)+'\n').encode())
            while True:
                line=f.readline()
                if not line: raise RuntimeError('QMP closed')
                r=json.loads(line)
                if 'return' in r: return r['return']
                if 'error' in r: raise RuntimeError(str(r['error']))
        call('qmp_capabilities')
        mice=call('query-mice'); (out/'query-mice.json').write_text(json.dumps(mice,indent=2)+'\n')
        idx=next((m['index'] for m in mice if ('usb' in m['name'].lower() or 'hid' in m['name'].lower()) and 'ps/2' not in m['name'].lower()),None)
        if idx is None: raise RuntimeError('USB pointer frontend missing')
        call('human-monitor-command',{'command-line':f'mouse_set {idx}'})
        ready=['FRAMES_V108_INPUT_TEST_RUNTIME_READY','FRAMES_V108_STABLE_INPUT_DIAG_OK']
        text=''
        for _ in range(1000):
            text=ser.read_text(errors='ignore') if ser.exists() else ''
            if all(m in text for m in ready): break
            time.sleep(.1)
        else: raise RuntimeError('runtime readiness marker timeout')
        if a.topology=='hub':
            for _ in range(300):
                text=ser.read_text(errors='ignore')
                if 'FRAMES_USB_HUB_CHILD_HID_OK' in text: break
                time.sleep(.1)
            result['child_hid_marker']='FRAMES_USB_HUB_CHILD_HID_OK' in text
            if not result['child_hid_marker']:
                raise RuntimeError('hub child HID marker not reached')
        else:
            result['child_hid_marker']=False
        def capture(name):
            ppm=out/(name+'.ppm')
            call('screendump',{'filename':str(ppm)})
            return read_ppm(ppm)
        time.sleep(.3)
        before=capture('BEFORE'); pos0=locate_cursor(before)
        if pos0 is None: raise RuntimeError('initial cursor not found')
        time.sleep(.25)
        stable=capture('STABLE'); posS=locate_cursor(stable,pos0[0],pos0[1],5)
        idle_changed,_=frame_delta(before,stable)
        if posS!=pos0 or idle_changed>8:
            raise RuntimeError(f'baseline unstable pos={pos0}->{posS} pixels={idle_changed}')
        required=['FRAMES_V108_PHYSICAL_CURSOR_VISIBLE_OK','FRAMES_V108_USB_LIVE_REPORT_OK','FRAMES_V108_USB_GUI_CURSOR_OK']
        markers=False
        for _ in range(32):
            call('input-send-event',{'events':[{'type':'rel','data':{'axis':'x','value':4}},{'type':'rel','data':{'axis':'y','value':2}}]})
            time.sleep(.08)
            text=ser.read_text(errors='ignore')
            if all(m in text for m in required): markers=True; break
        if not markers: raise RuntimeError('USB live-input markers not reached')
        time.sleep(.15)
        after=capture('AFTER'); pos1=locate_cursor(after,pos0[0]+8,pos0[1]+4,140)
        if pos1 is None: raise RuntimeError('moved cursor not found')
        changed,bbox=frame_delta(stable,after); dx=pos1[0]-pos0[0]; dy=pos1[1]-pos0[1]
        result.update(markers=True,initial_cursor=list(pos0),final_cursor=list(pos1),dx=dx,dy=dy,idle_changed_pixels=idle_changed,changed_pixels_outside_overlay=changed,changed_bbox=bbox,frame_size=[before[0],before[1]])
        if not (dx>0 and dy>0 and abs(dx)<=128 and abs(dy)<=128):
            raise RuntimeError('cursor displacement invalid')
        if not (20<=changed<=2500):
            raise RuntimeError('movement redraw not localized')
        result['status']='PASS'
        call('quit')
    except Exception as e:
        result['error']=str(e)
        raise
    finally:
        try: p.wait(timeout=5)
        except Exception:
            p.kill(); p.wait()
        err.close()
        (out/'RESULT.json').write_text(json.dumps(result,indent=2)+'\n')

if __name__=='__main__':
    main()
