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
    result={'status':'FAIL','gate':'r17_text_focus_persistence','iso_sha256':sha256(a.iso),'focused':False,'left_box':False,'sticky':False,'typed':False}
    if result['iso_sha256']!=a.expected_iso_sha: raise SystemExit('ISO identity mismatch')
    q=out/'qmp.sock'; ser=out/'serial.log'; err=(out/'qemu.stderr').open('wb')
    cmd=['qemu-system-x86_64','-machine','q35','-m','768M','-smp','2','-cpu','max','-accel','tcg,thread=single','-display','none','-no-reboot','-no-shutdown','-nic','none','-serial',f'file:{ser}','-qmp',f'unix:{q},server=on,wait=off','-drive',f'if=pflash,format=raw,readonly=on,file={a.ovmf}','-cdrom',a.iso,'-boot','d']
    (out/'qemu-command.json').write_text(json.dumps(cmd,indent=2)+'\n'); p=subprocess.Popen(cmd,stdout=subprocess.DEVNULL,stderr=err)
    try:
        for _ in range(600):
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
        call('qmp_capabilities'); mice=call('query-mice'); idx=next((m['index'] for m in mice if 'ps/2' in m['name'].lower() or 'ps2' in m['name'].lower()),None)
        if idx is None: raise RuntimeError('PS2 pointer missing')
        call('human-monitor-command',{'command-line':f'mouse_set {idx}'})
        for _ in range(1000):
            t=ser.read_text(errors='ignore') if ser.exists() else ''
            if 'FRAMES_V108_INPUT_TEST_RUNTIME_READY' in t and 'FRAMES_V108_PS2_ENABLE_OK' in t: break
            time.sleep(.1)
        else: raise RuntimeError('runtime readiness timeout')
        def rel(x=0,y=0):
            ev=[]
            if x: ev.append({'type':'rel','data':{'axis':'x','value':x}})
            if y: ev.append({'type':'rel','data':{'axis':'y','value':y}})
            if ev: call('input-send-event',{'events':ev})
        def btn(down): call('input-send-event',{'events':[{'type':'btn','data':{'down':down,'button':'left'}}]})
        def key(qcode):
            call('input-send-event',{'events':[{'type':'key','data':{'down':True,'key':{'type':'qcode','data':qcode}}}]}); time.sleep(.05)
            call('input-send-event',{'events':[{'type':'key','data':{'down':False,'key':{'type':'qcode','data':qcode}}}]}); time.sleep(.1)
        for _ in range(24): rel(-60,-60); time.sleep(.012)
        for _ in range(10): rel(10,0); time.sleep(.012)
        for _ in range(50): rel(0,10); time.sleep(.012)
        for _ in range(30):
            t=ser.read_text(errors='ignore') if ser.exists() else ''
            if 'FRAMES_V108_TEXT_IBEAM_OK' in t: break
            rel(0,5); time.sleep(.03)
        btn(True); time.sleep(.08); btn(False); time.sleep(.15); result['focused']=True
        for _ in range(5): rel(-20,-20); time.sleep(.04)
        result['left_box']=True
        key('a')
        deadline=time.time()+5
        while time.time()<deadline:
            t=ser.read_text(errors='ignore') if ser.exists() else ''
            result['sticky']='FRAMES_V108_TEXT_FOCUS_STICKY_OK' in t
            result['typed']='FRAMES_V108_KEYBOARD_TEXT_OK' in t
            if result['sticky'] and result['typed']: break
            time.sleep(.1)
        if not result['sticky']: raise RuntimeError('focus did not persist after pointer left text box')
        if not result['typed']: raise RuntimeError('typing did not remain routed to focused text box')
        result['status']='PASS'; call('quit')
    except Exception as e:
        result['error']=str(e); raise
    finally:
        try:p.wait(timeout=5)
        except Exception:p.kill(); p.wait()
        err.close(); (out/'FOCUS-PERSISTENCE.json').write_text(json.dumps(result,indent=2)+'\n')
if __name__=='__main__': main()
