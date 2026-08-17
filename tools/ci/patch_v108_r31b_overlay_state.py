#!/usr/bin/env python3
from pathlib import Path
import hashlib,subprocess,sys
if len(sys.argv)!=2: raise SystemExit('usage: patch_v108_r31b_overlay_state.py <kernel/main.nx>')
p=Path(sys.argv[1]); base=Path(__file__).with_name('patch_v108_r31_usb_state_isolation.py')
subprocess.run([sys.executable,str(base),str(p)],check=True,stdout=subprocess.DEVNULL)
s=p.read_text(); BASE='cf7a3f890811d6ff245ec822bf5fd38d01f405c990c7dce6161efb117699797c'
if hashlib.sha256(s.encode()).hexdigest()!=BASE: raise SystemExit('r31 base mismatch')

def span(text,name):
 st=text.index('fn '+name);op=text.index('{',st);d=0
 for i in range(op,len(text)):
  if text[i]=='{':d+=1
  elif text[i]=='}':
   d-=1
   if d==0:return st,i+1
 raise RuntimeError(name)
old='''v108_ehci_ro_probe_v122(hardware_state,phys_state,xhci_state,pml4); if volatile_read64(hardware_state+728)==0 { v108_log_msc_retain_v125(hardware_state,phys_state,xhci_state,pml4); } unsafe { volatile_write64(xhci_state+1680'''
new='''v108_ehci_ro_probe_v122(hardware_state,phys_state,xhci_state,pml4); if volatile_read64(hardware_state+728)==0 { v108_log_msc_retain_v125(hardware_state,phys_state,xhci_state,pml4); } unsafe { volatile_write64(xhci_state+2192,volatile_read64(hardware_state+976)); volatile_write64(xhci_state+2200,volatile_read64(hardware_state+984)); volatile_write64(xhci_state+2208,volatile_read64(hardware_state+992)); volatile_write64(xhci_state+2216,volatile_read64(hardware_state+1000)); volatile_write64(xhci_state+2224,volatile_read64(hardware_state+1008)); volatile_write64(xhci_state+2232,volatile_read64(hardware_state+1016)); volatile_write64(xhci_state+2240,volatile_read64(hardware_state+944)); volatile_write64(xhci_state+2248,volatile_read64(hardware_state+952)); volatile_write64(xhci_state+2256,volatile_read64(hardware_state+960)); volatile_write64(xhci_state+2264,volatile_read64(hardware_state+968)); volatile_write64(xhci_state+2272,volatile_read64(hardware_state+928)); volatile_write64(xhci_state+2280,volatile_read64(hardware_state+728)); } unsafe { volatile_write64(xhci_state+1680'''
if s.count(old)!=1: raise SystemExit(f'r31b telemetry-copy anchor mismatch {s.count(old)}')
s=s.replace(old,new,1)
st,en=span(s,'v108_input_overlay_draw'); ov=s[st:en]
for h,x in ((976,2192),(984,2200),(992,2208),(1000,2216),(1008,2224),(1016,2232),(944,2240),(952,2248),(960,2256),(968,2264),(928,2272),(728,2280)):
 oldr=f'volatile_read64(hardware_state+{h})'; newr=f'volatile_read64(xhci+{x})'; ov=ov.replace(oldr,newr)
if 'hardware_state+' in ov: raise SystemExit('r31b overlay still references unavailable hardware_state')
s=s[:st]+ov+s[en:]
for q in ('volatile_write64(xhci_state+2192','volatile_write64(xhci_state+2280','volatile_read64(xhci+2192)','volatile_read64(xhci+2280)'):
 if q not in s: raise SystemExit('r31b telemetry state bridge missing '+q)
if s.count('{')!=s.count('}'): raise SystemExit('brace imbalance')
expected='57944cdb9f5060b5b170a42280fe37dce32125040f5e1da6295df615e1f81e6e'
actual=hashlib.sha256(s.encode()).hexdigest()
if actual!=expected: raise SystemExit(f'r31b identity mismatch {actual}')
p.write_text(s); print(actual)
