#!/usr/bin/env python3
import hashlib,json,pathlib,shutil,subprocess,tempfile,struct
ROOT=pathlib.Path.cwd()
KIT_SHA='61b0fc25513719fce554729724c7848647de9cffe54434d4ab5f7ba8af42a36a'
SRC_SHA='5f8c13adac6d34e64bd47d9463a3e261cd0b51bb5ddb500aa9f7b87c2914a52d'
R21_SHA='bed3740e10c3bab8b5c81ca6b2fb77668b33bdc9109039a38e2e40aa09c7efb9'
R24_SHA='1b56b621de728aabdbbe8c100f92816564369e984f1fc2b5e4815080011aedaf'
R25L_SHA='01958cc0495a68ff12f399a21e7fb8a25d676e5e4a09e9810814d99bc57ca11d'
ISO_NAME='Frames-0.9.98-v108-Physical-Input-Repair-r25l-ISO-Native-FlightRecorder-Rufus-UEFI.iso'
CI_LOG_NAME='r25l-ci-rufus-log-volume.img'
NONCE=3545795563478602310
LOG_BYTES=4*1024*1024

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

def model_gate(r24,r25l):
 a=pathlib.Path(r24).read_text();s=pathlib.Path(r25l).read_text()
 needed=['fn flight_recorder_init_v125','fn flight_record_v125','fn flight_flush_one_v125','fn usb_msc_bot_write10_v125','fn flight_log_arm_v125','fn flight_fat32_find_root_v125','fn flight_fat32_contig_v125','fn flight_fat_name_v125','fn v108_msc_snapshot_v125','fn v108_log_msc_retain_v125','flight_input_record_v125(input_state,131072+typ,a,b)','typ>=1 && typ<=3','var need:u64=3','if eslot==slot && ep==dci','serial_usb_msc_diag(46','3550878661635560006','volatile_read64(fr+32)>=40','flight_recorder_init_v125(flight_state,flight_buffer,262144)']
 miss=[x for x in needed if x not in s];req(not miss,'r25l model missing '+repr(miss));req('desktop_redraw=1' not in s,'full desktop repaint re-enabled')
 for n in ('nvme_write_target_serial_ok','nvme_write_target_arm','nvme_io_write_block_cert','nvme_io_flush_cert'):req(fn_text(a,n)==fn_text(s,n),f'internal write function changed: {n}')
 arm=fn_text(s,'flight_log_arm_v125')
 for q in ('flight_fat32_find_root_v125','logsize!=4194304','volatile_read64(td+16)!=3545795563478602310','flight_fat32_contig_v125','volatile_write64(fr+72,start)','volatile_write64(fr+80,end)'):req(q in arm,'ISO-native log target gate missing '+q)
 req('133132' not in arm,'legacy fixed logging-image LBA still present')
 flush=fn_text(s,'flight_flush_one_v125')
 for q in ('usb_msc_bot_write10_v125','usb_msc_bot_nodata_v125','usb_msc_bot_read10','nvme_read_checksum(back,512)!=expected','volatile_write64(fr+64,0)'):req(q in flush,'verified/fail-closed flush missing '+q)
 wait=fn_text(s,'xhci_wait_bulk_event');req('while spins<500000' in wait,'bounded MSC wait missing')
 hid=fn_text(s,'xhci_wait_hid_event');req('while spins<16000000' in hid,'HID wait timing changed')
 delta=subprocess.run(['diff','-u',str(r24),str(r25l)],text=True,stdout=subprocess.PIPE).stdout.lower()
 for bad in ('nvme_io_write_block_cert(', 'nvme_write_target_arm(', 'storage_write_commit', 'ahci_write'):
  req(not any(line.startswith('+') and bad in line for line in delta.splitlines()),'new internal write path '+bad)

