#!/usr/bin/env python3
from pathlib import Path
import hashlib, subprocess, sys

if len(sys.argv)!=2:
    raise SystemExit('usage: patch_v108_r25d_structfix.py <kernel/main.nx>')
p=Path(sys.argv[1])
base=Path(__file__).with_name('patch_v108_r25c_bracefix.py')
subprocess.run([sys.executable,str(base),str(p)],check=True,stdout=subprocess.DEVNULL)
s=p.read_text()
expected_in='9224366a0d53bab0815d8c04f17017fc20858dc2a196f41cf159bf85ac24f395'
if hashlib.sha256(s.encode()).hexdigest()!=expected_in:
    raise SystemExit('r25c input identity mismatch')
start=s.index('fn v108_log_msc_retain_v125')
end=s.index('fn v108_xhci_scan_pointer_v116',start)
new=r'''fn v108_log_msc_retain_v125(hardware_state:u64,phys_state:u64,xhci_state:u64,pml4:u64) -> u64 {
    if hardware_state==0 || phys_state==0 || xhci_state==0 || pml4==0 { return 0; }
    let total=volatile_read64(hardware_state+24); let fr=volatile_read64(hardware_state+648); var ci:u64=0;
    while ci<total && ci<4 {
        let bdf=v108_pci_nth_xhci_v116(ci);
        if bdf==0 { ci=total; }
        else {
            let base=pci_bar_base(bdf,0);
            if base!=0 && ensure_identity_mmio_page(phys_state,pml4,base)!=0 {
                zero_page(xhci_state); v108_intel_xhci_route_ports_v120(bdf,xhci_state,hardware_state);
                if xhci_controller_init(hardware_state,phys_state,xhci_state,pml4)!=0 {
                    var start:u64=0; var tries:u64=0;
                    while tries<32 {
                        let port=xhci_reset_connected_port_from(xhci_state,start);
                        if port==0 { tries=32; }
                        else {
                            start=port; tries=tries+1;
                            if fr!=0 { flight_record_v125(fr,196609,2,port); }
                            let slot=xhci_enable_slot(xhci_state);
                            if slot!=0 {
                                if fr!=0 { flight_record_v125(fr,196609,3,(slot*256)+volatile_read64(xhci_state+488)); }
                                if xhci_address_default_device(xhci_state,phys_state)!=0 {
                                    if fr!=0 { flight_record_v125(fr,196609,4,volatile_read64(xhci_state+488)); }
                                    if xhci_get_device_descriptor8(xhci_state,phys_state)!=0 {
                                        if fr!=0 { flight_record_v125(fr,196609,5,volatile_read64(xhci_state+504)); }
                                        if xhci_finalize_address_and_descriptor(xhci_state,phys_state)!=0 {
                                            if fr!=0 { flight_record_v125(fr,196609,6,(volatile_read64(xhci_state+272)*65536)+volatile_read64(xhci_state+280)); }
                                            if v108_msc_snapshot_v125(xhci_state,hardware_state,phys_state,fr)!=0 && volatile_read64(hardware_state+728)!=0 {
                                                unsafe { volatile_write64(hardware_state+680,6); volatile_write64(hardware_state+688,0); volatile_write64(hardware_state+696,volatile_read64(xhci_state+272)); volatile_write64(hardware_state+704,volatile_read64(xhci_state+280)); }
                                                return 1;
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
            ci=ci+1;
        }
    }
    return 0;
}
'''
s=s[:start]+new+s[end:]
if s.count('{')!=s.count('}'):
    raise SystemExit('r25d brace imbalance')
expected='9a2d5a32837841d591fed2102f087efafbc664a135d80e16727e7ddf20a2bb25'
actual=hashlib.sha256(s.encode()).hexdigest()
if actual!=expected:
    raise SystemExit(f'r25d identity mismatch {actual}')
p.write_text(s)
print(actual)
