#!/usr/bin/env python3
import argparse,hashlib,json,pathlib,socket,subprocess,time

def sha256(p):
    h=hashlib.sha256()
    with open(p,'rb') as f:
        for b in iter(lambda:f.read(1024*1024),b''): h.update(b)
    return h.hexdigest()

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--ovmf',required=True); ap.add_argument('--iso',required=True); ap.add_argument('--out',required=True); ap.add_argument('--expected-iso-sha',required=True)
    a=ap.parse_args(); out=pathlib.Path(a.out); out.mkdir(parents=True,exist_ok=True)
    result={'status':'FAIL','gate':'r19_input_event_integrity','iso_sha256':sha256(a.iso),'runtime_ready':False,'down_did_not_open':False,'motion_cancelled':False,'release_opened':False,'hovered':False,'dismissed':False,'repeat':False}
    if result['iso_sha256']!=a.expected_iso_sha: raise SystemExit('ISO identity mismatch')
    q=out/'qmp.sock'; ser=out/'serial.log'; err=(out/'qemu.stderr').open('wb')
    cmd=['qemu-system-x86_64','-machine','q35','-m','768M','-smp','2','-cpu','max','-accel','tcg,thread=single','-display','none','-no-reboot','-no-shutdown','-nic','none','-serial',f'file:{ser}','-qmp',f'unix:{q},server=on,wait=off','-drive',f'if=pflash,format=raw,readonly=on,file={a.ovmf}','-cdrom',a.iso,'-boot','d']
    (out/'qemu-command.json').write_text(json.dumps(cmd,indent=2)+'\n'); p=subprocess.Popen(cmd,stdout=subprocess.DEVNULL,stderr=err)
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
        def text(): return ser.read_text(errors='ignore') if ser.exists() else ''
        def rel(x=0,y=0):
            ev=[]
            if x: ev.append({'type':'rel','data':{'axis':'x','value':x}})
            if y: ev.append({'type':'rel','data':{'axis':'y','value':y}})
            if ev: call('input-send-event',{'events':ev})
        def btn(name,down): call('input-send-event',{'events':[{'type':'btn','data':{'down':down,'button':name}}]})
        def click(name): btn(name,True); time.sleep(.10); btn(name,False); time.sleep(.16)
        def wait_marker(marker,seconds=2):
            end=time.time()+seconds
            while time.time()<end:
                if marker in text(): return True
                if p.poll() is not None: raise RuntimeError(f'qemu exited {p.returncode}')
                time.sleep(.04)
            return False
        call('qmp_capabilities'); mice=call('query-mice'); idx=next((m['index'] for m in mice if 'ps/2' in m['name'].lower() or 'ps2' in m['name'].lower()),None)
        if idx is None: raise RuntimeError('PS2 pointer frontend missing')
        call('human-monitor-command',{'command-line':f'mouse_set {idx}'})
        deadline=time.time()+110
        while time.time()<deadline:
            t=text()
            if 'FRAMES_V108_INPUT_TEST_RUNTIME_READY' in t and 'FRAMES_V108_STABLE_INPUT_DIAG_OK' in t: result['runtime_ready']=True; break
            if p.poll() is not None: raise RuntimeError(f'qemu exited {p.returncode}')
            time.sleep(.1)
        if not result['runtime_ready']: raise RuntimeError('runtime readiness timeout')
        baseline=text().count('FRAMES_V108_DESKTOP_CONTEXT_OK')
        btn('right',True); time.sleep(.25)
        result['down_did_not_open']=text().count('FRAMES_V108_DESKTOP_CONTEXT_OK')==baseline
        if not result['down_did_not_open']: raise RuntimeError('right-down alone opened menu')
        rel(20,0); time.sleep(.12); btn('right',False); time.sleep(.3)
        result['motion_cancelled']=text().count('FRAMES_V108_DESKTOP_CONTEXT_OK')==baseline
        if not result['motion_cancelled']: raise RuntimeError('right gesture was not cancelled by motion')
        click('right')
        result['release_opened']=wait_marker('FRAMES_V108_RIGHT_GESTURE_OK',1.0) and text().count('FRAMES_V108_DESKTOP_CONTEXT_OK')>baseline
        if not result['release_opened']: raise RuntimeError('stationary right press/release did not open')
        rel(20,20); result['hovered']=wait_marker('FRAMES_V108_CONTEXT_HOVER_OK',1.0)
        if not result['hovered']: raise RuntimeError('menu hover missing')
        for _ in range(4): rel(-80,-80); time.sleep(.04)
        click('left'); result['dismissed']=wait_marker('FRAMES_V108_CONTEXT_DISMISS_OK',1.0)
        if not result['dismissed']: raise RuntimeError('left outside dismiss missing')
        click('right'); result['repeat']=wait_marker('FRAMES_V108_CONTEXT_REPEAT_OK',1.0)
        if not result['repeat']: raise RuntimeError('repeat right-click missing')
        result['status']='PASS'; call('quit')
    except Exception as e:
        result['error']=str(e); raise
    finally:
        try:p.wait(timeout=5)
        except Exception:p.kill(); p.wait()
        err.close(); (out/'INPUT-INTEGRITY.json').write_text(json.dumps(result,indent=2)+'\n')
        try:q.unlink()
        except Exception:pass
if __name__=='__main__': main()
