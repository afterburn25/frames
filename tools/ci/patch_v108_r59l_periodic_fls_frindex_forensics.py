from pathlib import Path
import hashlib, subprocess, sys
if len(sys.argv)!=2: raise SystemExit('usage: patch_v108_r59l_periodic_fls_frindex_forensics.py <kernel/main.nx>')
p=Path(sys.argv[1]); here=Path(__file__).parent
base=here/'patch_v108_r59j_correct_split_schedule_overlay.py'
subprocess.run([sys.executable,str(base),str(p)],check=True,stdout=subprocess.DEVNULL)
s=p.read_text()
BASE='69168127d829d3b182ab874fef9bbdd1c734ecffca9e5457f94f8d53b012fc54'
actual=hashlib.sha256(s.encode()).hexdigest()
if actual!=BASE: raise SystemExit('r59l exact r59j base mismatch '+actual)

def rep(old,new,label,count=1):
    global s
    n=s.count(old)
    if n!=count: raise SystemExit(f'{label}: {n} expected {count}')
    s=s.replace(old,new,count)

def fn_text(name):
    st=s.index('fn '+name); op=s.index('{',st); d=0
    for i in range(op,len(s)):
        if s[i]=='{': d+=1
        elif s[i]=='}':
            d-=1
            if d==0:return s[st:i+1]
    raise SystemExit('unterminated '+name)

def fnrep(name,new): rep(fn_text(name),new,name)

def label_fn(name,text):
    out=f'fn {name}(surface:u64,x:u64,y:u64,color:u64) -> u64 {{'
    for i,ch in enumerate(text): out+=f' if gui_draw_char_scaled(surface,((x+{i*6})*65536)+y,({ord(ch)}*65536)+1,color)==0 {{ return 0; }}'
    return out+' return 1; }'

# Normalize USBCMD FLS[1:0] to 00 (1024-entry periodic list) only after
# both async/periodic schedules have reported inactive. The code constructs
# exactly 1024 frame entries, so this removes firmware-state ambiguity.
old="    if quiet>=4000000 { unsafe { volatile_write64(xhci_state+4056,17); } return 17; }\n    zero_page(frame); zero_page(dma);"
new="    if quiet>=4000000 { unsafe { volatile_write64(xhci_state+4056,17); } return 17; }\n    cmd=volatile_read32(op); cmd=clear_flag(cmd,4); cmd=clear_flag(cmd,8); unsafe { volatile_write32(op,cmd); }\n    zero_page(frame); zero_page(dma);"
rep(old,new,'FLS normalize')

