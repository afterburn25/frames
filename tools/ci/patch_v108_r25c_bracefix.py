#!/usr/bin/env python3
from pathlib import Path

base=Path(__file__).with_name('patch_v108_r25b_bracefix.py')
s=base.read_text()
old="expected='068ed900f8942ecec797e2f5fa5e79f95fce51ef817b2e3336af05d643528674'"
new="expected='9224366a0d53bab0815d8c04f17017fc20858dc2a196f41cf159bf85ac24f395'"
if s.count(old)!=1:
    raise SystemExit(f'r25c expected-SHA anchor mismatch: {s.count(old)}')
s=s.replace(old,new,1)
ns={'__name__':'__main__','__file__':str(base)}
exec(compile(s,str(base),'exec'),ns,ns)
