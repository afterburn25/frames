#!/usr/bin/env python3
from pathlib import Path
import sys, hashlib

if len(sys.argv)!=2:
    raise SystemExit('usage: patch_v108_r25b_bracefix.py <kernel/main.nx>')

target=Path(sys.argv[1])
base=Path(__file__).with_name('patch_v108_r25_flightrec_usbwrite.py')
src=base.read_text()
needle="if s.count('{')!=s.count('}'): raise SystemExit(f'brace imbalance {s.count(\"{\")} {s.count(\"}\")}')\np.write_text(s)\nprint(hashlib.sha256(s.encode()).hexdigest())"
replacement="p.write_text(s)\nprint(hashlib.sha256(s.encode()).hexdigest())"
if src.count(needle)!=1:
    raise SystemExit('r25 base final-check anchor mismatch')
src=src.replace(needle,replacement,1)
old_argv=sys.argv[:]
try:
    sys.argv=[str(base),str(target)]
    ns={'__name__':'__main__','__file__':str(base)}
    exec(compile(src,str(base),'exec'),ns,ns)
finally:
    sys.argv=old_argv

s=target.read_text()
opens=s.count('{'); closes=s.count('}')
if closes!=opens+1:
    raise SystemExit(f'unexpected generated brace delta open={opens} close={closes}')

bal=0; extra=-1
for i,ch in enumerate(s):
    if ch=='{': bal+=1
    elif ch=='}':
        bal-=1
        if bal<0:
            extra=i
            break
if extra<0:
    raise SystemExit('one extra brace exists but no top-level negative transition found')
fixed=s[:extra]+s[extra+1:]
if fixed.count('{')!=fixed.count('}'):
    raise SystemExit('brace correction did not balance kernel')
expected='068ed900f8942ecec797e2f5fa5e79f95fce51ef817b2e3336af05d643528674'
actual=hashlib.sha256(fixed.encode()).hexdigest()
if actual!=expected:
    lo=max(0,extra-120); hi=min(len(s),extra+120)
    raise SystemExit(f'brace correction identity mismatch actual={actual} extra={extra} context={s[lo:hi]!r}')
target.write_text(fixed)
print(actual)
