#!/usr/bin/env python3
import argparse,hashlib,json,pathlib,shutil,socket,subprocess,time

def sha(p):
 h=hashlib.sha256()
 with open(p,'rb') as f:
  for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
 return h.hexdigest()

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--ovmf',required=True);ap.add_argument('--iso',required=True);ap.add_argument('--target',required=True);ap.add_argument('--out',required=True);ap.add_argument('--expected-iso-sha',required=True);a=ap.parse_args()
 out=pathlib.Path(a.out);out.mkdir(parents=True,exist_ok=True);iso=pathlib.Path(a.iso)
 if sha(iso)!=a.expected_iso_sha:raise SystemExit('ISO mismatch')
 disk=out/'readonly-rufus-target.img';shutil.copy2(a.target,disk);before=sha(disk)
 qmp=out/'qmp.sock';serial=out/'serial.log';err=(out/'qemu.stderr').open('wb')
 cmd=['qemu-system-x86_64','-machine','q35','-m','768M','-smp','2','-cpu','max','-accel','tcg,thread=single','-display','none','-no-reboot','-no-shutdown','-nic','none','-serial',f'file:{serial}','-qmp',f'unix:{qmp},server=on,wait=off','-drive',f'if=pflash,format=raw,readonly=on,file={a.ovmf}','-cdrom',str(iso),'-boot','d','-device','qemu-xhci,id=xhci','-drive',f'file={disk},if=none,format=raw,readonly=on,id=logdisk','-device','usb-storage,drive=logdisk,bus=xhci.0,port=1']
 (out/'qemu-command.json').write_text(json.dumps(cmd,indent=2)+'\n');p=subprocess.Popen(cmd,stdout=subprocess.DEVNULL,stderr=err)
 result={'status':'FAIL','gate':'r26_log_failopen','armed':False,'persist_disabled':False,'input_after_failure':False,'runtime_alive':False,'readonly_target_unchanged':False}
 try:
  deadline=time.time()+25
  while time.time()<deadline and not qmp.exists():
   if p.poll() is not None:raise RuntimeError('qemu exited before qmp')
   time.sleep(.05)
  if not qmp.exists():raise RuntimeError('qmp timeout')
  sock=socket.socket(socket.AF_UNIX,socket.SOCK_STREAM);sock.connect(str(qmp));f=sock.makefile('rwb',0);json.loads(f.readline())
  def call(name,args=None):
   o={'execute':name};
   if args is not None:o['arguments']=args
   f.write((json.dumps(o)+'\n').encode())
   while True:
    r=json.loads(f.readline())
    if 'return' in r:return r['return']
    if 'error' in r:raise RuntimeError(str(r['error']))
  call('qmp_capabilities')
  deadline=time.time()+120
  while time.time()<deadline:
   txt=serial.read_text(errors='ignore') if serial.exists() else ''
   result['armed']='FRAMES_ISO_LOG_R26_ARMED' in txt
   result['runtime_alive']='FRAMES_V108_INPUT_TEST_RUNTIME_READY' in txt
   if result['armed'] and result['runtime_alive']:break
   if p.poll() is not None:break
   time.sleep(.15)
  if not result['armed']:raise RuntimeError('ISO-native log never armed on read-only target')
  if not result['runtime_alive']:raise RuntimeError('desktop runtime not ready')
  # Generate PS/2 input records, then become idle so the logger attempts one bounded write.
  for i in range(30):
   call('input-send-event',{'events':[{'type':'rel','data':{'axis':'x','value':2 if i%2==0 else -1}},{'type':'rel','data':{'axis':'y','value':1}}]});time.sleep(.02)
  deadline=time.time()+20
  while time.time()<deadline:
   txt=serial.read_text(errors='ignore')
   if 'FRAMES_LOG_PERSIST_R26_DISABLED' in txt:
    result['persist_disabled']=True;break
   if p.poll() is not None:break
   time.sleep(.1)
  if not result['persist_disabled']:raise RuntimeError('read-only persistence failure did not disarm')
  # Input after the write failure must still traverse the desktop loop.
  for i in range(20):
   call('input-send-event',{'events':[{'type':'rel','data':{'axis':'x','value':3}},{'type':'rel','data':{'axis':'y','value':-1 if i%2 else 1}}]});time.sleep(.02)
  deadline=time.time()+8
  while time.time()<deadline:
   txt=serial.read_text(errors='ignore')
   if 'FRAMES_INPUT_AFTER_LOG_FAIL_R26_OK' in txt:
    result['input_after_failure']=True;break
   time.sleep(.1)
  if not result['input_after_failure']:raise RuntimeError('input did not continue after persistence failure')
  result['runtime_alive']=p.poll() is None
  try:call('quit')
  except Exception:pass
 finally:
  try:p.wait(timeout=8)
  except Exception:p.kill();p.wait()
  err.close()
 result['readonly_target_unchanged']=sha(disk)==before
 if not result['runtime_alive']:raise RuntimeError('guest died after persistence failure')
 if not result['readonly_target_unchanged']:raise RuntimeError('read-only target changed')
 result['status']='PASS';(out/'R26-LOG-FAILOPEN.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,sort_keys=True))
if __name__=='__main__':main()
