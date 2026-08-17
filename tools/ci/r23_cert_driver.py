#!/usr/bin/env python3
import hashlib,json,os,pathlib,shutil,subprocess,tempfile

ROOT=pathlib.Path.cwd()
SOURCE_RUN='31979817129'
KIT_SHA='61b0fc25513719fce554729724c7848647de9cffe54434d4ab5f7ba8af42a36a'
SRC_SHA='5f8c13adac6d34e64bd47d9463a3e261cd0b51bb5ddb500aa9f7b87c2914a52d'
R21_SHA='bed3740e10c3bab8b5c81ca6b2fb77668b33bdc9109039a38e2e40aa09c7efb9'
R22_SHA='1dab5bf8336d90401faf2f27df670dc5a817bcca1bcb8be186889a9842d3af2f'
R23_SHA='ce61a788ca5aba773aef61c9e73d3d1eba25614984eeb5fe6930b20da0eaa556'
ISO_NAME='Frames-0.9.98-v108-Physical-Input-Repair-r23-Drag-Right-Guard-XHCI-Port-Census-Rufus-UEFI.iso'

def sha(p):
    h=hashlib.sha256()
    with open(p,'rb') as f:
        for b in iter(lambda:f.read(1024*1024),b''): h.update(b)
    return h.hexdigest()

def run(cmd,cwd=None,check=True,stdout=None,stderr=None):
    print('+',cmd,flush=True)
    return subprocess.run(cmd,cwd=cwd,shell=isinstance(cmd,str),check=check,text=True,stdout=stdout,stderr=stderr)

def require(cond,msg):
    if not cond: raise RuntimeError(msg)

def json_pass(p):
    d=json.loads(pathlib.Path(p).read_text())
    require(d.get('status')=='PASS',f'{p}: status != PASS: {d}')

def fn_text(s,name):
    st=s.index('fn '+name); i=s.index('{',st); d=0
    for j in range(i,len(s)):
        if s[j]=='{': d+=1
        elif s[j]=='}':
            d-=1
            if d==0:return s[st:j+1]
    raise RuntimeError('unterminated '+name)

def model_gate(k):
    s=pathlib.Path(k).read_text()
    req=[
      'fn v108_xhci_port_census_ro_v123','fn v108_text_xprt_v123','serial_marker_v108_xhci_port_census_v123',
      'left!=0 || old_left!=0 || volatile_read64(state+176)!=0',
      'if volatile_read64(state+128)!=0','dx<=4 && dy<=4',
      'volatile_write64(xhci_state+1600,volatile_read64(hardware_state+560))',
      'volatile_write64(xhci_state+1632,volatile_read64(hardware_state+592))',
      '(276*65536)+156','fn serial_marker_v108_drag_live_v122','fn serial_marker_v108_focus_transfer_v122'
    ]
    missing=[x for x in req if x not in s]; require(not missing,'model missing '+repr(missing))
    require('desktop_redraw=1' not in s,'full desktop repaint re-enabled')
    for n in ('v108_drag_proxy_present_v119','v108_drag_commit_present_v121'):
        body=fn_text(s,n); require('v108_drag_outline_toggle_v119' not in body,n+' still uses XOR outline'); require('v108_drag_window_draw_v116' in body,n+' does not draw full window')
    body=fn_text(s,'gui_input_buttons')
    for q in ('left!=0 || old_left!=0 || volatile_read64(state+176)!=0','if volatile_read64(state+128)!=0','dx<=4 && dy<=4'):
        require(q in body,'right/drag guard missing '+q)
    census=fn_text(s,'v108_xhci_port_census_ro_v123')
    for bad in ('volatile_write32','volatile_write16','volatile_write8','pci_cfg_write'):
        require(bad not in census,'xHCI census contains forbidden write '+bad)
    for n in ('v108_ehci_ro_one_v122','v108_ehci_ro_probe_v122'):
        body=fn_text(s,n)
        for bad in ('pci_cfg_write','volatile_write32(op','volatile_write8(op','volatile_write16(op'):
            require(bad not in body,n+' contains forbidden EHCI controller write '+bad)

