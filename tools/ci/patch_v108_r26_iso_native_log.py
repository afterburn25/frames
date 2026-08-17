#!/usr/bin/env python3
from pathlib import Path
import hashlib, subprocess, sys
if len(sys.argv)!=2: raise SystemExit('usage: patch_v108_r26_iso_native_log.py <kernel/main.nx>')
p=Path(sys.argv[1])
base=Path(__file__).with_name('patch_v108_r25k_large_media_log_gate.py')
subprocess.run([sys.executable,str(base),str(p)],check=True,stdout=subprocess.DEVNULL)
s=p.read_text()
R25K='af77b8f648dbb11fa6a31810e2150483818213635c92404dd956db892df9fdb0'
if hashlib.sha256(s.encode()).hexdigest()!=R25K: raise SystemExit('r25k identity mismatch')

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
def marker(name,text):
 return 'fn '+name+'() -> void { '+' '.join(f'serial_putc({ord(c)});' for c in text+'\n')+' return; }\n'

helpers=r'''fn flight_fat_le16_v126(p:u64) -> u64 { return volatile_read8(p)+(volatile_read8(p+1)*256); }
fn flight_fat_le32_v126(p:u64) -> u64 { return volatile_read8(p)+(volatile_read8(p+1)*256)+(volatile_read8(p+2)*65536)+(volatile_read8(p+3)*16777216); }
fn flight_fat32_vbr_ok_v126(p:u64) -> u64 {
    if p==0 || volatile_read8(p+510)!=85 || volatile_read8(p+511)!=170 { return 0; }
    let bps=flight_fat_le16_v126(p+11); let spc=volatile_read8(p+13); let reserved=flight_fat_le16_v126(p+14); let nf=volatile_read8(p+16); let fatsz=flight_fat_le32_v126(p+36); let root=flight_fat_le32_v126(p+44);
    if bps!=512 || spc==0 || spc>64 || reserved==0 || nf==0 || nf>4 || fatsz==0 || root<2 { return 0; } return 1;
}
fn flight_fat_name_log_v126(p:u64) -> u64 {
    if p==0 { return 0; }
    if volatile_read8(p)!=70 || volatile_read8(p+1)!=82 || volatile_read8(p+2)!=65 || volatile_read8(p+3)!=77 || volatile_read8(p+4)!=69 || volatile_read8(p+5)!=83 || volatile_read8(p+6)!=32 || volatile_read8(p+7)!=32 || volatile_read8(p+8)!=76 || volatile_read8(p+9)!=79 || volatile_read8(p+10)!=71 { return 0; } return 1;
}
fn flight_fat_next_v126(msc:u64,fat_start:u64,cluster:u64,tag:u64) -> u64 {
    let entry=cluster*4; let sec=fat_start+(entry/512); let off=entry%512; let data=usb_msc_bot_read10(msc,tag,sec,1); if data==0 || off>508 { return 0; } return flight_fat_le32_v126(data+off)%268435456;
}
fn flight_fat32_find_log_v126(msc:u64,root:u64,tagbase:u64) -> u64 {
    let data_start=volatile_read64(msc+1816); let fat_start=volatile_read64(msc+1824); let spc=volatile_read64(msc+1832); if data_start==0 || fat_start==0 || spc==0 { return 0; }
    var cluster=root; var depth:u64=0;
    while cluster>=2 && cluster<268435448 && depth<64 {
        var sec:u64=0; while sec<spc {
            let lba=data_start+((cluster-2)*spc)+sec; let data=usb_msc_bot_read10(msc,tagbase+(depth*64)+sec,lba,1); if data==0 { return 0; }
            var off:u64=0; while off<512 {
                let first=volatile_read8(data+off); if first==0 { return 0; }
                let attr=volatile_read8(data+off+11); if first!=229 && attr!=15 && attr%32<16 && flight_fat_name_log_v126(data+off)!=0 {
                    let hi=flight_fat_le16_v126(data+off+20); let lo=flight_fat_le16_v126(data+off+26); let fc=(hi*65536)+lo; let sz=flight_fat_le32_v126(data+off+28); return (fc*4294967296)+sz;
                }
                off=off+32;
            }
            sec=sec+1;
        }
        cluster=flight_fat_next_v126(msc,fat_start,cluster,tagbase+5000+depth); depth=depth+1;
    }
    return 0;
}
fn flight_fat32_contig_log_v126(msc:u64,start:u64,clusters:u64,tagbase:u64) -> u64 {
    let fat_start=volatile_read64(msc+1824); if fat_start==0 || start<2 || clusters==0 || clusters>8192 { return 0; }
    var c=start; var left=clusters; var group:u64=0;
    while left>1 && group<96 {
        let entry=c*4; let sec=fat_start+(entry/512); let data=usb_msc_bot_read10(msc,tagbase+group,sec,1); if data==0 { return 0; } var off=entry%512;
        while left>1 && off<=508 { let n=flight_fat_le32_v126(data+off)%268435456; if n!=c+1 { return 0; } c=n; left=left-1; off=off+4; }
        group=group+1;
    }
    if left!=1 { return 0; }
    let end=flight_fat_next_v126(msc,fat_start,c,tagbase+128); if end<268435448 { return 0; } return 1;
}
fn flight_persist_fail_v126(fr:u64,msc:u64) -> u64 {
    if msc!=0 { unsafe { volatile_write64(msc+1800,0); } }
    if fr!=0 { unsafe { volatile_write64(fr+104,volatile_read64(fr+104)+1); volatile_write64(fr+64,0); volatile_write64(fr+224,1); } flight_record_v125(fr,262403,volatile_read64(fr+104),volatile_read64(fr+88)); }
    serial_marker_log_persist_disabled_r26(); return 0;
}
'''
idx=s.index('fn flight_log_arm_v125')
s=s[:idx]+marker('serial_marker_iso_log_r26','FRAMES_ISO_LOG_R26_ARMED')+marker('serial_marker_log_persist_disabled_r26','FRAMES_LOG_PERSIST_R26_DISABLED')+marker('serial_marker_input_after_log_fail_r26','FRAMES_INPUT_AFTER_LOG_FAIL_R26_OK')+helpers+s[idx:]

