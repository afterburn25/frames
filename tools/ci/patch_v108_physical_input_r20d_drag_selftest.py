from pathlib import Path
import hashlib,sys
p=Path(sys.argv[1]); raw=p.read_bytes(); actual=hashlib.sha256(raw).hexdigest(); expected='17cf352e42806cbe2246cca92fc09993060f4f159c72e3785fbf4177b98ba453'
if actual!=expected: raise SystemExit(f'unexpected r20b source hash {actual}')
s=raw.decode()

def fn_span(text,name):
    st=text.index(name); op=text.index('{',st); d=0
    for j in range(op,len(text)):
        if text[j]=='{': d+=1
        elif text[j]=='}':
            d-=1
            if d==0:return st,j+1
    raise RuntimeError(name)

def marker(name,text):
    return 'fn '+name+'() -> void { '+' '.join(f'serial_putc({ord(c)});' for c in text+'\n')+' return; }\n'

anchor=s.index('fn desktop_input_runtime')
extra=marker('serial_marker_v108_drag_policy_selftest_ok_v120','FRAMES_V108_DRAG_POLICY_SELFTEST_OK')+'''fn v108_drag_policy_selftest_v120(state:u64,wm:u64,surface:u64) -> u64 {
    if state==0 || wm==0 || surface==0 { return 0; }
    let sx=volatile_read64(state+8); let sy=volatile_read64(state+16); let sb=volatile_read64(state+96); let swx=volatile_read64(state+160); let swy=volatile_read64(state+168); let sdrag=volatile_read64(state+176); let spx=volatile_read64(state+184); let spy=volatile_read64(state+192); let scount=volatile_read64(state+200); let smenu=volatile_read64(state+128); let spend=volatile_read64(state+392); let scx=volatile_read64(state+400); let scy=volatile_read64(state+408); let stime=volatile_read64(state+416); let soffx=volatile_read64(state+424); let soffy=volatile_read64(state+432); let sarms=volatile_read64(state+448); let sconfirm=volatile_read64(state+464);
    unsafe { volatile_write64(state+8,swx+20); volatile_write64(state+16,swy+18); volatile_write64(state+96,0); volatile_write64(state+128,0); volatile_write64(state+176,0); volatile_write64(state+392,0); volatile_write64(state+464,0); }
    if gui_input_buttons(state,wm,1,surface)==0 { return 0; }
    if volatile_read64(state+392)!=1 || volatile_read64(state+176)!=0 { return 0; }
    if gui_input_pointer_move(state,wm,10,1)==0 { return 0; }
    if volatile_read64(state+176)!=0 { return 0; }
    if gui_input_pointer_move(state,wm,6,2)==0 { return 0; }
    if volatile_read64(state+176)!=0 { return 0; }
    if gui_input_pointer_move(state,wm,2,1)==0 { return 0; }
    if volatile_read64(state+176)!=1 || volatile_read64(state+128)!=0 { return 0; }
    if gui_input_buttons(state,wm,0,surface)==0 || volatile_read64(state+176)!=0 || volatile_read64(state+392)!=0 { return 0; }
    unsafe { volatile_write64(state+8,sx); volatile_write64(state+16,sy); volatile_write64(state+96,sb); volatile_write64(state+160,swx); volatile_write64(state+168,swy); volatile_write64(state+176,sdrag); volatile_write64(state+184,spx); volatile_write64(state+192,spy); volatile_write64(state+200,scount); volatile_write64(state+128,smenu); volatile_write64(state+392,spend); volatile_write64(state+400,scx); volatile_write64(state+408,scy); volatile_write64(state+416,stime); volatile_write64(state+424,soffx); volatile_write64(state+432,soffy); volatile_write64(state+448,sarms); volatile_write64(state+464,sconfirm); }
    serial_marker_v108_drag_policy_selftest_ok_v120(); return 1;
}\n'''
s=s[:anchor]+extra+s[anchor:]
a,b=fn_span(s,'fn desktop_input_runtime'); f=s[a:b]
needle='if v108_input_backend_prepare(input_state)==0 { return 0; }'
if needle not in f: raise SystemExit('backend prepare anchor missing')
f=f.replace(needle,needle+'\n    if v108_drag_policy_selftest_v120(state,wm,surface)==0 { return 0; }',1)
s=s[:a]+f+s[b:]
p.write_text(s)
print(hashlib.sha256(p.read_bytes()).hexdigest())
