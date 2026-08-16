#!/usr/bin/env python3
import argparse,hashlib,json,pathlib,socket,subprocess,time

def sha256(p):
    h=hashlib.sha256()
    with open(p,'rb') as f:
        for b in iter(lambda:f.read(1024*1024),b''): h.update(b)
    return h.hexdigest()

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--ovmf',required=True); ap.add_argument('--iso',required=True)
    ap.add_argument('--out',required=True); ap.add_argument('--expected-iso-sha',required=True)
    a=ap.parse_args(); out=pathlib.Path(a.out); out.mkdir(parents=True,exist_ok=True)
    result={'status':'FAIL','gate':'v108_text_edit_r15','iso_sha256':sha256(a.iso),'runtime_ready':False,'ibeam':False,'caret':False,'blink':False,'keyboard_text':False,'left':False,'right':False,'delete':False}
    if result['iso_sha256']!=a.expected_iso_sha: raise SystemExit('ISO identity mismatch')
    q=out/'qmp.sock'; ser=out/'serial.log'; err=(out/'qemu.stderr').open('wb')
    cmd=['qemu-system-x86_64','-machine','q35','-m','768M','-smp','2','-cpu','max','-accel','tcg,thread=single','-display','none','-no-reboot','-no-shutdown','-nic','none','-serial',f'file:{ser}','-qmp',f'unix:{q},server=on,wait=off','-drive',f'if=pflash,format=raw,readonly=on,file={a.ovmf}','-cdrom',a.iso,'-boot','d']
    (out/'qemu-command.json').write_text(json.dumps(cmd,indent=2)+'\n')
    p=subprocess.Popen(cmd,stdout=subprocess.DEVNULL,stderr=err)
    try:
        for _ in range(600):
            if q.exists(): break
            if p.poll() is not None: raise RuntimeError(f'qemu exited {p.returncode}')
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
        call('qmp_capabilities')
        mice=call('query-mice'); (out/'query-mice.json').write_text(json.dumps(mice,indent=2)+'\n')
        idx=next((m['index'] for m in mice if 'ps/2' in m['name'].lower() or 'ps2' in m['name'].lower()),None)
        if idx is None: raise RuntimeError('PS2 pointer frontend missing')
        call('human-monitor-command',{'command-line':f'mouse_set {idx}'})
        for _ in range(1000):
            txt=ser.read_text(errors='ignore') if ser.exists() else ''
            if 'FRAMES_V108_INPUT_TEST_RUNTIME_READY' in txt and 'FRAMES_V108_PS2_ENABLE_OK' in txt:
                result['runtime_ready']=True; break
            if p.poll() is not None: break
            time.sleep(.1)
        if not result['runtime_ready']: raise RuntimeError('runtime readiness timeout')
        def mouse(dx=0,dy=0):
            ev=[]
            if dx: ev.append({'type':'rel','data':{'axis':'x','value':dx}})
            if dy: ev.append({'type':'rel','data':{'axis':'y','value':dy}})
            if ev: call('input-send-event',{'events':ev})
        def button(name,down): call('input-send-event',{'events':[{'type':'btn','data':{'down':down,'button':name}}]})
        def key(qcode):
            call('input-send-event',{'events':[{'type':'key','data':{'down':True,'key':{'type':'qcode','data':qcode}}}]}); time.sleep(.04)
            call('input-send-event',{'events':[{'type':'key','data':{'down':False,'key':{'type':'qcode','data':qcode}}}]}); time.sleep(.06)
        # Normalize to the top-left using bounded PS/2-relative steps, then enter the known input-test text band.
        for _ in range(24): mouse(-60,-60); time.sleep(.015)
        for _ in range(10): mouse(10,0); time.sleep(.015)   # x ~= 100
        for _ in range(48): mouse(0,10); time.sleep(.015)   # y ~= 480
        # Sweep vertically through the text box region; stop as soon as the real hover path emits its marker.
        for _ in range(36):
            mouse(0,5); time.sleep(.04)
            txt=ser.read_text(errors='ignore') if ser.exists() else ''
            if 'FRAMES_V108_TEXT_IBEAM_OK' in txt: result['ibeam']=True; break
        if not result['ibeam']: raise RuntimeError('I-beam hover marker not reached')
        # Focus at the current text-box position.
        button('left',True); time.sleep(.08); button('left',False); time.sleep(.2)
        deadline=time.time()+8
        while time.time()<deadline:
            txt=ser.read_text(errors='ignore') if ser.exists() else ''
            result['caret']='FRAMES_V108_TEXT_CARET_OK' in txt
            result['blink']='FRAMES_V108_TEXT_CARET_BLINK_OK' in txt
            if result['caret'] and result['blink']: break
            time.sleep(.1)
        if not result['caret']: raise RuntimeError('text caret marker not reached')
        if not result['blink']: raise RuntimeError('caret blink marker not reached')
        # Exercise insertion and navigation on the actual PS/2 keyboard path.
        for k in ('a','b','c','d'): key(k)
        key('left'); key('left'); key('right'); key('left'); key('delete')
        deadline=time.time()+5
        while time.time()<deadline:
            txt=ser.read_text(errors='ignore') if ser.exists() else ''
            result['keyboard_text']='FRAMES_V108_KEYBOARD_TEXT_OK' in txt
            result['left']='FRAMES_V108_TEXT_LEFT_OK' in txt
            result['right']='FRAMES_V108_TEXT_RIGHT_OK' in txt
            result['delete']='FRAMES_V108_TEXT_DELETE_OK' in txt
            if all(result[k] for k in ('keyboard_text','left','right','delete')): break
            time.sleep(.1)
        if not all(result[k] for k in ('keyboard_text','left','right','delete')):
            raise RuntimeError('text edit key markers incomplete')
        result['status']='PASS'
        try: call('quit')
        except Exception: pass
    except Exception as e:
        result['error']=str(e); raise
    finally:
        try:p.wait(timeout=5)
        except Exception:p.kill(); p.wait()
        err.close(); (out/'TEXT-EDIT.json').write_text(json.dumps(result,indent=2)+'\n')
        try:q.unlink()
        except Exception:pass

if __name__=='__main__': main()
