#!/usr/bin/env python3
import argparse,hashlib,json,pathlib,socket,subprocess,time
from PIL import Image

WHITE=(244,247,251)
CURSOR_PATTERN=[(1,1),(1,2),(1,3),(1,4),(1,5),(3,5),(4,5),(1,6),(1,7),(1,8),(5,8),(6,8),(1,9),(1,10),(1,11),(1,12),(1,13)]

def sha256(p):
    h=hashlib.sha256()
    with open(p,'rb') as f:
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

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--ovmf',required=True); ap.add_argument('--iso',required=True); ap.add_argument('--out',required=True); ap.add_argument('--expected-iso-sha',required=True)
    a=ap.parse_args(); out=pathlib.Path(a.out); out.mkdir(parents=True,exist_ok=True)
    result={'status':'FAIL','gate':'r14b_text_edit_ibeam','iso_sha256':sha256(a.iso),'runtime_ready':False,'ibeam':False,'caret_blink':False,'left':False,'right':False,'delete':False,'backspace':False,'edit_sequence':False}
    if result['iso_sha256']!=a.expected_iso_sha: raise SystemExit('ISO identity mismatch')
    q=out/'qmp.sock'; ser=out/'serial.log'; err=(out/'qemu.stderr').open('wb')
    cmd=['qemu-system-x86_64','-machine','q35','-m','768M','-smp','2','-cpu','max','-accel','tcg,thread=single','-display','none','-no-reboot','-no-shutdown','-nic','none','-serial',f'file:{ser}','-qmp',f'unix:{q},server=on,wait=off','-drive',f'if=pflash,format=raw,readonly=on,file={a.ovmf}','-cdrom',a.iso,'-boot','d']
    (out/'qemu-command.json').write_text(json.dumps(cmd,indent=2)+'\n')
    p=subprocess.Popen(cmd,stdout=subprocess.DEVNULL,stderr=err)
    try:
        for _ in range(500):
            if q.exists(): break
            time.sleep(.05)
        if not q.exists(): raise RuntimeError('qmp timeout')
        s=socket.socket(socket.AF_UNIX,socket.SOCK_STREAM); s.connect(str(q)); f=s.makefile('rwb',0); json.loads(f.readline())
        def call(name,args=None):
            o={'execute':name}
            if args is not None:o['arguments']=args
            f.write((json.dumps(o)+'\n').encode())
            while True:
                r=json.loads(f.readline())
                if 'return' in r:return r['return']
                if 'error' in r:raise RuntimeError(r['error'])
        def hmp(cmd): return call('human-monitor-command',{'command-line':cmd})
        def capture(name):
            ppm=out/(name+'.ppm'); call('screendump',{'filename':str(ppm)})
            im=Image.open(ppm).convert('RGB'); im.save(out/(name+'.png')); ppm.unlink(); return im
        call('qmp_capabilities'); mice=call('query-mice'); (out/'query-mice.json').write_text(json.dumps(mice,indent=2)+'\n')
        idx=next((m['index'] for m in mice if 'ps/2' in m['name'].lower() or 'ps2' in m['name'].lower()),None)
        if idx is None: raise RuntimeError('PS2 pointer frontend missing')
        hmp(f'mouse_set {idx}')
        for _ in range(1000):
            t=ser.read_text(errors='ignore') if ser.exists() else ''
            if 'FRAMES_V108_INPUT_TEST_RUNTIME_READY' in t and 'FRAMES_V108_PS2_ENABLE_OK' in t:
                result['runtime_ready']=True; break
            time.sleep(.1)
        if not result['runtime_ready']: raise RuntimeError('runtime readiness timeout')

        # Feedback-controlled standard-PS/2 walk. The key transition under test is that the
        # normal arrow cursor DISAPPEARS exactly as Frames draws the I-beam over the textbox,
        # so an arrow-template miss is accepted only when the I-beam runtime marker appears.
        time.sleep(.2); im=capture('START'); pos=locate_cursor(im)
        if pos is None: raise RuntimeError('initial cursor not found')
        result['initial_cursor']=list(pos)
        for _ in range(3):
            call('input-send-event',{'events':[{'type':'rel','data':{'axis':'x','value':1}}]}); time.sleep(.08)
        im=capture('WARM'); warm=locate_cursor(im,pos[0]+2,pos[1],12)
        if warm is None: raise RuntimeError('cursor missing after PS2 warm-up')
        pos=warm
        target_y=570; step_index=0; entered_ibeam=False
        while pos[1] < target_y and step_index < 120:
            req=min(3,target_y-pos[1])
            call('input-send-event',{'events':[{'type':'rel','data':{'axis':'y','value':req}}]})
            expected=(pos[0],pos[1]+req); moved=None
            for _ in range(14):
                time.sleep(.04)
                ppm=out/'STEP.ppm'; call('screendump',{'filename':str(ppm)})
                frame=Image.open(ppm).convert('RGB'); ppm.unlink()
                moved=locate_cursor(frame,expected[0],expected[1],12)
                if moved is None: moved=locate_cursor(frame,pos[0],pos[1],12)
                if moved is not None and moved!=pos: break
                t=ser.read_text(errors='ignore') if ser.exists() else ''
                if 'FRAMES_V108_IBEAM_OK' in t:
                    result['ibeam']=True; entered_ibeam=True; pos=expected; break
            step_index+=1
            if entered_ibeam: break
            if moved is None or moved==pos: raise RuntimeError(f'cursor failed while walking to textbox at {pos}')
            if moved[1] <= pos[1]: raise RuntimeError(f'cursor wrong direction while walking to textbox {pos}->{moved}')
            pos=moved
        result['textbox_hover_cursor']=list(pos); result['textbox_walk_steps']=step_index
        capture('HOVER')
        if not result['ibeam']:
            for _ in range(60):
                t=ser.read_text(errors='ignore') if ser.exists() else ''
                if 'FRAMES_V108_IBEAM_OK' in t: result['ibeam']=True; break
                time.sleep(.05)
        if not result['ibeam']: raise RuntimeError('I-beam marker not reached after verified textbox hover')

        call('input-send-event',{'events':[{'type':'btn','data':{'down':True,'button':'left'}}]}); time.sleep(.08)
        call('input-send-event',{'events':[{'type':'btn','data':{'down':False,'button':'left'}}]}); time.sleep(.12)
        # Exact editing proof deliberately uses uppercase ABC because the in-kernel sequence
        # marker validates final text == "A" after Left/Left/Right/Delete/Backspace.
        for key in ('shift-a','shift-b','shift-c','left','left','right','delete','backspace'):
            hmp('sendkey '+key); time.sleep(.18)
        deadline=time.time()+6
        while time.time()<deadline:
            t=ser.read_text(errors='ignore') if ser.exists() else ''
            result['ibeam']='FRAMES_V108_IBEAM_OK' in t
            result['caret_blink']='FRAMES_V108_CARET_BLINK_OK' in t
            result['left']='FRAMES_V108_TEXT_LEFT_OK' in t
            result['right']='FRAMES_V108_TEXT_RIGHT_OK' in t
            result['delete']='FRAMES_V108_TEXT_DELETE_OK' in t
            result['backspace']='FRAMES_V108_TEXT_BACKSPACE_OK' in t
            result['edit_sequence']='FRAMES_V108_TEXT_EDIT_SEQUENCE_OK' in t
            if all(result[k] for k in ('ibeam','caret_blink','left','right','delete','backspace','edit_sequence')): break
            time.sleep(.1)
        hmp(f'screendump {out}/FINAL.ppm')
        if not all(result[k] for k in ('ibeam','caret_blink','left','right','delete','backspace','edit_sequence')):
            raise RuntimeError('missing text-edit/I-beam runtime proof')
        result['status']='PASS'; call('quit')
    except Exception as e:
        result['error']=str(e); raise
    finally:
        try:p.wait(timeout=5)
        except Exception:p.kill(); p.wait()
        err.close(); (out/'TEXT-EDIT.json').write_text(json.dumps(result,indent=2)+'\n')
        try:q.unlink()
        except Exception:pass

if __name__=='__main__': main()
