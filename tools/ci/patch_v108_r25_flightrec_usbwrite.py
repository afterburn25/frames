from pathlib import Path
import hashlib, sys, subprocess
if len(sys.argv)!=2: raise SystemExit('usage: patch_v108_r25_flightrec_usbwrite.py <kernel/main.nx>')
p=Path(sys.argv[1])
base=Path(__file__).with_name('patch_v108_physical_input_r24b_fixbrace.py')
subprocess.run([sys.executable,str(base),str(p)],check=True,stdout=subprocess.DEVNULL)
s=p.read_text()
R24='1b56b621de728aabdbbe8c100f92816564369e984f1fc2b5e4815080011aedaf'
if hashlib.sha256(s.encode()).hexdigest()!=R24: raise SystemExit('r24 reconstruction identity mismatch')

def fn_span(text,name):
    st=text.index('fn '+name); op=text.index('{',st); d=0
    for j in range(op,len(text)):
        if text[j]=='{': d+=1
        elif text[j]=='}':
            d-=1
            if d==0:return st,j+1
    raise RuntimeError(name)
def fn_text(name):
    a,b=fn_span(s,name); return s[a:b]
def repl_fn(name,new):
    global s
    a,b=fn_span(s,name); s=s[:a]+new+s[b:]
def rep(old,new,label,count=1):
    global s
    n=s.count(old)
    if n!=count: raise SystemExit(f'{label}: {n}')
    s=s.replace(old,new,count)
def text_fn(name,text):
    parts=[]
    for i,ch in enumerate(text): parts.append(f'if gui_draw_char_scaled(surface,((x+{i*6})*65536)+y,({ord(ch)}*65536)+1,color)==0 {{ return 0; }}')
    return f"fn {name}(surface:u64,x:u64,y:u64,color:u64) -> u64 {{ "+' '.join(parts)+" return 1; }\n"
def marker_fn(name,text):
    return 'fn '+name+'() -> void { '+' '.join(f'serial_putc({ord(c)});' for c in text+'\n')+' return; }\n'

anchor='fn input_queue_init(state:u64) -> u64 {'
insert=r'''fn flight_recorder_init_v125(state:u64,buffer:u64,bytes:u64) -> u64 {
    if state==0 || buffer==0 || bytes<40960 { return 0; } zero_page(state); var i:u64=0; while i<bytes { unsafe { volatile_write8(buffer+i,0); } i=i+1; }
    let cap=bytes/40; if cap<128 { return 0; }
    unsafe { volatile_write64(state,1); volatile_write64(state+8,0); volatile_write64(state+16,0); volatile_write64(state+24,0); volatile_write64(state+32,0); volatile_write64(state+40,cap); volatile_write64(state+48,buffer); volatile_write64(state+56,0); volatile_write64(state+64,0); volatile_write64(state+72,0); volatile_write64(state+80,0); volatile_write64(state+88,0); volatile_write64(state+96,0); volatile_write64(state+104,0); volatile_write64(state+112,0); volatile_write64(state+120,0); volatile_write64(state+128,0); }
    return 1;
}
fn flight_record_v125(state:u64,code:u64,a:u64,b:u64) -> u64 {
    if state==0 || volatile_read64(state)!=1 { return 0; } let cap=volatile_read64(state+40); let buffer=volatile_read64(state+48); if cap==0 || buffer==0 { return 0; }
    var head=volatile_read64(state+16); var tail=volatile_read64(state+24); var count=volatile_read64(state+32); if count>=cap { head=(head+1)%cap; count=count-1; unsafe { volatile_write64(state+56,volatile_read64(state+56)+1); } }
    let seq=volatile_read64(state+8)+1; let rec=buffer+(tail*40); unsafe { volatile_write64(rec,seq); volatile_write64(rec+8,read_tsc()); volatile_write64(rec+16,code); volatile_write64(rec+24,a); volatile_write64(rec+32,b); }
    tail=(tail+1)%cap; count=count+1; unsafe { volatile_write64(state+8,seq); volatile_write64(state+16,head); volatile_write64(state+24,tail); volatile_write64(state+32,count); } return 1;
}
fn flight_input_record_v125(input_state:u64,code:u64,a:u64,b:u64) -> u64 { if input_state==0 { return 0; } let fr=volatile_read64(input_state+3792); if fr==0 { return 0; } return flight_record_v125(fr,code,a,b); }
'''
rep(anchor,insert+anchor,'flight core')