def main():
    r21=ROOT/'r21-candidate/evidence/kernel-r21.nx'; require(r21.is_file(),'r21 candidate kernel missing'); require(sha(r21)==R21_SHA,'r21 kernel identity mismatch')
    kit=ROOT/'Frames-0.9.98-Runtime-Certification-Kit-v108-r9.zip'; require(kit.is_file(),'cert kit missing'); require(sha(kit)==KIT_SHA,'cert kit SHA mismatch')
    for d in ('evidence','out','payload','final'):
        shutil.rmtree(ROOT/d,ignore_errors=True); (ROOT/d).mkdir(parents=True,exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='r23cert-') as td:
        td=pathlib.Path(td); kd=td/'kit'; sd=td/'src'; kd.mkdir(); sd.mkdir()
        run(['unzip','-q',str(kit),'-d',str(kd)])
        z=kd/'Frames-0.9.98-Source-v108.zip'; require(sha(z)==SRC_SHA,'canonical source SHA mismatch')
        run(['unzip','-q',str(z),'-d',str(sd)])
        F=sd/'Frames-0.9.98'; require(F.is_dir(),'Frames source root missing')
        shutil.copy2(r21,F/'kernel/main.nx'); shutil.copy2(r21,ROOT/'evidence/kernel-r21.nx')
        r22tmp=td/'kernel-r22.nx'; shutil.copy2(r21,r22tmp)
        rr22=run(['python3',str(ROOT/'tools/ci/patch_v108_physical_input_r22_livefocus_ehci.py'),str(r22tmp)],stdout=subprocess.PIPE)
        require(sha(r22tmp)==R22_SHA,'r22 comparison kernel SHA mismatch'); shutil.copy2(r22tmp,ROOT/'evidence/kernel-r22.nx'); (ROOT/'evidence/R22-SHA.txt').write_text(rr22.stdout)
        r=run(['python3',str(ROOT/'tools/ci/patch_v108_physical_input_r23_dragright_xhci_ro.py'),str(F/'kernel/main.nx')],stdout=subprocess.PIPE)
        (ROOT/'evidence/R23-SHA.txt').write_text(r.stdout)
        require(sha(F/'kernel/main.nx')==R23_SHA,'r23 kernel SHA mismatch')
        shutil.copy2(F/'kernel/main.nx',ROOT/'evidence/kernel-r23.nx')
        diff=run(['diff','-u',str(ROOT/'evidence/kernel-r21.nx'),str(ROOT/'evidence/kernel-r23.nx')],check=False,stdout=subprocess.PIPE).stdout
        (ROOT/'evidence/R21-R23.patch').write_text(diff)
        delta=run(['diff','-u',str(ROOT/'evidence/kernel-r22.nx'),str(ROOT/'evidence/kernel-r23.nx')],check=False,stdout=subprocess.PIPE).stdout
        (ROOT/'evidence/R22-R23.patch').write_text(delta)
        low=diff.lower(); bad=['nvme_write','storage_write','write10','write(10)','scsi_write','fat_write','block_write','destructive_write','physical_write_enable']; hits=[x for x in bad if x in low]
        (ROOT/'evidence/WRITE-SURFACE.txt').write_text('status='+('PASS' if not hits else 'FAIL')+'\nhits='+','.join(hits)+'\n'); require(not hits,'physical write surface changed '+repr(hits))
        model_gate(F/'kernel/main.nx')
        for p in F.rglob('*.sh'): p.chmod(p.stat().st_mode|0o111)
        for p in (F/'toolchain').rglob('nexus'): p.chmod(p.stat().st_mode|0o111)
        run(['./tools/build.sh'],cwd=F); run(['python3','tools/make_esp.py'],cwd=F); run(['python3','tools/sdk_selftest.py'],cwd=F); run(['python3','tools/make_desktop_preview_image.py'],cwd=F); run(['python3','tools/verify_desktop_preview_image.py','--image','build/Frames-0.9.98-Desktop-Preview.img','--require-pass'],cwd=F); run(['python3','tools/verify_release.py'],cwd=F)
        shutil.copy2(F/'build/Frames-0.9.98-Desktop-Preview.img',ROOT/'out/raw.img')
        first=subprocess.check_output("sgdisk -i 1 out/raw.img | awk -F: '/First sector/{gsub(/ /,\"\",$2);split($2,a,\"(\");print a[1]}'",cwd=ROOT,shell=True,text=True).strip()
        last=subprocess.check_output("sgdisk -i 1 out/raw.img | awk -F: '/Last sector/{gsub(/ /,\"\",$2);split($2,a,\"(\");print a[1]}'",cwd=ROOT,shell=True,text=True).strip()
        count=int(last)-int(first)+1
        run(f'dd if=out/raw.img of=out/esp.img bs=512 skip={first} count={count} status=none',cwd=ROOT)
        run("mcopy -s -i out/esp.img '::/EFI' payload/",cwd=ROOT); run("mcopy -s -i out/esp.img '::/FRAMES' payload/",cwd=ROOT)
        run('dd if=/dev/zero of=out/efiboot.img bs=1M count=16 status=none',cwd=ROOT); run('mkfs.fat -F 16 -n FRAMESBOOT out/efiboot.img >/dev/null',cwd=ROOT); run('mmd -i out/efiboot.img ::/EFI ::/EFI/BOOT ::/FRAMES',cwd=ROOT); run('mcopy -i out/efiboot.img payload/EFI/BOOT/BOOTX64.EFI ::/EFI/BOOT/BOOTX64.EFI',cwd=ROOT)
        for p in (ROOT/'payload/FRAMES').iterdir(): run(['mcopy','-i',str(ROOT/'out/efiboot.img'),str(p),'::/FRAMES/'])
        isoroot=td/'iso-root'; isoroot.mkdir(); shutil.copy2(ROOT/'out/efiboot.img',isoroot/'efiboot.img'); shutil.copytree(ROOT/'payload/EFI',isoroot/'EFI'); shutil.copytree(ROOT/'payload/FRAMES',isoroot/'FRAMES'); (isoroot/'README.TXT').write_text('Frames v108 r23 physical input corrective diagnostic\nr22 physical failure: spurious right-edge/menu spam stole left drag\nr23: left-drag priority + singleton context menu + read-only xHCI PORTSC census\nRufus ISO Image mode\nRead-only diagnostic only\n')
        iso=ROOT/'out'/ISO_NAME
        run(['xorriso','-as','mkisofs','-iso-level','3','-R','-J','-V','FRAMES_V108_R23','-eltorito-alt-boot','-e','efiboot.img','-no-emul-boot','-o',str(iso),str(isoroot)],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
    iso=ROOT/'out'/ISO_NAME; require(iso.is_file() and iso.stat().st_size>0,'ISO missing')
    iso_sha=sha(iso); (ROOT/'evidence/ISO-SHA256.txt').write_text(f'{iso_sha}  {ISO_NAME}\n'); (ROOT/'evidence/ISO-SIZE.txt').write_text(str(iso.stat().st_size)+'\n')
    ovmfs=list(pathlib.Path('/usr/share/OVMF').rglob('OVMF_CODE_4M.fd'))+list(pathlib.Path('/usr/share/OVMF').rglob('OVMF_CODE.fd')); require(ovmfs,'OVMF missing'); ovmf=str(ovmfs[0])
    gates=ROOT/'evidence/gates'; gates.mkdir(parents=True,exist_ok=True)
    tests=[
      ('interaction-r23',['python3','tools/ci/qemu_r23_dragright_guard_gate.py','--ovmf',ovmf,'--iso',str(iso),'--out',str(gates/'interaction-r23'),'--expected-iso-sha',iso_sha],gates/'interaction-r23/R23-INTERACTION.json'),
      ('usb-direct',['python3','tools/ci/qemu_usb_hub_topology_gate_r3.py','--ovmf',ovmf,'--iso',str(iso),'--out',str(gates/'usb-direct'),'--expected-iso-sha',iso_sha,'--topology','direct'],gates/'usb-direct/TOPOLOGY.json'),
      ('usb-hub',['python3','tools/ci/qemu_usb_hub_topology_gate_r3.py','--ovmf',ovmf,'--iso',str(iso),'--out',str(gates/'usb-hub'),'--expected-iso-sha',iso_sha,'--topology','hub'],gates/'usb-hub/TOPOLOGY.json'),
      ('usb-hub-multi',['python3','tools/ci/qemu_usb_hub_multichild_gate_r17.py','--ovmf',ovmf,'--iso',str(iso),'--out',str(gates/'usb-hub-multi'),'--expected-iso-sha',iso_sha],gates/'usb-hub-multi/MULTICHILD-R17.json'),
      ('usb-multicontroller',['python3','tools/ci/qemu_usb_multicontroller_gate_r16.py','--ovmf',ovmf,'--iso',str(iso),'--out',str(gates/'usb-multicontroller'),'--expected-iso-sha',iso_sha],gates/'usb-multicontroller/USB-MULTICONTROLLER.json'),
      ('usb-keyboard',['python3','tools/ci/qemu_usb_keyboard_gate_r17.py','--ovmf',ovmf,'--iso',str(iso),'--out',str(gates/'usb-keyboard'),'--expected-iso-sha',iso_sha],gates/'usb-keyboard/USB-KEYBOARD.json'),
      ('ps2',['python3','tools/ci/qemu_ps2_delivery_gate_r17.py','--ovmf',ovmf,'--iso',str(iso),'--out',str(gates/'ps2'),'--expected-iso-sha',iso_sha],gates/'ps2/PS2-DELIVERY.json'),
      ('smoothness',['python3','tools/ci/qemu_ps2_cursor_smoothness_r18.py','--ovmf',ovmf,'--iso',str(iso),'--out',str(gates/'smoothness'),'--expected-iso-sha',iso_sha],gates/'smoothness/SMOOTHNESS.json'),
      ('text-edit',['python3','tools/ci/qemu_text_edit_gate_r15.py','--ovmf',ovmf,'--iso',str(iso),'--out',str(gates/'text-edit'),'--expected-iso-sha',iso_sha],gates/'text-edit/TEXT-EDIT.json'),
      ('focus-persistence',['python3','tools/ci/qemu_focus_persistence_gate_r17.py','--ovmf',ovmf,'--iso',str(iso),'--out',str(gates/'focus-persistence'),'--expected-iso-sha',iso_sha],gates/'focus-persistence/FOCUS-PERSISTENCE.json'),
    ]
    statuses={}
    for name,cmd,jp in tests:
        pathlib.Path(cmd[cmd.index('--out')+1]).mkdir(parents=True,exist_ok=True); run(cmd,cwd=ROOT); json_pass(jp); statuses[name]='PASS'
    model_gate(ROOT/'evidence/kernel-r23.nx'); (gates/'model').mkdir(); (gates/'model/RESULT.status').write_text('PASS\n'); statuses['model']='PASS'
    sd=gates/'safety'; sd.mkdir(); sentinel=sd/'sentinel.img'; sentinel.write_bytes(b'\0'*(32*1024*1024)); before=sha(sentinel); serial=sd/'serial.log'; stderr=sd/'stderr'
    cmd=f'timeout 90 qemu-system-x86_64 -machine q35 -m 768M -smp 2 -cpu max -accel tcg,thread=single -display none -no-reboot -no-shutdown -nic none -serial file:{serial} -drive if=pflash,format=raw,readonly=on,file={ovmf} -cdrom {iso} -boot d -drive file={sentinel},if=none,format=raw,readonly=on,id=s -device nvme,drive=s,serial=R23_SENTINEL >/dev/null 2>{stderr}'
    run(cmd,cwd=ROOT,check=False); after=sha(sentinel); require(before==after,'safety sentinel changed'); require('FRAMES_V108_INPUT_TEST_RUNTIME_READY' in serial.read_text(errors='ignore'),'safety runtime marker missing'); (sd/'SAFETY.txt').write_text(f'before={before}\nafter={after}\n'); (sd/'RESULT.status').write_text('PASS\n'); statuses['safety']='PASS'
    for name,_,_ in tests: (gates/name/'RESULT.status').write_text('PASS\n')
    (ROOT/'evidence/R23-AGGREGATE.json').write_text(json.dumps({'status':'PASS','kernel_sha256':R23_SHA,'r22_physical_status':'FAIL','r21_no_full_repaint_status':'PASS','iso_sha256':iso_sha,'gates':statuses},indent=2)+'\n')
    shutil.copy2(iso,ROOT/'final'/ISO_NAME); (ROOT/'final/ISO-SHA256.txt').write_text(f'{iso_sha}  {ISO_NAME}\n'); (ROOT/'final/ISO-SIZE.txt').write_text(str(iso.stat().st_size)+'\n')
    cert='''Frames v108 Physical Input Repair r23 — Drag/Right Guard + xHCI Read-Only Port Census
status=PASS_VM_PENDING_PHYSICAL
r21_physical_full_repaint=PASS
r22_physical_status=FAIL
r22_physical_failure=spurious_right_edges_menu_spam_drag_hijack
r23_vm_left_drag_priority=PASS
r23_vm_context_singleton=PASS
r23_vm_live_full_window_drag=PASS
r23_vm_focus_transfer=PASS
r23_vm_right_click_single=PASS
r23_vm_no_full_repaint=PASS
xhci_port_census=READ_ONLY
ehci_probe=READ_ONLY_TRACE_ONLY
internal_media_readonly=PASS
physical_r23=PENDING
destructive_writes=BLOCKED
'''
    (ROOT/'final/CERTIFICATION.txt').write_text(cert)
    print('R23 PASS_VM_PENDING_PHYSICAL',iso_sha,iso.stat().st_size,flush=True)
if __name__=='__main__': main()
