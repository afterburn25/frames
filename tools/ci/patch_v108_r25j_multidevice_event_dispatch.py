#!/usr/bin/env python3
from pathlib import Path
import hashlib,subprocess,sys
if len(sys.argv)!=2: raise SystemExit('usage: patch_v108_r25j_multidevice_event_dispatch.py <kernel/main.nx>')
p=Path(sys.argv[1]); base=Path(__file__).with_name('patch_v108_r25i_log_marker_layout.py'); subprocess.run([sys.executable,str(base),str(p)],check=True,stdout=subprocess.DEVNULL); s=p.read_text()
if hashlib.sha256(s.encode()).hexdigest()!='a8a53408b754fcc83bc611725ba59fde71886f8cdfb0ffa154ccbcaeb4112b4a': raise SystemExit('r25i identity mismatch')
old='''if typ==32 { let status=volatile_read32(trb+8); let code=(status/16777216)%256; let residue=status%16777216; let ep=(control/65536)%32; let eslot=(control/16777216)%256; serial_usb_msc_diag(40,(code*72057594037927936)+(eslot*281474976710656)+(ep*4294967296)+residue); xhci_event_advance(xhci_state); if eslot!=slot || ep!=dci || (code!=1 && code!=13) || residue>requested { return 0; } return requested-residue; } xhci_event_advance(xhci_state);'''
new='''if typ==32 { let status=volatile_read32(trb+8); let code=(status/16777216)%256; let residue=status%16777216; let ep=(control/65536)%32; let eslot=(control/16777216)%256; serial_usb_msc_diag(40,(code*72057594037927936)+(eslot*281474976710656)+(ep*4294967296)+residue); xhci_event_advance(xhci_state); if eslot==slot && ep==dci { if (code!=1 && code!=13) || residue>requested { return 0; } return requested-residue; } serial_usb_msc_diag(46,(eslot*281474976710656)+(ep*4294967296)+residue); } else { xhci_event_advance(xhci_state); }'''
if s.count(old)!=1: raise SystemExit(f'xHCI multi-device event anchor mismatch {s.count(old)}')
s=s.replace(old,new,1)
expected='bccff173bc151d8fbd6e8f8c691e43124b8813bcf34cbae63bd407366d6f55ca'; actual=hashlib.sha256(s.encode()).hexdigest()
if actual!=expected: raise SystemExit(f'r25j identity mismatch {actual}')
p.write_text(s); print(actual)