old=fn_text('input_push')
new=old.replace('tail=(tail+1)%capacity; count=count+1; unsafe { volatile_write64(state,head); volatile_write64(state+8,tail); volatile_write64(state+16,count); } return 1;',
'''tail=(tail+1)%capacity; count=count+1; unsafe { volatile_write64(state,head); volatile_write64(state+8,tail); volatile_write64(state+16,count); } let fr=volatile_read64(state+3792); if fr!=0 { flight_record_v125(fr,65536+kind,code,value); } return 1;''')
if new==old: raise SystemExit('input_push anchor')
repl_fn('input_push',new)

new_buttons=r'''fn ps2_elan4_buttons_v111(input_state:u64,a:u64,typ:u64) -> u64 {
    if input_state==0 { return 0; }
    let old=volatile_read64(input_state+3560); var left=old%2; var raw_right=volatile_read64(input_state+3760); var out_right=volatile_read64(input_state+2816);
    if typ>=1 && typ<=3 {
        let raw=(a/65536)%4; if typ==1 || typ==2 { left=raw%2; } raw_right=(raw/2)%2; let cand=volatile_read64(input_state+2800); var stable=volatile_read64(input_state+2808);
        unsafe { volatile_write64(input_state+3760,raw_right); }
        if raw_right==cand { stable=stable+1; if stable>8 { stable=8; } } else { if stable!=0 && stable<2 { unsafe { volatile_write64(input_state+2824,volatile_read64(input_state+2824)+1); } } unsafe { volatile_write64(input_state+2800,raw_right); } stable=1; }
        unsafe { volatile_write64(input_state+2808,stable); }
        var need:u64=3; if typ==1 || typ==2 { need=1; }
        if raw_right!=out_right && stable>=need { out_right=raw_right; unsafe { volatile_write64(input_state+2816,out_right); volatile_write64(input_state+3768,volatile_read64(input_state+3768)+1); } serial_marker_v108_right_direct_v122(); }
        flight_input_record_v125(input_state,131328+typ,(raw*65536)+stable,(old*256)+(left+(out_right*2)));
    }
    let buttons=left+(out_right*2);
    if buttons!=old { unsafe { if buttons!=0 { volatile_write64(input_state+3056,1); } volatile_write64(input_state+3560,buttons); volatile_write64(input_state+3568,volatile_read64(input_state+3568)+1); if buttons%2!=0 && old%2==0 { volatile_write64(input_state+3576,volatile_read64(input_state+3576)+1); } } input_push(input_state,4,0,buttons); }
    return buttons;
}'''
repl_fn('ps2_elan4_buttons_v111',new_buttons)
rep('let typ=ps2_elan4_type_v110(a,b); unsafe { volatile_write64(input_state+2840,0); }','let typ=ps2_elan4_type_v110(a,b); flight_input_record_v125(input_state,131072+typ,a,b); unsafe { volatile_write64(input_state+2840,0); }','elan frame record')

