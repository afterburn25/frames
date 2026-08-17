#!/usr/bin/env python3
from pathlib import Path
import hashlib,subprocess,sys
if len(sys.argv)!=2: raise SystemExit('usage: patch_v108_r38_hid_event_identity_altsetting.py <kernel/main.nx>')
p=Path(sys.argv[1]); base=Path(__file__).with_name('patch_v108_r37b_stable_diag.py')
subprocess.run([sys.executable,str(base),str(p)],check=True,stdout=subprocess.DEVNULL)
s=p.read_text(); BASE='2cb422d2c7d00cdbb1da3eee4ee696c9ae0723b3f28669bf80efe256d14de650'
if hashlib.sha256(s.encode()).hexdigest()!=BASE: raise SystemExit('r37b base mismatch')
def rep(a,b,l,n=1):
 global s
 c=s.count(a)
 if c!=n: raise SystemExit(f'{l} count {c}')
 s=s.replace(a,b,n)
def fntext(name):
 st=s.index('fn '+name); op=s.index('{',st); d=0
 for i in range(op,len(s)):
  d += (s[i]=='{')-(s[i]=='}')
  if d==0:return s[st:i+1]
 raise SystemExit('unterminated '+name)
def fmut(name,a,b,l):
 global s
 f=fntext(name); c=f.count(a)
 if c!=1: raise SystemExit(f'{l} count {c}')
 nf=f.replace(a,b,1); s=s.replace(f,nf,1)
def label(name,text):
 z=f'fn {name}(surface:u64,x:u64,y:u64,color:u64) -> u64 {{'
 for i,ch in enumerate(text): z+=f' if gui_draw_char_scaled(surface,((x+{i*6})*65536)+y,({ord(ch)}*65536)+1,color)==0 {{ return 0; }}'
 return z+' return 1; }'
