#!/usr/bin/env python3
from pathlib import Path
import hashlib, subprocess, sys

if len(sys.argv) != 2:
    raise SystemExit('usage: patch_v108_r59o_periodic_endpoint_speed.py <kernel/main.nx>')

p = Path(sys.argv[1])
here = Path(__file__).parent
base = here / 'patch_v108_r59n3_bounded_periodic_window.py'
subprocess.run([sys.executable, str(base), str(p)], check=True, stdout=subprocess.DEVNULL)
s = p.read_text()

BASE = '24df5ece713f2eac409899296ccc34f8843332194e28e981d771bd01ad1db4f4'
actual = hashlib.sha256(s.encode()).hexdigest()
if actual != BASE:
    raise SystemExit('r59o exact r59n3 bounded base mismatch ' + actual)

def fn_text(src, name):
    st = src.index('fn ' + name)
    op = src.index('{', st)
    d = 0
    for i in range(op, len(src)):
        if src[i] == '{':
            d += 1
        elif src[i] == '}':
            d -= 1
            if d == 0:
                return src[st:i+1]
    raise RuntimeError(name)

def label_fn(name, text):
    out = f'fn {name}(surface:u64,x:u64,y:u64,color:u64) -> u64 {{'
    for i, ch in enumerate(text):
        out += f' if gui_draw_char_scaled(surface,((x+{i*6})*65536)+y,({ord(ch)}*65536)+1,color)==0 {{ return 0; }}'
    return out + ' return 1; }'

# r57 control transfers correctly encode the downstream child speed in the
# EHCI QH endpoint-characteristics word. r59's periodic QH accidentally
# omitted that speed field and therefore described every FS/LS interrupt
# endpoint as full-speed. Preserve all proven scheduling/TT geometry and add
# only the missing EPS bits (0=FS, 1=LS in the r56/r57 internal speed model).
old_info = 'let info1=2+(ep*256)+(mmps*65536); let info2=1090591745; let token=527744;'
new_info = 'let info1=2+(ep*256)+(speed*4096)+(mmps*65536); let info2=1090591745; let token=527744;'
if s.count(old_info) != 1:
    raise SystemExit('r59o periodic endpoint-speed anchor mismatch ' + str(s.count(old_info)))
s = s.replace(old_info, new_info, 1)

# Make the physical result self-identifying. S is the enumerated child speed
# (0 full-speed, 1 low-speed), followed by the already-proven periodic hit,
# split, active, remaining-byte, completion and schedule-status witnesses.
old_label = fn_text(s, 'v140_text_wifi_v140')
s = s.replace(old_label, label_fn('v140_text_wifi_v140', 'R5O S H X A R N P'), 1)
row_start = s.index('v140_text_wifi_v140(surface,px+10,py+748,white);')
row_end = s.index('\n    return 1;\n}', row_start)
old_row = s[row_start:row_end]
needle = 'v108_draw_small_u64(surface,((px+112)*65536)+(py+748),volatile_read64(xhci+3984)+(compat*0),green); v108_draw_small_u64(surface,((px+150)*65536)+(py+748),xseen,amber); v108_draw_small_u64(surface,((px+188)*65536)+(py+748),trans,white); v108_draw_small_u64(surface,((px+226)*65536)+(py+748),aseen,green); v108_draw_small_u64(surface,((px+264)*65536)+(py+748),minrem,amber); v108_draw_small_u64(surface,((px+306)*65536)+(py+748),volatile_read64(xhci+4064),white); v108_draw_small_u64(surface,((px+350)*65536)+(py+748),pss,white);'
replacement = 'v108_draw_small_u64(surface,((px+112)*65536)+(py+748),volatile_read64(xhci+4024)+(compat*0)+(trans*0),green); v108_draw_small_u64(surface,((px+150)*65536)+(py+748),volatile_read64(xhci+3984),amber); v108_draw_small_u64(surface,((px+188)*65536)+(py+748),xseen,white); v108_draw_small_u64(surface,((px+226)*65536)+(py+748),aseen,green); v108_draw_small_u64(surface,((px+264)*65536)+(py+748),minrem,amber); v108_draw_small_u64(surface,((px+306)*65536)+(py+748),volatile_read64(xhci+4064),white); v108_draw_small_u64(surface,((px+350)*65536)+(py+748),pss,white);'
if old_row.count(needle) != 1:
    raise SystemExit('r59o telemetry row anchor mismatch ' + str(old_row.count(needle)))
s = s[:row_start] + old_row.replace(needle, replacement, 1) + s[row_end:]

arm = s[s.index('fn v159_ehci_mouse_periodic_arm'):s.index('fn v159_ehci_mouse_periodic_tick')]
tick = s[s.index('fn v159_ehci_mouse_periodic_tick'):s.index('fn v135_hid_control_fallback_prepare')]
for q in (
    'let info1=2+(ep*256)+(speed*4096)+(mmps*65536)',
    'let info2=1090591745',
    'while transitions<32 && spins<500000',
    'volatile_write64(xhci_state+3984,hit)',
    'volatile_write64(xhci_state+3992,packed)',
    'volatile_read64(xhci+4024)',
    'volatile_read64(xhci+4064)',
):
    if q not in s:
        raise SystemExit('r59o required endpoint-speed/forensic witness missing ' + q)
if 'let info1=2+(ep*256)+(mmps*65536)' in arm:
    raise SystemExit('r59o old full-speed-only periodic QH encoding remains')
for bad in ('write(10)', 'nvme_submit_write', 'ahci_write', 'fat_write', 'block_write', 'input_push('):
    if bad in (arm + tick).lower():
        raise SystemExit('r59o exceeds diagnostic/read-only scope ' + bad)
if s.count('{') != s.count('}'):
    raise SystemExit('r59o brace mismatch')

out = hashlib.sha256(s.encode()).hexdigest()
EXPECTED = 'b33103bcbe4ad84ded6da2e1f4f85c9437fc2d1b0858ec269a3f505661615972'
if out != EXPECTED:
    raise SystemExit('r59o output sha mismatch ' + out)
p.write_text(s)
print(out)
