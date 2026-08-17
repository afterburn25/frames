#!/usr/bin/env python3
import hashlib,json,pathlib,shutil,subprocess,tempfile
from r26_log_format import build_log, LOG_BYTES, NONCE, MAGIC, HEADER_BYTES
ROOT=pathlib.Path.cwd()
KIT_SHA='61b0fc25513719fce554729724c7848647de9cffe54434d4ab5f7ba8af42a36a'
SRC_SHA='5f8c13adac6d34e64bd47d9463a3e261cd0b51bb5ddb500aa9f7b87c2914a52d'
R21_SHA='bed3740e10c3bab8b5c81ca6b2fb77668b33bdc9109039a38e2e40aa09c7efb9'
R25K_SHA='af77b8f648dbb11fa6a31810e2150483818213635c92404dd956db892df9fdb0'
R26_SHA='5dc6c6b04f7103a3981287d048264c94b75bfb12fd50538ca0a285979aa001fc'
ISO_NAME='Frames-0.9.98-v108-r26-ISO-Native-FlightRecorder-Input-USB-Repair-Rufus-UEFI.iso'

def sha(p):
 h=hashlib.sha256()
 with open(p,'rb') as f:
  for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
 return h.hexdigest()
def run(cmd,cwd=None,check=True,stdout=None,stderr=None):
 print('+',cmd,flush=True);return subprocess.run(cmd,cwd=cwd,shell=isinstance(cmd,str),check=check,text=True,stdout=stdout,stderr=stderr)
def req(x,msg):
 if not x:raise RuntimeError(msg)
def fn_text(s,name):
 st=s.index('fn '+name);op=s.index('{',st);d=0
 for i in range(op,len(s)):
  if s[i]=='{':d+=1
  elif s[i]=='}':
   d-=1
   if d==0:return s[st:i+1]
 raise RuntimeError(name)
def jsonpass(p):
 d=json.loads(pathlib.Path(p).read_text());req(d.get('status')=='PASS',f'{p} failed {d}')

def model_gate(r25k,r26):
 a=pathlib.Path(r25k).read_text();s=pathlib.Path(r26).read_text()
 needed=['fn flight_fat32_find_log_v126','fn flight_fat32_contig_log_v126','fn flight_persist_fail_v126','FRAMES_ISO_LOG_R26_ARMED','FRAMES_LOG_PERSIST_R26_DISABLED','FRAMES_INPUT_AFTER_LOG_FAIL_R26_OK','volatile_read64(hd+128)!=3905238009226482246','volatile_write64(fr+224,1)','volatile_read64(xhci_state+1800)==1','quiet_now-last_event>300000000','flight_buffer,262144','fn v108_msc_snapshot_v125','flight_input_record_v125(input_state,131072+typ,a,b)']
 miss=[x for x in needed if x not in s];req(not miss,'r26 model missing '+repr(miss))
 req('desktop_redraw=1' not in s,'full desktop repaint re-enabled')
 arm=fn_text(s,'flight_log_arm_v125')
 for q in ('flight_fat32_find_log_v126','logsize!=4194304','let start=first+1','serial_marker_iso_log_r26'):
  req(q in arm,'ISO-native log target gate missing '+q)
 for fixed in ('133132','2391787741383512646','133152','395264'):
  req(fixed not in arm,'old raw logging-image geometry still present '+fixed)
 flush=fn_text(s,'flight_flush_one_v125')
 for q in ('usb_msc_bot_write10_v125','usb_msc_bot_nodata_v125','usb_msc_bot_read10','nvme_read_checksum(back,512)!=expected','flight_persist_fail_v126'):
  req(q in flush,'verified fail-open flush missing '+q)
 desktop=fn_text(s,'desktop_input_runtime');top=desktop.index('while true {');poll=desktop.index('if xhci!=0',top);flushpos=desktop.index('flight_flush_one_v125',poll)
 req(flushpos>poll,'persistent flush still precedes input polling')
 for n in ('nvme_write_target_serial_ok','nvme_write_target_arm','nvme_io_write_block_cert','nvme_io_flush_cert'):
  req(fn_text(a,n)==fn_text(s,n),f'internal write function changed: {n}')
 delta=subprocess.run(['diff','-u',str(r25k),str(r26)],text=True,stdout=subprocess.PIPE).stdout.lower()
 for bad in ('nvme_io_write_block_cert(', 'nvme_write_target_arm(', 'storage_write_commit', 'ahci_write'):
  req(not any(line.startswith('+') and bad in line for line in delta.splitlines()),'new internal write path '+bad)

