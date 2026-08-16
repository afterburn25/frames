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
    result={'status':'FAIL','gate':'v108_usb_hub_multichild_r17','iso_sha256':sha256(a.iso),'runtime_ready':False,'hub_found':False,'hid_children_seen':0,'hub_child_hid':False,'usb_live_report':False,'usb_gui_cursor':False}
    if result['iso_sha256']!=a.expected_iso_sha: raise SystemExit('ISO identity mismatch')
    qmp=out/'qmp.sock'; serial=out/'serial.log'; stderr=(out/'qemu.stderr').open('wb')
    cmd=['qemu-system-x86_64','-machine','q35','-m','768M','-smp','2','-cpu','max','-accel','tcg,thread=single','-display','none','-no-reboot','-no-shutdown','-nic','none','-serial',f'file:{serial}','-qmp',f'unix:{qmp},server=on,wait=off','-drive',f'if=pflash,format=raw,readonly=on,file={a.ovmf}','-cdrom',a.iso,'-boot','d','-device','qemu-xhci,id=xhci','-device','usb-hub,bus=xhci.0,port=1,id=hub','-device','usb-kbd,bus=xhci.0,port=1.1,id=usbkbd','-device','usb-mouse,bus=xhci.0,port=1.2,id=usbmouse']
    (out/'qemu-command.json').write_text(json.dumps(cmd,indent=2)+'\n'); p=subprocess.Popen(cmd,stdout=subprocess.DEVNULL,stderr=stderr)
    try:
        deadline=time.time()+25
        while time.time()<deadline and not qmp.exists():
            if p.poll() is not None: raise RuntimeError(f'qemu exited {p.returncode}')
            time.sleep(.05)
        if not qmp.exists(): raise RuntimeError('qmp timeout')
        s=socket.socket(socket.AF_UNIX,socket.SOCK_STREAM); s.connect(str(qmp)); f=s.makefile('rwb',0); json.loads(f.readline())
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
        deadline=time.time()+100
        while time.time()<deadline:
            txt=serial.read_text(errors='ignore') if serial.exists() else ''
            if 'FRAMES_V108_INPUT_TEST_RUNTIME_READY' in txt: result['runtime_ready']=True; break
            if p.poll() is not None: break
            time.sleep(.15)
        if not result['runtime_ready']: raise RuntimeError('runtime readiness timeout')
        for _ in range(160):
            call('input-send-event',{'events':[{'type':'rel','data':{'axis':'x','value':6}},{'type':'rel','data':{'axis':'y','value':3}}]}); time.sleep(.05)
            txt=serial.read_text(errors='ignore') if serial.exists() else ''
            result['hub_found']='FRAMES_USB_HUB_FOUND' in txt
            result['hid_children_seen']=txt.count('FRAMES_USB_HID_FOUND')
            result['hub_child_hid']='FRAMES_USB_HUB_CHILD_HID_OK' in txt
            result['usb_live_report']='FRAMES_V108_USB_LIVE_REPORT_OK' in txt
            result['usb_gui_cursor']='FRAMES_V108_USB_GUI_CURSOR_OK' in txt
            if result['hub_found'] and result['hid_children_seen']>=2 and result['hub_child_hid'] and result['usb_live_report'] and result['usb_gui_cursor']: break
        if not result['hub_found']: raise RuntimeError('hub not discovered')
        if result['hid_children_seen']<2: raise RuntimeError('keyboard+mouse HID children were not both enumerated')
        if not result['hub_child_hid']: raise RuntimeError('mouse HID child was not configured')
        if not result['usb_live_report']: raise RuntimeError('USB mouse report marker missing')
        if not result['usb_gui_cursor']: raise RuntimeError('USB mouse did not reach GUI cursor')
        result['status']='PASS'; call('quit')
    except Exception as e:
        result['error']=str(e); raise
    finally:
        try:p.wait(timeout=5)
        except Exception:p.kill(); p.wait()
        stderr.close(); (out/'MULTICHILD-R17.json').write_text(json.dumps(result,indent=2)+'\n')
        try:qmp.unlink()
        except Exception:pass
if __name__=='__main__': main()