# Alternate setting capture and selection.
rep('var iface:u64=0; var endpoint:u64=0;','var iface:u64=0; var alt:u64=0; var endpoint:u64=0;','select alt var')
rep('if wanted==1 { iface=volatile_read64(xhci_state+1096); endpoint=','if wanted==1 { iface=volatile_read64(xhci_state+1096); alt=volatile_read64(xhci_state+2856); endpoint=','select keyboard alt')
rep('if wanted==2 { iface=volatile_read64(xhci_state+1144); endpoint=','if wanted==2 { iface=volatile_read64(xhci_state+1144); alt=volatile_read64(xhci_state+2864); endpoint=','select mouse alt')
rep('volatile_write64(xhci_state+328,iface); volatile_write64(xhci_state+336,wanted);','volatile_write64(xhci_state+328,iface); volatile_write64(xhci_state+2848,alt); volatile_write64(xhci_state+336,wanted);','selected alt')
rep('volatile_write64(xhci_state+1208,0);\n    }','volatile_write64(xhci_state+1208,0); volatile_write64(xhci_state+2848,0); volatile_write64(xhci_state+2856,0); volatile_write64(xhci_state+2864,0);\n    }','alt reset')
rep('if full_ok==0 { return 0; }\n    var off:u64=0; var active:u64=0; var interface_num:u64=0;','if full_ok==0 { return 0; }\n    var off:u64=0; var active:u64=0; var interface_num:u64=0; var interface_alt:u64=0;','alt parser state')
rep('active=pro; interface_num=volatile_read8(full+off+2); }','active=pro; interface_num=volatile_read8(full+off+2); interface_alt=volatile_read8(full+off+3); }','alt descriptor')
rep('volatile_write64(xhci_state+1096,interface_num); volatile_write64(xhci_state+1104,addr);','volatile_write64(xhci_state+1096,interface_num); volatile_write64(xhci_state+2856,interface_alt); volatile_write64(xhci_state+1104,addr);','keyboard alt candidate')
rep('volatile_write64(xhci_state+1144,interface_num); volatile_write64(xhci_state+1152,addr);','volatile_write64(xhci_state+1144,interface_num); volatile_write64(xhci_state+2864,interface_alt); volatile_write64(xhci_state+1152,addr);','mouse alt candidate')
rep('serial_usb_config_diag(20,config);\n    let interface_num=volatile_read64(xhci_state+328); let protocol_setup=', 'serial_usb_config_diag(20,config);\n    let interface_num=volatile_read64(xhci_state+328); let interface_alt=volatile_read64(xhci_state+2848); if interface_alt!=0 { let interface_setup=2817+(interface_alt*65536)+(interface_num*4294967296); if xhci_control_no_data_out(xhci_state,interface_setup)==0 { serial_usb_config_diag(23,(interface_num*65536)+interface_alt); return 0; } serial_usb_config_diag(24,(interface_num*65536)+interface_alt); }\n    let protocol_setup=','SET_INTERFACE')
# Record the one outstanding Normal TRB as the current HID generation.
fmut('xhci_hid_arm_continuous','volatile_write64(xhci_state+408,tail); volatile_write64(xhci_state+800,cycle); volatile_write64(xhci_state+808,1); volatile_write32(doorbells+(slot*4),dci);','volatile_write64(xhci_state+408,tail); volatile_write64(xhci_state+800,cycle); volatile_write64(xhci_state+2928,trb); volatile_write64(xhci_state+2888,(trb-ring)/16); volatile_write64(xhci_state+808,1); volatile_write32(doorbells+(slot*4),dci);','active trb arm')
# Quarantine stopped-generation events before a fresh ring is armed.
anchor='fn v137_xhci_hid_rebase_ring(xhci_state:u64) -> u64 {'
helper=r'''fn v138_xhci_hid_drain_old_events(xhci_state:u64) -> u64 {
    if xhci_state==0 { return 0; } let slot=volatile_read64(xhci_state+136); let dci=volatile_read64(xhci_state+352); if slot==0 || dci<2 || dci>31 { return 0; }
    var drained:u64=0; var q:u64=0; while q<16 { let queued=xhci_event_mailbox_take_v127(xhci_state,slot,dci); if queued==0 { q=16; } else { let packed=queued-1; unsafe { volatile_write64(xhci_state+2880,packed/16777216); volatile_write64(xhci_state+2872,volatile_read64(xhci_state+2872)+1); } drained=drained+1; q=q+1; } }
    let er=volatile_read64(xhci_state+24); if er==0 { return drained; } var spins:u64=0; var idle:u64=0;
    while spins<250000 && idle<5000 { let i=volatile_read64(xhci_state+96); let cyc=volatile_read64(xhci_state+104); let e=er+(i*16); let ctl=volatile_read32(e+12); if ctl%2==cyc { idle=0; let typ=(ctl/1024)%64; if typ==32 { let st=volatile_read32(e+8); let code=(st/16777216)%256; let residue=st%16777216; let ep=(ctl/65536)%32; let eslot=(ctl/16777216)%256; let source=volatile_read64(e); xhci_event_advance(xhci_state); if eslot==slot && ep==dci { unsafe { volatile_write64(xhci_state+2880,code); volatile_write64(xhci_state+2920,source); volatile_write64(xhci_state+2872,volatile_read64(xhci_state+2872)+1); } drained=drained+1; } else { xhci_event_mailbox_put_v127(xhci_state,eslot,ep,(code*16777216)+residue); } } else { idle=5000; } } else { idle=idle+1; cpu_pause(); } spins=spins+1; }
    return drained;
}
'''+anchor
rep(anchor,helper,'drain helper')
rep('volatile_write64(xhci_state+408,0); volatile_write64(xhci_state+800,1); volatile_write64(xhci_state+808,0);','volatile_write64(xhci_state+408,0); volatile_write64(xhci_state+800,1); volatile_write64(xhci_state+808,0); volatile_write64(xhci_state+2928,0); volatile_write64(xhci_state+2888,255);','rebase generation reset')
rep('if v136_xhci_command_endpoint(xhci_state,15,0)==0 { ok=0; }\n            let first=', 'if v136_xhci_command_endpoint(xhci_state,15,0)==0 { ok=0; } pit_wait(11932); v138_xhci_hid_drain_old_events(xhci_state);\n            let first=','running stop drain')
rep('v136_xhci_command_endpoint(xhci_state,16,first)==0 { ok=0; }\n            unsafe', 'v136_xhci_command_endpoint(xhci_state,16,first)==0 { ok=0; } v138_xhci_hid_drain_old_events(xhci_state);\n            unsafe','running post-deq drain')
rep('if state==2 { if v136_xhci_command_endpoint(xhci_state,14,0)==0 { ok=0; } }\n        let next=', 'if state==2 { if v136_xhci_command_endpoint(xhci_state,14,0)==0 { ok=0; } } v138_xhci_hid_drain_old_events(xhci_state);\n        let next=','halted pre-deq drain')
rep('v136_xhci_command_endpoint(xhci_state,16,next)==0 { ok=0; }\n        unsafe', 'v136_xhci_command_endpoint(xhci_state,16,next)==0 { ok=0; } v138_xhci_hid_drain_old_events(xhci_state);\n        unsafe','halted post-deq drain')
# A transfer event may only retire the currently armed Normal TRB.
fmut('xhci_hid_poll_continuous','let packet=volatile_read64(xhci_state+360); var code:u64=0; var residue:u64=0; var matched:u64=0;','let packet=volatile_read64(xhci_state+360); let active_trb=volatile_read64(xhci_state+2928); var code:u64=0; var residue:u64=0; var matched:u64=0; var source:u64=0;','poll identity vars')
fmut('xhci_hid_poll_continuous','if queued!=0 { let packed=queued-1; code=packed/16777216; residue=packed%16777216; matched=1; }','if queued!=0 { let packed=queued-1; code=packed/16777216; residue=packed%16777216; if code>=26 && code<=28 { unsafe { volatile_write64(xhci_state+2880,code); volatile_write64(xhci_state+2872,volatile_read64(xhci_state+2872)+1); } return 1; } matched=1; }','queued stopped quarantine')
fmut('xhci_hid_poll_continuous','let event_slot=(control/16777216)%256; xhci_event_advance(xhci_state);','let event_slot=(control/16777216)%256; source=volatile_read64(trb); xhci_event_advance(xhci_state);','event source capture')
fmut('xhci_hid_poll_continuous','if event_slot!=slot || event_ep!=dci { xhci_event_mailbox_put_v127(xhci_state,event_slot,event_ep,(code*16777216)+residue); return 1; }\n    }','if event_slot!=slot || event_ep!=dci { xhci_event_mailbox_put_v127(xhci_state,event_slot,event_ep,(code*16777216)+residue); return 1; }\n        unsafe { volatile_write64(xhci_state+2920,source); } let ring=volatile_read64(xhci_state+392); if ring!=0 && source>=ring && source<ring+4080 { unsafe { volatile_write64(xhci_state+2896,(source-ring)/16); } } else { unsafe { volatile_write64(xhci_state+2896,255); } } if active_trb!=0 && source!=active_trb { unsafe { volatile_write64(xhci_state+2912,volatile_read64(xhci_state+2912)+1); volatile_write64(xhci_state+2880,code); } return 1; }\n    }','event identity gate')
fmut('xhci_hid_poll_continuous','volatile_write64(xhci_state+808,0); volatile_write64(xhci_state+2784,code);','volatile_write64(xhci_state+808,0); volatile_write64(xhci_state+2928,0); volatile_write64(xhci_state+2784,code);','accepted generation clear')
rep('volatile_write64(xhci_state+1248,0); volatile_write64(xhci_state+1256,0); }','volatile_write64(xhci_state+1248,0); volatile_write64(xhci_state+1256,0); volatile_write64(xhci_state+2872,0); volatile_write64(xhci_state+2880,0); volatile_write64(xhci_state+2888,255); volatile_write64(xhci_state+2896,255); volatile_write64(xhci_state+2912,0); volatile_write64(xhci_state+2920,0); volatile_write64(xhci_state+2928,0); }','telemetry init')
# Stable compact physical row: R38 S Q A T V E.
rep(fntext('v108_text_r37_v137'),label('v108_text_r37_v137','R38 S Q A T V E'),'row label')
row='v108_draw_small_u64(surface,((px+208)*65536)+(py+730),volatile_read64(xhci+2832),white); v108_draw_small_u64(surface,((px+256)*65536)+(py+730),volatile_read64(xhci+2728),white); v108_draw_small_u64(surface,((px+316)*65536)+(py+730),volatile_read64(xhci+2816),green);'
rep(row,'v108_draw_small_u64(surface,((px+208)*65536)+(py+730),volatile_read64(xhci+2848),white); v108_draw_small_u64(surface,((px+256)*65536)+(py+730),volatile_read64(xhci+2888),white); v108_draw_small_u64(surface,((px+316)*65536)+(py+730),volatile_read64(xhci+2896),green);','full row')
row2='''        v108_draw_small_u64(surface,((px+208)*65536)+(py+730),volatile_read64(xhci+2832),white);
        v108_draw_small_u64(surface,((px+256)*65536)+(py+730),volatile_read64(xhci+2728),white);
        v108_draw_small_u64(surface,((px+316)*65536)+(py+730),volatile_read64(xhci+2816),green);'''
