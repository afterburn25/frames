#!/usr/bin/env python3
from pathlib import Path
import sys, hashlib, subprocess

if len(sys.argv)!=2:
    raise SystemExit('usage: patch_v108_physical_input_r24_elan_frame_xhci_reset.py <kernel/main.nx>')
p=Path(sys.argv[1])
# r24 is a corrective delta over the exact r23 transform. Recreate r23 from
# the protected r21 source first so r22/r23 remain immutable physical records.
r23=Path(__file__).with_name('patch_v108_physical_input_r23_dragright_xhci_ro.py')
subprocess.run([sys.executable,str(r23),str(p)],check=True,stdout=subprocess.DEVNULL)
s=p.read_text()

def replace_once(old,new,label):
    global s
    n=s.count(old)
    if n!=1: raise SystemExit(f'{label}: expected 1 anchor got {n}')
    s=s.replace(old,new,1)

def fn_text(name):
    start=s.index('fn '+name); i=s.index('{',start); d=0
    for j in range(i,len(s)):
        if s[j]=='{': d+=1
        elif s[j]=='}':
            d-=1
            if d==0: return s[start:j+1]
    raise SystemExit('unterminated '+name)

def text_fn(name,text):
    parts=[]
    for i,ch in enumerate(text):
        parts.append(f'if gui_draw_char_scaled(surface,((x+{i*6})*65536)+y,({ord(ch)}*65536)+1,color)==0 {{ return 0; }}')
    return f"fn {name}(surface:u64,x:u64,y:u64,color:u64) -> u64 {{ "+' '.join(parts)+" return 1; }\n"

