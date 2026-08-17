#!/usr/bin/env python3
from pathlib import Path
import hashlib, subprocess, sys
if len(sys.argv)!=2: raise SystemExit('usage: patch_v108_r25l_iso_native_log.py <kernel/main.nx>')
p=Path(sys.argv[1]); base=Path(__file__).with_name('patch_v108_r25k_large_media_log_gate.py')
subprocess.run([sys.executable,str(base),str(p)],check=True,stdout=subprocess.DEVNULL); s=p.read_text()
if hashlib.sha256(s.encode()).hexdigest()!='af77b8f648dbb11fa6a31810e2150483818213635c92404dd956db892df9fdb0': raise SystemExit('r25k identity mismatch')

def span(text,name):
 st=text.index('fn '+name); op=text.index('{',st); d=0
 for i in range(op,len(text)):
  if text[i]=='{': d+=1
  elif text[i]=='}':
   d-=1
   if d==0:return st,i+1
 raise RuntimeError(name)
def repl_fn(name,new):
 global s
 a,b=span(s,name); s=s[:a]+new+s[b:]

fat_helpers=r'''fn flight_fat_le16_v125(p:u64) -> u64 { return volatile_read8(p)+(volatile_read8(p+1)*256); }
fn flight_fat_le32_v125(p:u64) -> u64 { return volatile_read8(p)+(volatile_read8(p+1)*256)+(volatile_read8(p+2)*65536)+(volatile_read8(p+3)*16777216); }
fn flight_fat_name_v125(p:u64,which:u64) -> u64 {
    if p==0 { return 0; }
    if volatile_read8(p)!=70 || volatile_read8(p+1)!=82 || volatile_read8(p+2)!=65 || volatile_read8(p+3)!=77 || volatile_read8(p+4)!=69 || volatile_read8(p+5)!=83 { return 0; }
    if which==1 { if volatile_read8(p+6)!=32 || volatile_read8(p+7)!=32 || volatile_read8(p+8)!=76 || volatile_read8(p+9)!=79 || volatile_read8(p+10)!=71 { return 0; } return 1; }
    if which==2 { if volatile_read8(p+6)!=32 || volatile_read8(p+7)!=32 || volatile_read8(p+8)!=84 || volatile_read8(p+9)!=65 || volatile_read8(p+10)!=71 { return 0; } return 1; }
    return 0;
}
fn flight_fat_next_v125(msc:u64,fat_start:u64,cluster:u64,tag:u64) -> u64 {
    let entry=cluster*4; let sec=fat_start+(entry/512); let off=entry%512; let data=usb_msc_bot_read10(msc,tag,sec,1); if data==0 { return 0; } return flight_fat_le32_v125(data+off)%268435456;
}
fn flight_fat32_find_root_v125(msc:u64,fr:u64,which:u64,tagbase:u64) -> u64 {
    if msc==0 || fr==0 { return 0; } let data_start=volatile_read64(fr+160); let fat_start=volatile_read64(fr+168); let spc=volatile_read64(fr+176); var cluster=volatile_read64(fr+184); var depth:u64=0;
    if data_start==0 || fat_start==0 || spc==0 || cluster<2 { return 0; }
    while cluster>=2 && cluster<268435448 && depth<16 {
        var sec:u64=0; while sec<spc && sec<64 {
            let lba=data_start+((cluster-2)*spc)+sec; let data=usb_msc_bot_read10(msc,tagbase+depth*65+sec,lba,1); if data==0 { return 0; }
            var off:u64=0; while off<512 { let first=volatile_read8(data+off); if first==0 { return 0; } if first!=229 && volatile_read8(data+off+11)!=15 { if flight_fat_name_v125(data+off,which)!=0 { let hi=flight_fat_le16_v125(data+off+20); let lo=flight_fat_le16_v125(data+off+26); let fc=(hi*65536)+lo; let sz=flight_fat_le32_v125(data+off+28); return (fc*4294967296)+sz; } } off=off+32; }
            sec=sec+1;
        }
        cluster=flight_fat_next_v125(msc,fat_start,cluster,tagbase+1024+depth); depth=depth+1;
    }
    return 0;
}
fn flight_fat32_contig_v125(msc:u64,fr:u64,start:u64,clusters:u64) -> u64 {
    if msc==0 || fr==0 || start<2 || clusters==0 { return 0; } let fat_start=volatile_read64(fr+168); if fat_start==0 { return 0; } var c=start; var left=clusters; var group:u64=0;
    while left>1 && group<128 {
        let entry=c*4; let sec=fat_start+(entry/512); let data=usb_msc_bot_read10(msc,2500+group,sec,1); if data==0 { return 0; } var off=entry%512;
        while left>1 && off<=508 { let n=flight_fat_le32_v125(data+off)%268435456; if n!=c+1 { return 0; } c=n; left=left-1; off=off+4; }
        group=group+1;
    }
    if left!=1 { return 0; } let end=flight_fat_next_v125(msc,fat_start,c,2756); if end<268435448 { return 0; } return 1;
}
'''
idx=s.index('fn flight_log_arm_v125'); s=s[:idx]+fat_helpers+s[idx:]
new_arm=r'''fn flight_log_arm_v125(fr:u64,msc:u64) -> u64 {
    serial_usb_msc_diag(30,0);
    if fr==0 || msc==0 || volatile_read64(fr)!=1 || volatile_read64(msc+664)!=1 { return 0; }
    if usb_msc_capacity_v125(msc)==0 || volatile_read64(msc+680)!=512 { flight_record_v125(fr,262401,1,0); return 0; }
    var tag:u64=200; let sec0=usb_msc_bot_read10(msc,tag,0,1); if sec0==0 { flight_record_v125(fr,262401,2,0); return 0; }
    var pstart:u64=0; var boot=sec0;
    let bps0=flight_fat_le16_v125(sec0+11); if bps0!=512 || volatile_read8(sec0+13)==0 {
        var pi:u64=0; var found:u64=0; while pi<4 { let e=sec0+446+(pi*16); let typ=volatile_read8(e+4); if found==0 && (typ==11 || typ==12 || typ==6 || typ==14) { pstart=flight_fat_le32_v125(e+8); found=1; } pi=pi+1; }
        if found==0 { flight_record_v125(fr,262401,3,0); return 0; } tag=tag+1; boot=usb_msc_bot_read10(msc,tag,pstart,1); if boot==0 { return 0; }
    }
    let bps=flight_fat_le16_v125(boot+11); let spc=volatile_read8(boot+13); let reserved=flight_fat_le16_v125(boot+14); let nf=volatile_read8(boot+16); let fatsz=flight_fat_le32_v125(boot+36); let root=flight_fat_le32_v125(boot+44);
    if bps!=512 || spc==0 || spc>64 || reserved<1 || nf<1 || fatsz==0 || root<2 { flight_record_v125(fr,262401,4,(spc*65536)+reserved); return 0; }
    let fat_start=pstart+reserved; let data_start=pstart+reserved+(nf*fatsz); unsafe { volatile_write64(fr+160,data_start); volatile_write64(fr+168,fat_start); volatile_write64(fr+176,spc); volatile_write64(fr+184,root); }
    let loginfo=flight_fat32_find_root_v125(msc,fr,1,300); let taginfo=flight_fat32_find_root_v125(msc,fr,2,1600);
    if loginfo==0 || taginfo==0 { flight_record_v125(fr,262401,5,loginfo); return 0; }
    let logcluster=loginfo/4294967296; let logsize=loginfo%4294967296; let tagcluster=taginfo/4294967296; let tagsize=taginfo%4294967296;
    if logsize!=4194304 || tagsize<32 || tagcluster<2 { flight_record_v125(fr,262401,6,logsize); return 0; }
    let taglba=data_start+((tagcluster-2)*spc); let td=usb_msc_bot_read10(msc,2400,taglba,1); if td==0 { return 0; }
    if volatile_read64(td)!=3550878661635560006 || volatile_read64(td+8)!=1 || volatile_read64(td+16)!=3545795563478602310 || volatile_read64(td+24)!=4194304 { flight_record_v125(fr,262401,7,volatile_read64(td)); return 0; }
    let cluster_bytes=spc*512; let needed=(logsize+cluster_bytes-1)/cluster_bytes; if flight_fat32_contig_v125(msc,fr,logcluster,needed)==0 { flight_record_v125(fr,262401,8,logcluster); return 0; }
    let start=data_start+((logcluster-2)*spc); let end=start+(needed*spc)-1; if end>volatile_read64(msc+688) { return 0; }
    unsafe { volatile_write64(fr+64,1); volatile_write64(fr+72,start); volatile_write64(fr+80,end); volatile_write64(fr+88,start); volatile_write64(fr+120,2); volatile_write64(fr+128,3545795563478602310); volatile_write64(fr+136,spc); volatile_write64(fr+144,fat_start); volatile_write64(fr+152,logcluster); }
    flight_record_v125(fr,262400,start,end); serial_usb_msc_diag(37,start); serial_marker_controlled_usb_log_r25(); return 1;
}'''
repl_fn('flight_log_arm_v125',new_arm)
# Bound only MSC waits; preserve HID polling timing.
a,b=span(s,'xhci_wait_bulk_event'); wf=s[a:b]
if 'while spins<16000000 {' not in wf: raise SystemExit('MSC bulk wait anchor missing')
wf=wf.replace('while spins<16000000 {','while spins<500000 {',1); s=s[:a]+wf+s[b:]
# Remove synchronous persistence from the top of the desktop loop.
old="        let fr=volatile_read64(hardware_state+648); let msc=volatile_read64(hardware_state+640); if fr!=0 && msc!=0 && volatile_read64(fr+64)!=0 { if flight_flush_one_v125(fr,msc,xhci)==0 { flight_record_v125(fr,262402,volatile_read64(fr+104),volatile_read64(fr+88)); } }\n        if xhci!=0"
if old not in s: raise SystemExit('synchronous desktop flush anchor missing')
s=s.replace(old,"        let fr=volatile_read64(hardware_state+648); let msc=volatile_read64(hardware_state+640);\n        if xhci!=0",1)
start,end=span(s,'flight_flush_one_v125'); f=s[start:end]
if 'now-last<60000000 && count<20' not in f: raise SystemExit('flush throttle anchor missing')
f=f.replace('now-last<60000000 && count<20','now-last<250000000 && count<40')
f=f.replace('unsafe { volatile_write64(fr+104,volatile_read64(fr+104)+1); } return 0;','unsafe { volatile_write64(fr+104,volatile_read64(fr+104)+1); volatile_write64(fr+64,0); } return 0;')
s=s[:start]+f+s[end:]
old='        if telemetry_redraw!=0 { if v108_input_overlay_present(process,state,input_state,xhci)==0 { return 0; } }\n        cpu_pause();'
if old not in s: raise SystemExit('end-loop flush anchor missing')
new='        if telemetry_redraw!=0 { if v108_input_overlay_present(process,state,input_state,xhci)==0 { return 0; } }\n        if fr!=0 && msc!=0 && volatile_read64(fr+64)!=0 && volatile_read64(fr+32)>=40 { if flight_flush_one_v125(fr,msc,xhci)==0 { flight_record_v125(fr,262402,volatile_read64(fr+104),volatile_read64(fr+88)); } }\n        cpu_pause();'
s=s.replace(old,new,1)
if s.count('let flight_buffer = bump_alloc(&mut heap_cursor, heap_end, 65536);')!=1: raise SystemExit('flight buffer allocation anchor missing')
s=s.replace('let flight_buffer = bump_alloc(&mut heap_cursor, heap_end, 65536);','let flight_buffer = bump_alloc(&mut heap_cursor, heap_end, 262144);',1)
if s.count('flight_recorder_init_v125(flight_state,flight_buffer,65536)')!=1: raise SystemExit('flight buffer init anchor missing')
s=s.replace('flight_recorder_init_v125(flight_state,flight_buffer,65536)','flight_recorder_init_v125(flight_state,flight_buffer,262144)',1)
expected='a27cb9e33e6cf060a4e405e63699e2f079d2e0b6c9c30c7dd06fac13b1077f6d'; actual=hashlib.sha256(s.encode()).hexdigest()
if actual!=expected: raise SystemExit(f'r25l identity mismatch {actual}')
p.write_text(s); print(actual)
