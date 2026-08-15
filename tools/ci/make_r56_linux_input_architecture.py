#!/usr/bin/env python3
from pathlib import Path
import subprocess, sys

p=Path(sys.argv[1])
subprocess.check_call([sys.executable, str(Path(__file__).with_name('make_r55_physical_protocol_probe.py')), str(p)])
s=p.read_text()

def rep(old,new,label):
    global s
    n=s.count(old)
    if n!=1:
        raise SystemExit(f'{label}: expected 1 site, found {n}')
    s=s.replace(old,new)

rep('pointer_diag_draw_tag4(surface,(78*65536)+18,82+(53*256)+(53*65536)+(32*16777216),green);    // R55',
    'pointer_diag_draw_tag4(surface,(78*65536)+18,82+(53*256)+(54*65536)+(32*16777216),green);    // R56',
    'title')

rep('var ucfg:u64=0; var uprt:u64=0; var uarm:u64=0; var urpt:u64=0; var ulen:u64=0; var u0b:u64=0; var u1b:u64=0;',
    'var ucfg:u64=0; var uprt:u64=0; var uarm:u64=0; var urpt:u64=0; var ulen:u64=0; var u0b:u64=0; var u1b:u64=0; var xini:u64=0; var xbas:u64=0; var xopb:u64=0;',
    'controller locals')
rep('if r53b_xhci!=0 { ucfg=volatile_read64(r53b_xhci+416); uprt=volatile_read64(r53b_xhci+336); uarm=volatile_read64(r53b_xhci+808); urpt=volatile_read64(r53b_xhci+816); ulen=volatile_read64(r53b_xhci+440); u0b=volatile_read64(r53b_xhci+456); u1b=volatile_read64(r53b_xhci+464); }',
    'if r53b_xhci!=0 { ucfg=volatile_read64(r53b_xhci+416); uprt=volatile_read64(r53b_xhci+336); uarm=volatile_read64(r53b_xhci+808); urpt=volatile_read64(r53b_xhci+816); ulen=volatile_read64(r53b_xhci+440); u0b=volatile_read64(r53b_xhci+456); u1b=volatile_read64(r53b_xhci+464); xini=volatile_read64(r53b_xhci+56); xbas=volatile_read64(r53b_xhci); xopb=volatile_read64(r53b_xhci+8); }',
    'controller state reads')

rep('pointer_diag_row(surface,(330*65536)+134,1195787093,ucfg);                                                                  // UCFG',
    'pointer_diag_row(surface,(330*65536)+134,1229867096,xini);                                                                 // XINI',
    'init state row')
rep('pointer_diag_row(surface,(330*65536)+146,1414680661,uprt);                                                                  // UPRT',
    'pointer_diag_row(surface,(330*65536)+146,1396785752,xbas);                                                                 // XBAS',
    'controller base row')
rep('pointer_diag_row(surface,(330*65536)+182,1313164373,ulen);                                                                  // ULEN',
    'pointer_diag_row(surface,(330*65536)+182,542134360,xopb);                                                                  // XOP ',
    'operational base row')

p.write_text(s)
