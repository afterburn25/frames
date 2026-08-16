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
    result={'status':'FAIL','gate':'r14b_text_edit_ibeam','iso_sha256':sha256(a.iso),'runtime_ready':False,'ibeam':False,'caret_blink':False,'left':False,'right':False,'delete':False,'backspace':False,'edit_sequence':False}
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
        def hmp(cmd): return call('human-monitor-command',{'command-line':cmd})
        call('qmp_capabilities'); mice=call('query-mice'); (out/'query-mice.json').write_text(json.dumps(mice,indent=2)+'\n')
        idx=next((m['index'] for m in mice if 'ps/2' in m['name'].lower() or 'ps2' in m['name'].lower()),None)
        if idx is None: raise RuntimeError('PS2 pointer frontend missing')
        hmp(f'mouse_set {idx}')
        for _ in range(1000):
            t=ser.read_text(errors='ignore') if ser.exists() else ''
            if 'FRAMES_V108_INPUT_TEST_RUNTIME_READY' in t and 'FRAMES_V108_PS2_ENABLE_OK' in t:
                result['runtime_ready']=True; break
            time.sleep(.1)
        if not result['runtime_ready']: raise RuntimeError('runtime readiness timeout')
        def rel(dx,dy,delay=.025):
            call('input-send-event',{'events':[{'type':'rel','data':{'axis':'x','value':dx}},{'type':'rel','data':{'axis':'y','value':dy}}]}); time.sleep(delay)
        # Standard-PS/2 physical conversion is deliberately bounded/scaled. Large synthetic deltas
        # can be rejected, so walk from the deterministic initial cursor (~396,290) into the
        # 1280x800 INPUT TEST textbox (~x 60..640, y 556..604) using ordinary small packets.
        for _ in range(78): rel(-6,0)
        for _ in range(73): rel(0,6)
        hmp(f'screendump {out}/HOVER.ppm')
        # Hover must switch to I-beam before focus/click.
        for _ in range(60):
            t=ser.read_text(errors='ignore') if ser.exists() else ''
            if 'FRAMES_V108_IBEAM_OK' in t: result['ibeam']=True; break
            time.sleep(.05)
        if not result['ibeam']:
            # Search a small rectangle around the expected textbox location using valid PS/2-sized moves.
            for dy in (-6,6,-6,6):
                for _ in range(8):
                    rel(6,dy)
                    t=ser.read_text(errors='ignore') if ser.exists() else ''
                    if 'FRAMES_V108_IBEAM_OK' in t: result['ibeam']=True; break
                if result['ibeam']: break
        call('input-send-event',{'events':[{'type':'btn','data':{'down':True,'button':'left'}}]}); time.sleep(.08)
        call('input-send-event',{'events':[{'type':'btn','data':{'down':False,'button':'left'}}]}); time.sleep(.12)
        # Exact editing proof: ABC -> Left -> Left -> Right -> Delete -> Backspace == A.
        for key in ('a','b','c','left','left','right','delete','backspace'):
            hmp('sendkey '+key); time.sleep(.18)
        deadline=time.time()+6
        while time.time()<deadline:
            t=ser.read_text(errors='ignore') if ser.exists() else ''
            result['ibeam']='FRAMES_V108_IBEAM_OK' in t
            result['caret_blink']='FRAMES_V108_CARET_BLINK_OK' in t
            result['left']='FRAMES_V108_TEXT_LEFT_OK' in t
            result['right']='FRAMES_V108_TEXT_RIGHT_OK' in t
            result['delete']='FRAMES_V108_TEXT_DELETE_OK' in t
            result['backspace']='FRAMES_V108_TEXT_BACKSPACE_OK' in t
            result['edit_sequence']='FRAMES_V108_TEXT_EDIT_SEQUENCE_OK' in t
            if all(result[k] for k in ('ibeam','caret_blink','left','right','delete','backspace','edit_sequence')): break
            time.sleep(.1)
        hmp(f'screendump {out}/FINAL.ppm')
        if not all(result[k] for k in ('ibeam','caret_blink','left','right','delete','backspace','edit_sequence')):
            raise RuntimeError('missing text-edit/I-beam runtime proof')
        result['status']='PASS'; call('quit')
    except Exception as e:
        result['error']=str(e); raise
    finally:
        try:p.wait(timeout=5)
        except Exception:p.kill(); p.wait()
        err.close(); (out/'TEXT-EDIT.json').write_text(json.dumps(result,indent=2)+'\n')
        try:q.unlink()
        except Exception:pass

if __name__=='__main__': main()
