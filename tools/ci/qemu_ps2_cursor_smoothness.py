#!/usr/bin/env python3
import argparse, hashlib, json, pathlib, socket, statistics, subprocess, time
from PIL import Image

WHITE=(244,247,251)
CURSOR_PATTERN=[(1,1),(1,2),(1,3),(1,4),(1,5),(3,5),(4,5),(1,6),(1,7),(1,8),(5,8),(6,8),(1,9),(1,10),(1,11),(1,12),(1,13)]
OVERLAY_X=850; OVERLAY_Y=205

def sha256(path):
    h=hashlib.sha256()
    with open(path,'rb') as f:
        for b in iter(lambda:f.read(1024*1024),b''): h.update(b)
    return h.hexdigest()

def locate_cursor(im,cx,cy,radius=20):
    cand=[]
    for y in range(max(0,cy-radius),min(im.height-16,cy+radius)+1):
        for x in range(max(0,cx-radius),min(im.width-8,cx+radius)+1):
            if all(im.getpixel((x+dx,y+dy))==WHITE for dx,dy in CURSOR_PATTERN):
                wc=sum(1 for yy in range(y,y+16) for xx in range(x,x+8) if im.getpixel((xx,yy))==WHITE)
                cand.append((abs(x-cx)+abs(y-cy),abs(wc-17),x,y,wc))
    if not cand: return None
    cand.sort(); return (cand[0][2],cand[0][3])

def initial_cursor(im):
    return locate_cursor(im,396,290,120)

