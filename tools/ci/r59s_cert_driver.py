#!/usr/bin/env python3
from pathlib import Path
import traceback, hashlib
here=Path(__file__).parent
base=here/'r59r_cert_driver.py'; src=base.read_text()
def one(old,new,label):
 global src
 n=src.count(old)
 if n!=1: raise SystemExit(f'r59s cert anchor {label} count {n}')
 src=src.replace(old,new,1)
def alln(old,new,count,label):
 global src
 n=src.count(old)
 if n!=count: raise SystemExit(f'r59s cert anchor {label} count {n}, expected {count}')
 src=src.replace(old,new)
one("'patch_v108_r59r_qh_overlay_completion_capture.py'","'patch_v108_r59s_qh_current_completion_gate.py'",'patch target')
alln('kernel-r59r.nx','kernel-r59s.nx',2,'kernel target')
alln('cb5144a7abb7e610cf893f942360e1b9321fd402494f77e07513cbdcb231a324','10a1a6550abafe7c593d059eeb983d6a576b19ab46c1dcde6ec71888aa6d4a03',2,'identity')
one("'Frames-0.9.98-v108-r59r-QH-Overlay-Completion-Capture-Rufus-UEFI.iso'","'Frames-0.9.98-v108-r59s-QH-Current-Completion-Gate-Rufus-UEFI.iso'",'ISO')
one("'R59R-SHA.txt'","'R59S-SHA.txt'",'SHA file'); one("'R25K-R59R.patch'","'R25K-R59S.patch'",'patch evidence')
one("'FRAMES_V108_R59R'","'FRAMES_V108_R59S'",'label'); one('R59R-AGGREGATE.json','R59S-AGGREGATE.json','aggregate')
one("'frames-0.9.98-v108-r59r-qh-overlay-completion-capture'","'frames-0.9.98-v108-r59s-qh-current-completion-gate'",'profile')
one("'Frames 0.9.98 v108 r59r — EHCI QH Overlay Completion Capture'","'Frames 0.9.98 v108 r59s — EHCI QH Current-Only Completion Gate'",'title')
one('R59R PASS_VM_PENDING_PHYSICAL','R59S PASS_VM_PENDING_PHYSICAL','PASS'); alln('R59R-FAILURE.txt','R59S-FAILURE.txt',2,'failure')
one('r59r exact kernel identity mismatch','r59s exact kernel identity mismatch','identity label')
one("'physical_r59r':'PENDING'","'physical_r59r':'PHYSICAL_COMPLETION_COUNTER_ZERO_RAW_REPORT_ZERO','physical_r59r_telemetry':'R5R_N0_B0_0_B1_0_B2_0_B3_0_B4_0_B5_0_B6_0_B7_0','physical_r59s':'PENDING'",'physical result')
one("        'if cur!=qtdlo || next!=1 { return 0; }',","        'if cur!=qtdlo { return 0; }',",'next-gate witness')
ns={'__name__':'__main__','__file__':str(base)}
try:
 exec(compile(src,str(base),'exec'),ns,ns)
 k=Path('evidence/kernel-r59s.nx')
 if not k.exists(): raise SystemExit('r59s evidence kernel missing')
 s=k.read_text()
 if hashlib.sha256(s.encode()).hexdigest()!='10a1a6550abafe7c593d059eeb983d6a576b19ab46c1dcde6ec71888aa6d4a03': raise SystemExit('r59s evidence kernel SHA mismatch')
 arm=s[s.index('fn v159_ehci_mouse_periodic_arm'):s.index('fn v159_ehci_mouse_periodic_tick')]
 tick=s[s.index('fn v159_ehci_mouse_periodic_tick'):s.index('fn v135_hid_control_fallback_prepare')]
 for q in ('var qmatch:u64=0; if cur==qtdlo { qmatch=1; }','let nterm=next%2','let active=(live_tok/128)%2','let errs=(live_tok/4)%32','let rem=(live_tok/65536)%32768','volatile_write64(xhci_state+3984,gate)','if cur!=qtdlo { return 0; }','let raw=volatile_read64(data)','volatile_write64(xhci_state+4088,raw)','volatile_write32(qh+16,qtdlo)'):
  if q not in tick: raise SystemExit('r59s witness missing '+q)
 if 'if cur!=qtdlo || next!=1 { return 0; }' in tick: raise SystemExit('r59s redundant next gate remains')
 for q in ('volatile_write64(xhci_state+3984,tr_s)','volatile_write64(xhci_state+4072,tr_c)','volatile_write64(xhci_state+4088,tr_changes)'):
  if q not in arm: raise SystemExit('r59s split trace witness missing '+q)
 if 'R5S' in s or not all(q in s for q in ('raw%256','(raw/256)%256','(raw/65536)%256','(raw/16777216)%256')): raise SystemExit('r59s visible row witness missing')
 low=(arm+tick).lower()
 if any(x in low for x in ('write(10)','nvme_submit_write','ahci_write','fat_write','block_write','input_push(')): raise SystemExit('r59s exceeds raw diagnostic/read-only scope')
except BaseException:
 out=Path('evidence'); out.mkdir(parents=True,exist_ok=True); (out/'R59S-FAILURE.txt').write_text(traceback.format_exc()); raise