new_arm=r'''fn flight_log_arm_v125(fr:u64,msc:u64) -> u64 {
    serial_usb_msc_diag(30,0);
    if fr==0 || msc==0 || volatile_read64(fr)!=1 || volatile_read64(msc+664)!=1 { return 0; }
    if usb_msc_capacity_v125(msc)==0 || volatile_read64(msc+680)!=512 { flight_record_v125(fr,262401,1,0); return 0; }
    var tag:u64=200; let sec0=usb_msc_bot_read10(msc,tag,0,1); if sec0==0 { flight_record_v125(fr,262401,2,0); return 0; }
    var pstart:u64=0; var boot=sec0; var found:u64=flight_fat32_vbr_ok_v126(sec0);
    if found==0 {
        if volatile_read8(sec0+510)!=85 || volatile_read8(sec0+511)!=170 { flight_record_v125(fr,262401,3,0); return 0; }
        var pi:u64=0; while pi<4 && found==0 {
            let e=sec0+446+(pi*16); let candidate=flight_fat_le32_v126(e+8); let sectors=flight_fat_le32_v126(e+12);
            if candidate!=0 && sectors!=0 { tag=tag+1; let vb=usb_msc_bot_read10(msc,tag,candidate,1); if vb!=0 && flight_fat32_vbr_ok_v126(vb)!=0 { pstart=candidate; boot=vb; found=1; } }
            pi=pi+1;
        }
        if found==0 && volatile_read8(sec0+450)==238 {
            let gh=usb_msc_bot_read10(msc,230,1,1); if gh!=0 && volatile_read64(gh)==6075990659671082565 {
                let entry_lba=volatile_read64(gh+72); let entry_count=flight_fat_le32_v126(gh+80); let entry_size=flight_fat_le32_v126(gh+84); var ei:u64=0;
                while ei<entry_count && ei<32 && found==0 {
                    let byteoff=ei*entry_size; let elba=entry_lba+(byteoff/512); let eoff=byteoff%512; let ed=usb_msc_bot_read10(msc,300+ei,elba,1);
                    if ed!=0 && eoff+48<=512 { let candidate=volatile_read64(ed+eoff+32); if candidate!=0 { let vb=usb_msc_bot_read10(msc,400+ei,candidate,1); if vb!=0 && flight_fat32_vbr_ok_v126(vb)!=0 { pstart=candidate; boot=vb; found=1; } } }
                    ei=ei+1;
                }
            }
        }
        if found==0 { flight_record_v125(fr,262401,4,0); return 0; }
    }
    let spc=volatile_read8(boot+13); let reserved=flight_fat_le16_v126(boot+14); let nf=volatile_read8(boot+16); let fatsz=flight_fat_le32_v126(boot+36); let root=flight_fat_le32_v126(boot+44); let fat_start=pstart+reserved; let data_start=pstart+reserved+(nf*fatsz);
    unsafe { volatile_write64(msc+1816,data_start); volatile_write64(msc+1824,fat_start); volatile_write64(msc+1832,spc); }
    let info=flight_fat32_find_log_v126(msc,root,1000); if info==0 { flight_record_v125(fr,262401,5,pstart); return 0; }
    let logcluster=info/4294967296; let logsize=info%4294967296; if logcluster<2 || logsize!=4194304 { flight_record_v125(fr,262401,6,logsize); return 0; }
    let first=data_start+((logcluster-2)*spc); let hd=usb_msc_bot_read10(msc,7000,first,1); if hd==0 { return 0; }
    if volatile_read64(hd+128)!=3905238009226482246 || volatile_read64(hd+136)!=1 || volatile_read64(hd+144)!=3545795563478602310 || volatile_read64(hd+152)!=4194304 || volatile_read64(hd+160)!=512 { flight_record_v125(fr,262401,7,volatile_read64(hd+128)); return 0; }
    let cluster_bytes=spc*512; let needed=(logsize+cluster_bytes-1)/cluster_bytes; if flight_fat32_contig_log_v126(msc,logcluster,needed,7100)==0 { flight_record_v125(fr,262401,8,logcluster); return 0; }
    let sectors=logsize/512; let start=first+1; let end=first+sectors-1; if start>end || end>volatile_read64(msc+688) { return 0; }
    unsafe { volatile_write64(fr+64,1); volatile_write64(fr+72,start); volatile_write64(fr+80,end); volatile_write64(fr+88,start); volatile_write64(fr+112,read_tsc()); volatile_write64(fr+120,3); volatile_write64(fr+128,3545795563478602310); volatile_write64(fr+136,pstart); volatile_write64(fr+144,spc); volatile_write64(fr+152,fat_start); volatile_write64(fr+160,data_start); volatile_write64(fr+168,logcluster); volatile_write64(fr+224,0); volatile_write64(msc+1800,1); }
    flight_record_v125(fr,262400,start,end); serial_usb_msc_diag(37,start); serial_marker_controlled_usb_log_r25(); serial_marker_iso_log_r26(); return 1;
}'''
repl_fn('flight_log_arm_v125',new_arm)