rep(row2,'''        v108_draw_small_u64(surface,((px+208)*65536)+(py+730),volatile_read64(xhci+2848),white);
        v108_draw_small_u64(surface,((px+256)*65536)+(py+730),volatile_read64(xhci+2888),white);
        v108_draw_small_u64(surface,((px+316)*65536)+(py+730),volatile_read64(xhci+2896),green);''','compact row')
rep('var last_r37_c:u64=0; var last_r37_f:u64=0; var last_r37_e:u64=0;','var last_r37_c:u64=0; var last_r37_f:u64=255; var last_r38_v:u64=255; var last_r37_e:u64=0;','baseline vars')
rep('last_r37_c=volatile_read64(xhci+2832); last_r37_f=volatile_read64(xhci+2816); last_r37_e=', 'last_r37_c=volatile_read64(xhci+2848); last_r37_f=volatile_read64(xhci+2888); last_r38_v=volatile_read64(xhci+2896); last_r37_e=','baseline values')
rep('let rc=volatile_read64(xhci+2832); let rf=volatile_read64(xhci+2816); let re=', 'let rc=volatile_read64(xhci+2848); let rf=volatile_read64(xhci+2888); let rv=volatile_read64(xhci+2896); let re=','live values')
rep('rc!=last_r37_c || rf!=last_r37_f || re!=last_r37_e','rc!=last_r37_c || rf!=last_r37_f || rv!=last_r38_v || re!=last_r37_e','live changed')
rep('last_r37_c=rc; last_r37_f=rf; last_r37_e=re;','last_r37_c=rc; last_r37_f=rf; last_r38_v=rv; last_r37_e=re;','live baselines')
p.write_text(s); out=hashlib.sha256(s.encode()).hexdigest(); EXPECTED='c6962f3cb939e6b83308f85f07cb8b319ee322747cd419b99b1c2e82e5c8375d'
if out!=EXPECTED: raise SystemExit(f'r38 output sha mismatch {out}')
print(out)
