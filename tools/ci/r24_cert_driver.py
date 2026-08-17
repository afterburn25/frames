#!/usr/bin/env python3
from pathlib import Path

base=Path(__file__).with_name('r23_cert_driver.py')
s=base.read_text()

def rep(old,new,label,count=1):
    global s
    n=s.count(old)
    if n!=count:
        raise SystemExit(f'{label}: expected {count} anchor(s), got {n}')
    s=s.replace(old,new,count)

# Identity / candidate construction.
rep("R23_SHA='ce61a788ca5aba773aef61c9e73d3d1eba25614984eeb5fe6930b20da0eaa556'\nISO_NAME='Frames-0.9.98-v108-Physical-Input-Repair-r23-Drag-Right-Guard-XHCI-Port-Census-Rufus-UEFI.iso'",
    "R23_SHA='ce61a788ca5aba773aef61c9e73d3d1eba25614984eeb5fe6930b20da0eaa556'\nR24_SHA='4cb9eb6b00e05917f6eb3ea4cf69649420b1e14c9c165761097cab64c40c5f16'\nISO_NAME='Frames-0.9.98-v108-Physical-Input-Repair-r24-Elan-Frame-Lock-XHCI-Reset-Diag-Rufus-UEFI.iso'",
    'identity')
rep("prefix='r23cert-'","prefix='r24cert-'",'temp prefix')
rep("patch_v108_physical_input_r23_dragright_xhci_ro.py","patch_v108_physical_input_r24_elan_frame_xhci_reset.py",'r24 patch invocation')
rep("(ROOT/'evidence/R23-SHA.txt').write_text(r.stdout)","(ROOT/'evidence/R24-SHA.txt').write_text(r.stdout)",'r24 sha evidence')
rep("require(sha(F/'kernel/main.nx')==R23_SHA,'r23 kernel SHA mismatch')","require(sha(F/'kernel/main.nx')==R24_SHA,'r24 kernel SHA mismatch')",'r24 kernel identity')
rep("ROOT/'evidence/kernel-r23.nx'","ROOT/'evidence/kernel-r24.nx'",'r24 kernel evidence',4)
rep("R21-R23.patch","R21-R24.patch",'r21-r24 diff')
rep("R22-R23.patch","R22-R24.patch",'r22-r24 diff')
rep("FRAMES_V108_R23","FRAMES_V108_R24",'iso volume')
rep("Frames v108 r23 physical input corrective diagnostic\\nr22 physical failure: spurious right-edge/menu spam stole left drag\\nr23: left-drag priority + singleton context menu + read-only xHCI PORTSC census",
    "Frames v108 r24 physical input corrective diagnostic\\nr23 physical: drag restored, singleton menu PASS, spontaneous right edges remain\\nr24: exact Elantech 6-byte frame lock + strict xHCI reset/enable diagnostics",
    'README text')

# Use the full-overlay-isolated smoothness gate introduced for the successful
# r23 r2 certification run.
rep("'python3','tools/ci/qemu_ps2_cursor_smoothness_r18.py'","'python3','tools/ci/qemu_ps2_cursor_smoothness_r23.py'",'smoothness wrapper')

