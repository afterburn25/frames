#!/usr/bin/env python3
"""Frames 0.9.98 Pointer Isolation CI v3.

Purpose:
- remove framebuffer OCR from pass/fail
- assert only rendered crosshair coordinates
- preserve QMP, serial and USB PCAP evidence
- classify missing/coalesced/scaled motion deterministically
"""
import argparse, hashlib, json, pathlib, socket, subprocess, sys, time

def sha256(path):
    h=hashlib.sha256()
    with open(path,"rb") as f:
        for b in iter(lambda:f.read(1024*1024),b""): h.update(b)
    return h.hexdigest()

def read_ppm(path):
    b=pathlib.Path(path).read_bytes()
    if not b.startswith(b"P6"): raise ValueError("not P6 PPM")
    i=2; toks=[]
    while len(toks)<3:
        while b[i:i+1].isspace(): i+=1
        j=i
        while not b[j:j+1].isspace(): j+=1
        toks.append(int(b[i:j])); i=j
    while b[i:i+1].isspace(): i+=1
    w,h,maxv=toks; pix=b[i:]
    if maxv != 255 or len(pix) != w*h*3: raise ValueError("bad PPM")
    return w,h,pix

def find_crosshair(pix,w,h):
    pts=[]
    for y in range(280,h):
        row=y*w*3
        for x in range(w):
            i=row+x*3; r,g,b=pix[i:i+3]
            if r>=245 and g<=20 and b>=245: pts.append((x,y))
    if len(pts)<30: raise ValueError(f"crosshair missing ({len(pts)} px)")
    xs=[p[0] for p in pts]; ys=[p[1] for p in pts]
    return [(min(xs)+max(xs))//2,(min(ys)+max(ys))//2,len(pts)]

class QMP:
    def __init__(self,path,transcript):
        self.transcript=pathlib.Path(transcript)
        self.s=socket.socket(socket.AF_UNIX,socket.SOCK_STREAM)
        self.s.connect(str(path)); self.f=self.s.makefile("rwb",buffering=0)
        self.recv(); self.cmd("qmp_capabilities")
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
        try:self.f.close(); self.s.close()
        except:pass

def qemu_cmd(a,qmp,serial,pcap):
    cmd=[a.qemu,"-machine","q35","-m","512M","-smp","2","-cpu","max",
         "-accel","tcg,thread=single","-display","none","-no-reboot","-no-shutdown",
         "-nic","none","-serial",f"file:{serial}","-qmp",f"unix:{qmp},server=on,wait=off",
         "-drive",f"if=pflash,format=raw,readonly=on,file={a.ovmf}",
         "-drive",f"if=none,id=framesdisk,format=raw,file={a.image}",
         "-device","nvme,serial=FRAMEPTRCI,drive=framesdisk"]
    if a.lane=="usb":
        cmd += ["-device","qemu-xhci,id=xhci",
                "-device",f"usb-mouse,bus=xhci.0,id=usbmouse,pcap={pcap}"]
    return cmd

def start(a,out):
    qmp=out/"main-qmp.sock"; serial=out/"main-serial.log"
    transcript=out/"main-qmp.jsonl"; pcap=out/"main-usb-mouse.pcap"
    try:qmp.unlink()
    except FileNotFoundError:pass
    cmd=qemu_cmd(a,qmp,serial,pcap)
    (out/"main-qemu-command.json").write_text(json.dumps(cmd,indent=2)+"\n")
    err=(out/"main-qemu.stderr").open("wb")
    p=subprocess.Popen(cmd,stdout=subprocess.DEVNULL,stderr=err)
    deadline=time.time()+20
    while time.time()<deadline and not qmp.exists():
        if p.poll() is not None: raise RuntimeError(f"QEMU exited rc={p.returncode}")
        time.sleep(.05)
    if not qmp.exists(): p.kill(); raise RuntimeError("QMP timeout")
    return p,QMP(qmp,transcript)

def screenshot(q,out,name):
    path=out/f"{name}.ppm"; q.cmd("screendump",{"filename":str(path)})
    w,h,pix=read_ppm(path); c=find_crosshair(pix,w,h)
    return {"name":name,"width":w,"height":h,"cursor":c[:2],"cursor_pixels":c[2]}

def stable_cursor(q,out,name,timeout=5.0):
    end=time.time()+timeout; prev=None; idx=0; last=None
    while time.time()<end:
        try: cur=screenshot(q,out,f"{name}-probe-{idx}")
        except Exception:
            time.sleep(.1); idx+=1; continue
        last=cur
        key=tuple(cur["cursor"])
        if key==prev:
            canonical=out/f"{name}.ppm"
            canonical.write_bytes((out/f"{name}-probe-{idx}.ppm").read_bytes())
            cur["name"]=name; cur["settled_samples"]=2
            return cur
        prev=key; idx+=1; time.sleep(.1)
    if last: return last
    raise RuntimeError(f"no readable cursor for {name}")

def send_rel(q,dx,dy):
    ev=[]
    if dx: ev.append({"type":"rel","data":{"axis":"x","value":int(dx)}})
    if dy: ev.append({"type":"rel","data":{"axis":"y","value":int(dy)}})
    q.cmd("input-send-event",{"events":ev})

def classify(expected_delta,actual_delta):
    if actual_delta==expected_delta: return "exact"
    if actual_delta==0: return "no-motion"
    if expected_delta and abs(actual_delta)<abs(expected_delta):
        return f"short-motion ratio={actual_delta/expected_delta:.3f}"
    if expected_delta and abs(actual_delta)>abs(expected_delta):
        return f"excess-motion ratio={actual_delta/expected_delta:.3f}"
    return "direction-or-sign-mismatch"

def run(a,out):
    p,q=start(a,out)
    report={"schema":"frames-pointer-isolation-v3","lane":a.lane,"checkpoints":[],"assertions":[]}
    try:
        report["query_mice"]=q.cmd("query-mice")
        (out/"query-mice.json").write_text(json.dumps(report["query_mice"],indent=2)+"\n")
        start_pos=None; deadline=time.time()+30
        while time.time()<deadline:
            try:
                start_pos=stable_cursor(q,out,"start",2.0); break
            except Exception: time.sleep(.25)
        if start_pos is None: raise AssertionError("pointer diagnostic crosshair did not appear")
        report["start"]=start_pos
        expected=start_pos["cursor"][:]
        phases=[("right",4,0,10),("left",-4,0,10),("down",0,4,10),("up",0,-4,10)]
        for label,dx,dy,n in phases:
            before=stable_cursor(q,out,label+"-before")
            for _ in range(n):
                send_rel(q,dx,dy); time.sleep(.03)
            after=stable_cursor(q,out,label)
            ex=expected[0]+2*dx*n; ey=expected[1]+2*dy*n
            ex=max(0,min(after["width"]-1,ex)); ey=max(0,min(after["height"]-1,ey))
            expected=[ex,ey]
            actual_dx=after["cursor"][0]-before["cursor"][0]
            actual_dy=after["cursor"][1]-before["cursor"][1]
            expected_dx=2*dx*n; expected_dy=2*dy*n
            cp={"name":label,"before":before["cursor"],"cursor":after["cursor"],
                "expected":expected[:],"actual_delta":[actual_dx,actual_dy],
                "expected_delta":[expected_dx,expected_dy],
                "x_class":classify(expected_dx,actual_dx) if expected_dx else "n/a",
                "y_class":classify(expected_dy,actual_dy) if expected_dy else "n/a"}
            cp["pass"]=after["cursor"]==expected
            report["checkpoints"].append(cp)
            report["assertions"].append({"name":label,"pass":cp["pass"],
                "detail":f"expected={expected} actual={after['cursor']} delta={cp['actual_delta']}"})
        report["pass"]=all(x["pass"] for x in report["assertions"])
    except Exception as e:
        report["pass"]=False; report["error"]=f"{type(e).__name__}: {e}"
    finally:
        try:q.cmd("quit")
        except:pass
        q.close()
        try:p.wait(timeout=5)
        except:
            p.kill(); p.wait()
    serial=out/"main-serial.log"
    if serial.exists():
        txt=serial.read_text(errors="replace")
        lines=[ln for ln in txt.splitlines() if "PTR" in ln.upper() or "POINTER" in ln.upper() or "HID" in ln.upper() or "PS2" in ln.upper()]
        (out/"pointer-serial-lines.txt").write_text("\n".join(lines)+("\n" if lines else ""))
        report["pointer_serial_line_count"]=len(lines)
    else:
        (out/"pointer-serial-lines.txt").write_text("")
        report["pointer_serial_line_count"]=0
    (out/"summary.json").write_text(json.dumps(report,indent=2,sort_keys=True)+"\n")
    sums=[]
    for f in sorted(out.iterdir()):
        if f.is_file() and f.name!="SHA256SUMS.txt": sums.append(f"{sha256(f)}  {f.name}")
    (out/"SHA256SUMS.txt").write_text("\n".join(sums)+"\n")
    return 0 if report.get("pass") else 1

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--qemu",required=True); ap.add_argument("--ovmf",required=True)
    ap.add_argument("--image",required=True); ap.add_argument("--lane",choices=["ps2","usb"],required=True)
    ap.add_argument("--out",required=True)
    a=ap.parse_args(); out=pathlib.Path(a.out); out.mkdir(parents=True,exist_ok=True)
    return run(a,out)
if __name__=="__main__": sys.exit(main())
