#!/usr/bin/env python3
import hashlib,json,pathlib,shutil,subprocess,tempfile
ROOT=pathlib.Path.cwd()
KIT_SHA='61b0fc25513719fce554729724c7848647de9cffe54434d4ab5f7ba8af42a36a'
SRC_SHA='5f8c13adac6d34e64bd47d9463a3e261cd0b51bb5ddb500aa9f7b87c2914a52d'
R21_SHA='bed3740e10c3bab8b5c81ca6b2fb77668b33bdc9109039a38e2e40aa09c7efb9'
R24_SHA='1b56b621de728aabdbbe8c100f92816564369e984f1fc2b5e4815080011aedaf'
R25_SHA='068ed900f8942ecec797e2f5fa5e79f95fce51ef817b2e3336af05d643528674'
ISO_NAME='Frames-0.9.98-v108-Physical-Input-Repair-r25-FlightRecorder-USB-Write-Gate-Rufus-UEFI.iso'
IMG_NAME='Frames-0.9.98-v108-r25-FlightRecorder-Logging-USB.img'
def sha(p):
 h=hashlib.sha256()
 with open(p,'rb') as f:
  for b in iter(lambda:f.read(1024*1024),b''): h.update(b)
 return h.hexdigest()
def run(cmd,cwd=None,check=True,stdout=None,stderr=None):
 print('+',cmd,flush=True); return subprocess.run(cmd,cwd=cwd,shell=isinstance(cmd,str),check=check,text=True,stdout=stdout,stderr=stderr)
def req(x,msg):
 if not x: raise RuntimeError(msg)
def fn_text(s,name):
 st=s.index('fn '+name); op=s.index('{',st);d=0
 for i in range(op,len(s)):
  if s[i]=='{':d+=1
  elif s[i]=='}':
   d-=1
   if d==0:return s[st:i+1]
 raise RuntimeError(name)
def jsonpass(p):
 d=json.loads(pathlib.Path(p).read_text()); req(d.get('status')=='PASS',f'{p} failed {d}')
def model_gate(r24,r25):
 a=pathlib.Path(r24).read_text(); s=pathlib.Path(r25).read_text()
 needed=['fn flight_recorder_init_v125','fn flight_record_v125','fn flight_flush_one_v125','fn usb_msc_bot_write10_v125','fn flight_log_arm_v125','FRAMES_FLIGHT_RECORDER_R25_READY','FRAMES_CONTROLLED_USB_LOG_R25_ARMED','fn v108_msc_snapshot_v125','fn v108_log_msc_retain_v125','flight_input_record_v125(input_state,131072+typ,a,b)','typ>=1 && typ<=3','var need:u64=3','XENU ST FL VID PID MSC LOG','FREC Q DROP ARM W ERR']
 miss=[x for x in needed if x not in s]; req(not miss,'r25 model missing '+repr(miss)); req('desktop_redraw=1' not in s,'full desktop repaint re-enabled')
 for n in ('nvme_write_target_serial_ok','nvme_write_target_arm','nvme_io_write_block_cert','nvme_io_flush_cert'): req(fn_text(a,n)==fn_text(s,n),f'internal write function changed: {n}')
 arm=fn_text(s,'flight_log_arm_v125')
 for q in ('volatile_read64(msc+688)!=524287','volatile_read64(data)!=2391787741383512646','volatile_read64(data+80)!=3545795563478602310','start<133152','end>=395264'): req(q in arm,'USB log target gate missing '+q)
 flush=fn_text(s,'flight_flush_one_v125')
 for q in ('usb_msc_bot_write10_v125','usb_msc_bot_nodata_v125','usb_msc_bot_read10','nvme_read_checksum(back,512)!=expected'): req(q in flush,'verified flush missing '+q)
 delta=subprocess.run(['diff','-u',str(r24),str(r25)],text=True,stdout=subprocess.PIPE).stdout.lower()
 for bad in ('nvme_io_write_block_cert(', 'nvme_write_target_arm(', 'storage_write_commit', 'ahci_write'): req(not any(line.startswith('+') and bad in line for line in delta.splitlines()),'new internal write path '+bad)
