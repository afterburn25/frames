#!/usr/bin/env python3
"""
Frames 0.9.98 Pointer Diagnostics CI v2.1

Deterministic QEMU pointer tester:
- PS/2 relative mouse lane
- USB HID boot mouse over XHCI lane
- exact crosshair-coordinate assertions at every checkpoint
- framebuffer OCR of Frames pointer diagnostic counters
- packet/report invariants
- deterministic stress/fuzz input
- USB transfer PCAP
- best-effort QEMU record/replay capture on failure
"""
import argparse, json, os, pathlib, random, socket, subprocess, sys, time, hashlib

GLYPH = {
    "0":15629733422,"1":15170933124,"2":33558693422,"3":32247317566,
    "4":2247698626,"5":32247857695,"6":15621636622,"7":8866891839,
    "8":15621113390,"9":15067498030,
    "A":18842895918,"B":32801506878,"C":16660316687,
    "D":32801080894,"E":33840644639,"F":17734517279,
}
ROWDIV=[1,32,1024,32768,1048576,33554432,1073741824]
BITDIV=[16,8,4,2,1]

FIELD_POS = {
    "SRC":(49,38),"UP":(49,50),"CORE":(49,62),"TRNS":(49,74),
    "P2IR":(49,86),"P2PK":(49,98),"PRAW":(49,110),"USBR":(49,122),
    "JNUM":(49,134),"FROZ":(49,146),"JHDR":(49,158),"JPDX":(49,170),
    "JPDY":(49,182),"JXMG":(49,194),"AUXN":(49,206),
    "ABSX":(361,38),"ABSY":(361,50),"GUIX":(361,62),"GUIY":(361,74),
    "BTNS":(361,86),"CLMP":(361,98),"DROP":(361,110),"ABSP":(361,122),
    "P2ER":(361,134),"RING":(361,146),"CBKV":(361,158),"CBKX":(361,170),
    "CBKY":(361,182),"FULL":(361,194),"CURP":(361,206),
    "PKSZ":(673,38),"DEVI":(673,50),"SYNC":(673,62),"POLL":(673,74),
    "GOOD":(673,86),"GPEN":(673,98),"BHDR":(673,110),"ACKN":(673,122),
    "ACKP":(673,134),"PAUX":(673,146),"OVFL":(673,158),"H000":(673,170),
    "H001":(673,182),"H002":(673,194),"H003":(673,206),"KBYT":(673,218),
    "BARR":(673,230),"BARF":(673,242),
}