def make_root_log_files(root):
 log=root/'FRAMES.LOG';tag=root/'FRAMES.TAG'
 header=b'Frames r25l System Flight Recorder\r\nPersistent records begin below; trailing spaces are unused.\r\n'
 with open(log,'wb') as f:
  f.write(header);remaining=LOG_BYTES-len(header);chunk=b' '*1024*1024
  while remaining:
   n=min(remaining,len(chunk));f.write(chunk[:n]);remaining-=n
 tag.write_bytes(b'FRMSTAG1'+struct.pack('<QQQ',1,NONCE,LOG_BYTES))
 req(log.stat().st_size==LOG_BYTES,'root FRAMES.LOG size');req(tag.stat().st_size==32,'root FRAMES.TAG size')

def build_iso(F,iso):
 for p in F.rglob('*.sh'):p.chmod(p.stat().st_mode|0o111)
 for p in (F/'toolchain').rglob('nexus'):p.chmod(p.stat().st_mode|0o111)
 run(['./tools/build.sh'],cwd=F);run(['python3','tools/make_esp.py'],cwd=F);run(['python3','tools/sdk_selftest.py'],cwd=F);run(['python3','tools/make_desktop_preview_image.py'],cwd=F);run(['python3','tools/verify_desktop_preview_image.py','--image','build/Frames-0.9.98-Desktop-Preview.img','--require-pass'],cwd=F);run(['python3','tools/verify_release.py'],cwd=F)
 shutil.copy2(F/'build/Frames-0.9.98-Desktop-Preview.img',ROOT/'out/raw.img')
 first=subprocess.check_output("sgdisk -i 1 out/raw.img | awk -F: '/First sector/{gsub(/ /,\"\",$2);split($2,a,\"(\");print a[1]}'",cwd=ROOT,shell=True,text=True).strip();last=subprocess.check_output("sgdisk -i 1 out/raw.img | awk -F: '/Last sector/{gsub(/ /,\"\",$2);split($2,a,\"(\");print a[1]}'",cwd=ROOT,shell=True,text=True).strip();count=int(last)-int(first)+1
 run(f'dd if=out/raw.img of=out/esp.img bs=512 skip={first} count={count} status=none',cwd=ROOT);run("mcopy -s -i out/esp.img '::/EFI' payload/",cwd=ROOT);run("mcopy -s -i out/esp.img '::/FRAMES' payload/",cwd=ROOT)
 run('dd if=/dev/zero of=out/efiboot.img bs=1M count=16 status=none',cwd=ROOT);run('mkfs.fat -F 16 -n FRAMESBOOT out/efiboot.img >/dev/null',cwd=ROOT);run('mmd -i out/efiboot.img ::/EFI ::/EFI/BOOT ::/FRAMES',cwd=ROOT);run('mcopy -i out/efiboot.img payload/EFI/BOOT/BOOTX64.EFI ::/EFI/BOOT/BOOTX64.EFI',cwd=ROOT)
 for p in (ROOT/'payload/FRAMES').iterdir():run(['mcopy','-i',str(ROOT/'out/efiboot.img'),str(p),'::/FRAMES/'])
 with tempfile.TemporaryDirectory(prefix='r25liso-') as t:
  r=pathlib.Path(t);shutil.copy2(ROOT/'out/efiboot.img',r/'efiboot.img');shutil.copytree(ROOT/'payload/EFI',r/'EFI');shutil.copytree(ROOT/'payload/FRAMES',r/'FRAMES');make_root_log_files(r)
  (r/'README.TXT').write_text('Frames v108 r25l ISO-native Flight Recorder physical candidate\nFlash this ISO with Rufus in normal ISO mode. FRAMES.LOG stays at the USB root and is the only authorized persistent write target.\nInternal NVMe/SATA/ESP and all other USB ranges remain read-only.\n')
  run(['xorriso','-as','mkisofs','-iso-level','3','-R','-J','-V','FRAMES_V108_R25L','-eltorito-alt-boot','-e','efiboot.img','-no-emul-boot','-o',str(iso),str(r)],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)

