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
    result={'status':'FAIL','gate':'r16_desktop_interaction','iso_sha256':sha256(a.iso),'tap_selftest':False,'bottom':False,'context':False,'drag':False}
    if result['iso_sha256']!=a.expected_iso_sha: raise SystemExit('ISO identity mismatch')
    q=out/'qmp.sock'; ser=out/'serial.log'; err=(out/'qemu.stderr').open('wb')
    cmd=['qemu-system-x86_64','-machine','q35','-m','768M','-smp','2','-cpu','max','-accel','tcg,thread=single','-display','none','-no-reboot','-no-shutdown','-nic','none','-serial',f'file:{ser}','-qmp',f'unix:{q},server=on,wait=off','-drive',f'if=pflash,format=raw,readonly=on,file={a.ovmf}','-cdrom',a.iso,'-boot','d']
    (out/'qemu-command.json').write_text(json.dumps(cmd,indent=2)+'\n'); p=subprocess.Popen(cmd,stdout=subprocess.DEVNULL,stderr=err)
    try:
        for _ in range(500):
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
        call('qmp_capabilities'); mice=call('query-mice'); (out/'query-mice.json').write_text(json.dumps(mice,indent=2)+'\n')
        idx=next((m['index'] for m in mice if 'ps/2' in m['name'].lower() or 'ps2' in m['name'].lower()),None)
        if idx is None: raise RuntimeError('PS2 pointer frontend missing')
        call('human-monitor-command',{'command-line':f'mouse_set {idx}'})
        for _ in range(1000):
            t=ser.read_text(errors='ignore') if ser.exists() else ''
            if 'FRAMES_V108_INPUT_TEST_RUNTIME_READY' in t and 'FRAMES_V108_TOUCHPAD_TAP_SELFTEST_OK' in t: break
            if p.poll() is not None: raise RuntimeError(f'qemu exited {p.returncode}')
            time.sleep(.1)
        else: raise RuntimeError('runtime/tap selftest readiness timeout')
        result['tap_selftest']=True
        def rel(x=0,y=0):
            ev=[]
            if x: ev.append({'type':'rel','data':{'axis':'x','value':x}})
            if y: ev.append({'type':'rel','data':{'axis':'y','value':y}})
            if ev: call('input-send-event',{'events':ev})
        def btn(name,down): call('input-send-event',{'events':[{'type':'btn','data':{'down':down,'button':name}}]})
        for _ in range(12): rel(-120,-120); time.sleep(.02)
        for _ in range(2): rel(60,80); time.sleep(.03)
        btn('right',True); time.sleep(.08); btn('right',False); time.sleep(.12)
        t=ser.read_text(errors='ignore'); result['context']='FRAMES_V108_DESKTOP_CONTEXT_OK' in t
        btn('left',True); time.sleep(.05); btn('left',False); time.sleep(.08)
        for _ in range(12): rel(-120,-120); time.sleep(.02)
        rel(120,120); time.sleep(.03); rel(0,55); time.sleep(.05)
        btn('left',True); time.sleep(.08)
        for _ in range(6): rel(15,10); time.sleep(.05)
        btn('left',False); time.sleep(.15)
        t=ser.read_text(errors='ignore'); result['drag']='FRAMES_V108_WINDOW_DRAG_OK' in t
        for _ in range(12): rel(0,120); time.sleep(.03)
        t=ser.read_text(errors='ignore'); result['bottom']='FRAMES_V108_POINTER_BOTTOM_OK' in t
        if not result['context']: raise RuntimeError('desktop context marker missing')
        if not result['drag']: raise RuntimeError('window drag marker missing')
        if not result['bottom']: raise RuntimeError('bottom-edge marker missing')
        result['status']='PASS'; call('quit')
    except Exception as e:
        result['error']=str(e); raise
    finally:
        try:p.wait(timeout=5)
        except Exception:p.kill(); p.wait()
        err.close(); (out/'DESKTOP-INTERACTION.json').write_text(json.dumps(result,indent=2)+'\n')

if __name__=='__main__': main()
