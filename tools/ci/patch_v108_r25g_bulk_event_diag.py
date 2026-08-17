#!/usr/bin/env python3
from pathlib import Path
import hashlib,subprocess,sys
if len(sys.argv)!=2: raise SystemExit('usage: patch_v108_r25g_bulk_event_diag.py <kernel/main.nx>')
p=Path(sys.argv[1]);base=Path(__file__).with_name('patch_v108_r25f_msc_inquiry_first.py');subprocess.run([sys.executable,str(base),str(p)],check=True,stdout=subprocess.DEVNULL);s=p.read_text()
if hashlib.sha256(s.encode()).hexdigest()!='067a87bc97ae725795bedffd611e4e55dcf9def2f063868768fb4084232c81a5': raise SystemExit('r25f identity mismatch')
def span(name):
 st=s.index('fn '+name);op=s.index('{',st);d=0
 for i in range(op,len(s)):
  if s[i]=='{':d+=1
  elif s[i]=='}':
   d-=1
   if d==0:return st,i+1
 raise SystemExit('unterminated '+name)
a,b=span('xhci_wait_bulk_event');s=s[:a]+r'''fn xhci_wait_bulk_event(xhci_state:u64, slot:u64, dci:u64, requested:u64) -> u64 {
    let event_ring=volatile_read64(xhci_state+24); var spins:u64=0;
    while spins<16000000 { let index=volatile_read64(xhci_state+96); let cycle=volatile_read64(xhci_state+104); let trb=event_ring+(index*16); let control=volatile_read32(trb+12); if control%2==cycle { let typ=(control/1024)%64; if typ==32 { let status=volatile_read32(trb+8); let code=(status/16777216)%256; let residue=status%16777216; let ep=(control/65536)%32; let eslot=(control/16777216)%256; serial_usb_msc_diag(40,(code*72057594037927936)+(eslot*281474976710656)+(ep*4294967296)+residue); xhci_event_advance(xhci_state); if eslot!=slot || ep!=dci || (code!=1 && code!=13) || residue>requested { return 0; } return requested-residue; } xhci_event_advance(xhci_state); } cpu_pause(); spins=spins+1; }
    serial_usb_msc_diag(41,(slot*4294967296)+(dci*65536)+requested); return 0;
}'''+s[b:]
a,b=span('usb_msc_bulk_td');old=s[a:b];new=old.replace('if ring==0 || dci==0 { return 0; }','if ring==0 || dci==0 { serial_usb_msc_diag(42,(incoming*4294967296)+dci); return 0; }').replace('if tail>=254 { return 0; }','if tail>=254 { serial_usb_msc_diag(43,tail); return 0; }').replace('return xhci_wait_bulk_event(xhci_state,slot,dci,length);','serial_usb_msc_diag(44,(incoming*72057594037927936)+(slot*281474976710656)+(dci*4294967296)+length); let got=xhci_wait_bulk_event(xhci_state,slot,dci,length); serial_usb_msc_diag(45,(dci*4294967296)+got); return got;');s=s[:a]+new+s[b:]
expected='c2c0a71417e40f21e1ab4bc50daa42b8e105a1a22b2e56e046e7a0c51d672f2b';actual=hashlib.sha256(s.encode()).hexdigest();
if actual!=expected: raise SystemExit(f'r25g identity mismatch {actual}')
p.write_text(s);print(actual)