def build_iso(F,iso):
 for p in F.rglob('*.sh'): p.chmod(p.stat().st_mode|0o111)
 for p in (F/'toolchain').rglob('nexus'): p.chmod(p.stat().st_mode|0o111)
 run(['./tools/build.sh'],cwd=F); run(['python3','tools/make_esp.py'],cwd=F); run(['python3','tools/sdk_selftest.py'],cwd=F); run(['python3','tools/make_desktop_preview_image.py'],cwd=F); run(['python3','tools/verify_desktop_preview_image.py','--image','build/Frames-0.9.98-Desktop-Preview.img','--require-pass'],cwd=F); run(['python3','tools/verify_release.py'],cwd=F)
 shutil.copy2(F/'build/Frames-0.9.98-Desktop-Preview.img',ROOT/'out/raw.img')
 first=subprocess.check_output("sgdisk -i 1 out/raw.img | awk -F: '/First sector/{gsub(/ /,\"\",$2);split($2,a,\"(\");print a[1]}'",cwd=ROOT,shell=True,text=True).strip(); last=subprocess.check_output("sgdisk -i 1 out/raw.img | awk -F: '/Last sector/{gsub(/ /,\"\",$2);split($2,a,\"(\");print a[1]}'",cwd=ROOT,shell=True,text=True).strip(); count=int(last)-int(first)+1
 run(f'dd if=out/raw.img of=out/esp.img bs=512 skip={first} count={count} status=none',cwd=ROOT); run("mcopy -s -i out/esp.img '::/EFI' payload/",cwd=ROOT); run("mcopy -s -i out/esp.img '::/FRAMES' payload/",cwd=ROOT)
 run('dd if=/dev/zero of=out/efiboot.img bs=1M count=16 status=none',cwd=ROOT); run('mkfs.fat -F 16 -n FRAMESBOOT out/efiboot.img >/dev/null',cwd=ROOT); run('mmd -i out/efiboot.img ::/EFI ::/EFI/BOOT ::/FRAMES',cwd=ROOT); run('mcopy -i out/efiboot.img payload/EFI/BOOT/BOOTX64.EFI ::/EFI/BOOT/BOOTX64.EFI',cwd=ROOT)
 for p in (ROOT/'payload/FRAMES').iterdir(): run(['mcopy','-i',str(ROOT/'out/efiboot.img'),str(p),'::/FRAMES/'])
 with tempfile.TemporaryDirectory(prefix='r25iso-') as t:
  r=pathlib.Path(t); shutil.copy2(ROOT/'out/efiboot.img',r/'efiboot.img'); shutil.copytree(ROOT/'payload/EFI',r/'EFI'); shutil.copytree(ROOT/'payload/FRAMES',r/'FRAMES'); (r/'README.TXT').write_text('Frames v108 r25 combined physical-input + Flight Recorder + controlled USB diagnostic-write candidate\nInternal NVMe/SATA/ESP remain read-only. General writes remain blocked.\nUse the separate r25 Logging USB image for persistent FRAMES.LOG.\n')
  run(['xorriso','-as','mkisofs','-iso-level','3','-R','-J','-V','FRAMES_V108_R25','-eltorito-alt-boot','-e','efiboot.img','-no-emul-boot','-o',str(iso),str(r)],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
def main():
 r21=ROOT/'r21-candidate/evidence/kernel-r21.nx'; req(r21.is_file() and sha(r21)==R21_SHA,'exact r21 source missing'); kit=ROOT/'Frames-0.9.98-Runtime-Certification-Kit-v108-r9.zip'; req(kit.is_file() and sha(kit)==KIT_SHA,'cert kit identity')
 for d in ('evidence','out','payload','final'): shutil.rmtree(ROOT/d,ignore_errors=True); (ROOT/d).mkdir(parents=True,exist_ok=True)
 with tempfile.TemporaryDirectory(prefix='r25cert-') as td:
  td=pathlib.Path(td); kd=td/'kit';sd=td/'src';kd.mkdir();sd.mkdir(); run(['unzip','-q',kit,'-d',kd]); z=kd/'Frames-0.9.98-Source-v108.zip'; req(sha(z)==SRC_SHA,'canonical source identity');run(['unzip','-q',z,'-d',sd]);F=sd/'Frames-0.9.98';shutil.copy2(r21,F/'kernel/main.nx')
  r24=td/'kernel-r24.nx';shutil.copy2(r21,r24); run(['python3',ROOT/'tools/ci/patch_v108_physical_input_r24b_fixbrace.py',r24],stdout=subprocess.PIPE);req(sha(r24)==R24_SHA,'r24 reconstruction');shutil.copy2(r24,ROOT/'evidence/kernel-r24.nx')
  rr=run(['python3',ROOT/'tools/ci/patch_v108_r25_flightrec_usbwrite.py',F/'kernel/main.nx'],stdout=subprocess.PIPE);(ROOT/'evidence/R25-SHA.txt').write_text(rr.stdout);req(sha(F/'kernel/main.nx')==R25_SHA,'r25 identity');shutil.copy2(F/'kernel/main.nx',ROOT/'evidence/kernel-r25.nx')
  diff=run(['diff','-u',r24,F/'kernel/main.nx'],check=False,stdout=subprocess.PIPE).stdout;(ROOT/'evidence/R24-R25.patch').write_text(diff);model_gate(r24,F/'kernel/main.nx');(ROOT/'evidence/WRITE-POLICY.txt').write_text('status=PASS\ninternal_media=READ_ONLY_UNCHANGED\nnew_write_path=USB_MSC_WRITE10_ONLY\ntarget=FRAMESLOG_EXACT_256M_IMAGE\nrange=PREALLOCATED_FRAMES.LOG_CLUSTERS_ONLY\nreadback_verify=REQUIRED\n'); build_iso(F,ROOT/'out'/ISO_NAME)
 iso_sha=sha(ROOT/'out'/ISO_NAME);(ROOT/'evidence/ISO-SHA256.txt').write_text(f'{iso_sha}  {ISO_NAME}\n');(ROOT/'evidence/ISO-SIZE.txt').write_text(str((ROOT/'out'/ISO_NAME).stat().st_size)+'\n')
 logimg=ROOT/'out'/IMG_NAME;run(['python3','tools/ci/make_r25_logging_usb.py','--payload','payload','--out',logimg,'--evidence','evidence'],cwd=ROOT); man=ROOT/'evidence/R25-LOG-IMAGE.json'; req(logimg.stat().st_size==268435456,'logging image size')
 ovmfs=list(pathlib.Path('/usr/share/OVMF').rglob('OVMF_CODE_4M.fd'))+list(pathlib.Path('/usr/share/OVMF').rglob('OVMF_CODE.fd'));req(ovmfs,'OVMF');ovmf=str(ovmfs[0]);g=ROOT/'evidence/gates';g.mkdir()
 tests=[('interaction',['python3','tools/ci/qemu_r23_dragright_guard_gate.py','--ovmf',ovmf,'--iso',str(ROOT/'out'/ISO_NAME),'--out',str(g/'interaction'),'--expected-iso-sha',iso_sha],g/'interaction/R23-INTERACTION.json'),('usb-direct',['python3','tools/ci/qemu_usb_hub_topology_gate_r3.py','--ovmf',ovmf,'--iso',str(ROOT/'out'/ISO_NAME),'--out',str(g/'usb-direct'),'--expected-iso-sha',iso_sha,'--topology','direct'],g/'usb-direct/TOPOLOGY.json'),('usb-hub',['python3','tools/ci/qemu_usb_hub_topology_gate_r3.py','--ovmf',ovmf,'--iso',str(ROOT/'out'/ISO_NAME),'--out',str(g/'usb-hub'),'--expected-iso-sha',iso_sha,'--topology','hub'],g/'usb-hub/TOPOLOGY.json'),('usb-multi',['python3','tools/ci/qemu_usb_hub_multichild_gate_r17.py','--ovmf',ovmf,'--iso',str(ROOT/'out'/ISO_NAME),'--out',str(g/'usb-multi'),'--expected-iso-sha',iso_sha],g/'usb-multi/MULTICHILD-R17.json'),('usb-ctl',['python3','tools/ci/qemu_usb_multicontroller_gate_r16.py','--ovmf',ovmf,'--iso',str(ROOT/'out'/ISO_NAME),'--out',str(g/'usb-ctl'),'--expected-iso-sha',iso_sha],g/'usb-ctl/USB-MULTICONTROLLER.json'),('usb-kbd',['python3','tools/ci/qemu_usb_keyboard_gate_r17.py','--ovmf',ovmf,'--iso',str(ROOT/'out'/ISO_NAME),'--out',str(g/'usb-kbd'),'--expected-iso-sha',iso_sha],g/'usb-kbd/USB-KEYBOARD.json'),('ps2',['python3','tools/ci/qemu_ps2_delivery_gate_r17.py','--ovmf',ovmf,'--iso',str(ROOT/'out'/ISO_NAME),'--out',str(g/'ps2'),'--expected-iso-sha',iso_sha],g/'ps2/PS2-DELIVERY.json'),('smooth',['python3','tools/ci/qemu_ps2_cursor_smoothness_r23.py','--ovmf',ovmf,'--iso',str(ROOT/'out'/ISO_NAME),'--out',str(g/'smooth'),'--expected-iso-sha',iso_sha],g/'smooth/SMOOTHNESS.json'),('text',['python3','tools/ci/qemu_text_edit_gate_r15.py','--ovmf',ovmf,'--iso',str(ROOT/'out'/ISO_NAME),'--out',str(g/'text'),'--expected-iso-sha',iso_sha],g/'text/TEXT-EDIT.json'),('focus',['python3','tools/ci/qemu_focus_persistence_gate_r17.py','--ovmf',ovmf,'--iso',str(ROOT/'out'/ISO_NAME),'--out',str(g/'focus'),'--expected-iso-sha',iso_sha],g/'focus/FOCUS-PERSISTENCE.json')]
 status={}
 for n,cmd,jp in tests: pathlib.Path(cmd[cmd.index('--out')+1]).mkdir(parents=True,exist_ok=True);run(cmd,cwd=ROOT);jsonpass(jp);status[n]='PASS';(g/n/'RESULT.status').write_text('PASS\n')
 lg=g/'flight-log';lg.mkdir();run(['python3','tools/ci/qemu_r25_flight_log_gate.py','--ovmf',ovmf,'--iso',ROOT/'out'/ISO_NAME,'--log-image',logimg,'--manifest',man,'--out',lg,'--expected-iso-sha',iso_sha],cwd=ROOT);jsonpass(lg/'R25-FLIGHT-LOG.json');status['flight-log']='PASS';(lg/'RESULT.status').write_text('PASS\n')
 sd=g/'safety';sd.mkdir();sent=sd/'sentinel.img';sent.write_bytes(b'\0'*(32*1024*1024));b=sha(sent);ser=sd/'serial.log';err=sd/'stderr';cmd=f'timeout 90 qemu-system-x86_64 -machine q35 -m 768M -smp 2 -cpu max -accel tcg,thread=single -display none -no-reboot -no-shutdown -nic none -serial file:{ser} -drive if=pflash,format=raw,readonly=on,file={ovmf} -cdrom {ROOT/"out"/ISO_NAME} -boot d -drive file={sent},if=none,format=raw,readonly=on,id=s -device nvme,drive=s,serial=R25_INTERNAL_SENTINEL >/dev/null 2>{err}';run(cmd,cwd=ROOT,check=False);a=sha(sent);req(a==b,'internal safety sentinel changed');req('FRAMES_FLIGHT_RECORDER_R25_READY' in ser.read_text(errors='ignore'),'flight recorder not initialized');(sd/'SAFETY.txt').write_text(f'before={b}\nafter={a}\n');(sd/'RESULT.status').write_text('PASS\n');status['safety']='PASS'
 model_gate(ROOT/'evidence/kernel-r24.nx',ROOT/'evidence/kernel-r25.nx');(g/'model').mkdir();(g/'model/RESULT.status').write_text('PASS\n');status['model']='PASS'
 m=json.loads(man.read_text());agg={'status':'PASS','profile':'frames-v108-r25-flight-recorder-controlled-usb-write','kernel_sha256':R25_SHA,'iso_sha256':iso_sha,'logging_usb_sha256':m['sha256'],'gates':status,'physical_r24':'PARTIAL_PASS_RIGHT_CLICK_USB_OPEN','physical_r25':'PENDING','internal_media_writes':'BLOCKED','controlled_usb_log_write':'VM_CERTIFIED_PHYSICAL_PENDING'};(ROOT/'evidence/R25-AGGREGATE.json').write_text(json.dumps(agg,indent=2)+'\n')
 final=ROOT/'final';shutil.copy2(ROOT/'out'/ISO_NAME,final/ISO_NAME);shutil.copy2(logimg,final/IMG_NAME);(final/'ISO-SHA256.txt').write_text(f'{iso_sha}  {ISO_NAME}\n');(final/'LOGGING-USB-SHA256.txt').write_text(f'{m["sha256"]}  {IMG_NAME}\n');(final/'CERTIFICATION.txt').write_text('Frames v108 r25 Flight Recorder + controlled USB diagnostic-write candidate\nstatus=PASS_VM_PENDING_PHYSICAL\nr24_working_desktop_regressions=PASS_VM\nright_click_tweak=PHYSICAL_PENDING\nxhci_post_reset_enumeration_flight_recording=ENABLED\nram_flight_recorder=PASS_VM\ncontrolled_usb_log_write=PASS_VM_PENDING_PHYSICAL\nwindows_readable_log=FRAMESLOG/FRAMES.LOG\ninternal_nvme_sata_esp=READ_ONLY\ngeneral_writes=BLOCKED\n'); print('R25 PASS_VM_PENDING_PHYSICAL',iso_sha,m['sha256'])
if __name__=='__main__': main()