anchor='fn usb_msc_readonly_selftest(xhci_state:u64) -> u64 {'
msc=r'''fn usb_msc_prepare_write10_cbw_v125(xhci_state:u64,tag:u64,lba:u64,blocks:u64) -> u64 {
    let cbw=volatile_read64(xhci_state+752); if cbw==0 || blocks==0 || blocks>8 { return 0; } zero_page(cbw); let transfer=blocks*512;
    unsafe { volatile_write32(cbw,1128420181); volatile_write32(cbw+4,tag); volatile_write32(cbw+8,transfer); volatile_write8(cbw+12,0); volatile_write8(cbw+13,0); volatile_write8(cbw+14,10); volatile_write8(cbw+15,42); volatile_write8(cbw+17,(lba/16777216)%256); volatile_write8(cbw+18,(lba/65536)%256); volatile_write8(cbw+19,(lba/256)%256); volatile_write8(cbw+20,lba%256); volatile_write8(cbw+22,(blocks/256)%256); volatile_write8(cbw+23,blocks%256); } return cbw;
}
fn usb_msc_bot_write10_v125(xhci_state:u64,tag:u64,lba:u64,blocks:u64) -> u64 {
    let cbw=usb_msc_prepare_write10_cbw_v125(xhci_state,tag,lba,blocks); let data=volatile_read64(xhci_state+768); let csw=volatile_read64(xhci_state+760); if cbw==0 || data==0 || csw==0 { return 0; } let length=blocks*512; zero_page(csw);
    if usb_msc_bulk_td(xhci_state,0,cbw,31)!=31 { return 0; } if usb_msc_bulk_td(xhci_state,0,data,length)!=length { return 0; } if usb_msc_bulk_td(xhci_state,1,csw,13)!=13 { return 0; } if usb_msc_check_csw(xhci_state,tag)==0 { return 0; } return 1;
}
fn usb_msc_bot_nodata_v125(xhci_state:u64,tag:u64,opcode:u64) -> u64 {
    let cbw=usb_msc_prepare_cbw(xhci_state,tag,opcode,0); let csw=volatile_read64(xhci_state+760); if cbw==0 || csw==0 { return 0; } zero_page(csw); if usb_msc_bulk_td(xhci_state,0,cbw,31)!=31 { return 0; } if usb_msc_bulk_td(xhci_state,1,csw,13)!=13 { return 0; } return usb_msc_check_csw(xhci_state,tag);
}
fn usb_msc_capacity_v125(xhci_state:u64) -> u64 {
    if xhci_state==0 || volatile_read64(xhci_state+664)!=1 { return 0; } var tag:u64=65; if usb_msc_bot_tur(xhci_state,tag)==0 { tag=tag+1; let sense=usb_msc_bot_in(xhci_state,tag,3,18); if sense==0 { return 0; } tag=tag+1; if usb_msc_bot_tur(xhci_state,tag)==0 { return 0; } }
    tag=tag+1; let cap=usb_msc_bot_in(xhci_state,tag,37,8); if cap==0 { return 0; } let last=usb_read_be32(cap); let block=usb_read_be32(cap+4); if block!=512 { return 0; } unsafe { volatile_write64(xhci_state+680,block); volatile_write64(xhci_state+688,last); } return 1;
}
fn flight_log_arm_v125(fr:u64,msc:u64) -> u64 {
    if fr==0 || msc==0 || volatile_read64(fr)!=1 || volatile_read64(msc+664)!=1 { return 0; } if usb_msc_capacity_v125(msc)==0 { flight_record_v125(fr,262401,1,0); return 0; }
    if volatile_read64(msc+680)!=512 || volatile_read64(msc+688)!=524287 { flight_record_v125(fr,262401,2,volatile_read64(msc+688)); return 0; }
    let data=usb_msc_bot_read10(msc,73,133132,1); if data==0 { flight_record_v125(fr,262401,3,0); return 0; }
    if volatile_read64(data)!=2391787741383512646 || volatile_read64(data+8)!=1 || volatile_read64(data+16)!=524288 || volatile_read64(data+24)!=512 || volatile_read64(data+32)!=133120 || volatile_read64(data+72)!=133132 || volatile_read64(data+80)!=3545795563478602310 { flight_record_v125(fr,262401,4,volatile_read64(data)); return 0; }
    let start=volatile_read64(data+40); let end=volatile_read64(data+48); if start<133152 || end<start || end>=395264 || end-start+1>8192 { flight_record_v125(fr,262401,5,start); return 0; }
    unsafe { volatile_write64(fr+64,1); volatile_write64(fr+72,start); volatile_write64(fr+80,end); volatile_write64(fr+88,start); volatile_write64(fr+120,1); volatile_write64(fr+128,3545795563478602310); }
    flight_record_v125(fr,262400,start,end); serial_marker_controlled_usb_log_r25(); return 1;
}
fn flight_hex16_v125(dst:u64,off:u64,value:u64) -> u64 { if dst==0 { return 0; } var div:u64=1152921504606846976; var i:u64=0; while i<16 { let d=(value/div)%16; var c:u64=48+d; if d>=10 { c=55+d; } unsafe { volatile_write8(dst+off+i,c); } if div>1 { div=div/16; } i=i+1; } return 1; }
fn flight_render_record_v125(dst:u64,off:u64,rec:u64) -> u64 {
    if dst==0 || rec==0 { return 0; } unsafe { volatile_write8(dst+off,83); volatile_write8(dst+off+1,61); volatile_write8(dst+off+18,32); volatile_write8(dst+off+19,84); volatile_write8(dst+off+20,61); volatile_write8(dst+off+37,32); volatile_write8(dst+off+38,69); volatile_write8(dst+off+39,61); volatile_write8(dst+off+56,32); volatile_write8(dst+off+57,65); volatile_write8(dst+off+58,61); volatile_write8(dst+off+75,32); volatile_write8(dst+off+76,66); volatile_write8(dst+off+77,61); volatile_write8(dst+off+94,13); volatile_write8(dst+off+95,10); }
    flight_hex16_v125(dst,off+2,volatile_read64(rec)); flight_hex16_v125(dst,off+21,volatile_read64(rec+8)); flight_hex16_v125(dst,off+40,volatile_read64(rec+16)); flight_hex16_v125(dst,off+59,volatile_read64(rec+24)); flight_hex16_v125(dst,off+78,volatile_read64(rec+32)); return 1;
}
fn flight_sync_events_v125(msc:u64,active:u64,back:u64) -> u64 { if msc==0 || active==0 || volatile_read64(msc)!=volatile_read64(active) { return 1; } if back==0 { unsafe { volatile_write64(msc+96,volatile_read64(active+96)); volatile_write64(msc+104,volatile_read64(active+104)); } } else { unsafe { volatile_write64(active+96,volatile_read64(msc+96)); volatile_write64(active+104,volatile_read64(msc+104)); } } return 1; }
fn flight_flush_one_v125(fr:u64,msc:u64,active:u64) -> u64 {
    if fr==0 || msc==0 || volatile_read64(fr+64)!=1 || volatile_read64(msc+664)!=1 { return 1; } let count=volatile_read64(fr+32); if count==0 { return 1; } let now=read_tsc(); let last=volatile_read64(fr+112); if last!=0 && now>last && now-last<60000000 && count<20 { return 1; }
    let data=volatile_read64(msc+768); let buffer=volatile_read64(fr+48); let cap=volatile_read64(fr+40); if data==0 || buffer==0 || cap==0 { return 0; } var i:u64=0; while i<512 { unsafe { volatile_write8(data+i,32); } i=i+1; }
    var head=volatile_read64(fr+16); var n:u64=0; var take=count; if take>5 { take=5; } while n<take { let rec=buffer+(head*40); flight_render_record_v125(data,n*96,rec); head=(head+1)%cap; n=n+1; }
    unsafe { volatile_write8(data+511,10); } let expected=nvme_read_checksum(data,512); let lba=volatile_read64(fr+88); if lba<volatile_read64(fr+72) || lba>volatile_read64(fr+80) { return 0; } let tag=1000+volatile_read64(fr+96)*4;
    flight_sync_events_v125(msc,active,0); if usb_msc_bot_write10_v125(msc,tag,lba,1)==0 { flight_sync_events_v125(msc,active,1); unsafe { volatile_write64(fr+104,volatile_read64(fr+104)+1); } return 0; } if usb_msc_bot_nodata_v125(msc,tag+1,53)==0 { flight_sync_events_v125(msc,active,1); unsafe { volatile_write64(fr+104,volatile_read64(fr+104)+1); } return 0; }
    let back=usb_msc_bot_read10(msc,tag+2,lba,1); if back==0 || nvme_read_checksum(back,512)!=expected { flight_sync_events_v125(msc,active,1); unsafe { volatile_write64(fr+104,volatile_read64(fr+104)+1); } return 0; } flight_sync_events_v125(msc,active,1);
    var cursor=lba+1; if cursor>volatile_read64(fr+80) { cursor=volatile_read64(fr+72); } unsafe { volatile_write64(fr+16,head); volatile_write64(fr+32,count-take); volatile_write64(fr+88,cursor); volatile_write64(fr+96,volatile_read64(fr+96)+1); volatile_write64(fr+112,now); } return 1;
}
'''
rep(anchor,msc+anchor,'msc write funcs')

