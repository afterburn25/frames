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
    result={'status':'FAIL','gate':'r17_usb_keyboard_fallback','iso_sha256':sha256(a.iso),'runtime_ready':False,'keyboard_selected':False,'keyboard_report':False}
    if result['iso_sha256']!=a.expected_iso_sha: raise SystemExit('ISO identity mismatch')
    q=out/'qmp.sock'; ser=out/'serial.log'; err=(out/'qemu.stderr').open('wb')
    cmd=['qemu-system-x86_64','-machine','q35','-m','768M','-smp','2','-cpu','max','-accel','tcg,thread=single','-display','none','-no-reboot','-no-shutdown','-nic','none','-serial',f'file:{ser}','-qmp',f'unix:{q},server=on,wait=off','-drive',f'if=pflash,format=raw,readonly=on,file={a.ovmf}','-cdrom',a.iso,'-boot','d','-device','qemu-xhci,id=xhci','-device','usb-kbd,bus=xhci.0,port=1,id=usbkbd']
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
        call('qmp_capabilities')
        for _ in range(1200):
            t=ser.read_text(errors='ignore') if ser.exists() else ''
            result['runtime_ready']='FRAMES_V108_INPUT_TEST_RUNTIME_READY' in t
            result['keyboard_selected']='FRAMES_V108_USB_KEYBOARD_SELECTED_OK' in t
            if result['runtime_ready'] and result['keyboard_selected']: break
            if p.poll() is not None: raise RuntimeError(f'qemu exited {p.returncode}')
            time.sleep(.1)
        if not result['runtime_ready']: raise RuntimeError('runtime readiness timeout')
        if not result['keyboard_selected']: raise RuntimeError('USB keyboard fallback was not selected')
        def key(qcode):
            call('input-send-event',{'events':[{'type':'key','data':{'down':True,'key':{'type':'qcode','data':qcode}}}]}); time.sleep(.08)
            call('input-send-event',{'events':[{'type':'key','data':{'down':False,'key':{'type':'qcode','data':qcode}}}]}); time.sleep(.12)
        for _ in range(12):
            key('a'); t=ser.read_text(errors='ignore') if ser.exists() else ''
            if 'FRAMES_V108_USB_KEYBOARD_REPORT_OK' in t: result['keyboard_report']=True; break
        if not result['keyboard_report']: raise RuntimeError('USB keyboard interrupt report marker missing')
        result['status']='PASS'; call('quit')
    except Exception as e:
        result['error']=str(e); raise
    finally:
        try:p.wait(timeout=5)
        except Exception:p.kill(); p.wait()
        err.close(); (out/'USB-KEYBOARD.json').write_text(json.dumps(result,indent=2)+'\n')
        try:q.unlink()
        except Exception:pass
if __name__=='__main__': main()