# Exact 6-byte Elantech v4 frame lock once the sliding detector has established alignment.
old=fn_text('ps2_mouse_decode_v108')
new=r'''fn ps2_mouse_decode_v108(input_state:u64,data:u64) -> u64 {
    if input_state==0 || volatile_read64(input_state+32)!=1 { return 0; }
    let byte=data%256; unsafe { volatile_write64(input_state+3184,volatile_read64(input_state+3184)+1); }
    if byte==250 || byte==170 { return 1; }

    // Preserve the rolling six-byte telemetry history for diagnostics.
    let n=volatile_read64(input_state+3424); unsafe {
        volatile_write64(input_state+3432,volatile_read64(input_state+3440)); volatile_write64(input_state+3440,volatile_read64(input_state+3448)); volatile_write64(input_state+3448,volatile_read64(input_state+3456));
        volatile_write64(input_state+3456,volatile_read64(input_state+3464)); volatile_write64(input_state+3464,volatile_read64(input_state+3472)); volatile_write64(input_state+3472,byte);
        if n<6 { volatile_write64(input_state+3424,n+1); } volatile_write64(input_state+3536,volatile_read64(input_state+3536)+1);
    }

    let mode=volatile_read64(input_state+3488);
    if mode==4 {
        // Once Elantech v4 is locked, consume exactly six bytes per frame.  Do
        // not classify overlapping rolling windows as packets; that was the
        // physical source of motion-generated L/R edges in r22/r23.
        var fc=volatile_read64(input_state+2840); if fc>=6 { fc=0; }
        unsafe { volatile_write64(input_state+2848+(fc*8),byte); volatile_write64(input_state+2840,fc+1); }
        if fc+1<6 { return 1; }
        let a=(volatile_read64(input_state+2848)*65536)+(volatile_read64(input_state+2856)*256)+volatile_read64(input_state+2864);
        let b=(volatile_read64(input_state+2872)*65536)+(volatile_read64(input_state+2880)*256)+volatile_read64(input_state+2888);
        let typ=ps2_elan4_type_v110(a,b); unsafe { volatile_write64(input_state+2840,0); }
        if typ==0 {
            unsafe { volatile_write64(input_state+3488,0); volatile_write64(input_state+2896,volatile_read64(input_state+2896)+1); volatile_write64(input_state+3552,0); }
            return 1;
        }
        unsafe { volatile_write64(input_state+2904,volatile_read64(input_state+2904)+1); }
        return ps2_elan4_emit_v110(input_state,a,b,typ);
    }

    if volatile_read64(input_state+3424)>=6 && mode!=1 {
        let a=(volatile_read64(input_state+3432)*65536)+(volatile_read64(input_state+3440)*256)+volatile_read64(input_state+3448);
        let b=(volatile_read64(input_state+3456)*65536)+(volatile_read64(input_state+3464)*256)+volatile_read64(input_state+3472);
        let typ=ps2_elan4_type_v110(a,b);
        if typ!=0 {
            let idx=volatile_read64(input_state+3536); let last=volatile_read64(input_state+3544); var hits:u64=1; if last!=0 && idx>=last && idx-last<=8 { hits=volatile_read64(input_state+3552)+1; }
            if hits>3 { hits=3; } unsafe { volatile_write64(input_state+3544,idx); volatile_write64(input_state+3552,hits); volatile_write64(input_state+3528,volatile_read64(input_state+3528)+1); }
            if hits>=2 && mode==0 {
                unsafe { volatile_write64(input_state+3488,4); volatile_write64(input_state+2840,0); volatile_write64(input_state+2904,volatile_read64(input_state+2904)+1); }
                return ps2_elan4_emit_v110(input_state,a,b,typ);
            }
        }
    }

    var count=volatile_read64(input_state+3376);
    if count==0 { unsafe { volatile_write64(input_state+3384,byte); volatile_write64(input_state+3376,1); } return 1; }
    if count==1 { unsafe { volatile_write64(input_state+3392,byte); volatile_write64(input_state+3376,2); } return 1; }
    let h=volatile_read64(input_state+3384)%256; let dx=volatile_read64(input_state+3392)%256; let dy=byte;
    unsafe { volatile_write64(input_state+3400,dy); volatile_write64(input_state+3296,h); volatile_write64(input_state+3304,dx); volatile_write64(input_state+3312,dy); }
    let xsign=(h/16)%2; let ysign=(h/32)%2; var valid:u64=1;
    if (h/8)%2==0 || (h/64)%2!=0 || (h/128)%2!=0 { valid=0; unsafe { volatile_write64(input_state+3280,volatile_read64(input_state+3280)+1); } }
    if valid!=0 && (xsign!=(dx/128)%2 || ysign!=(dy/128)%2) { valid=0; unsafe { volatile_write64(input_state+3288,volatile_read64(input_state+3288)+1); } }
    var ax=dx; if xsign!=0 { ax=256-dx; } var ay=dy; if ysign!=0 { ay=256-dy; }
    if valid!=0 && (ax>80 || ay>80) { valid=0; unsafe { volatile_write64(input_state+3416,volatile_read64(input_state+3416)+1); } }
    if valid==0 {
        unsafe { volatile_write64(input_state+3384,dx); volatile_write64(input_state+3392,dy); volatile_write64(input_state+3376,2); volatile_write64(input_state+3408,0); volatile_write64(input_state+3272,volatile_read64(input_state+3272)+1); }
        return 1;
    }
    unsafe { volatile_write64(input_state+3376,0); }
    var run=volatile_read64(input_state+3408)+1; if run>3 { run=3; } unsafe { volatile_write64(input_state+3408,run); }
    if run<2 { return 1; }
    if volatile_read64(input_state+3488)==0 { unsafe { volatile_write64(input_state+3488,1); } }
    let buttons=h%8; let yscreen=(256-dy)%256;
    unsafe { volatile_write64(input_state+3104,2); volatile_write64(input_state+3176,volatile_read64(input_state+3176)+1); }
    if volatile_read64(input_state+3168)==0 { unsafe { volatile_write64(input_state+3168,1); } serial_marker_v108_ps2_packet_ok(); }
    input_push(input_state,4,0,buttons); input_push(input_state,5,0,dx); input_push(input_state,6,0,yscreen);
    return 1;
}'''
replace_once(old,new,'Elantech v4 exact-frame lock')

# Make the xHCI port reset evidence explicit and require the physical port to
# become enabled before the higher-level slot/address state machine proceeds.
old=fn_text('xhci_port_write_base')
new=r'''fn xhci_port_write_base(value:u64) -> u64 {
    var v=value; v=clear_flag(v,2); v=clear_flag(v,131072); v=clear_flag(v,262144); v=clear_flag(v,524288); v=clear_flag(v,1048576); v=clear_flag(v,2097152); v=clear_flag(v,4194304); v=clear_flag(v,8388608); return v;
}'''
replace_once(old,new,'PORTSC write base does not write-one-disable PED')

