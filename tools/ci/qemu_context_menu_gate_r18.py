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
    result={'status':'FAIL','gate':'r18_context_menu_behavior_r2','iso_sha256':sha256(a.iso),'runtime_ready':False,'opened':False,'hovered':False,'selected':False,'dismissed':False,'repeat':False,'outside_dismiss':False}
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
        def click(name): btn(name,True); time.sleep(.09); btn(name,False); time.sleep(.12)
        def wait_marker(marker,seconds=2.0):
            end=time.time()+seconds
            while time.time()<end:
                if marker in text(): return True
                if p.poll() is not None: raise RuntimeError(f'qemu exited {p.returncode}')
                time.sleep(.04)
            return False
        call('qmp_capabilities'); mice=call('query-mice'); (out/'query-mice.json').write_text(json.dumps(mice,indent=2)+'\n')
        idx=next((m['index'] for m in mice if 'ps/2' in m['name'].lower() or 'ps2' in m['name'].lower()),None)
        if idx is None: raise RuntimeError('PS2 pointer frontend missing')
        call('human-monitor-command',{'command-line':f'mouse_set {idx}'})
        deadline=time.time()+110
        while time.time()<deadline:
            t=text()
            if 'FRAMES_V108_INPUT_TEST_RUNTIME_READY' in t and 'FRAMES_V108_STABLE_INPUT_DIAG_OK' in t:
                result['runtime_ready']=True; break
            if p.poll() is not None: raise RuntimeError(f'qemu exited {p.returncode}')
            time.sleep(.1)
        if not result['runtime_ready']: raise RuntimeError('stable runtime readiness timeout')
        for _ in range(4): rel(1,0); time.sleep(.08)
        for _ in range(8):
            click('right')
            if wait_marker('FRAMES_V108_DESKTOP_CONTEXT_OK',.35): result['opened']=True; break
            rel(1,0); time.sleep(.08)
        if not result['opened']: raise RuntimeError('context open marker missing after retries')
        rel(20,20)
        result['hovered']=wait_marker('FRAMES_V108_CONTEXT_HOVER_OK',1.5)
        if not result['hovered']: raise RuntimeError('context hover marker missing')
        click('left')
        result['selected']=wait_marker('FRAMES_V108_CONTEXT_SELECT_OK',1.0)
        result['dismissed']=wait_marker('FRAMES_V108_CONTEXT_DISMISS_OK',1.0)
        if not result['selected'] or not result['dismissed']: raise RuntimeError('context selection/dismiss markers missing')
        for _ in range(8):
            click('right')
            if wait_marker('FRAMES_V108_CONTEXT_REPEAT_OK',.35): result['repeat']=True; break
            rel(1,0); time.sleep(.08)
        if not result['repeat']: raise RuntimeError('repeat context-open marker missing')
        for _ in range(3): rel(-80,-80); time.sleep(.05)
        click('left')
        result['outside_dismiss']=wait_marker('FRAMES_V108_CONTEXT_OUTSIDE_DISMISS_OK',1.0)
        if not result['outside_dismiss']: raise RuntimeError('outside dismiss marker missing')
        result['status']='PASS'; call('quit')
    except Exception as e:
        result['error']=str(e); raise
    finally:
        try:p.wait(timeout=5)
        except Exception:p.kill(); p.wait()
        err.close(); (out/'CONTEXT-MENU.json').write_text(json.dumps(result,indent=2)+'\n')
        try:q.unlink()
        except Exception:pass
if __name__=='__main__': main()