def frame_delta(a,b):
    pts=[]
    for y in range(a.height):
        for x in range(a.width):
            if x>=OVERLAY_X and y<OVERLAY_Y: continue
            if a.getpixel((x,y))!=b.getpixel((x,y)): pts.append((x,y))
    if not pts:return 0,None
    return len(pts),[min(x for x,y in pts),min(y for x,y in pts),max(x for x,y in pts),max(y for x,y in pts)]

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--ovmf',required=True); ap.add_argument('--iso',required=True); ap.add_argument('--out',required=True); ap.add_argument('--expected-iso-sha',required=True)
    a=ap.parse_args(); out=pathlib.Path(a.out); out.mkdir(parents=True,exist_ok=True)
    result={'status':'FAIL','iso_sha256':sha256(a.iso),'gate':'ps2_cursor_smoothness_v1','steps':[]}
    if result['iso_sha256']!=a.expected_iso_sha: raise SystemExit('unexpected ISO SHA '+result['iso_sha256'])
    q=out/'qmp.sock'; ser=out/'serial.log'; err=(out/'qemu.stderr').open('wb')
    cmd=['qemu-system-x86_64','-machine','q35','-m','768M','-smp','2','-cpu','max','-accel','tcg,thread=single','-display','none','-no-reboot','-no-shutdown','-nic','none','-serial',f'file:{ser}','-qmp',f'unix:{q},server=on,wait=off','-drive',f'if=pflash,format=raw,readonly=on,file={a.ovmf}','-cdrom',a.iso,'-boot','d']
    (out/'qemu-command.json').write_text(json.dumps(cmd,indent=2)+'\n')
    p=subprocess.Popen(cmd,stdout=subprocess.DEVNULL,stderr=err)
    try:
        for _ in range(500):
            if q.exists():break
            time.sleep(.05)
        if not q.exists():raise RuntimeError('qmp timeout')
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
        if idx is None:raise RuntimeError('PS/2 frontend missing')
        call('human-monitor-command',{'command-line':f'mouse_set {idx}'})
        ready=['FRAMES_V108_INPUT_TEST_RUNTIME_READY','FRAMES_V108_PS2_ENABLE_OK','FRAMES_V108_STABLE_INPUT_DIAG_OK']
        for _ in range(800):
            t=ser.read_text(errors='ignore') if ser.exists() else ''
            if all(m in t for m in ready):break
            time.sleep(.1)
        else:raise RuntimeError('stable PS/2 runtime marker timeout')
        def capture(name,save=True):
            ppm=out/(name+'.ppm'); call('screendump',{'filename':str(ppm)}); im=Image.open(ppm).convert('RGB')
            if save:im.save(out/(name+'.png'))
            ppm.unlink(); return im
        time.sleep(.25)
        idle0=capture('IDLE-0'); pos0=initial_cursor(idle0)
        if pos0 is None:raise RuntimeError('initial cursor template not found')
        time.sleep(.25); idle1=capture('IDLE-1'); pos1=locate_cursor(idle1,pos0[0],pos0[1],4)
        if pos1!=pos0:raise RuntimeError(f'pre-input cursor drift: {pos0}->{pos1}')
        idle_changed,idle_bbox=frame_delta(idle0,idle1)
        if idle_changed>4:raise RuntimeError(f'pre-input framebuffer not stable: {idle_changed} pixels')
        result['pre_input_position']=list(pos0); result['pre_input_idle_changed_pixels']=idle_changed; result['pre_input_idle_bbox']=idle_bbox

        # Warm the new two-packet lock without making warm-up part of the smoothness statistics.
        for _ in range(3):
            call('input-send-event',{'events':[{'type':'rel','data':{'axis':'x','value':1}}]}); time.sleep(.08)
        warm=capture('WARMED'); warm_pos=locate_cursor(warm,pos0[0]+2,pos0[1],8)
        if warm_pos is None:raise RuntimeError('cursor not found after parser warm-up')
        if not (1<=warm_pos[0]-pos0[0]<=3 and abs(warm_pos[1]-pos0[1])<=1):raise RuntimeError(f'unexpected warm-up displacement {pos0}->{warm_pos}')
        time.sleep(.2); warm_idle=capture('WARMED-IDLE'); warm_idle_pos=locate_cursor(warm_idle,warm_pos[0],warm_pos[1],3)
        if warm_idle_pos!=warm_pos:raise RuntimeError('cursor drift immediately after warm-up')
        wc,_=frame_delta(warm,warm_idle)
        if wc>4:raise RuntimeError('framebuffer still changing after warm-up')
        baseline=warm_idle; baseline_pos=warm_pos; current=baseline; current_pos=baseline_pos
        result['measurement_origin']=list(baseline_pos)

        frame_index=0
        segment_values={}
        max_changed=0; max_jump=0; max_cross=0
        def send_step(dx,dy,segment,requested):
            nonlocal current,current_pos,frame_index,max_changed,max_jump,max_cross
            events=[]
            if dx!=0:events.append({'type':'rel','data':{'axis':'x','value':dx}})
            if dy!=0:events.append({'type':'rel','data':{'axis':'y','value':dy}})
            call('input-send-event',{'events':events})
            expected=(current_pos[0]+dx,current_pos[1]+dy)
            found=None; im=None
            for _ in range(16):
                time.sleep(.05); im=capture('TEMP',save=False)
                found=locate_cursor(im,expected[0],expected[1],10)
                if found is None:found=locate_cursor(im,current_pos[0],current_pos[1],12)
                if found is not None and found!=current_pos:break
            if found is None or found==current_pos:raise RuntimeError(f'cursor did not move for {segment} request {(dx,dy)}')
            frame_index+=1; name=f'STEP-{frame_index:02d}-{segment}'; im.save(out/(name+'.png'))
            changed,bbox=frame_delta(current,im); adx=found[0]-current_pos[0]; ady=found[1]-current_pos[1]
            primary=adx if dx!=0 else ady; cross=ady if dx!=0 else adx; req=dx if dx!=0 else dy
            jump=max(abs(adx),abs(ady)); max_changed=max(max_changed,changed); max_jump=max(max_jump,jump); max_cross=max(max_cross,abs(cross))
            lo=max(1,abs(req)-1); hi=abs(req)+1
            if req>0 and primary<=0:raise RuntimeError(f'wrong direction in {segment}: request {req}, actual {primary}')
            if req<0 and primary>=0:raise RuntimeError(f'wrong direction in {segment}: request {req}, actual {primary}')
            if not (lo<=abs(primary)<=hi):raise RuntimeError(f'non-proportional step in {segment}: request {req}, actual {primary}')
            if abs(cross)>1:raise RuntimeError(f'cross-axis drift in {segment}: {cross}')
            if jump>7:raise RuntimeError(f'cursor jump too large in {segment}: {(adx,ady)}')
            if changed>500:raise RuntimeError(f'non-local redraw during {segment}: {changed} pixels')
            if bbox is None:raise RuntimeError('cursor moved but no framebuffer delta found')
            bw=bbox[2]-bbox[0]+1; bh=bbox[3]-bbox[1]+1
            if bw>32 or bh>32:raise RuntimeError(f'non-local movement bbox during {segment}: {bbox}')
            row={'segment':segment,'requested':[dx,dy],'before':list(current_pos),'after':list(found),'actual':[adx,ady],'changed_pixels':changed,'bbox':bbox}
            result['steps'].append(row); segment_values.setdefault(segment,[]).append(abs(primary)); current=im; current_pos=found

        for _ in range(8):send_step(1,0,'micro_right',1)
        for _ in range(8):send_step(-1,0,'micro_left',-1)
        for _ in range(8):send_step(0,3,'normal_down',3)
        for _ in range(8):send_step(0,-3,'normal_up',-3)
        for qv in (1,2,3,4,5):send_step(qv,0,'ramp_right',qv)
        for qv in (-5,-4,-3,-2,-1):send_step(qv,0,'ramp_left',qv)

        for seg in ('micro_right','micro_left','normal_down','normal_up'):
            vals=segment_values[seg]
            if max(vals)-min(vals)>1:raise RuntimeError(f'constant-step jitter too high in {seg}: {vals}')
        rr=segment_values['ramp_right']; rl=segment_values['ramp_left']
        if any(rr[i+1]<rr[i] for i in range(len(rr)-1)):raise RuntimeError(f'ramp-right proportionality failed: {rr}')
        if any(rl[i+1]>rl[i] for i in range(len(rl)-1)):raise RuntimeError(f'ramp-left proportionality failed: {rl}')

        return_error=[current_pos[0]-baseline_pos[0],current_pos[1]-baseline_pos[1]]
        if abs(return_error[0])>2 or abs(return_error[1])>2:raise RuntimeError(f'round-trip cursor error too high: {return_error}')

        idle_positions=[]; last=current
        for i in range(3):
            time.sleep(.25); im=capture(f'POST-IDLE-{i}'); pos=locate_cursor(im,current_pos[0],current_pos[1],3)
            if pos is None:raise RuntimeError('cursor missing during post-test idle check')
            ch,_=frame_delta(last,im)
            if pos!=current_pos or ch>4:raise RuntimeError(f'post-test idle drift: pos={pos}, expected={current_pos}, changed={ch}')
            idle_positions.append(list(pos)); last=im

        t=ser.read_text(errors='ignore')
        required=['FRAMES_V108_PS2_PACKET_OK','FRAMES_V108_PS2_GUI_CURSOR_OK','FRAMES_V108_PHYSICAL_CURSOR_VISIBLE_OK']
        if not all(m in t for m in required):raise RuntimeError('required PS/2 runtime markers missing after smoothness run')
        result.update(status='PASS',final_position=list(current_pos),return_error=return_error,post_idle_positions=idle_positions,max_changed_pixels_outside_overlay=max_changed,max_single_step_jump=max_jump,max_cross_axis_drift=max_cross,segment_primary_steps=segment_values)
        call('quit')
    except Exception as e:
        result['error']=str(e); raise
    finally:
        try:p.wait(timeout=5)
        except Exception:
            p.kill(); p.wait()
        err.close(); (out/'SMOOTHNESS.json').write_text(json.dumps(result,indent=2)+'\n')

if __name__=='__main__':main()
