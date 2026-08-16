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
    result={'status':'FAIL','gate':'r20_hover_rightclick','iso_sha256':sha256(a.iso),'runtime_ready':False,'hover_no_repaint':False,'hover_no_drag':False,'hover_no_context':False,'right_open':False,'right_dismiss':False,'right_repeat':False,'drag_proxy':False,'drag_no_context':False}
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
            if x:ev.append({'type':'rel','data':{'axis':'x','value':x}})
            if y:ev.append({'type':'rel','data':{'axis':'y','value':y}})
            if ev:call('input-send-event',{'events':ev})
        def btn(name,down):call('input-send-event',{'events':[{'type':'btn','data':{'down':down,'button':name}}]})
        def home():
            for _ in range(28): rel(-60,-60); time.sleep(.01)
        def goto(x,y):
            home(); cx=0; cy=0
            while cx<x:
                d=min(40,x-cx); rel(d,0); cx+=d; time.sleep(.015)
            while cy<y:
                d=min(40,y-cy); rel(0,d); cy+=d; time.sleep(.015)
        call('qmp_capabilities'); mice=call('query-mice'); idx=next((m['index'] for m in mice if 'ps/2' in m['name'].lower() or 'ps2' in m['name'].lower()),None)
        if idx is None: raise RuntimeError('PS2 pointer frontend missing')
        call('human-monitor-command',{'command-line':f'mouse_set {idx}'})
        deadline=time.time()+110
        while time.time()<deadline:
            t=text()
            if 'FRAMES_V108_INPUT_TEST_RUNTIME_READY' in t and 'FRAMES_V108_TAP_STATE_ISOLATED_OK' in t: result['runtime_ready']=True; break
            if p.poll() is not None: raise RuntimeError(f'qemu exited {p.returncode}')
            time.sleep(.1)
        if not result['runtime_ready']: raise RuntimeError('runtime readiness timeout')
        time.sleep(.4); t=text(); base_repaint=t.count('FRAMES_V108_FULL_REPAINT_V120'); base_drag=t.count('FRAMES_V108_DRAG_PROXY_OK'); base_ctx=t.count('FRAMES_V108_DESKTOP_CONTEXT_OK')
        # Hover repeatedly through the drag-window title without pressing any button.
        goto(60,120)
        for _ in range(6):
            goto(120,175); rel(80,0); rel(-60,10); rel(35,-8); time.sleep(.08)
        time.sleep(.25); t=text()
        result['hover_no_repaint']=t.count('FRAMES_V108_FULL_REPAINT_V120')==base_repaint
        result['hover_no_drag']=t.count('FRAMES_V108_DRAG_PROXY_OK')==base_drag
        result['hover_no_context']=t.count('FRAMES_V108_DESKTOP_CONTEXT_OK')==base_ctx
        if not result['hover_no_repaint']: raise RuntimeError('drag-window hover triggered full repaint')
        if not result['hover_no_drag']: raise RuntimeError('drag-window hover triggered drag proxy')
        if not result['hover_no_context']: raise RuntimeError('drag-window hover triggered context menu')
        # Intentional right press/release with a mechanical-scale hold should open exactly once.
        goto(720,300); before=text().count('FRAMES_V108_DESKTOP_CONTEXT_OK'); btn('right',True); time.sleep(.04); btn('right',False); time.sleep(.25); t=text()
        result['right_open']=t.count('FRAMES_V108_DESKTOP_CONTEXT_OK')==before+1 and 'FRAMES_V108_RIGHT_GESTURE_V120_OK' in t
        if not result['right_open']: raise RuntimeError('validated right-click did not open menu')
        # Left click outside dismisses.
        goto(500,520); btn('left',True); time.sleep(.04); btn('left',False); time.sleep(.25); t=text(); result['right_dismiss']='FRAMES_V108_CONTEXT_DISMISS_OK' in t
        if not result['right_dismiss']: raise RuntimeError('context menu did not dismiss')
        # Repeatability.
        goto(700,330); before=t.count('FRAMES_V108_DESKTOP_CONTEXT_OK'); btn('right',True); time.sleep(.04); btn('right',False); time.sleep(.25); t=text(); result['right_repeat']=t.count('FRAMES_V108_DESKTOP_CONTEXT_OK')==before+1 and 'FRAMES_V108_CONTEXT_REPEAT_OK' in t
        if not result['right_repeat']: raise RuntimeError('context menu did not reopen')
        goto(520,520); btn('left',True); time.sleep(.04); btn('left',False); time.sleep(.18)
        # Real left-button drag produces proxy but never context.
        before_ctx=text().count('FRAMES_V108_DESKTOP_CONTEXT_OK'); goto(120,175); btn('left',True); time.sleep(.06)
        for _ in range(10): rel(12,8); time.sleep(.04)
        t=text(); result['drag_proxy']=t.count('FRAMES_V108_DRAG_PROXY_OK')>base_drag; result['drag_no_context']=t.count('FRAMES_V108_DESKTOP_CONTEXT_OK')==before_ctx
        btn('left',False); time.sleep(.2)
        if not result['drag_proxy']: raise RuntimeError('left drag proxy not reached')
        if not result['drag_no_context']: raise RuntimeError('left drag opened context menu')
        result['status']='PASS'; call('quit')
    except Exception as e:
        result['error']=str(e); raise
    finally:
        try:p.wait(timeout=5)
        except Exception:p.kill(); p.wait()
        err.close(); (out/'R20-INTERACTION.json').write_text(json.dumps(result,indent=2)+'\n')
        try:q.unlink()
        except Exception:pass
if __name__=='__main__': main()
