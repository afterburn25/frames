#!/usr/bin/env python3
from pathlib import Path
import hashlib,subprocess,sys
if len(sys.argv)!=2: raise SystemExit('usage: patch_v108_r32_usb_settle_input_recovery.py <kernel/main.nx>')
p=Path(sys.argv[1]); base=Path(__file__).with_name('patch_v108_r31b_overlay_state.py')
subprocess.run([sys.executable,str(base),str(p)],check=True,stdout=subprocess.DEVNULL)
s=p.read_text(); BASE='57944cdb9f5060b5b170a42280fe37dce32125040f5e1da6295df615e1f81e6e'
if hashlib.sha256(s.encode()).hexdigest()!=BASE: raise SystemExit('r31b base mismatch')

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

def rep(old,new,label,count=1):
    global s
    n=s.count(old)
    if n!=count: raise RuntimeError(f'{label} count {n}')
    s=s.replace(old,new,count)

# 1) xHCI physical settle after route/controller reset. r31b physical evidence showed
#    the controller healthy but only the boot medium visible at the immediate census.
#    Give switchable Intel root ports/devices time to reconnect after HCRST, record the
#    before/after count, then scan. This is bounded and leaves storage policy untouched.
helper=r'''fn xhci_root_port_settle_v132(xhci_state:u64) -> u64 {
    if xhci_state==0 || volatile_read64(xhci_state+56)!=1 { return 0; }
    let before=xhci_count_connected_ports_v119(xhci_state); var best=before; var stable:u64=0; var rounds:u64=0;
    while rounds<10 && stable<5 {
        pit_wait(119320); let now=xhci_count_connected_ports_v119(xhci_state);
        if now>best { best=now; stable=0; } else { stable=stable+1; }
        rounds=rounds+1;
    }
    unsafe { volatile_write64(xhci_state+2288,before); volatile_write64(xhci_state+2296,best); volatile_write64(xhci_state+2304,rounds); }
    return best;
}
'''
rep('fn xhci_controller_init(hardware_state:u64, phys_state:u64, xhci_state:u64, pml4:u64) -> u64 {', helper+'fn xhci_controller_init(hardware_state:u64, phys_state:u64, xhci_state:u64, pml4:u64) -> u64 {','settle helper insert')
rep('    xhci_power_root_ports_v129(xhci_state); let connected=xhci_count_connected_ports_v119(xhci_state); unsafe { volatile_write64(xhci_state+1320,connected); }',
    '    xhci_power_root_ports_v129(xhci_state); let connected=xhci_root_port_settle_v132(xhci_state); unsafe { volatile_write64(xhci_state+1320,connected); }',
    'settled connected census')

# 2) Elantech v4 right-button hardening. Motion packets may report button bits, but
#    physical r31b showed movement manufacturing a right edge. Only status/head packets
#    may change button state. Status accepts the edge immediately; head requires two
#    stable samples. Motion remains diagnostic-only for buttons.
new_btn=r'''fn ps2_elan4_buttons_v111(input_state:u64,a:u64,typ:u64) -> u64 {
    if input_state==0 { return 0; }
    let old=volatile_read64(input_state+3560); var left=old%2; var raw_right=volatile_read64(input_state+3760); var out_right=volatile_read64(input_state+2816);
    if typ==1 || typ==2 {
        let raw=(a/65536)%4; left=raw%2; raw_right=(raw/2)%2; let cand=volatile_read64(input_state+2800); var stable=volatile_read64(input_state+2808);
        unsafe { volatile_write64(input_state+3760,raw_right); }
        if raw_right==cand { stable=stable+1; if stable>8 { stable=8; } } else { if stable!=0 && stable<2 { unsafe { volatile_write64(input_state+2824,volatile_read64(input_state+2824)+1); } } unsafe { volatile_write64(input_state+2800,raw_right); } stable=1; }
        unsafe { volatile_write64(input_state+2808,stable); }
        var need:u64=2; if typ==1 { need=1; }
        if raw_right!=out_right && stable>=need { out_right=raw_right; unsafe { volatile_write64(input_state+2816,out_right); volatile_write64(input_state+3768,volatile_read64(input_state+3768)+1); } serial_marker_v108_right_direct_v122(); }
        flight_input_record_v125(input_state,131328+typ,(raw*65536)+stable,(old*256)+(left+(out_right*2)));
    }
    if typ==3 { let raw=(a/65536)%4; unsafe { volatile_write64(input_state+2832,volatile_read64(input_state+2832)+1); } flight_input_record_v125(input_state,131331,(raw*65536)+volatile_read64(input_state+2808),(old*256)+(left+(out_right*2))); }
    let buttons=left+(out_right*2);
    if buttons!=old { unsafe { if buttons!=0 { volatile_write64(input_state+3056,1); } volatile_write64(input_state+3560,buttons); volatile_write64(input_state+3568,volatile_read64(input_state+3568)+1); if buttons%2!=0 && old%2==0 { volatile_write64(input_state+3576,volatile_read64(input_state+3576)+1); } } input_push(input_state,4,0,buttons); }
    return buttons;
}'''
repl_fn('ps2_elan4_buttons_v111',new_btn)

