#!/usr/bin/env python3
from pathlib import Path
import hashlib, subprocess, sys
if len(sys.argv)!=2: raise SystemExit('usage: patch_v108_r59d_dma_ledger_capacity.py <kernel/main.nx>')
p=Path(sys.argv[1]); here=Path(__file__).parent
base=here/'patch_v108_r59c_ehci_periodic_reserved_fallback.py'
subprocess.run([sys.executable,str(base),str(p)],check=True,stdout=subprocess.DEVNULL)
s=p.read_text()
BASE='e1218ffe017749b252b6e939534f9d191bccbc68433f6a478f8f19c1506cb66c'
actual=hashlib.sha256(s.encode()).hexdigest()
if actual!=BASE: raise SystemExit('r59d exact r59c base mismatch '+actual)

def rep(old,new,label,count=1):
    global s
    n=s.count(old)
    if n!=count: raise SystemExit(f'r59d {label}: {n} expected {count}')
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

rep('fn dma_ledger_init(state:u64) -> u64 { if state==0 { return 0; } zero_page(state); unsafe { volatile_write64(state,1); volatile_write64(state+8,0); volatile_write64(state+16,64); } return 1; }',
    'fn dma_ledger_init(state:u64) -> u64 { if state==0 { return 0; } zero_page(state); unsafe { volatile_write64(state,1); volatile_write64(state+8,0); volatile_write64(state+16,80); } return 1; }','ledger capacity init')
rep('fn dma_record(state:u64,page:u64,owner:u64) -> u64 { if state==0 || page==0 || owner==0 || volatile_read64(state)!=1 { return 0; } let count=volatile_read64(state+8); if count>=64 { return 0; } let rec=state+64+(count*48); unsafe { volatile_write64(rec,page); volatile_write64(rec+8,4096); volatile_write64(rec+16,owner); volatile_write64(rec+24,1); volatile_write64(rec+32,read_tsc()); volatile_write64(rec+40,0); volatile_write64(state+8,count+1); } return 1; }',
    'fn dma_record(state:u64,page:u64,owner:u64) -> u64 { if state==0 || page==0 || owner==0 || volatile_read64(state)!=1 { return 0; } let count=volatile_read64(state+8); let limit=volatile_read64(state+16); if limit==0 || limit>80 || count>=limit { return 0; } let rec=state+64+(count*48); unsafe { volatile_write64(rec,page); volatile_write64(rec+8,4096); volatile_write64(rec+16,owner); volatile_write64(rec+24,1); volatile_write64(rec+32,read_tsc()); volatile_write64(rec+40,0); volatile_write64(state+8,count+1); } return 1; }','ledger bounded record')
rep('fn dma_ledger_audit(state:u64) -> u64 { if state==0 || volatile_read64(state)!=1 { return 0; } let count=volatile_read64(state+8); if count>64 { return 0; } var i:u64=0; while i<count { let rec=state+64+(i*48); if volatile_read64(rec)==0 || volatile_read64(rec+8)!=4096 || volatile_read64(rec+16)==0 { return 0; } i=i+1; } unsafe { volatile_write64(state+24,1); } serial_marker_dma_ledger_ok(); return 1; }',
    'fn dma_ledger_audit(state:u64) -> u64 { if state==0 || volatile_read64(state)!=1 { return 0; } let limit=volatile_read64(state+16); let count=volatile_read64(state+8); if limit==0 || limit>80 || count>limit { return 0; } var i:u64=0; while i<count { let rec=state+64+(i*48); if volatile_read64(rec)==0 || volatile_read64(rec+8)!=4096 || volatile_read64(rec+16)==0 { return 0; } i=i+1; } unsafe { volatile_write64(state+24,1); } serial_marker_dma_ledger_ok(); return 1; }','ledger bounded audit')
rep('    var d:u64=0;\n    while d<64 {\n        if dma_record(ledger,first+(d*4096),99)==0 {',
    '    var d:u64=0;\n    while d<80 {\n        if dma_record(ledger,first+((d%64)*4096),99)==0 {','ledger stress fill')
rep('    if dma_record(ledger,first+(64*4096),99)!=0 || volatile_read64(ledger+8)!=64 || dma_ledger_audit(ledger)==0 {',
    '    if dma_record(ledger,first,99)!=0 || volatile_read64(ledger+8)!=80 || dma_ledger_audit(ledger)==0 {','ledger stress ceiling')
fnrep('v140_text_wifi_v140',label_fn('v140_text_wifi_v140','R5D S N C B X Y W'))

for q in ['volatile_write64(state+16,80)','limit>80','count>=limit','count>limit','while d<80','volatile_read64(ledger+8)!=80','v159_ehci_mouse_periodic_tick']:
    if q not in s: raise SystemExit('r59d model missing '+q)
if 'state+64+(count*48)' not in s: raise SystemExit('r59d ledger record layout lost')
# 64-byte header + 80 records * 48 bytes = 3904, remains within one 4096-byte page.
if 64+(80*48)>4096: raise SystemExit('r59d ledger capacity overflows page')
for bad in ('write(10)','nvme_submit_write','ahci_write','fat_write','block_write','input_push('):
    section=s[s.index('fn v159_ehci_mouse_periodic_arm'):s.index('fn v135_hid_control_fallback_prepare')].lower()
    if bad in section: raise SystemExit('r59d exceeds raw diagnostic scope '+bad)
if s.count('{')!=s.count('}'): raise SystemExit('r59d brace mismatch')
out=hashlib.sha256(s.encode()).hexdigest()
EXPECTED='0b66bdc0bc1733985f835b86d5ed7862638dea7af682aec703e224b6b3d34f3d'
if out!=EXPECTED: raise SystemExit('r59d output sha mismatch '+out)
p.write_text(s)
print(out)