def verify_iso_log_payload(iso):
 with tempfile.TemporaryDirectory(prefix='r25l-iso-check-') as td:
  td=pathlib.Path(td);log=td/'FRAMES.LOG';tag=td/'FRAMES.TAG'
  run(['xorriso','-osirrox','on','-indev',str(iso),'-extract','/FRAMES.LOG',str(log)],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
  run(['xorriso','-osirrox','on','-indev',str(iso),'-extract','/FRAMES.TAG',str(tag)],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
  req(log.stat().st_size==LOG_BYTES,'ISO FRAMES.LOG missing/wrong size');req(tag.read_bytes()==b'FRMSTAG1'+struct.pack('<QQQ',1,NONCE,LOG_BYTES),'ISO FRAMES.TAG mismatch')

def main():
 r21=ROOT/'r21-candidate/evidence/kernel-r21.nx';req(r21.is_file() and sha(r21)==R21_SHA,'exact r21 source missing')
 kit=ROOT/'Frames-0.9.98-Runtime-Certification-Kit-v108-r9.zip';req(kit.is_file() and sha(kit)==KIT_SHA,'cert kit identity')
 for d in ('evidence','out','payload','final'):shutil.rmtree(ROOT/d,ignore_errors=True);(ROOT/d).mkdir(parents=True,exist_ok=True)
 with tempfile.TemporaryDirectory(prefix='r25lcert-') as td:
  td=pathlib.Path(td);kd=td/'kit';sd=td/'src';kd.mkdir();sd.mkdir();run(['unzip','-q',kit,'-d',kd]);z=kd/'Frames-0.9.98-Source-v108.zip';req(sha(z)==SRC_SHA,'canonical source identity');run(['unzip','-q',z,'-d',sd]);F=sd/'Frames-0.9.98';shutil.copy2(r21,F/'kernel/main.nx')
  r24=td/'kernel-r24.nx';shutil.copy2(r21,r24);run(['python3',ROOT/'tools/ci/patch_v108_physical_input_r24b_fixbrace.py',r24],stdout=subprocess.PIPE);req(sha(r24)==R24_SHA,'r24 reconstruction');shutil.copy2(r24,ROOT/'evidence/kernel-r24.nx')
  rr=run(['python3',ROOT/'tools/ci/patch_v108_r25l_iso_native_log.py',F/'kernel/main.nx'],stdout=subprocess.PIPE);(ROOT/'evidence/R25L-SHA.txt').write_text(rr.stdout);req(sha(F/'kernel/main.nx')==R25L_SHA,'r25l identity');shutil.copy2(F/'kernel/main.nx',ROOT/'evidence/kernel-r25l.nx')
  diff=run(['diff','-u',r24,F/'kernel/main.nx'],check=False,stdout=subprocess.PIPE).stdout;(ROOT/'evidence/R24-R25L.patch').write_text(diff);model_gate(r24,F/'kernel/main.nx');(ROOT/'evidence/WRITE-POLICY.txt').write_text('status=PASS\ninternal_media=READ_ONLY_UNCHANGED\nphysical_boot=RUFUS_ISO_MODE\nnew_write_path=USB_MSC_WRITE10_ONLY\ntarget=USB_CONTAINING_EXACT_FRAMES.LOG_AND_FRAMES.TAG\nrange=PREALLOCATED_CONTIGUOUS_FRAMES.LOG_CLUSTERS_ONLY\nfat_metadata_writes=BLOCKED\nreadback_verify=REQUIRED\npersistence_failure=DISABLE_PERSISTENCE_KEEP_RAM_RECORDER_AND_DESKTOP\n')
  build_iso(F,ROOT/'out'/ISO_NAME)
 iso=ROOT/'out'/ISO_NAME;iso_sha=sha(iso);verify_iso_log_payload(iso);(ROOT/'evidence/ISO-SHA256.txt').write_text(f'{iso_sha}  {ISO_NAME}\n');(ROOT/'evidence/ISO-SIZE.txt').write_text(str(iso.stat().st_size)+'\n')
 ci_log=ROOT/'out'/CI_LOG_NAME;run(['python3','tools/ci/make_r25l_rufus_log_volume.py','--out',ci_log,'--evidence','evidence'],cwd=ROOT);man=ROOT/'evidence/R25L-RUFUS-LOG-VOLUME.json';req(ci_log.stat().st_size==268435456,'CI log volume size')
 ovmfs=list(pathlib.Path('/usr/share/OVMF').rglob('OVMF_CODE_4M.fd'))+list(pathlib.Path('/usr/share/OVMF').rglob('OVMF_CODE.fd'));req(ovmfs,'OVMF');ovmf=str(ovmfs[0]);g=ROOT/'evidence/gates';g.mkdir()
 tests=[
 ('interaction',['python3','tools/ci/qemu_r23_dragright_guard_gate.py','--ovmf',ovmf,'--iso',str(iso),'--out',str(g/'interaction'),'--expected-iso-sha',iso_sha],g/'interaction/R23-INTERACTION.json'),
 ('usb-direct',['python3','tools/ci/qemu_usb_hub_topology_gate_r3.py','--ovmf',ovmf,'--iso',str(iso),'--out',str(g/'usb-direct'),'--expected-iso-sha',iso_sha,'--topology','direct'],g/'usb-direct/TOPOLOGY.json'),
 ('usb-hub',['python3','tools/ci/qemu_usb_hub_topology_gate_r3.py','--ovmf',ovmf,'--iso',str(iso),'--out',str(g/'usb-hub'),'--expected-iso-sha',iso_sha,'--topology','hub'],g/'usb-hub/TOPOLOGY.json'),
 ('usb-multi',['python3','tools/ci/qemu_usb_hub_multichild_gate_r17.py','--ovmf',ovmf,'--iso',str(iso),'--out',str(g/'usb-multi'),'--expected-iso-sha',iso_sha],g/'usb-multi/MULTICHILD-R17.json'),
 ('usb-ctl',['python3','tools/ci/qemu_usb_multicontroller_gate_r16.py','--ovmf',ovmf,'--iso',str(iso),'--out',str(g/'usb-ctl'),'--expected-iso-sha',iso_sha],g/'usb-ctl/USB-MULTICONTROLLER.json'),
 ('usb-kbd',['python3','tools/ci/qemu_usb_keyboard_gate_r17.py','--ovmf',ovmf,'--iso',str(iso),'--out',str(g/'usb-kbd'),'--expected-iso-sha',iso_sha],g/'usb-kbd/USB-KEYBOARD.json'),
 ('ps2',['python3','tools/ci/qemu_ps2_delivery_gate_r17.py','--ovmf',ovmf,'--iso',str(iso),'--out',str(g/'ps2'),'--expected-iso-sha',iso_sha],g/'ps2/PS2-DELIVERY.json'),
 ('smooth',['python3','tools/ci/qemu_ps2_cursor_smoothness_r23.py','--ovmf',ovmf,'--iso',str(iso),'--out',str(g/'smooth'),'--expected-iso-sha',iso_sha],g/'smooth/SMOOTHNESS.json'),
 ('text',['python3','tools/ci/qemu_text_edit_gate_r15.py','--ovmf',ovmf,'--iso',str(iso),'--out',str(g/'text'),'--expected-iso-sha',iso_sha],g/'text/TEXT-EDIT.json'),
 ('focus',['python3','tools/ci/qemu_focus_persistence_gate_r17.py','--ovmf',ovmf,'--iso',str(iso),'--out',str(g/'focus'),'--expected-iso-sha',iso_sha],g/'focus/FOCUS-PERSISTENCE.json')]
 status={}
 for n,cmd,jp in tests:pathlib.Path(cmd[cmd.index('--out')+1]).mkdir(parents=True,exist_ok=True);run(cmd,cwd=ROOT);jsonpass(jp);status[n]='PASS';(g/n/'RESULT.status').write_text('PASS\n')
 lg=g/'flight-log';lg.mkdir();run(['python3','tools/ci/qemu_r25_flight_log_gate.py','--ovmf',ovmf,'--iso',iso,'--log-image',ci_log,'--manifest',man,'--out',lg,'--expected-iso-sha',iso_sha],cwd=ROOT);jsonpass(lg/'R25-FLIGHT-LOG.json');status['iso-native-flight-log']='PASS';(lg/'RESULT.status').write_text('PASS\n')
 sd=g/'safety';sd.mkdir();sent=sd/'sentinel.img';sent.write_bytes(b'\0'*(32*1024*1024));b=sha(sent);ser=sd/'serial.log';err=sd/'stderr';cmd=f'timeout 90 qemu-system-x86_64 -machine q35 -m 768M -smp 2 -cpu max -accel tcg,thread=single -display none -no-reboot -no-shutdown -nic none -serial file:{ser} -drive if=pflash,format=raw,readonly=on,file={ovmf} -cdrom {iso} -boot d -drive file={sent},if=none,format=raw,readonly=on,id=s -device nvme,drive=s,serial=R25L_INTERNAL_SENTINEL >/dev/null 2>{err}';run(cmd,cwd=ROOT,check=False);a=sha(sent);req(a==b,'internal safety sentinel changed');req('FRAMES_FLIGHT_RECORDER_R25_READY' in ser.read_text(errors='ignore'),'flight recorder not initialized');(sd/'SAFETY.txt').write_text(f'before={b}\nafter={a}\n');(sd/'RESULT.status').write_text('PASS\n');status['safety']='PASS'
 model_gate(ROOT/'evidence/kernel-r24.nx',ROOT/'evidence/kernel-r25l.nx');(g/'model').mkdir();(g/'model/RESULT.status').write_text('PASS\n');status['model']='PASS'
 agg={'status':'PASS','profile':'frames-v108-r25l-iso-native-flight-recorder','kernel_sha256':R25L_SHA,'iso_sha256':iso_sha,'gates':status,'physical_r24':'PARTIAL_PASS_RIGHT_CLICK_USB_OPEN','physical_r25_logging_img':'FAIL_BOOT_AND_INPUT_REGRESSION','physical_r25l':'PENDING','handoff_media':'RUFUS_ISO_ONLY','internal_media_writes':'BLOCKED','fat_metadata_writes':'BLOCKED','controlled_iso_usb_log_write':'VM_CERTIFIED_PHYSICAL_PENDING'};(ROOT/'evidence/R25L-AGGREGATE.json').write_text(json.dumps(agg,indent=2)+'\n')
 final=ROOT/'final';shutil.copy2(iso,final/ISO_NAME);(final/'ISO-SHA256.txt').write_text(f'{iso_sha}  {ISO_NAME}\n');(final/'CERTIFICATION.txt').write_text('Frames v108 r25l ISO-native Flight Recorder + controlled boot-USB log candidate\nstatus=PASS_VM_PENDING_PHYSICAL\nphysical_media=RUFUS_ISO_ONLY\nFRAMES.LOG=ISO_ROOT_PREALLOCATED_4MiB\nFRAMES.TAG=ISO_ROOT_AUTHORIZATION_MARKER\nram_flight_recorder=PASS_VM\ncontrolled_same_usb_log_write=PASS_VM_PENDING_PHYSICAL\nlog_failure_policy=DISABLE_PERSISTENCE_KEEP_DESKTOP_RUNNING\ninternal_nvme_sata_esp=READ_ONLY\nfat_metadata_writes=BLOCKED\ngeneral_writes=BLOCKED\nright_click_and_physical_usb=STILL_ACTIVE_REPAIR_WORK\n')
 print('R25L PASS_VM_PENDING_PHYSICAL',iso_sha)
if __name__=='__main__':main()