# Add r24-specific structural/model evidence without weakening the inherited
# runtime gates.
r24_model=r'''
def r24_model_gate(k):
    s=pathlib.Path(k).read_text()
    req=[
      'volatile_write64(input_state+2848+(fc*8),byte)',
      'if fc+1<6 { return 1; }',
      'volatile_write64(input_state+3488,4)',
      'volatile_write64(input_state+2896,volatile_read64(input_state+2896)+1)',
      'fn v108_text_xrst_v124',
      'v=clear_flag(v,2)',
      'volatile_write64(xhci_state+1672,3)',
      'volatile_write64(hardware_state+600,volatile_read64(xhci_state+1640))',
      'var connected_sample:u64=0',
      'if connected_sample==0 { connected_sample=ps; }',
      'var sample=connected_sample; if sample==0 { sample=any_sample; }'
    ]
    missing=[x for x in req if x not in s]
    require(not missing,'r24 model missing '+repr(missing))
    require('desktop_redraw=1' not in s,'r24 re-enabled full desktop repaint')
    dec=fn_text(s,'ps2_mouse_decode_v108')
    require('if mode==4' in dec and 'fc+1<6' in dec and 'ps2_elan4_emit_v110' in dec,'Elantech exact-frame path incomplete')
    rst=fn_text(s,'xhci_reset_connected_port_from')
    for q in ('pit_wait(11932)','(done/2)%2==0','volatile_write64(xhci_state+1664,1)'):
        require(q in rst,'xHCI reset/enable evidence missing '+q)
    wb=fn_text(s,'xhci_port_write_base')
    require('clear_flag(v,2)' in wb,'PORTSC PED write-one-disable protection missing')
'''
rep("def main():",r24_model+"\ndef main():",'inject r24 model gate')
rep("model_gate(F/'kernel/main.nx')","model_gate(F/'kernel/main.nx'); r24_model_gate(F/'kernel/main.nx')",'pre-build r24 model')
rep("model_gate(ROOT/'evidence/kernel-r24.nx')","model_gate(ROOT/'evidence/kernel-r24.nx'); r24_model_gate(ROOT/'evidence/kernel-r24.nx')",'post-gate r24 model')

# Aggregate/final identity and physical-history wording.
rep("evidence/R23-AGGREGATE.json","evidence/R24-AGGREGATE.json",'aggregate filename')
rep("'kernel_sha256':R23_SHA","'kernel_sha256':R24_SHA",'aggregate kernel')
rep("'r22_physical_status':'FAIL','r21_no_full_repaint_status':'PASS'",
    "'r22_physical_status':'FAIL','r23_physical_status':'FAIL_PARTIAL','r21_no_full_repaint_status':'PASS'",
    'aggregate physical history')
rep("R23_SENTINEL","R24_SENTINEL",'sentinel serial')
rep("Frames v108 Physical Input Repair r23 — Drag/Right Guard + xHCI Read-Only Port Census",
    "Frames v108 Physical Input Repair r24 — Elantech Exact Frame Lock + xHCI Reset/Enable Diagnostics",
    'cert title')
rep("r22_physical_failure=spurious_right_edges_menu_spam_drag_hijack\nr23_vm_left_drag_priority=PASS",
    "r22_physical_failure=spurious_right_edges_menu_spam_drag_hijack\nr23_physical_status=FAIL_PARTIAL\nr23_physical_result=drag_restored_singleton_menu_but_motion_still_generates_false_right_and_real_right_missing\nr24_vm_left_drag_priority=PASS",
    'cert history')
rep("r23_vm_context_singleton=PASS","r24_vm_context_singleton=PASS",'cert singleton')
rep("r23_vm_live_full_window_drag=PASS","r24_vm_live_full_window_drag=PASS",'cert live drag')
rep("r23_vm_focus_transfer=PASS","r24_vm_focus_transfer=PASS",'cert focus')
rep("r23_vm_right_click_single=PASS","r24_vm_right_click_single=PASS",'cert right')
rep("r23_vm_no_full_repaint=PASS","r24_vm_no_full_repaint=PASS",'cert repaint')
rep("xhci_port_census=READ_ONLY\nehci_probe=READ_ONLY_TRACE_ONLY",
    "elantech_v4_exact_six_byte_framing=MODEL_GATED_PHYSICAL_PENDING\nxhci_port_census=READ_ONLY_CONNECTED_SAMPLE\nxhci_port_reset_enable=VM_CERTIFIED_PHYSICAL_PENDING\nehci_probe=READ_ONLY_TRACE_ONLY",
    'cert subsystem status')
rep("physical_r23=PENDING","physical_r24=PENDING",'cert physical')
rep("print('R23 PASS_VM_PENDING_PHYSICAL'","print('R24 PASS_VM_PENDING_PHYSICAL'",'final print')

ns={'__name__':'__main__','__file__':str(base)}
exec(compile(s,str(base),'exec'),ns,ns)