def build_iso(F,iso):
 for p in F.rglob('*.sh'):p.chmod(p.stat().st_mode|0o111)
 for p in (F/'toolchain').rglob('nexus'):p.chmod(p.stat().st_mode|0o111)
 run(['./tools/build.sh'],cwd=F);run(['python3','tools/make_esp.py'],cwd=F);run(['python3','tools/sdk_selftest.py'],cwd=F);run(['python3','tools/make_desktop_preview_image.py'],cwd=F);run(['python3','tools/verify_desktop_preview_image.py','--image','build/Frames-0.9.98-Desktop-Preview.img','--require-pass'],cwd=F);run(['python3','tools/verify_release.py'],cwd=F)
 shutil.copy2(F/'build/Frames-0.9.98-Desktop-Preview.img',ROOT/'out/raw.img')
 first=subprocess.check_output("sgdisk -i 1 out/raw.img | awk -F: '/First sector/{gsub(/ /,\"\",$2);split($2,a,\"(\");print a[1]}'",cwd=ROOT,shell=True,text=True).strip();last=subprocess.check_output("sgdisk -i 1 out/raw.img | awk -F: '/Last sector/{gsub(/ /,\"\",$2);split($2,a,\"(\");print a[1]}'",cwd=ROOT,shell=True,text=True).strip();count=int(last)-int(first)+1
 run(f'dd if=out/raw.img of=out/esp.img bs=512 skip={first} count={count} status=none',cwd=ROOT);run("mcopy -s -i out/esp.img '::/EFI' payload/",cwd=ROOT);run("mcopy -s -i out/esp.img '::/FRAMES' payload/",cwd=ROOT)
 run('dd if=/dev/zero of=out/efiboot.img bs=1M count=16 status=none',cwd=ROOT);run('mkfs.fat -F 16 -n FRAMESBOOT out/efiboot.img >/dev/null',cwd=ROOT);run('mmd -i out/efiboot.img ::/EFI ::/EFI/BOOT ::/FRAMES',cwd=ROOT);run('mcopy -i out/efiboot.img payload/EFI/BOOT/BOOTX64.EFI ::/EFI/BOOT/BOOTX64.EFI',cwd=ROOT)
 for p in (ROOT/'payload/FRAMES').iterdir():run(['mcopy','-i',str(ROOT/'out/efiboot.img'),str(p),'::/FRAMES/'])
 with tempfile.TemporaryDirectory(prefix='r26iso-') as t:
  r=pathlib.Path(t);shutil.copy2(ROOT/'out/efiboot.img',r/'efiboot.img');shutil.copytree(ROOT/'payload/EFI',r/'EFI');shutil.copytree(ROOT/'payload/FRAMES',r/'FRAMES');build_log(r/'FRAMES.LOG');(r/'README.TXT').write_text('Frames 0.9.98 v108 r26 ISO-native Flight Recorder physical candidate (0.9.99 controlled-write groundwork)\nFlash this ISO with Rufus in normal ISO mode. FRAMES.LOG is preallocated at the USB root and is the only authorized persistent diagnostic file.\nInternal NVMe/SATA/ESP and all other USB files remain read-only.\n')
  req((r/'FRAMES.LOG').stat().st_size==LOG_BYTES,'FRAMES.LOG template size')
  run(['xorriso','-as','mkisofs','-iso-level','3','-R','-J','-V','FRAMES_V108_R26','-eltorito-alt-boot','-e','efiboot.img','-no-emul-boot','-o',str(iso),str(r)],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)