# Only logger snapshot transfers get a short fail-fast wait budget.
a,b=span(s,'xhci_wait_bulk_event');f=s[a:b]
old='let event_ring=volatile_read64(xhci_state+24); var spins:u64=0;\n    while spins<16000000 {'
if old not in f: raise SystemExit('bulk wait anchor')
f=f.replace(old,'let event_ring=volatile_read64(xhci_state+24); var spins:u64=0; var limit:u64=16000000; if volatile_read64(xhci_state+1800)==1 { limit=500000; }\n    while spins<limit {',1);s=s[:a]+f+s[b:]

# Write one log sector at a time; first failure disarms persistence but leaves RAM recorder and desktop alive.
a,b=span(s,'flight_flush_one_v125');f=s[a:b]
old='if fr==0 || msc==0 || volatile_read64(fr+64)!=1 || volatile_read64(msc+664)!=1 { return 1; } let count=volatile_read64(fr+32); if count==0 { return 1; } let now=read_tsc(); let last=volatile_read64(fr+112); if last!=0 && now>last && now-last<60000000 && count<20 { return 1; }'
if old not in f: raise SystemExit('flush header anchor')
f=f.replace(old,'if fr==0 || msc==0 || volatile_read64(fr+64)!=1 || volatile_read64(msc+664)!=1 { return 1; } let count=volatile_read64(fr+32); if count<5 { return 1; } let now=read_tsc();',1)
f=f.replace('if data==0 || buffer==0 || cap==0 { return 0; }','if data==0 || buffer==0 || cap==0 { return flight_persist_fail_v126(fr,msc); }',1)
f=f.replace('if lba<volatile_read64(fr+72) || lba>volatile_read64(fr+80) { return 0; }','if lba<volatile_read64(fr+72) || lba>volatile_read64(fr+80) { return flight_persist_fail_v126(fr,msc); }',1)
oldfail='flight_sync_events_v125(msc,active,1); unsafe { volatile_write64(fr+104,volatile_read64(fr+104)+1); } return 0;'
if f.count(oldfail)!=3: raise SystemExit(f'flush fail branches {f.count(oldfail)}')
f=f.replace(oldfail,'flight_sync_events_v125(msc,active,1); return flight_persist_fail_v126(fr,msc);')
s=s[:a]+f+s[b:]

