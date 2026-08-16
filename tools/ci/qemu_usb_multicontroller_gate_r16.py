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
    result={'status':'FAIL','gate':'r16_usb_multicontroller','iso_sha256':sha256(a.iso),'fallback':False,'usb_live':False,'usb_cursor':False}
    if result['iso_sha256']!=a.expected_iso_sha: raise SystemExit('ISO identity mismatch')
    stick=out/'usb-stick.img'; stick.write_bytes(b'\0'*(1024*1024))
    q=out/'qmp.sock'; ser=out/'serial.log'; err=(out/'qemu.stderr').open('wb')
    cmd=['qemu-system-x86_64','-machine','q35','-m','768M','-smp','2','-cpu','max','-accel','tcg,thread=single','-display','none','-no-reboot','-no-shutdown','-nic','none','-serial',f'file:{ser}','-qmp',f'unix:{q},server=on,wait=off','-drive',f'if=pflash,format=raw,readonly=on,file={a.ovmf}','-cdrom',a.iso,'-boot','d','-device','qemu-xhci,id=xhci1','-drive',f'if=none,id=stick,file={stick},format=raw,readonly=on','-device','usb-storage,drive=stick,bus=xhci1.0,port=1','-device','qemu-xhci,id=xhci2','-device','usb-mouse,bus=xhci2.0,port=1']
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
        idx=next((m['index'] for m in mice if ('usb' in m['name'].lower() or 'hid' in m['name'].lower()) and 'ps/2' not in m['name'].lower()),None)
        if idx is None: raise RuntimeError('USB mouse frontend missing')
        call('human-monitor-command',{'command-line':f'mouse_set {idx}'})
        for _ in range(1100):
            t=ser.read_text(errors='ignore') if ser.exists() else ''
            if 'FRAMES_V108_INPUT_TEST_RUNTIME_READY' in t: break
            if p.poll() is not None: raise RuntimeError(f'qemu exited {p.returncode}')
            time.sleep(.1)
        else: raise RuntimeError('runtime readiness timeout')
        for _ in range(160):
            call('input-send-event',{'events':[{'type':'rel','data':{'axis':'x','value':5}},{'type':'rel','data':{'axis':'y','value':2}}]}); time.sleep(.05)
            t=ser.read_text(errors='ignore') if ser.exists() else ''
            result['fallback']='FRAMES_V108_USB_CONTROLLER_FALLBACK_OK' in t
            result['usb_live']='FRAMES_V108_USB_LIVE_REPORT_OK' in t
            result['usb_cursor']='FRAMES_V108_USB_GUI_CURSOR_OK' in t
            if all((result['fallback'],result['usb_live'],result['usb_cursor'])): break
        if not result['fallback']: raise RuntimeError('second xHCI fallback marker missing')
        if not result['usb_live']: raise RuntimeError('USB report marker missing')
        if not result['usb_cursor']: raise RuntimeError('USB GUI cursor marker missing')
        result['status']='PASS'; call('quit')
    except Exception as e:
        result['error']=str(e); raise
    finally:
        try:p.wait(timeout=5)
        except Exception:p.kill(); p.wait()
        err.close(); (out/'USB-MULTICONTROLLER.json').write_text(json.dumps(result,indent=2)+'\n')

if __name__=='__main__': main()