def glyph_pattern(bits):
    return tuple(((bits // ROWDIV[r]) // BITDIV[c]) % 2 for r in range(7) for c in range(5))
TEMPLATES={k:glyph_pattern(v) for k,v in GLYPH.items()}

def sha256(path):
    h=hashlib.sha256()
    with open(path,"rb") as f:
        for b in iter(lambda:f.read(1024*1024),b""):
            h.update(b)
    return h.hexdigest()

def read_ppm(path):
    b=pathlib.Path(path).read_bytes()
    if not b.startswith(b"P6"):
        raise ValueError("not a P6 PPM")
    i=2; toks=[]
    while len(toks)<3:
        while b[i:i+1].isspace(): i+=1
        j=i
        while not b[j:j+1].isspace(): j+=1
        toks.append(int(b[i:j])); i=j
    while b[i:i+1].isspace(): i+=1
    w,h,maxv=toks
    pix=b[i:]
    if maxv!=255 or len(pix)!=w*h*3:
        raise ValueError("unexpected PPM shape")
    return w,h,pix

def pixel(pix,w,x,y):
    i=(y*w+x)*3
    return pix[i],pix[i+1],pix[i+2]

def decode_hex(pix,w,x,y):
    text=""; worst=0
    for pos in range(8):
        obs=[]
        for r in range(7):
            for c in range(5):
                rr,gg,bb=pixel(pix,w,x+pos*6+c,y+r)
                obs.append(1 if (rr+gg+bb)>=360 else 0)
        best=None; best_dist=999
        for ch,pat in TEMPLATES.items():
            dist=sum(a!=b for a,b in zip(obs,pat))
            if dist<best_dist:
                best_dist=dist; best=ch
        worst=max(worst,best_dist); text+=best
    return int(text,16),text,worst

def find_crosshair(pix,w,h):
    pts=[]
    for y in range(280,h):
        row=(y*w)*3
        for x in range(w):
            i=row+x*3; rr,gg,bb=pix[i],pix[i+1],pix[i+2]
            if rr>=245 and gg<=20 and bb>=245: pts.append((x,y))
    if len(pts)<30: raise ValueError(f"magenta crosshair not found ({len(pts)} pixels)")
    xs=[p[0] for p in pts]; ys=[p[1] for p in pts]
    return ((min(xs)+max(xs))//2,(min(ys)+max(ys))//2,len(pts))

class QMP:
    def __init__(self,sock_path,transcript):
        self.transcript=pathlib.Path(transcript)
        self.s=socket.socket(socket.AF_UNIX,socket.SOCK_STREAM); self.s.connect(str(sock_path))
        self.f=self.s.makefile("rwb",buffering=0); self.recv(); self.cmd("qmp_capabilities")
    def log(self,prefix,obj):
        with self.transcript.open("a") as f: f.write(prefix+json.dumps(obj,sort_keys=True)+"\n")
    def recv(self):
        line=self.f.readline()
        if not line: return None
        obj=json.loads(line); self.log("< ",obj); return obj
    def cmd(self,name,args=None):
        obj={"execute":name}
        if args is not None: obj["arguments"]=args
        self.log("> ",obj); self.f.write((json.dumps(obj)+"\n").encode())
        while True:
            r=self.recv()
            if r is None: raise RuntimeError(f"QMP disconnected during {name}")
            if "return" in r: return r["return"]
            if "error" in r: raise RuntimeError(f"QMP {name}: {r['error']}")
    def close(self):
        try:self.f.close()
        except:pass
        try:self.s.close()
        except:pass

def qemu_cmd(args,qmp_sock,serial_log,usb_pcap=None,rr_mode=None,rrfile=None):
    cmd=[args.qemu,"-machine","q35","-m","512M","-smp","2","-cpu","max",
         "-accel","tcg,thread=single","-display","none","-no-reboot","-no-shutdown","-nic","none",
         "-serial",f"file:{serial_log}","-qmp",f"unix:{qmp_sock},server=on,wait=off",
         "-drive",f"if=pflash,format=raw,readonly=on,file={args.ovmf}",
         "-drive",f"if=none,id=framesdisk,format=raw,file={args.image}",
         "-device","nvme,serial=FRAMEPTRCI,drive=framesdisk"]
    if args.lane=="usb":
        cmd += ["-device","qemu-xhci,id=xhci","-device",f"usb-mouse,bus=xhci.0,id=usbmouse,pcap={usb_pcap}"]
    if rr_mode: cmd += ["-icount",f"shift=auto,rr={rr_mode},rrfile={rrfile}"]
    return cmd

def start_qemu(args,out,tag="main",rr_mode=None,rrfile=None):
    qmp_sock=out/f"{tag}-qmp.sock"; serial=out/f"{tag}-serial.log"; transcript=out/f"{tag}-qmp.jsonl"; usb_pcap=out/f"{tag}-usb-mouse.pcap"
    try:qmp_sock.unlink()
    except FileNotFoundError:pass
    cmd=qemu_cmd(args,qmp_sock,serial,usb_pcap,rr_mode,rrfile)
    (out/f"{tag}-qemu-command.json").write_text(json.dumps(cmd,indent=2)+"\n")
    p=subprocess.Popen(cmd,stdout=subprocess.DEVNULL,stderr=(out/f"{tag}-qemu.stderr").open("wb"))
    deadline=time.time()+20
    while time.time()<deadline and not qmp_sock.exists():
        if p.poll() is not None: raise RuntimeError(f"QEMU exited before QMP rc={p.returncode}")
        time.sleep(.05)
    if not qmp_sock.exists(): p.kill(); raise RuntimeError("QMP socket timeout")
    return p,QMP(qmp_sock,transcript)

def stable_snapshot(qmp,out,name,fields,retries=15):
    last_error=None
    for attempt in range(retries):
        path=out/f"{name}-{attempt:02d}.ppm"; qmp.cmd("screendump",{"filename":str(path)})
        try:
            w,h,pix=read_ppm(path); cursor=find_crosshair(pix,w,h); vals={}; bad={}
            for field in fields:
                x,y=FIELD_POS[field]; val,text,dist=decode_hex(pix,w,x,y); vals[field]=val
                if dist!=0: bad[field]={"text":text,"distance":dist}
            if not bad:
                canonical=out/f"{name}.ppm"; canonical.write_bytes(path.read_bytes())
                for old in out.glob(f"{name}-*.ppm"):
                    if old!=canonical:
                        try:old.unlink()
                        except:pass
                return {"width":w,"height":h,"cursor":[cursor[0],cursor[1]],"cursor_pixels":cursor[2],"fields":vals}
            last_error=f"OCR unstable {bad}"
        except Exception as e: last_error=str(e)
        time.sleep(.08)
    raise RuntimeError(f"could not obtain stable snapshot {name}: {last_error}")

def send_rel(qmp,dx,dy):
    ev=[]
    if dx: ev.append({"type":"rel","data":{"axis":"x","value":int(dx)}})
    if dy: ev.append({"type":"rel","data":{"axis":"y","value":int(dy)}})
    if ev: qmp.cmd("input-send-event",{"events":ev})

def send_button(qmp,down):
    qmp.cmd("input-send-event",{"events":[{"type":"btn","data":{"button":"left","down":bool(down)}}]})

def clamp(v,lo,hi): return max(lo,min(hi,v))

def scenario(args,out,assertions=True):
    p,q=start_qemu(args,out); report={"lane":args.lane,"checkpoints":[],"assertions":[],"seed":0xF47A2026}
    essential=["SRC","UP","CORE","P2IR","P2PK","USBR","AUXN","GUIX","GUIY","BTNS","CLMP","DROP","P2ER","RING","PKSZ","SYNC","GOOD","GPEN","BHDR","ACKN","POLL","PAUX","OVFL"]
    try:
        report["query_mice"]=q.cmd("query-mice"); (out/"query-mice.json").write_text(json.dumps(report["query_mice"],indent=2)+"\n")
        start=None; deadline=time.time()+30; idx=0
        while time.time()<deadline:
            try: start=stable_snapshot(q,out,f"bootprobe-{idx}",essential,retries=2); break
            except Exception: time.sleep(.25); idx+=1
        if start is None: raise AssertionError("Pointer Diagnostic canvas/crosshair did not appear")
        (out/"start.ppm").write_bytes((out/f"bootprobe-{idx}.ppm").read_bytes()); report["start"]=start
        x0,y0=start["cursor"]; expected=[x0,y0]; core0=start["fields"]["CORE"]; p2pk0=start["fields"]["P2PK"]; good0=start["fields"]["GOOD"]; usbr0=start["fields"]["USBR"]; clmp0=start["fields"]["CLMP"]; commands=0
        def check(label,dxsum=0,dysum=0,delay=.45):
            # QMP screendump can pause the vCPU between backend report accounting
            # and pointer_diag_apply_relative() in the same guest loop. v2.0
            # falsely failed the first USB checkpoint with USBR/CORE=10 while
            # GUIX/crosshair reflected only 9 reports. Never judge a checkpoint
            # from a single asynchronous framebuffer sample.
            nonlocal expected
            expected[0]=clamp(expected[0]+2*dxsum,0,start["width"]-1)
            expected[1]=clamp(expected[1]+2*dysum,0,start["height"]-1)
            time.sleep(delay)
            deadline=time.time()+4.0
            last=None
            previous_key=None
            settle_index=0
            while time.time()<deadline:
                probe=f"{label}-settle-{settle_index}"
                snap=stable_snapshot(q,out,probe,essential,retries=3)
                snap["name"]=label
                snap["expected"]=expected.copy()
                snap["coordinate_pass"]=(snap["cursor"]==expected and
                                         snap["fields"]["GUIX"]==expected[0] and
                                         snap["fields"]["GUIY"]==expected[1])
                key=(tuple(snap["cursor"]),snap["fields"]["GUIX"],snap["fields"]["GUIY"],
                     snap["fields"]["CORE"],snap["fields"]["P2PK"],snap["fields"]["USBR"],
                     snap["fields"]["GOOD"],snap["fields"]["BTNS"])
                # Require two consecutive identical guest states at the expected
                # coordinate. This makes the checkpoint quiescent rather than
                # merely OCR-clean.
                if snap["coordinate_pass"] and key==previous_key:
                    source=out/f"{probe}.ppm"
                    target=out/f"{label}.ppm"
                    if source.exists():
                        target.write_bytes(source.read_bytes())
                    snap["settled_samples"]=2
                    report["checkpoints"].append(snap)
                    return snap
                previous_key=key
                last=snap
                settle_index+=1
                time.sleep(.08)
            if last is None:
                raise AssertionError(f"{label}: no stable framebuffer sample")
            last["coordinate_pass"]=(last["cursor"]==expected and
                                     last["fields"]["GUIX"]==expected[0] and
                                     last["fields"]["GUIY"]==expected[1])
            last["settled_samples"]=0
            report["checkpoints"].append(last)
            if assertions:
                raise AssertionError(
                    f"{label}: expected settled {expected}, cursor={last['cursor']}, "
                    f"GUI=({last['fields']['GUIX']},{last['fields']['GUIY']}), "
                    f"CORE={last['fields']['CORE']}, P2PK={last['fields']['P2PK']}, "
                    f"USBR={last['fields']['USBR']}"
                )
            return last

        # Exact directional checkpoints.
        phases=[
            ("right",[(4,0)]*10),
            ("left",[(-4,0)]*10),
            ("down",[(0,4)]*10),
            ("up",[(0,-4)]*10),
            ("diag_out",[(3,2)]*5),
            ("diag_back",[(-3,-2)]*5),
        ]
        for label,events in phases:
            sx=sy=0
            for dx,dy in events:
                send_rel(q,dx,dy); commands+=1; sx+=dx; sy+=dy; time.sleep(.012)
            check(label,sx,sy)

        # Button transitions should never move the cursor.
        send_button(q,True); commands+=1; time.sleep(.06)
        snap_down=check("button_down",0,0,.25)
        if assertions and snap_down["fields"]["BTNS"]&1 != 1:
            raise AssertionError(f"button_down: BTNS={snap_down['fields']['BTNS']:x}")
        send_button(q,False); commands+=1; time.sleep(.06)
        snap_up=check("button_up",0,0,.25)
        if assertions and snap_up["fields"]["BTNS"]&1 != 0:
            raise AssertionError(f"button_up: BTNS={snap_up['fields']['BTNS']:x}")

        # Clamp/edge packet pair: +120 then -120 should return exactly and increment CLMP by 2.
        send_rel(q,120,0); commands+=1
        check("clamp_positive",96,0,.3)
        send_rel(q,-120,0); commands+=1
        check("clamp_negative",-96,0,.3)

        # Deterministic stress/fuzz: paired random movements guarantee net zero.
        rng=random.Random(report["seed"]); sx=sy=0
        for i in range(250):
            dx=rng.randint(-8,8); dy=rng.randint(-8,8)
            if dx==0 and dy==0: dx=1
            send_rel(q,dx,dy); commands+=1; sx+=dx; sy+=dy
            send_rel(q,-dx,-dy); commands+=1; sx-=dx; sy-=dy
            time.sleep(.02 if i%25==0 else .004)
        final=check("stress_fuzz",sx,sy,.8); report["commands_sent"]=commands; f=final["fields"]
        inv=[("GPEN==1",f["GPEN"]==1),("CORE advanced",f["CORE"]>core0),("DROP==0",f["DROP"]==0),("P2ER==0",f["P2ER"]==0),("RING==0",f["RING"]==0),("BHDR==0",f["BHDR"]==0),("OVFL==0",f["OVFL"]==0),("CLMP exactly +2",f["CLMP"]==clmp0+2),("final coordinate returned",final["cursor"]==[x0,y0])]
        if args.lane=="ps2":
            inv += [("SRC==1",f["SRC"]==1),("PS2 backend up",(f["UP"]&1)==1),("SYNC==1",f["SYNC"]==1),("P2PK advanced",f["P2PK"]>p2pk0),("GOOD tracks P2PK",f["GOOD"]-good0==f["P2PK"]-p2pk0),("CORE tracks GOOD",f["CORE"]-core0==f["GOOD"]-good0),("USBR unchanged",f["USBR"]==usbr0)]
        else:
            inv += [("SRC==2",f["SRC"]==2),("USB backend up",(f["UP"]&2)==2),("USBR advanced",f["USBR"]>usbr0),("CORE tracks USBR",f["CORE"]-core0==f["USBR"]-usbr0)]
            pcap=out/"main-usb-mouse.pcap"; inv.append(("USB PCAP nonempty",pcap.exists() and pcap.stat().st_size>24))
        report["assertions"]=[{"name":n,"pass":bool(ok)} for n,ok in inv]; failed=[n for n,ok in inv if not ok]
        if assertions and failed: raise AssertionError("invariants failed: "+", ".join(failed))
        q.cmd("query-status"); q.cmd("quit")
        try:p.wait(timeout=5)
        except subprocess.TimeoutExpired:p.kill()
        report["status"]="PASS"; return report
    finally:
        try:q.close()
        except:pass
        if p.poll() is None:
            try:p.kill()
            except:pass

def best_effort_rr(args,out):
    rr=out/"failure-replay.bin"; info={"attempted":True,"rrfile":str(rr),"record":"NOT_RUN","replay":"NOT_RUN"}
    for mode in ("record","replay"):
        tag=f"rr-{mode}"; p=q=None
        try:
            p,q=start_qemu(args,out,tag=tag,rr_mode=mode,rrfile=rr); time.sleep(7)
            if mode=="record":
                for _ in range(12): send_rel(q,4,0); time.sleep(.015)
                for _ in range(12): send_rel(q,-4,0); time.sleep(.015)
                for _ in range(8): send_rel(q,0,4); time.sleep(.015)
                for _ in range(8): send_rel(q,0,-4); time.sleep(.015)
                time.sleep(1)
            else: time.sleep(2)
            try:q.cmd("screendump",{"filename":str(out/f"{tag}-final.ppm")})
            except Exception:pass
            try:q.cmd("quit")
            except Exception:pass
            try:p.wait(timeout=4)
            except subprocess.TimeoutExpired:p.kill()
            info[mode]="PASS"
        except Exception as e:
            info[mode]="FAIL"; info[f"{mode}_error"]=repr(e)
            if p is not None and p.poll() is None:
                try:p.kill()
                except:pass
        finally:
            if q is not None:
                try:q.close()
                except:pass
    if rr.exists(): info["rr_sha256"]=sha256(rr); info["rr_bytes"]=rr.stat().st_size
    (out/"record-replay.json").write_text(json.dumps(info,indent=2)+"\n"); return info

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--qemu",required=True); ap.add_argument("--ovmf",required=True); ap.add_argument("--image",required=True); ap.add_argument("--out",required=True); ap.add_argument("--lane",choices=["ps2","usb"],required=True); args=ap.parse_args()
    out=pathlib.Path(args.out); out.mkdir(parents=True,exist_ok=True)
    summary={"lane":args.lane,"status":"FAIL","qemu_version":subprocess.check_output([args.qemu,"--version"],text=True).splitlines()[0],"image_sha256":sha256(args.image)}; rc=1
    try: summary.update(scenario(args,out,assertions=True)); rc=0
    except Exception as e:
        summary["error"]=repr(e)
        try:summary["record_replay"]=best_effort_rr(args,out)
        except Exception as rr:summary["record_replay_error"]=repr(rr)
    finally:
        (out/"summary.json").write_text(json.dumps(summary,indent=2,sort_keys=True)+"\n"); manifest=[]
        for p in sorted(out.iterdir()):
            if p.is_file():
                try:manifest.append(f"{sha256(p)}  {p.name}")
                except:pass
        (out/"SHA256SUMS.txt").write_text("\n".join(manifest)+"\n")
    print(json.dumps(summary,indent=2,sort_keys=True)); return rc

if __name__=="__main__": raise SystemExit(main())