# 3) A released stale right bit must not block the next legitimate left click into
#    INPUT TEST. Current right-down is still rejected; a previous right state alone is not.
rep('    if (buttons/2)%2!=0 || (old_buttons/2)%2!=0 { return 0; }',
    '    if (buttons/2)%2!=0 { return 0; }',
    'textbox stale-right focus gate')

# 4) One compact physical row: immediate and settled root-connection counts + rounds.
def label_fn(name,text):
    out=f'fn {name}(surface:u64,x:u64,y:u64,color:u64) -> u64 {{'
    for i,ch in enumerate(text): out+=f' if gui_draw_char_scaled(surface,((x+{i*6})*65536)+y,({ord(ch)}*65536)+1,color)==0 {{ return 0; }}'
    return out+' return 1; }\n'
rep('fn v108_input_overlay_draw(surface:u64,state:u64,input_state:u64,xhci:u64) -> u64 {',
    label_fn('v108_text_r32_v132','R32 USB B A W')+'fn v108_input_overlay_draw(surface:u64,state:u64,input_state:u64,xhci:u64) -> u64 {',
    'r32 label insert')
rep('(410*65536)+724','(410*65536)+742','r32 overlay height',count=s.count('(410*65536)+724'))
a,b=span(s,'v108_input_overlay_draw'); ov=s[a:b]
old='''    v108_text_xlog_v131(surface,px+10,py+676,white); v108_draw_small_u64(surface,((px+112)*65536)+(py+676),volatile_read64(xhci+2240),amber); v108_draw_small_u64(surface,((px+166)*65536)+(py+676),volatile_read64(xhci+2248),red); v108_draw_small_u64(surface,((px+220)*65536)+(py+676),volatile_read64(xhci+2256),green); v108_draw_small_u64(surface,((px+274)*65536)+(py+676),volatile_read64(xhci+2264),white); v108_draw_small_u64(surface,((px+328)*65536)+(py+676),volatile_read64(xhci+2272),amber); v108_draw_small_u64(surface,((px+376)*65536)+(py+676),volatile_read64(xhci+2280),green);
    return 1;'''
new='''    v108_text_xlog_v131(surface,px+10,py+676,white); v108_draw_small_u64(surface,((px+112)*65536)+(py+676),volatile_read64(xhci+2240),amber); v108_draw_small_u64(surface,((px+166)*65536)+(py+676),volatile_read64(xhci+2248),red); v108_draw_small_u64(surface,((px+220)*65536)+(py+676),volatile_read64(xhci+2256),green); v108_draw_small_u64(surface,((px+274)*65536)+(py+676),volatile_read64(xhci+2264),white); v108_draw_small_u64(surface,((px+328)*65536)+(py+676),volatile_read64(xhci+2272),amber); v108_draw_small_u64(surface,((px+376)*65536)+(py+676),volatile_read64(xhci+2280),green);
    v108_text_r32_v132(surface,px+10,py+694,white); if xhci!=0 { v108_draw_small_u64(surface,((px+130)*65536)+(py+694),volatile_read64(xhci+2288),amber); v108_draw_small_u64(surface,((px+202)*65536)+(py+694),volatile_read64(xhci+2296),green); v108_draw_small_u64(surface,((px+274)*65536)+(py+694),volatile_read64(xhci+2304),white); }
    return 1;'''
if ov.count(old)!=1: raise RuntimeError('overlay anchor '+str(ov.count(old)))
ov=ov.replace(old,new,1); s=s[:a]+ov+s[b:]

# Contracts.
assert 'xhci_root_port_settle_v132' in s
assert 'if typ==1 || typ==2 {' in s[span(s,'ps2_elan4_buttons_v111')[0]:span(s,'ps2_elan4_buttons_v111')[1]]
btn=s[span(s,'ps2_elan4_buttons_v111')[0]:span(s,'ps2_elan4_buttons_v111')[1]]
assert 'if typ==3' in btn and 'raw_right=(raw/2)%2' not in btn.split('if typ==3',1)[1]
click=s[span(s,'v108_input_test_click_v112')[0]:span(s,'v108_input_test_click_v112')[1]]
assert '(old_buttons/2)%2' not in click
assert s.count('{')==s.count('}')
expected='dab5d471bf8cc80a38573fa52aa502f1bc488d9d3ecb655ce734350e123d732f'
actual=hashlib.sha256(s.encode()).hexdigest()
if actual!=expected: raise SystemExit(f'r32 identity mismatch {actual}')
p.write_text(s); print(actual)
