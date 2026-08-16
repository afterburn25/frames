#!/usr/bin/env python3
from pathlib import Path
import hashlib,re,sys

if len(sys.argv)!=3:
    raise SystemExit('usage: patch_integrated_gui_physical_test_policy.py PATH_TO_frames_boot.c PATH_TO_main.nx')
loader=Path(sys.argv[1]); kernel=Path(sys.argv[2])
loader_expected='5a95d237500bf8803bc192d6a179334710204bb83dfda05d7479fe18bed40f5f'
kernel_expected='2320afc66e4de50a65b352659f9d7bcf2d84948e0f07f1c1d12da34aadda7aee'
loader_actual=hashlib.sha256(loader.read_bytes()).hexdigest(); kernel_actual=hashlib.sha256(kernel.read_bytes()).hexdigest()
if loader_actual!=loader_expected: raise SystemExit(f'unexpected splash-enabled loader hash: {loader_actual}')
if kernel_actual!=kernel_expected: raise SystemExit(f'unexpected repaired v116 kernel hash: {kernel_actual}')

# Add a dedicated test-only boot-policy bit. This is intentionally separate
# from DESKTOP.CFG so normal desktop boots retain the complete post-desktop
# system/connected-services train. The physical-test image alone carries the
# exact GUITEST.CFG challenge and receives bit 8192.
s=loader.read_text()
insert_anchor='''    UINTN code_pages=(UINTN)((h->code_size+PAGE_SIZE-1)/PAGE_SIZE); EFI_PHYSICAL_ADDRESS code_addr=0;\n'''
if s.count(insert_anchor)!=1: raise SystemExit('loader GUI-test insertion anchor mismatch')
gui_policy=r'''    void *gui_test_file=0; UINTN gui_test_size=0;
    EFI_STATUS gui_test_status=load_file(bs,image,L"\\Frames\\GUITEST.CFG",&gui_test_file,&gui_test_size);
    if(!EFI_ERROR(gui_test_status)){
        static const uint8_t gui_test_challenge[]={'F','R','A','M','E','S','_','I','N','T','E','G','R','A','T','E','D','_','G','U','I','_','P','H','Y','S','I','C','A','L','_','T','E','S','T','_','V','1','\n'};
        if(gui_test_size!=sizeof(gui_test_challenge) || !mem_equal(gui_test_file,gui_test_challenge,sizeof(gui_test_challenge))) fatal(L"Invalid integrated GUI physical-test challenge",0);
        if((boot_policy_flags & (1|2048|4096))!=(1|2048|4096) || !theme_pack_verified || !appearance_cfg_verified) fatal(L"Integrated GUI physical test requires verified desktop/FAPP/theme/appearance policy",0);
        boot_policy_flags|=8192;
        print16(L"[GUI-TEST] Integrated GUI physical-test policy armed\r\n");
    }

'''
s=s.replace(insert_anchor,gui_policy+insert_anchor,1)
loader.write_text(s)

