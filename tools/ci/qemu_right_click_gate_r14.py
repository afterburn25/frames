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
    result={'status':'FAIL','gate':'r14_ps2_right_click_context','iso_sha256':sha256(a.iso)}
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
        call('qmp_capabilities'); mice=call('query-mice'); (out/'query-mice.json').write_text(json.dumps(mice,indent=2)+'\n')
        idx=next((m['index'] for m in mice if 'ps/2' in m['name'].lower() or 'ps2' in m['name'].lower()),None)
        if idx is None: raise RuntimeError('PS2 pointer frontend missing')
        call('human-monitor-command',{'command-line':f'mouse_set {idx}'})
        for _ in range(800):
            t=ser.read_text(errors='ignore') if ser.exists() else ''
            if 'FRAMES_V108_INPUT_TEST_RUNTIME_READY' in t and 'FRAMES_V108_PS2_ENABLE_OK' in t: break
            time.sleep(.1)
        else: raise RuntimeError('runtime readiness timeout')
        for _ in range(4):
            call('input-send-event',{'events':[{'type':'rel','data':{'axis':'x','value':1}}]}); time.sleep(.06)
        ok=False
        for _ in range(8):
            call('input-send-event',{'events':[{'type':'btn','data':{'down':True,'button':'right'}}]}); time.sleep(.08)
            call('input-send-event',{'events':[{'type':'btn','data':{'down':False,'button':'right'}}]}); time.sleep(.08)
            t=ser.read_text(errors='ignore') if ser.exists() else ''
            if 'FRAMES_V108_RIGHT_CLICK_OK' in t: ok=True; break
        if not ok: raise RuntimeError('right-click context marker not reached')
        result.update(status='PASS',right_click_marker=True)
        call('quit')
    except Exception as e:
        result['error']=str(e); raise
    finally:
        try:p.wait(timeout=5)
        except Exception:p.kill(); p.wait()
        err.close(); (out/'RIGHT-CLICK.json').write_text(json.dumps(result,indent=2)+'\n')

if __name__=='__main__': main()