def main():
 r21=ROOT/'r21-candidate/evidence/kernel-r21.nx';req(r21.is_file() and sha(r21)==R21_SHA,'exact r21 source missing')
 kit=ROOT/'Frames-0.9.98-Runtime-Certification-Kit-v108-r9.zip';req(kit.is_file() and sha(kit)==KIT_SHA,'cert kit identity')
 for d in ('evidence','out','payload','final'):shutil.rmtree(ROOT/d,ignore_errors=True);(ROOT/d).mkdir(parents=True,exist_ok=True)
 with tempfile.TemporaryDirectory(prefix='r26cert-') as td:
  td=pathlib.Path(td);kd=td/'kit';sd=td/'src';kd.mkdir();sd.mkdir();run(['unzip','-q',kit,'-d',kd]);z=kd/'Frames-0.9.98-Source-v108.zip';req(sha(z)==SRC_SHA,'canonical source identity');run(['unzip','-q',z,'-d',sd]);F=sd/'Frames-0.9.98';shutil.copy2(r21,F/'kernel/main.nx')
  r25k=td/'kernel-r25k.nx';shutil.copy2(r21,r25k);run(['python3',ROOT/'tools/ci/patch_v108_r25k_large_media_log_gate.py',r25k],stdout=subprocess.PIPE);req(sha(r25k)==R25K_SHA,'r25k reconstruction');shutil.copy2(r25k,ROOT/'evidence/kernel-r25k.nx')
  rr=run(['python3',ROOT/'tools/ci/patch_v108_r26_iso_native_log.py',F/'kernel/main.nx'],stdout=subprocess.PIPE);(ROOT/'evidence/R26-SHA.txt').write_text(rr.stdout);req(sha(F/'kernel/main.nx')==R26_SHA,'r26 identity');shutil.copy2(F/'kernel/main.nx',ROOT/'evidence/kernel-r26.nx')
  diff=run(['diff','-u',r25k,F/'kernel/main.nx'],check=False,stdout=subprocess.PIPE).stdout;(ROOT/'evidence/R25K-R26.patch').write_text(diff);model_gate(r25k,F/'kernel/main.nx')
  (ROOT/'evidence/WRITE-POLICY.txt').write_text('status=PASS\nphysical_handoff=RUFUS_ISO_ONLY\nram_flight_recorder=ALWAYS_ON\npersistent_target=ROOT_FRAMES.LOG_ON_RUFUS_FAT_VOLUME\nlog_header=READ_ONLY_FIRST_512_BYTES\nwrite_range=PREALLOCATED_FRAMES.LOG_DATA_CLUSTERS_ONLY\nfilesystem_metadata_writes=BLOCKED\nother_usb_files=READ_ONLY\ninternal_nvme_sata_esp=READ_ONLY_UNCHANGED\nfirst_persistence_failure=DISARM_PERSISTENCE_KEEP_RAM_AND_DESKTOP\nreadback_verify=REQUIRED\n')
  build_iso(F,ROOT/'out'/ISO_NAME)
 iso_sha=sha(ROOT/'out'/ISO_NAME);(ROOT/'evidence/ISO-SHA256.txt').write_text(f'{iso_sha}  {ISO_NAME}\n');(ROOT/'evidence/ISO-SIZE.txt').write_text(str((ROOT/'out'/ISO_NAME).stat().st_size)+'\n')
 target=ROOT/'out/r26-rufus-target-ci.img';run(['python3','tools/ci/make_r26_rufus_target.py','--payload','payload','--out',target,'--evidence','evidence'],cwd=ROOT);man=ROOT/'evidence/R26-RUFUS-TARGET.json';req(json.loads(man.read_text())['status']=='PASS','Rufus target builder')
 ovmfs=list(pathlib.Path('/usr/share/OVMF').rglob('OVMF_CODE_4M.fd'))+list(pathlib.Path('/usr/share/OVMF').rglob('OVMF_CODE.fd'));req(ovmfs,'OVMF');ovmf=str(ovmfs[0]);g=ROOT/'evidence/gates';g.mkdir()
 tests=[
  ('interaction',['python3','tools/ci/qemu_r23_dragright_guard_gate.py','--ovmf',ovmf,'--iso',str(ROOT/'out'/ISO_NAME),'--out',str(g/'interaction'),'--expected-iso-sha',iso_sha],g/'interaction/R23-INTERACTION.json'),
  ('usb-direct',['python3','tools/ci/qemu_usb_hub_topology_gate_r3.py','--ovmf',ovmf,'--iso',str(ROOT/'out'/ISO_NAME),'--out',str(g/'usb-direct'),'--expected-iso-sha',iso_sha,'--topology','direct'],g/'usb-direct/TOPOLOGY.json'),
  ('usb-hub',['python3','tools/ci/qemu_usb_hub_topology_gate_r3.py','--ovmf',ovmf,'--iso',str(ROOT/'out'/ISO_NAME),'--out',str(g/'usb-hub'),'--expected-iso-sha',iso_sha,'--topology','hub'],g/'usb-hub/TOPOLOGY.json'),
  ('usb-multi',['python3','tools/ci/qemu_usb_hub_multichild_gate_r17.py','--ovmf',ovmf,'--iso',str(ROOT/'out'/ISO_NAME),'--out',str(g/'usb-multi'),'--expected-iso-sha',iso_sha],g/'usb-multi/MULTICHILD-R17.json'),
  ('usb-ctl',['python3','tools/ci/qemu_usb_multicontroller_gate_r16.py','--ovmf',ovmf,'--iso',str(ROOT/'out'/ISO_NAME),'--out',str(g/'usb-ctl'),'--expected-iso-sha',iso_sha],g/'usb-ctl/USB-MULTICONTROLLER.json'),
  ('usb-kbd',['python3','tools/ci/qemu_usb_keyboard_gate_r17.py','--ovmf',ovmf,'--iso',str(ROOT/'out'/ISO_NAME),'--out',str(g/'usb-kbd'),'--expected-iso-sha',iso_sha],g/'usb-kbd/USB-KEYBOARD.json'),
  ('ps2',['python3','tools/ci/qemu_ps2_delivery_gate_r17.py','--ovmf',ovmf,'--iso',str(ROOT/'out'/ISO_NAME),'--out',str(g/'ps2'),'--expected-iso-sha',iso_sha],g/'ps2/PS2-DELIVERY.json'),
  ('smooth',['python3','tools/ci/qemu_ps2_cursor_smoothness_r23.py','--ovmf',ovmf,'--iso',str(ROOT/'out'/ISO_NAME),'--out',str(g/'smooth'),'--expected-iso-sha',iso_sha],g/'smooth/SMOOTHNESS.json'),
  ('text',['python3','tools/ci/qemu_text_edit_gate_r15.py','--ovmf',ovmf,'--iso',str(ROOT/'out'/ISO_NAME),'--out',str(g/'text'),'--expected-iso-sha',iso_sha],g/'text/TEXT-EDIT.json'),
  ('focus',['python3','tools/ci/qemu_focus_persistence_gate_r17.py','--ovmf',ovmf,'--iso',str(ROOT/'out'/ISO_NAME),'--out',str(g/'focus'),'--expected-iso-sha',iso_sha],g/'focus/FOCUS-PERSISTENCE.json')]
 status={}
 for n,cmd,jp in tests:pathlib.Path(cmd[cmd.index('--out')+1]).mkdir(parents=True,exist_ok=True);run(cmd,cwd=ROOT);jsonpass(jp);status[n]='PASS';(g/n/'RESULT.status').write_text('PASS\n')
 lg=g/'iso-log';lg.mkdir();run(['python3','tools/ci/qemu_r25_flight_log_gate.py','--ovmf',ovmf,'--iso',ROOT/'out'/ISO_NAME,'--log-image',target,'--manifest',man,'--out',lg,'--expected-iso-sha',iso_sha],cwd=ROOT);jsonpass(lg/'R25-FLIGHT-LOG.json');status['iso-log']='PASS';(lg/'RESULT.status').write_text('PASS\n')
 fo=g/'log-failopen';fo.mkdir();run(['python3','tools/ci/qemu_r26_log_failopen_gate.py','--ovmf',ovmf,'--iso',ROOT/'out'/ISO_NAME,'--target',target,'--out',fo,'--expected-iso-sha',iso_sha],cwd=ROOT);jsonpass(fo/'R26-LOG-FAILOPEN.json');status['log-failopen']='PASS';(fo/'RESULT.status').write_text('PASS\n')
 sd2=g/'safety';sd2.mkdir();sent=sd2/'sentinel.img';sent.write_bytes(b'\0'*(32*1024*1024));before=sha(sent);ser=sd2/'serial.log';err=sd2/'stderr';cmd=f'timeout 90 qemu-system-x86_64 -machine q35 -m 768M -smp 2 -cpu max -accel tcg,thread=single -display none -no-reboot -no-shutdown -nic none -serial file:{ser} -drive if=pflash,format=raw,readonly=on,file={ovmf} -cdrom {ROOT/"out"/ISO_NAME} -boot d -drive file={sent},if=none,format=raw,readonly=on,id=s -device nvme,drive=s,serial=R26_INTERNAL_SENTINEL >/dev/null 2>{err}';run(cmd,cwd=ROOT,check=False);after=sha(sent);req(after==before,'internal safety sentinel changed');req('FRAMES_FLIGHT_RECORDER_R25_READY' in ser.read_text(errors='ignore'),'RAM flight recorder not initialized');(sd2/'SAFETY.txt').write_text(f'before={before}\nafter={after}\n');(sd2/'RESULT.status').write_text('PASS\n');status['safety']='PASS'
 model_gate(ROOT/'evidence/kernel-r25k.nx',ROOT/'evidence/kernel-r26.nx');(g/'model').mkdir();(g/'model/RESULT.status').write_text('PASS\n');status['model']='PASS'
 m=json.loads(man.read_text());agg={'status':'PASS','profile':'frames-0.9.98-v108-r26-iso-native-flight-recorder-write-groundwork','kernel_sha256':R26_SHA,'iso_sha256':iso_sha,'gates':status,'physical_r24':'PARTIAL_PASS_RIGHT_CLICK_USB_OPEN','physical_r25_iso':'DESKTOP_GOOD_LOG_NOT_ARMED','physical_r25_img':'FAIL_BOOT_INPUT','physical_r26':'PENDING','physical_handoff':'RUFUS_ISO_ONLY','persistent_log':'ROOT_FRAMES.LOG','authorized_lba_policy':'PREALLOCATED_FILE_DATA_ONLY','internal_media_writes':'BLOCKED','controlled_usb_log_write':'VM_CERTIFIED_PHYSICAL_PENDING'};(ROOT/'evidence/R26-AGGREGATE.json').write_text(json.dumps(agg,indent=2)+'\n')
 final=ROOT/'final';shutil.copy2(ROOT/'out'/ISO_NAME,final/ISO_NAME);(final/'ISO-SHA256.txt').write_text(f'{iso_sha}  {ISO_NAME}\n');(final/'CERTIFICATION.txt').write_text('Frames 0.9.98 v108 r26 — ISO-Native Flight Recorder + Input/USB Repair\nstatus=PASS_VM_PENDING_PHYSICAL\nphysical_handoff=RUFUS_ISO_ONLY\nFRAMES.LOG=PREALLOCATED_AT_ISO_ROOT_FOR_RUFUS_FAT_VOLUME\nram_flight_recorder=PASS_VM\niso_native_controlled_log_write=PASS_VM_PENDING_PHYSICAL\nlog_write_failure=DISARM_PERSISTENCE_KEEP_DESKTOP_AND_RAM_RECORDER\nright_click=PHYSICAL_PENDING\nphysical_usb_hid=PHYSICAL_PENDING\ninternal_nvme_sata_esp=READ_ONLY\nall_other_usb_files=READ_ONLY\ngeneral_writes=BLOCKED\n')
 target.unlink(missing_ok=True)
 print('R26 PASS_VM_PENDING_PHYSICAL',iso_sha)
if __name__=='__main__':main()
