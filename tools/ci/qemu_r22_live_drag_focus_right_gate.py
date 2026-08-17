#!/usr/bin/env python3
import argparse,hashlib,json,pathlib,socket,subprocess,time
from PIL import Image

def sha256(p):
    h=hashlib.sha256()
    with open(p,'rb') as f:
        for b in iter(lambda:f.read(1024*1024),b''): h.update(b)
    return h.hexdigest()

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--ovmf',required=True); ap.add_argument('--iso',required=True); ap.add_argument('--out',required=True); ap.add_argument('--expected-iso-sha',required=True)
    a=ap.parse_args(); out=pathlib.Path(a.out); out.mkdir(parents=True,exist_ok=True)
    result={'status':'FAIL','gate':'r22_live_drag_focus_right','iso_sha256':sha256(a.iso),'runtime_ready':False,'hover_no_repaint':False,'focus_transfer':False,'right_direct':False,'right_direct_marker_observed':False,'right_local_no_repaint':False,'dismiss_no_repaint':False,'repeat_no_repaint':False,'drag_motion_marker':False,'drag_live':False,'drag_commit':False,'drag_no_repaint':False}
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
            for _ in range(30): rel(-60,-60); time.sleep(.008)
        def goto(x,y):
            home(); cx=0; cy=0
            while cx<x:
                d=min(40,x-cx); rel(d,0); cx+=d; time.sleep(.012)
            while cy<y:
                d=min(40,y-cy); rel(0,d); cy+=d; time.sleep(.012)
        def click_left(x,y,hold=.04):
            goto(x,y); btn('left',True); time.sleep(hold); btn('left',False); time.sleep(.18)
        call('qmp_capabilities'); mice=call('query-mice'); idx=next((m['index'] for m in mice if 'ps/2' in m['name'].lower() or 'ps2' in m['name'].lower()),None)
        if idx is None: raise RuntimeError('PS2 pointer frontend missing')
        call('human-monitor-command',{'command-line':f'mouse_set {idx}'})
        deadline=time.time()+110
        while time.time()<deadline:
            t=text()
            if 'FRAMES_V108_INPUT_TEST_RUNTIME_READY' in t: result['runtime_ready']=True; break
            if p.poll() is not None: raise RuntimeError(f'qemu exited {p.returncode}')
            time.sleep(.1)
        if not result['runtime_ready']: raise RuntimeError('runtime readiness timeout')
        time.sleep(.4); t=text(); base_rep=t.count('FRAMES_V108_FULL_REPAINT_V120'); base_ctx=t.count('FRAMES_V108_DESKTOP_CONTEXT_OK')
        # Motion-only hover through the draggable title must remain repaint/context free.
        for _ in range(6):
            goto(120,175); rel(90,0); rel(-70,12); rel(35,-8); time.sleep(.05)
        t=text(); result['hover_no_repaint']=t.count('FRAMES_V108_FULL_REPAINT_V120')==base_rep and t.count('FRAMES_V108_DESKTOP_CONTEXT_OK')==base_ctx
        if not result['hover_no_repaint']: raise RuntimeError('hover changed repaint/context state')
        # Prove full-window live drag first, before focus or menu interactions can
        # influence custom-window state. Also retain the lower-level drag-state
        # marker so a failure identifies whether dispatch or presentation failed.
        drag_before_ppm=out/'R22-DRAG-BEFORE.ppm'; call('screendump',{'filename':str(drag_before_ppm)})
        goto(120,175); live_before=text().count('FRAMES_V108_DRAG_LIVE_V122_OK'); motion_before=text().count('FRAMES_V108_WINDOW_DRAG_OK'); commit_before=text().count('FRAMES_V108_DRAG_COMMIT_LOCAL_V121_OK'); btn('left',True); time.sleep(.05)
        for _ in range(10): rel(12,8); time.sleep(.035)
        drag_mid_ppm=out/'R22-DRAG-MID.ppm'; call('screendump',{'filename':str(drag_mid_ppm)})
        mid=text(); result['drag_motion_marker']=mid.count('FRAMES_V108_WINDOW_DRAG_OK')>motion_before; result['drag_live']=mid.count('FRAMES_V108_DRAG_LIVE_V122_OK')>live_before
        result['drag_marker_counts']={'motion_before':motion_before,'motion_mid':mid.count('FRAMES_V108_WINDOW_DRAG_OK'),'live_before':live_before,'live_mid':mid.count('FRAMES_V108_DRAG_LIVE_V122_OK')}
        if not result['drag_motion_marker']: raise RuntimeError('drag input state was not reached at clean initial window position')
        if not result['drag_live']: raise RuntimeError('drag state moved but full-window live present path was not reached')
        btn('left',False); time.sleep(.28); t=text(); result['drag_commit']=t.count('FRAMES_V108_DRAG_COMMIT_LOCAL_V121_OK')>commit_before; result['drag_no_repaint']=t.count('FRAMES_V108_FULL_REPAINT_V120')==base_rep
        if not result['drag_commit']: raise RuntimeError('live drag did not commit locally')
        if not result['drag_no_repaint']: raise RuntimeError('live drag/commit triggered full repaint')
        # Focus Input Test text box, then click the now-moved Drag Window. Derive
        # panel Y from the actual framebuffer height rather than assuming 768p.
        size_ppm=out/'R22-SIZE.ppm'; call('screendump',{'filename':str(size_ppm)})
        with Image.open(size_ppm) as sim:
            fb_w,fb_h=sim.size
        result['framebuffer']=[fb_w,fb_h]
        test_y=(fb_h-250) if fb_h>300 else 300
        text_y=test_y+80
        click_left(100,text_y)
        before=text().count('FRAMES_V108_FOCUS_TRANSFER_V122_OK')
        # The drag above moves the custom window by roughly +120,+80. Click well
        # inside its title to transfer focus away from Input Test.
        click_left(240,255)
        t=text(); result['focus_transfer']=t.count('FRAMES_V108_FOCUS_TRANSFER_V122_OK')==before+1
        if not result['focus_transfer']: raise RuntimeError('Input Test focus was not transferred on outside window click')
        if t.count('FRAMES_V108_FULL_REPAINT_V120')!=base_rep: raise RuntimeError('focus transfer triggered full repaint')
        # A short physical-scale right press/release must work; no artificial long dwell.
        goto(700,300); before_ctx=t.count('FRAMES_V108_DESKTOP_CONTEXT_OK'); before_direct=t.count('FRAMES_V108_RIGHT_DIRECT_V122_OK'); btn('right',True); time.sleep(.012); btn('right',False); time.sleep(.24); t=text()
        # QEMU's generic PS/2 frontend is not the physical Elantech-v4 decoder, so
        # the V122 raw-edge marker is informative here rather than mandatory. The
        # runtime proof is that a 12 ms press/release opens exactly one context menu.
        result['right_direct_marker_observed']=t.count('FRAMES_V108_RIGHT_DIRECT_V122_OK')>before_direct
        result['right_direct']=t.count('FRAMES_V108_DESKTOP_CONTEXT_OK')==before_ctx+1
        result['right_local_no_repaint']=result['right_direct'] and t.count('FRAMES_V108_FULL_REPAINT_V120')==base_rep and 'FRAMES_V108_CONTEXT_LOCAL_PRESENT_V121_OK' in t
        if not result['right_direct']: raise RuntimeError('short right press/release did not open exactly one context menu')
        if not result['right_local_no_repaint']: raise RuntimeError('right-click did not locally open context without repaint')
        click_left(500,520); t=text(); result['dismiss_no_repaint']='FRAMES_V108_CONTEXT_DISMISS_OK' in t and t.count('FRAMES_V108_FULL_REPAINT_V120')==base_rep
        if not result['dismiss_no_repaint']: raise RuntimeError('context dismiss failed or repainted')
        goto(720,330); c=t.count('FRAMES_V108_DESKTOP_CONTEXT_OK'); btn('right',True); time.sleep(.012); btn('right',False); time.sleep(.2); click_left(520,520); t=text(); result['repeat_no_repaint']=t.count('FRAMES_V108_DESKTOP_CONTEXT_OK')==c+1 and t.count('FRAMES_V108_FULL_REPAINT_V120')==base_rep
        if not result['repeat_no_repaint']: raise RuntimeError('repeat right-click cycle failed or repainted')
        result['status']='PASS'; call('quit')
    except Exception as e:
        result['error']=str(e); raise
    finally:
        try:p.wait(timeout=5)
        except Exception:p.kill(); p.wait()
        err.close(); (out/'R22-INTERACTION.json').write_text(json.dumps(result,indent=2)+'\n')
        try:q.unlink()
        except Exception:pass
if __name__=='__main__': main()