anchor='fn v108_xhci_scan_pointer_v116(hardware_state:u64,phys_state:u64,xhci_state:u64,pml4:u64) -> u64 {'
scanhelp=r'''fn v108_msc_snapshot_v125(xhci_state:u64,hardware_state:u64,phys_state:u64,fr:u64) -> u64 {
    if xhci_state==0 || hardware_state==0 || phys_state==0 { return 0; }
    let msc=volatile_read64(hardware_state+640); if msc==0 { return 0; }
    if usb_msc_discover(xhci_state,phys_state)==0 { return 0; }
    if usb_msc_configure(xhci_state,phys_state)==0 { return 0; }
    zero_page(msc); var q:u64=0; while q<4096 { unsafe { volatile_write64(msc+q,volatile_read64(xhci_state+q)); } q=q+8; }
    unsafe { volatile_write64(hardware_state+712,1); }
    if fr!=0 { flight_record_v125(fr,196864,volatile_read64(msc+136),(volatile_read64(msc+272)*65536)+volatile_read64(msc+280)); if flight_log_arm_v125(fr,msc)!=0 { unsafe { volatile_write64(hardware_state+728,1); } } }
    return 1;
}
fn v108_log_msc_retain_v125(hardware_state:u64,phys_state:u64,xhci_state:u64,pml4:u64) -> u64 {
    if hardware_state==0 || phys_state==0 || xhci_state==0 || pml4==0 { return 0; }
    let total=volatile_read64(hardware_state+24); let fr=volatile_read64(hardware_state+648); var ci:u64=0;
    while ci<total && ci<4 {
        let bdf=v108_pci_nth_xhci_v116(ci); if bdf==0 { ci=total; }
        else { let base=pci_bar_base(bdf,0); if base!=0 && ensure_identity_mmio_page(phys_state,pml4,base)!=0 {
            zero_page(xhci_state); v108_intel_xhci_route_ports_v120(bdf,xhci_state,hardware_state); if xhci_controller_init(hardware_state,phys_state,xhci_state,pml4)!=0 {
                var start:u64=0; var tries:u64=0; while tries<32 { let port=xhci_reset_connected_port_from(xhci_state,start); if port==0 { tries=32; } else { start=port; tries=tries+1; if fr!=0 { flight_record_v125(fr,196609,2,port); } let slot=xhci_enable_slot(xhci_state); if slot!=0 { if fr!=0 { flight_record_v125(fr,196609,3,(slot*256)+volatile_read64(xhci_state+488)); } if xhci_address_default_device(xhci_state,phys_state)!=0 { if fr!=0 { flight_record_v125(fr,196609,4,volatile_read64(xhci_state+488)); } if xhci_get_device_descriptor8(xhci_state,phys_state)!=0 { if fr!=0 { flight_record_v125(fr,196609,5,volatile_read64(xhci_state+504)); } if xhci_finalize_address_and_descriptor(xhci_state,phys_state)!=0 { if fr!=0 { flight_record_v125(fr,196609,6,(volatile_read64(xhci_state+272)*65536)+volatile_read64(xhci_state+280)); } if v108_msc_snapshot_v125(xhci_state,hardware_state,phys_state,fr)!=0 && volatile_read64(hardware_state+728)!=0 { unsafe { volatile_write64(hardware_state+680,6); volatile_write64(hardware_state+688,0); volatile_write64(hardware_state+696,volatile_read64(xhci_state+272)); volatile_write64(hardware_state+704,volatile_read64(xhci_state+280)); } return 1; } } } } } } } }
            }
        } ci=ci+1; }
    }
    return 0;
}'''
rep(anchor,scanhelp+anchor,'scan helpers')
rep('let total=volatile_read64(hardware_state+24); var pass:u64=0; var any_ready:u64=0;','let total=volatile_read64(hardware_state+24); let fr=volatile_read64(hardware_state+648); var pass:u64=0; var any_ready:u64=0; unsafe { volatile_write64(hardware_state+680,0); volatile_write64(hardware_state+688,0); volatile_write64(hardware_state+696,0); volatile_write64(hardware_state+704,0); volatile_write64(hardware_state+712,0); volatile_write64(hardware_state+728,0); }','scan start')
rep('let slot_ok=xhci_enable_slot(xhci_state); if slot_ok==0 { unsafe { volatile_write64(xhci_state+1328,3); } }','if fr!=0 { flight_record_v125(fr,196609,2,port); } unsafe { volatile_write64(hardware_state+680,2); } let slot_ok=xhci_enable_slot(xhci_state); if slot_ok==0 { unsafe { volatile_write64(xhci_state+1328,3); volatile_write64(hardware_state+688,3); volatile_write64(hardware_state+704,volatile_read64(xhci_state+488)); } if fr!=0 { flight_record_v125(fr,196610,3,volatile_read64(xhci_state+488)); } }','slot stage')
rep('let address_ok=xhci_address_default_device(xhci_state,phys_state); if address_ok==0 { unsafe { volatile_write64(xhci_state+1328,4); } }','unsafe { volatile_write64(hardware_state+680,3); } let address_ok=xhci_address_default_device(xhci_state,phys_state); if address_ok==0 { unsafe { volatile_write64(xhci_state+1328,4); volatile_write64(hardware_state+688,4); volatile_write64(hardware_state+704,volatile_read64(xhci_state+488)); } if fr!=0 { flight_record_v125(fr,196610,4,volatile_read64(xhci_state+488)); } }','address stage')
rep('let d8_ok=xhci_get_device_descriptor8(xhci_state,phys_state); if d8_ok==0 { unsafe { volatile_write64(xhci_state+1328,5); } }','unsafe { volatile_write64(hardware_state+680,4); } let d8_ok=xhci_get_device_descriptor8(xhci_state,phys_state); if d8_ok==0 { unsafe { volatile_write64(xhci_state+1328,5); volatile_write64(hardware_state+688,5); volatile_write64(hardware_state+704,volatile_read64(xhci_state+504)); } if fr!=0 { flight_record_v125(fr,196610,5,volatile_read64(xhci_state+504)); } }','d8 stage')
rep('let final_ok=xhci_finalize_address_and_descriptor(xhci_state,phys_state); if final_ok==0 { unsafe { volatile_write64(xhci_state+1328,6); } }','unsafe { volatile_write64(hardware_state+680,5); } let final_ok=xhci_finalize_address_and_descriptor(xhci_state,phys_state); if final_ok==0 { unsafe { volatile_write64(xhci_state+1328,6); volatile_write64(hardware_state+688,6); volatile_write64(hardware_state+704,volatile_read64(xhci_state+504)); } if fr!=0 { flight_record_v125(fr,196610,6,volatile_read64(xhci_state+504)); } }','final stage')
old='let desc=volatile_read64(xhci_state+264); var root_class:u64=0; if desc!=0 { root_class=volatile_read8(desc+4); } unsafe { volatile_write64(xhci_state+1056,6); volatile_write64(xhci_state+1080,root_class); volatile_write64(xhci_state+1328,0); }'
new='let desc=volatile_read64(xhci_state+264); var root_class:u64=0; if desc!=0 { root_class=volatile_read8(desc+4); } unsafe { volatile_write64(xhci_state+1056,6); volatile_write64(xhci_state+1080,root_class); volatile_write64(xhci_state+1328,0); volatile_write64(hardware_state+680,6); volatile_write64(hardware_state+688,0); volatile_write64(hardware_state+696,volatile_read64(xhci_state+272)); volatile_write64(hardware_state+704,volatile_read64(xhci_state+280)); } if fr!=0 { flight_record_v125(fr,196609,6,(volatile_read64(xhci_state+272)*65536)+volatile_read64(xhci_state+280)); } if volatile_read64(hardware_state+712)==0 { v108_msc_snapshot_v125(xhci_state,hardware_state,phys_state,fr); }'
rep(old,new,'final success')
rep('v108_ehci_ro_probe_v122(hardware_state,phys_state,xhci_state,pml4);\n    return any_ready;','v108_ehci_ro_probe_v122(hardware_state,phys_state,xhci_state,pml4); if volatile_read64(hardware_state+728)==0 { v108_log_msc_retain_v125(hardware_state,phys_state,xhci_state,pml4); } unsafe { volatile_write64(xhci_state+1680,volatile_read64(hardware_state+680)); volatile_write64(xhci_state+1688,volatile_read64(hardware_state+688)); volatile_write64(xhci_state+1696,volatile_read64(hardware_state+696)); volatile_write64(xhci_state+1704,volatile_read64(hardware_state+704)); volatile_write64(xhci_state+1712,volatile_read64(hardware_state+712)); volatile_write64(xhci_state+1720,volatile_read64(hardware_state+728)); }\n    return any_ready;','scan end')
rep('let xhci_state = bump_alloc(&mut heap_cursor, heap_end, 4096); let input_state = bump_alloc(&mut heap_cursor, heap_end, 4096);','let xhci_state = bump_alloc(&mut heap_cursor, heap_end, 4096); let usb_log_state = bump_alloc(&mut heap_cursor, heap_end, 4096); let flight_state = bump_alloc(&mut heap_cursor, heap_end, 4096); let flight_buffer = bump_alloc(&mut heap_cursor, heap_end, 65536); let input_state = bump_alloc(&mut heap_cursor, heap_end, 4096);','alloc flight')
rep('if input_state != 0 { input_queue_ready = input_queue_init(input_state); if input_queue_ready!=0 { input_queue_ready=v108_elan_tap_selftest_v116(input_state); } }','if input_state != 0 { input_queue_ready = input_queue_init(input_state); if input_queue_ready!=0 { input_queue_ready=v108_elan_tap_selftest_v116(input_state); } } if input_queue_ready!=0 && flight_state!=0 && flight_buffer!=0 && usb_log_state!=0 { if flight_recorder_init_v125(flight_state,flight_buffer,65536)!=0 { unsafe { volatile_write64(input_state+3792,flight_state); volatile_write64(hardware_state+640,usb_log_state); volatile_write64(hardware_state+648,flight_state); } flight_record_v125(flight_state,65537,108,25); serial_marker_flight_recorder_r25(); } }','flight init')
rep('while true {\n        if xhci!=0 && volatile_read64(xhci+808)!=0','while true {\n        let fr=volatile_read64(hardware_state+648); let msc=volatile_read64(hardware_state+640); if fr!=0 && msc!=0 && volatile_read64(fr+64)!=0 { if flight_flush_one_v125(fr,msc,xhci)==0 { flight_record_v125(fr,262402,volatile_read64(fr+104),volatile_read64(fr+88)); } }\n        if xhci!=0 && volatile_read64(xhci+808)!=0','runtime flush')
rep('if context_before==0 && context_after!=0 { unsafe { volatile_write64(input_state+3696,volatile_read64(input_state+3696)+1); }','if context_before==0 && context_after!=0 { if fr!=0 { flight_record_v125(fr,131585,volatile_read64(state+136),volatile_read64(state+144)); } unsafe { volatile_write64(input_state+3696,volatile_read64(input_state+3696)+1); }','context record')
rep('if drag_before!=0 && drag_after==0 { drag_commit=1; }','if drag_before!=0 && drag_after==0 { drag_commit=1; if fr!=0 { flight_record_v125(fr,131586,volatile_read64(state+160),volatile_read64(state+168)); } }','drag record')
s=s.replace('(410*65536)+562,bg','(410*65536)+598,bg',1); s=s.replace('(410*65536)+562,16','(410*65536)+598,16')
anchor='fn v108_input_overlay_draw(surface:u64,state:u64,input_state:u64,xhci:u64) -> u64 {'
labels=text_fn('v108_text_xenu_v125','XENU ST FL VID PID MSC LOG')+text_fn('v108_text_frec_v125','FREC Q DROP ARM W ERR')
rep(anchor,labels+anchor,'overlay labels')
old='    v108_text_xprt_v123(surface,px+10,py+532,white); if xhci!=0 { v108_draw_small_u64(surface,((px+112)*65536)+(py+532),volatile_read64(xhci+1600),white); v108_draw_small_u64(surface,((px+166)*65536)+(py+532),volatile_read64(xhci+1608),green); v108_draw_small_u64(surface,((px+220)*65536)+(py+532),volatile_read64(xhci+1616),amber); v108_draw_small_u64(surface,((px+274)*65536)+(py+532),volatile_read64(xhci+1624),green); v108_draw_small_u64(surface,((px+328)*65536)+(py+532),volatile_read64(xhci+1632),white); }\n    return 1;'
new='    v108_text_xprt_v123(surface,px+10,py+532,white); if xhci!=0 { v108_draw_small_u64(surface,((px+112)*65536)+(py+532),volatile_read64(xhci+1600),white); v108_draw_small_u64(surface,((px+166)*65536)+(py+532),volatile_read64(xhci+1608),green); v108_draw_small_u64(surface,((px+220)*65536)+(py+532),volatile_read64(xhci+1616),amber); v108_draw_small_u64(surface,((px+274)*65536)+(py+532),volatile_read64(xhci+1624),green); v108_draw_small_u64(surface,((px+328)*65536)+(py+532),volatile_read64(xhci+1632),white); }\n    v108_text_xenu_v125(surface,px+10,py+550,white); if xhci!=0 { v108_draw_small_u64(surface,((px+142)*65536)+(py+550),volatile_read64(xhci+1680),amber); v108_draw_small_u64(surface,((px+190)*65536)+(py+550),volatile_read64(xhci+1688),red); v108_draw_small_u64(surface,((px+238)*65536)+(py+550),volatile_read64(xhci+1696),white); v108_draw_small_u64(surface,((px+286)*65536)+(py+550),volatile_read64(xhci+1704),white); v108_draw_small_u64(surface,((px+334)*65536)+(py+550),volatile_read64(xhci+1712),green); v108_draw_small_u64(surface,((px+382)*65536)+(py+550),volatile_read64(xhci+1720),green); }\n    let fr=volatile_read64(input_state+3792); v108_text_frec_v125(surface,px+10,py+568,white); if fr!=0 { v108_draw_small_u64(surface,((px+130)*65536)+(py+568),volatile_read64(fr+32),white); v108_draw_small_u64(surface,((px+184)*65536)+(py+568),volatile_read64(fr+56),amber); v108_draw_small_u64(surface,((px+238)*65536)+(py+568),volatile_read64(fr+64),green); v108_draw_small_u64(surface,((px+292)*65536)+(py+568),volatile_read64(fr+96),green); v108_draw_small_u64(surface,((px+346)*65536)+(py+568),volatile_read64(fr+104),red); }\n    return 1;'
rep(old,new,'overlay tail')
insert_at=s.index('fn flight_recorder_init_v125')
s=s[:insert_at]+marker_fn('serial_marker_flight_recorder_r25','FRAMES_FLIGHT_RECORDER_R25_READY')+marker_fn('serial_marker_controlled_usb_log_r25','FRAMES_CONTROLLED_USB_LOG_R25_ARMED')+s[insert_at:]
if s.count('{')!=s.count('}'): raise SystemExit(f'brace imbalance {s.count("{")} {s.count("}")}')
p.write_text(s)
print(hashlib.sha256(s.encode()).hexdigest())