old=fn_text('xhci_reset_connected_port_from')
new=r'''fn xhci_reset_connected_port_from(xhci_state:u64,start:u64) -> u64 {
    if xhci_state==0 || volatile_read64(xhci_state+56)!=1 { return 0; }
    let base=volatile_read64(xhci_state); let op=volatile_read64(xhci_state+8); let hcs1=volatile_read32(base+4); var ports=(hcs1/16777216)%256; if ports>32 { ports=32; }
    unsafe { volatile_write64(xhci_state+1640,0); volatile_write64(xhci_state+1648,0); volatile_write64(xhci_state+1656,0); volatile_write64(xhci_state+1664,0); volatile_write64(xhci_state+1672,0); }
    var p=start;
    while p<ports {
        let port=op+1024+(p*16); let ps=volatile_read32(port);
        if ps%2!=0 {
            unsafe { volatile_write64(xhci_state+1640,p+1); volatile_write64(xhci_state+1648,ps); }
            var write=xhci_port_write_base(ps); write=set_flag(write,16); unsafe { volatile_write32(port,write); }
            var spins:u64=0; while (volatile_read32(port)/16)%2!=0 && spins<5000000 { cpu_pause(); spins=spins+1; }
            if spins>=5000000 { unsafe { volatile_write64(xhci_state+1656,volatile_read32(port)); volatile_write64(xhci_state+1672,1); } return 0; }
            // Give USB2 reset recovery time before consuming PED and before
            // issuing Enable Slot / Address Device on real silicon.
            pit_wait(11932);
            var done=volatile_read32(port); if done%2==0 { unsafe { volatile_write64(xhci_state+1656,done); volatile_write64(xhci_state+1672,2); } return 0; }
            spins=0; while (done/2)%2==0 && spins<2000000 { cpu_pause(); done=volatile_read32(port); spins=spins+1; }
            unsafe { volatile_write64(xhci_state+1656,done); }
            if (done/2)%2==0 { unsafe { volatile_write64(xhci_state+1672,3); } return 0; }
            unsafe { volatile_write64(xhci_state+1664,1); volatile_write64(xhci_state+1672,0); volatile_write64(xhci_state+112,p+1); volatile_write64(xhci_state+120,done); volatile_write64(xhci_state+128,1); volatile_write64(xhci_state+384,0); volatile_write64(xhci_state+416,0); }
            serial_marker_xhci_port_ready(); return p+1;
        }
        p=p+1;
    }
    unsafe { volatile_write64(xhci_state+1672,4); }
    return 0;
}'''
replace_once(old,new,'strict xHCI reset/enable')

# Freeze first Intel physical reset attempt before later controller/pass scratch reuse.
old='''let port=xhci_reset_connected_port_from(xhci_state,scan_start); if port==0 { tries=32; }
                            else { scan_start=port; tries=tries+1; unsafe { volatile_write64(xhci_state+1056,2); volatile_write64(xhci_state+1064,tries); volatile_write64(xhci_state+1072,port); }'''
new='''let port=xhci_reset_connected_port_from(xhci_state,scan_start); if (pci_cfg_read32(bdf/65536,(bdf/256)%256,bdf%256,0)%65536)==32902 && ((pci_cfg_read32(bdf/65536,(bdf/256)%256,bdf%256,0)/65536)%65536)==35889 && volatile_read64(hardware_state+600)==0 { unsafe { volatile_write64(hardware_state+600,volatile_read64(xhci_state+1640)); volatile_write64(hardware_state+608,volatile_read64(xhci_state+1648)); volatile_write64(hardware_state+616,volatile_read64(xhci_state+1656)); volatile_write64(hardware_state+624,volatile_read64(xhci_state+1664)); volatile_write64(hardware_state+632,volatile_read64(xhci_state+1672)); } if port==0 { tries=32; }
                            else { scan_start=port; tries=tries+1; unsafe { volatile_write64(xhci_state+1056,2); volatile_write64(xhci_state+1064,tries); volatile_write64(xhci_state+1072,port); }'''
replace_once(old,new,'freeze Intel xHCI reset attempt')

old='''volatile_write64(xhci_state+1600,volatile_read64(hardware_state+560)); volatile_write64(xhci_state+1608,volatile_read64(hardware_state+568)); volatile_write64(xhci_state+1616,volatile_read64(hardware_state+576)); volatile_write64(xhci_state+1624,volatile_read64(hardware_state+584)); volatile_write64(xhci_state+1632,volatile_read64(hardware_state+592)); }'''
new='''volatile_write64(xhci_state+1600,volatile_read64(hardware_state+560)); volatile_write64(xhci_state+1608,volatile_read64(hardware_state+568)); volatile_write64(xhci_state+1616,volatile_read64(hardware_state+576)); volatile_write64(xhci_state+1624,volatile_read64(hardware_state+584)); volatile_write64(xhci_state+1632,volatile_read64(hardware_state+592)); volatile_write64(xhci_state+1640,volatile_read64(hardware_state+600)); volatile_write64(xhci_state+1648,volatile_read64(hardware_state+608)); volatile_write64(xhci_state+1656,volatile_read64(hardware_state+616)); volatile_write64(xhci_state+1664,volatile_read64(hardware_state+624)); volatile_write64(xhci_state+1672,volatile_read64(hardware_state+632)); }'''
replace_once(old,new,'preserve reset diagnostic')