# Track last RAM event so disk I/O occurs only after a quiet gap.
a,b=span(s,'flight_record_v125');f=s[a:b]
old='tail=(tail+1)%cap; count=count+1; unsafe { volatile_write64(state+8,seq); volatile_write64(state+16,head); volatile_write64(state+24,tail); volatile_write64(state+32,count); } return 1;'
if old not in f: raise SystemExit('flight activity anchor')
f=f.replace(old,'tail=(tail+1)%cap; count=count+1; unsafe { volatile_write64(state+8,seq); volatile_write64(state+16,head); volatile_write64(state+24,tail); volatile_write64(state+32,count); volatile_write64(state+216,read_tsc()); } return 1;',1);s=s[:a]+f+s[b:]

# Never perform persistent storage work before input polling.
old='        let fr=volatile_read64(hardware_state+648); let msc=volatile_read64(hardware_state+640); if fr!=0 && msc!=0 && volatile_read64(fr+64)!=0 { if flight_flush_one_v125(fr,msc,xhci)==0 { flight_record_v125(fr,262402,volatile_read64(fr+104),volatile_read64(fr+88)); } }\n        if xhci!=0'
if old not in s: raise SystemExit('top-loop flush anchor')
s=s.replace(old,'        let fr=volatile_read64(hardware_state+648); let msc=volatile_read64(hardware_state+640);\n        if xhci!=0',1)
old='''        if pointer_changed!=0 && (newx!=oldx || newy!=oldy) {
            let source=volatile_read64(input_state+3104);'''
if old not in s: raise SystemExit('post-failure pointer anchor')
s=s.replace(old,'''        if pointer_changed!=0 && (newx!=oldx || newy!=oldy) {
            if fr!=0 && volatile_read64(fr+224)!=0 && volatile_read64(fr+232)==0 { unsafe { volatile_write64(fr+232,1); } serial_marker_input_after_log_fail_r26(); }
            let source=volatile_read64(input_state+3104);''',1)

old='        if telemetry_redraw!=0 { if v108_input_overlay_present(process,state,input_state,xhci)==0 { return 0; } }\n        cpu_pause();'
if old not in s: raise SystemExit('end-loop anchor')
new='''        if telemetry_redraw!=0 { if v108_input_overlay_present(process,state,input_state,xhci)==0 { return 0; } }
        if fr!=0 && msc!=0 && volatile_read64(fr+64)!=0 && volatile_read64(fr+32)>=5 && volatile_read64(input_state+4064)==0 { let quiet_now=read_tsc(); let last_event=volatile_read64(fr+216); if last_event!=0 && quiet_now>last_event && quiet_now-last_event>300000000 { if flight_flush_one_v125(fr,msc,xhci)==0 { flight_record_v125(fr,262402,volatile_read64(fr+104),volatile_read64(fr+88)); } } }
        cpu_pause();'''
s=s.replace(old,new,1)

# Expand the RAM ring so active desktop work can continue while persistent writes wait for idle time.
for old,new in [('let flight_buffer = bump_alloc(&mut heap_cursor, heap_end, 65536);','let flight_buffer = bump_alloc(&mut heap_cursor, heap_end, 262144);'),('flight_recorder_init_v125(flight_state,flight_buffer,65536)','flight_recorder_init_v125(flight_state,flight_buffer,262144)')]:
 if s.count(old)!=1: raise SystemExit('flight buffer anchor '+old)
 s=s.replace(old,new,1)

expected='5dc6c6b04f7103a3981287d048264c94b75bfb12fd50538ca0a285979aa001fc'
actual=hashlib.sha256(s.encode()).hexdigest()
if actual!=expected: raise SystemExit(f'r26 identity mismatch {actual}')
p.write_text(s);print(actual)
