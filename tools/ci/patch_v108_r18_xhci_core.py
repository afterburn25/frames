#!/usr/bin/env python3
from pathlib import Path
import sys
p=Path(sys.argv[1])
s=p.read_text()
def rep(old,new,count=1):
    global s
    n=s.count(old)
    if n!=count:
        raise SystemExit(f"replacement count {n} != {count} for {old[:120]!r}")
    s=s.replace(old,new,count)
# --- xHCI legacy ownership + scratchpad support ---
anchor='fn xhci_controller_init(hardware_state:u64, phys_state:u64, xhci_state:u64, pml4:u64) -> u64 {'
legacy='''fn xhci_legacy_handoff_v118(base:u64,phys_state:u64,pml4:u64) -> u64 {
    if base==0 || phys_state==0 || pml4==0 { return 0; }
    let hcc=volatile_read32(base+16); var off=(hcc/65536)%65536; if off==0 { return 1; }
    var cap=base+(off*4); var seen:u64=0;
    while cap!=0 && seen<64 {
        if ensure_identity_mmio_page(phys_state,pml4,cap)==0 { return 0; }
        let v=volatile_read32(cap); let cid=v%256; let next=(v/256)%256;
        if cid==1 {
            var leg=v; if (leg/16777216)%2==0 { leg=set_flag(leg,16777216); unsafe { volatile_write32(cap,leg); } }
            var spins:u64=0; while (volatile_read32(cap)/65536)%2!=0 && spins<4000000 { cpu_pause(); spins=spins+1; }
            if (volatile_read32(cap)/65536)%2!=0 { return 3; }
            return 2;
        }
        if next==0 { return 1; } cap=cap+(next*4); seen=seen+1;
    }
    return 1;
}
'''
rep(anchor,legacy+anchor)

old='''    let bdf=volatile_read64(hardware_state+80); if pci_enable_mmio_busmaster(bdf)==0 { return 0; }
    let base=volatile_read64(hardware_state+192); if base==0 { return 0; } let caplen=volatile_read8(base); if caplen<32 || caplen>255 { return 0; } let op=base+caplen;
    var cmd=volatile_read32(op+0); cmd=clear_flag(cmd,1); unsafe { volatile_write32(op+0,cmd); } if xhci_wait_halted(op,1)==0 { return 0; }
'''
new='''    let bdf=volatile_read64(hardware_state+80); if pci_enable_mmio_busmaster(bdf)==0 { return 0; }
    let base=volatile_read64(hardware_state+192); if base==0 { return 0; } let caplen=volatile_read8(base); if caplen<32 || caplen>255 { return 0; } let op=base+caplen;
    let legacy=xhci_legacy_handoff_v118(base,phys_state,pml4); if legacy==0 { return 0; }
    var cmd=volatile_read32(op+0); cmd=clear_flag(cmd,1); unsafe { volatile_write32(op+0,cmd); } if xhci_wait_halted(op,1)==0 { return 0; }
'''
rep(old,new)

old='''    let command_ring=alloc_dma_page(phys_state,3); let event_ring=alloc_dma_page(phys_state,3); let erst=alloc_dma_page(phys_state,3); let dcbaa=alloc_dma_page(phys_state,3); if command_ring==0 || event_ring==0 || erst==0 || dcbaa==0 { return 0; }
    zero_page(command_ring); zero_page(event_ring); zero_page(erst); zero_page(dcbaa);
    // Link TRB at entry 255: pointer back to ring, Toggle Cycle + Type=Link + cycle.
'''
new='''    let command_ring=alloc_dma_page(phys_state,3); let event_ring=alloc_dma_page(phys_state,3); let erst=alloc_dma_page(phys_state,3); let dcbaa=alloc_dma_page(phys_state,3); if command_ring==0 || event_ring==0 || erst==0 || dcbaa==0 { return 0; }
    zero_page(command_ring); zero_page(event_ring); zero_page(erst); zero_page(dcbaa);
    let hcs2=volatile_read32(base+8); let scratch_lo=(hcs2/134217728)%32; let scratch_hi=(hcs2/2097152)%32; let scratch_count=scratch_lo+(scratch_hi*32); var scratch_array:u64=0; var scratch_ready:u64=0;
    if scratch_count>0 {
        if scratch_count>48 { return 0; }
        scratch_array=alloc_dma_page(phys_state,3); if scratch_array==0 { return 0; } zero_page(scratch_array);
        var si:u64=0; while si<scratch_count { let sp=alloc_dma_page(phys_state,3); if sp==0 { return 0; } zero_page(sp); unsafe { volatile_write64(scratch_array+(si*8),sp); } si=si+1; }
        unsafe { volatile_write64(dcbaa,scratch_array); } scratch_ready=1;
    }
    // Link TRB at entry 255: pointer back to ring, Toggle Cycle + Type=Link + cycle.
'''
rep(old,new)

old='''    unsafe { volatile_write64(xhci_state+0,base); volatile_write64(xhci_state+8,op); volatile_write64(xhci_state+16,command_ring); volatile_write64(xhci_state+24,event_ring); volatile_write64(xhci_state+32,erst); volatile_write64(xhci_state+40,dcbaa); volatile_write64(xhci_state+48,maxslots); volatile_write64(xhci_state+56,1); volatile_write64(xhci_state+64,0); volatile_write64(xhci_state+72,1); volatile_write64(xhci_state+80,runtime); volatile_write64(xhci_state+88,doorbells); volatile_write64(xhci_state+96,0); volatile_write64(xhci_state+104,1); }
'''
new='''    unsafe { volatile_write64(xhci_state+0,base); volatile_write64(xhci_state+8,op); volatile_write64(xhci_state+16,command_ring); volatile_write64(xhci_state+24,event_ring); volatile_write64(xhci_state+32,erst); volatile_write64(xhci_state+40,dcbaa); volatile_write64(xhci_state+48,maxslots); volatile_write64(xhci_state+56,1); volatile_write64(xhci_state+64,0); volatile_write64(xhci_state+72,1); volatile_write64(xhci_state+80,runtime); volatile_write64(xhci_state+88,doorbells); volatile_write64(xhci_state+96,0); volatile_write64(xhci_state+104,1); volatile_write64(xhci_state+1216,scratch_count); volatile_write64(xhci_state+1224,scratch_ready); volatile_write64(xhci_state+1232,legacy); volatile_write64(xhci_state+1240,0); }
'''
rep(old,new)

p.write_text(s)
