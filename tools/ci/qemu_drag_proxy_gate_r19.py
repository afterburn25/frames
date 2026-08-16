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
    result={'status':'FAIL','gate':'r19_drag_proxy','iso_sha256':sha256(a.iso),'runtime_ready':False,'drag':False,'proxy':False,'context_during_drag':False}
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
        def home():
            for _ in range(24): rel(-60,-60); time.sleep(.012)
        def goto(x,y):
            home(); cx=0; cy=0
            while cx<x:
                d=min(40,x-cx); rel(d,0); cx+=d; time.sleep(.018)
            while cy<y:
                d=min(40,y-cy); rel(0,d); cy+=d; time.sleep(.018)
        call('qmp_capabilities'); mice=call('query-mice'); idx=next((m['index'] for m in mice if 'ps/2' in m['name'].lower() or 'ps2' in m['name'].lower()),None)
        if idx is None: raise RuntimeError('PS2 pointer frontend missing')
        call('human-monitor-command',{'command-line':f'mouse_set {idx}'})
        deadline=time.time()+110
        while time.time()<deadline:
            t=text()
            if 'FRAMES_V108_INPUT_TEST_RUNTIME_READY' in t and 'FRAMES_V108_TOUCHPAD_TAP_SELFTEST_OK' in t: result['runtime_ready']=True; break
            if p.poll() is not None: raise RuntimeError(f'qemu exited {p.returncode}')
            time.sleep(.1)
        if not result['runtime_ready']: raise RuntimeError('runtime readiness timeout')
        base_context=text().count('FRAMES_V108_DESKTOP_CONTEXT_OK')
        goto(120,175); btn('left',True); time.sleep(.08)
        for _ in range(10): rel(12,8); time.sleep(.05)
        t=text(); result['drag']='FRAMES_V108_WINDOW_DRAG_OK' in t; result['proxy']='FRAMES_V108_DRAG_PROXY_OK' in t; result['context_during_drag']=t.count('FRAMES_V108_DESKTOP_CONTEXT_OK')>base_context
        btn('left',False); time.sleep(.25)
        if not result['drag']: raise RuntimeError('window drag marker missing')
        if not result['proxy']: raise RuntimeError('drag proxy marker missing')
        if result['context_during_drag']: raise RuntimeError('context menu opened during left drag')
        result['status']='PASS'; call('quit')
    except Exception as e:
        result['error']=str(e); raise
    finally:
        try:p.wait(timeout=5)
        except Exception:p.kill(); p.wait()
        err.close(); (out/'DRAG-PROXY.json').write_text(json.dumps(result,indent=2)+'\n')
        try:q.unlink()
        except Exception:pass
if __name__=='__main__': main()