k=kernel.read_text()
# Preserve the legacy integrated marker and add the user's canonical marker plus
# an explicit test-ready marker. They are emitted only after phase 12 AND the
# appearance system have succeeded.
m=re.search(r'^fn serial_marker_integrated_gui_ok\(\) -> void \{.*\}$',k,re.M)
if not m: raise SystemExit('integrated GUI legacy marker function not found')
new_markers='''\nfn serial_marker_frames_integrated_gui_ok() -> void { serial_putc(70); serial_putc(82); serial_putc(65); serial_putc(77); serial_putc(69); serial_putc(83); serial_putc(95); serial_putc(73); serial_putc(78); serial_putc(84); serial_putc(69); serial_putc(71); serial_putc(82); serial_putc(65); serial_putc(84); serial_putc(69); serial_putc(68); serial_putc(95); serial_putc(71); serial_putc(85); serial_putc(73); serial_putc(95); serial_putc(79); serial_putc(75); serial_putc(10); return; }
fn serial_marker_gui_physical_test_policy_ok() -> void { serial_putc(70); serial_putc(82); serial_putc(65); serial_putc(77); serial_putc(69); serial_putc(83); serial_putc(95); serial_putc(71); serial_putc(85); serial_putc(73); serial_putc(95); serial_putc(80); serial_putc(72); serial_putc(89); serial_putc(83); serial_putc(73); serial_putc(67); serial_putc(65); serial_putc(76); serial_putc(95); serial_putc(84); serial_putc(69); serial_putc(83); serial_putc(84); serial_putc(95); serial_putc(80); serial_putc(79); serial_putc(76); serial_putc(73); serial_putc(67); serial_putc(89); serial_putc(95); serial_putc(79); serial_putc(75); serial_putc(10); return; }
fn serial_marker_gui_physical_test_ready() -> void { serial_putc(70); serial_putc(82); serial_putc(65); serial_putc(77); serial_putc(69); serial_putc(83); serial_putc(95); serial_putc(71); serial_putc(85); serial_putc(73); serial_putc(95); serial_putc(80); serial_putc(72); serial_putc(89); serial_putc(83); serial_putc(73); serial_putc(67); serial_putc(65); serial_putc(76); serial_putc(95); serial_putc(84); serial_putc(69); serial_putc(83); serial_putc(84); serial_putc(95); serial_putc(82); serial_putc(69); serial_putc(65); serial_putc(68); serial_putc(89); serial_putc(10); return; }
'''
k=k[:m.end()]+new_markers+k[m.end():]

mode_decl='var physical_preview_mode:u64=0; var hardware_compat_ready:u64=0; var usb_msc_cert_mode:u64=0; var developer_preview_mode:u64=0; var desktop_mode:u64=0;'
if k.count(mode_decl)!=1: raise SystemExit('kernel mode declaration anchor mismatch')
k=k.replace(mode_decl,mode_decl+' var gui_physical_test_mode:u64=0;',1)

desktop_policy='if (info.boot_policy_flags / 2048) % 2 != 0 { if (info.boot_policy_flags % 2)==0 || physical_preview_mode!=0 || usb_msc_cert_mode!=0 || developer_preview_mode!=0 { serial_marker_desktop_cert_fail(); return; } desktop_mode=1; serial_marker_desktop_policy_ok(); }'
if k.count(desktop_policy)!=1: raise SystemExit('kernel desktop policy anchor mismatch')
gui_mode=desktop_policy+'\n        if (info.boot_policy_flags / 8192) % 2 != 0 { if desktop_mode==0 || (info.boot_policy_flags/4096)%2==0 { serial_marker_desktop_cert_fail(); return; } gui_physical_test_mode=1; serial_marker_gui_physical_test_policy_ok(); }'
k=k.replace(desktop_policy,gui_mode,1)

appearance='appearance_ready=appearance_system_phase1_compose(appearance_state,display_state,process_state,window_manager_state); if appearance_ready==0 { serial_marker_desktop_cert_fail(); return; }'
if k.count(appearance)!=1: raise SystemExit('appearance completion anchor mismatch')
# A GUI physical-test boot deliberately stops at the product boundary the user
# asked us to certify: integrated desktop phase 12 + appearance. It does not
# claim the storage-indexed search, system-service, live-network, TLS, or online
# service trains are certified. Normal desktop boots continue through those.
replacement=appearance+'\n            if gui_physical_test_mode!=0 { serial_marker_frames_integrated_gui_ok(); serial_marker_gui_physical_test_ready(); return; }'
k=k.replace(appearance,replacement,1)
kernel.write_text(k)

print('integrated_gui_physical_test_policy=PASS')
print('base_loader_sha256='+loader_actual)
print('base_kernel_sha256='+kernel_actual)
print('patched_loader_sha256='+hashlib.sha256(loader.read_bytes()).hexdigest())
print('patched_kernel_sha256='+hashlib.sha256(kernel.read_bytes()).hexdigest())
