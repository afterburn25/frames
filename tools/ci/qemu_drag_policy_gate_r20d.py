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
    result={'status':'FAIL','gate':'r20d_drag_policy_isolation','iso_sha256':sha256(a.iso),'runtime_ready':False,'policy_selftest':False,'hover_clean':False,'left_down_clean':False,'release_clean':False,'context_absent':False}
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
        def count(m): return text().count(m)
        def rel(x=0,y=0):
            ev=[]
            if x: ev.append({'type':'rel','data':{'axis':'x','value':x}})
            if y: ev.append({'type':'rel','data':{'axis':'y','value':y}})
            if ev: call('input-send-event',{'events':ev})
        def btn(name,down): call('input-send-event',{'events':[{'type':'btn','data':{'down':down,'button':name}}]})
        def home():
            for _ in range(24): rel(-60,-60); time.sleep(.012)
        call('qmp_capabilities'); mice=call('query-mice'); idx=next((m['index'] for m in mice if 'ps/2' in m['name'].lower() or 'ps2' in m['name'].lower()),None)
        if idx is None: raise RuntimeError('PS2 pointer frontend missing')
        call('human-monitor-command',{'command-line':f'mouse_set {idx}'})
        deadline=time.time()+110
        while time.time()<deadline:
            t=text()
            if 'FRAMES_V108_INPUT_TEST_RUNTIME_READY' in t and 'FRAMES_V108_STABLE_INPUT_DIAG_OK' in t:
                result['runtime_ready']=True
                result['policy_selftest']='FRAMES_V108_DRAG_POLICY_SELFTEST_OK' in t
                break
            if p.poll() is not None: raise RuntimeError(f'qemu exited {p.returncode}')
            time.sleep(.1)
        if not result['runtime_ready']: raise RuntimeError('runtime readiness timeout')
        if not result['policy_selftest']: raise RuntimeError('GUI drag policy selftest marker missing')
        home(); time.sleep(.25)
        base_full=count('FRAMES_V108_FULL_REPAINT_V120'); base_ctx=count('FRAMES_V108_DESKTOP_CONTEXT_OK'); base_arm=count('FRAMES_V108_DRAG_ARM_OK'); base_drag=count('FRAMES_V108_WINDOW_DRAG_OK')
        cx=0; cy=0
        while cx<120:
            d=min(20,120-cx); rel(d,0); cx+=d; time.sleep(.035)
        while cy<175:
            d=min(20,175-cy); rel(0,d); cy+=d; time.sleep(.035)
        time.sleep(.30)
        result['hover_clean']=(count('FRAMES_V108_FULL_REPAINT_V120')==base_full and count('FRAMES_V108_DRAG_ARM_OK')==base_arm and count('FRAMES_V108_WINDOW_DRAG_OK')==base_drag)
        if not result['hover_clean']: raise RuntimeError('hovering drag title caused repaint or drag activation')
        btn('left',True); time.sleep(.20)
        result['left_down_clean']=(count('FRAMES_V108_FULL_REPAINT_V120')==base_full and count('FRAMES_V108_DRAG_ARM_OK')==base_arm and count('FRAMES_V108_WINDOW_DRAG_OK')==base_drag)
        if not result['left_down_clean']: raise RuntimeError('left-down alone activated drag/repaint')
        btn('left',False); time.sleep(.30)
        result['release_clean']=count('FRAMES_V108_FULL_REPAINT_V120')==base_full
        result['context_absent']=count('FRAMES_V108_DESKTOP_CONTEXT_OK')==base_ctx
        if not result['release_clean']: raise RuntimeError('click-without-drag triggered full desktop repaint')
        if not result['context_absent']: raise RuntimeError('context menu opened during hover/left-click isolation')
        result['status']='PASS'; call('quit')
    except Exception as e:
        result['error']=str(e); raise
    finally:
        try:p.wait(timeout=5)
        except Exception:p.kill(); p.wait()
        err.close(); (out/'DRAG-POLICY.json').write_text(json.dumps(result,indent=2)+'\n')
        try:q.unlink()
        except Exception:pass
if __name__=='__main__': main()