# Replace now-conclusive EHCI row with reset-stage evidence.
anchor='fn v108_input_overlay_draw(surface:u64,state:u64,input_state:u64,xhci:u64) -> u64 {'
replace_once(anchor,text_fn('v108_text_xrst_v124','XRST P B A E F')+anchor,'XRST label')
old='''    v108_text_ehci_v121(surface,px+10,py+514,white); if xhci!=0 { v108_draw_small_u64(surface,((px+112)*65536)+(py+514),volatile_read64(xhci+1416),amber); v108_draw_small_u64(surface,((px+184)*65536)+(py+514),volatile_read64(xhci+1472),white); v108_draw_small_u64(surface,((px+286)*65536)+(py+514),volatile_read64(xhci+1480),white); }'''
new='''    v108_text_xrst_v124(surface,px+10,py+514,white); if xhci!=0 { v108_draw_small_u64(surface,((px+112)*65536)+(py+514),volatile_read64(xhci+1640),amber); v108_draw_small_u64(surface,((px+166)*65536)+(py+514),volatile_read64(xhci+1648),white); v108_draw_small_u64(surface,((px+250)*65536)+(py+514),volatile_read64(xhci+1656),white); v108_draw_small_u64(surface,((px+334)*65536)+(py+514),volatile_read64(xhci+1664),green); v108_draw_small_u64(surface,((px+382)*65536)+(py+514),volatile_read64(xhci+1672),red); }'''
replace_once(old,new,'XRST telemetry')

# Initialize exact-frame state when PS/2 path starts.
old='''volatile_write64(input_state+3560,0); volatile_write64(input_state+3568,0); volatile_write64(input_state+3576,0); volatile_write64(input_state+3584,0); volatile_write64(input_state+3592,0); volatile_write64(input_state+3600,0);'''
new='''volatile_write64(input_state+3560,0); volatile_write64(input_state+3568,0); volatile_write64(input_state+3576,0); volatile_write64(input_state+3584,0); volatile_write64(input_state+3592,0); volatile_write64(input_state+3600,0); volatile_write64(input_state+2840,0); volatile_write64(input_state+2896,0); volatile_write64(input_state+2904,0);'''
replace_once(old,new,'initialize exact-frame state')

# Make XPRT sample the connected port, not the first nonzero disconnected
# powered port. r23 physical evidence showed why the old sample could be even
# while C=1.
old=fn_text('v108_xhci_port_census_ro_v123')
new=r'''fn v108_xhci_port_census_ro_v123(xhci_state:u64,hardware_state:u64) -> u64 {
    if xhci_state==0 || hardware_state==0 || volatile_read64(xhci_state+56)!=1 { return 0; }
    let base=volatile_read64(xhci_state); let op=volatile_read64(xhci_state+8); if base==0 || op==0 { return 0; }
    var ports=(volatile_read32(base+4)/16777216)%256; if ports>32 { ports=32; } if ports==0 { return 0; }
    var connected:u64=0; var enabled:u64=0; var powered:u64=0; var connected_sample:u64=0; var any_sample:u64=0; var p:u64=0;
    while p<ports {
        let ps=volatile_read32(op+1024+(p*16));
        if ps%2!=0 { connected=connected+1; if connected_sample==0 { connected_sample=ps; } }
        if (ps/2)%2!=0 { enabled=enabled+1; }
        if (ps/512)%2!=0 { powered=powered+1; }
        if any_sample==0 && ps!=0 { any_sample=ps; }
        p=p+1;
    }
    var sample=connected_sample; if sample==0 { sample=any_sample; }
    unsafe { volatile_write64(hardware_state+560,ports); volatile_write64(hardware_state+568,connected); volatile_write64(hardware_state+576,enabled); volatile_write64(hardware_state+584,powered); volatile_write64(hardware_state+592,sample); }
    serial_marker_v108_xhci_port_census_v123(); return 1;
}'''
replace_once(old,new,'connected-port XPRT sample')

# Invariants
if 'desktop_redraw=1' in s: raise SystemExit('full desktop repaint re-enabled')
if 'volatile_write64(input_state+2848+(fc*8),byte)' not in s: raise SystemExit('exact-frame collector missing')
if 'v=clear_flag(v,2)' not in fn_text('xhci_port_write_base'): raise SystemExit('PED write-one-disable guard missing')
if 'volatile_write64(xhci_state+1672,3)' not in fn_text('xhci_reset_connected_port_from'): raise SystemExit('PED enable failure telemetry missing')
p.write_text(s)
print(hashlib.sha256(s.encode()).hexdigest())