fnrep('v140_text_wifi_v140',label_fn('v140_text_wifi_v140','R5L F I L Q N A P'))
oldrow="v140_text_wifi_v140(surface,px+10,py+748,white); if xhci!=0 { let rr=volatile_read64(xhci+4080); let dm=volatile_read64(xhci+4040); var sm:u64=0; var cm:u64=0; var ot:u64=0; if dm!=0 { let qi=volatile_read32(dm+8); sm=qi%256; cm=(qi/256)%256; ot=volatile_read32(dm+24); } let oi=volatile_read64(xhci+3976); let ox=(rr/2)%2; let oe=(rr/4)%32; v108_draw_small_u64(surface,((px+112)*65536)+(py+748),volatile_read64(xhci+4056)+(oi*0)+(ox*0)+(oe*0)+(sm*0)+(cm*0),green); v108_draw_small_u64(surface,((px+150)*65536)+(py+748),volatile_read64(xhci+4064),amber); v108_draw_small_u64(surface,((px+188)*65536)+(py+748),(ot/128)%2,white); v108_draw_small_u64(surface,((px+226)*65536)+(py+748),(ot/2)%2,green); v108_draw_small_u64(surface,((px+264)*65536)+(py+748),(ot/4)%32+(volatile_read64(xhci+3984)*0),amber); v108_draw_small_u64(surface,((px+306)*65536)+(py+748),(ot/65536)%32768,white); v108_draw_small_u64(surface,((px+350)*65536)+(py+748),(ot/2147483648)%2,white); }"
newrow="v140_text_wifi_v140(surface,px+10,py+748,white); if xhci!=0 { let dm=volatile_read64(xhci+4040); let frame=volatile_read64(xhci+4048); let rr=volatile_read64(xhci+4080); let oi=volatile_read64(xhci+3976); let compat_stage=volatile_read64(xhci+4056); let compat_q=volatile_read64(xhci+4072); var sm:u64=0; var cm:u64=0; var fls:u64=3; var fi:u64=0; var linked:u64=0; var qmatch:u64=0; var active:u64=0; var pss:u64=0; var ot:u64=0; if dm!=0 && frame!=0 { let qi=volatile_read32(dm+8); sm=qi%256; cm=(qi/256)%256; ot=volatile_read32(dm+24); let eb=v108_pci_nth_ehci_v121(1); if eb!=0 { let bb=pci_bar_base(eb,0); if bb!=0 { let cl=volatile_read8(bb); if cl>=16 && cl<=128 { let op=bb+cl; let c=volatile_read32(op); fls=(c/4)%4; let fri59l=volatile_read32(op+12)%16384; fi=(fri59l/8)%1024; pss=(volatile_read32(op+4)/16384)%2; let qlo=dm%4294967296; let tdlo=(dm+128)%4294967296; if volatile_read32(frame+(fi*4))==qlo+2 { linked=1; } if volatile_read32(dm+12)==tdlo { qmatch=1; } active=(ot/128)%2; } } } } let compat=(rr/2)%2+(rr/4)%32+(ot/2)%2+(ot/4)%32+(ot/65536)%32768+(ot/2147483648)%2+compat_stage+compat_q+oi+sm+cm; v108_draw_small_u64(surface,((px+112)*65536)+(py+748),fls+(compat*0),green); v108_draw_small_u64(surface,((px+150)*65536)+(py+748),fi,amber); v108_draw_small_u64(surface,((px+188)*65536)+(py+748),linked,white); v108_draw_small_u64(surface,((px+226)*65536)+(py+748),qmatch,green); v108_draw_small_u64(surface,((px+264)*65536)+(py+748),volatile_read64(xhci+4064),amber); v108_draw_small_u64(surface,((px+306)*65536)+(py+748),active,white); v108_draw_small_u64(surface,((px+350)*65536)+(py+748),pss,white); }"
rep(oldrow,newrow,'telemetry row')

# Scope/invariant checks
r=s[s.index('fn v159_ehci_mouse_periodic_arm'):s.index('fn v135_hid_control_fallback_prepare')]
for q in ['let info1=2+(ep*256)+(mmps*65536)','let info2=1090591745','let token=527744','volatile_write32(op+20,flo)','cmd=set_flag(cmd,16)','cmd=clear_flag(cmd,4)','cmd=clear_flag(cmd,8)']:
    if q not in r: raise SystemExit('missing '+q)
for q in ['fls=(c/4)%4','fi=(fri59l/8)%1024','volatile_read32(frame+(fi*4))==qlo+2','volatile_read32(dm+12)==tdlo','(ot/128)%2','(volatile_read32(op+4)/16384)%2','volatile_read64(xhci+3976)','sm=qi%256','cm=(qi/256)%256']:
    if q not in s: raise SystemExit('telemetry missing '+q)
for bad in ('write(10)','nvme_submit_write','ahci_write','fat_write','block_write','input_push('):
    if bad in r.lower(): raise SystemExit('scope exceeds '+bad)
assert s.count('{')==s.count('}')
out=hashlib.sha256(s.encode()).hexdigest()
EXPECTED='2c4734c29577a4710b27577ec2dfa33dcf6f117a25e21607dff5ee6b9632a6de'
if out!=EXPECTED: raise SystemExit('r59l output sha mismatch '+out)
p.write_text(s)
print(out)
