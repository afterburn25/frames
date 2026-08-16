#!/usr/bin/env python3
from pathlib import Path
import re, subprocess, sys

if len(sys.argv) != 3:
    raise SystemExit('usage: wire_v72_gui_fapp_into_esp.py SOURCE_ROOT ESP_IMAGE')
root = Path(sys.argv[1])
esp = Path(sys.argv[2])
loader = root / 'boot/uefi/frames_boot.c'
s = loader.read_text(errors='replace')

# Frames calls the package format FAPP, but this v72 loader uses the on-disk
# extension .FAP (HELLO.FAP). Discover the exact wide-string path instead of
# assuming either .fap or the conceptual .fapp spelling.
literals = re.findall(r'L"([^"\n]+)"', s)
paths = [x for x in literals if x.lower().endswith(('.fap', '.fapp'))]
if not paths:
    nearby = [line for line in s.splitlines() if 'hello_fapp' in line.lower() or 'fapp' in line.lower() or '.fap' in line.lower()]
    print('FAPP-related loader source:')
    for line in nearby:
        print(line)
    raise SystemExit('no literal loader FAP/FAPP path found')
expected = paths[0].replace('\\\\','\\')
print(f'loader_fapp_path={expected}')


def packages():
    out=[]
    for p in root.rglob('*'):
        if p.is_file() and p.suffix.lower() in ('.fap', '.fapp') and p.stat().st_size>0:
            out.append(p)
    return out

# v72's ordinary kernel/System build does not necessarily package the sample
# application. If no package exists, discover the source tree's own FAPP
# builder and invoke only CLI forms supported by its help text.
candidates=packages()
if not candidates:
    print('no prebuilt FAP/FAPP; discovering supplied package tooling')
    tool_hits=[]
    for base in (root/'tools', root/'sdk', root/'apps'):
        if not base.exists():
            continue
        for p in base.rglob('*'):
            if not p.is_file() or p.stat().st_size > 2_000_000:
                continue
            try:
                text=p.read_text(errors='ignore')
            except Exception:
                continue
            hay=(p.name+'\n'+text).lower()
            if 'fapp' in hay or '.fap' in hay:
                tool_hits.append(p)
                print(f'fapp_tool_hit={p.relative_to(root)}')

    scripts=[]
    for p in tool_hits:
        n=p.name.lower()
        if p.suffix.lower() in ('.py','.sh') and ('fapp' in n or 'fap' in n or 'package' in n or 'pack' in n):
            scripts.append(p)

    hello=[]
    for p in root.rglob('*'):
        if p.is_file() and ('helloframes' in str(p).lower() or ('hello' in p.name.lower() and 'example' not in str(p).lower())):
            hello.append(p)
            print(f'hello_source_hit={p.relative_to(root)}')

    build_dir=root/'build'
    build_dir.mkdir(exist_ok=True)
    for tool in scripts:
        cmd0=['python3',str(tool)] if tool.suffix.lower()=='.py' else ['bash',str(tool)]
        try:
            help_out=subprocess.run(cmd0+['--help'],cwd=root,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=20).stdout
        except Exception as e:
            print(f'help_failed={tool.relative_to(root)}:{e}')
            continue
        print(f'help_begin={tool.relative_to(root)}')
        print(help_out[:6000])
        print('help_end')
        low=help_out.lower()
        attempts=[]
        if hello and ('output' in low or '-o' in low):
            src=hello[0]
            out=build_dir/'HELLO.FAP'
            attempts += [cmd0+[str(src),'-o',str(out)], cmd0+['--input',str(src),'--output',str(out)]]
        if 'helloframes' in low or 'hello' in low:
            attempts += [cmd0+['HelloFrames'], cmd0+['helloframes']]
        for cmd in attempts:
            try:
                print('trying='+' '.join(cmd))
                r=subprocess.run(cmd,cwd=root,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=60)
                print(r.stdout[:8000])
                print(f'exit={r.returncode}')
            except Exception as e:
                print(f'attempt_failed={e}')
            candidates=packages()
            if candidates:
                break
        if candidates:
            break

if not candidates:
    raise SystemExit('no .FAP/.FAPP package could be produced by supplied v72 tooling')

def score(p: Path):
    n=p.name.lower(); path=str(p).lower()
    return (('helloframes' in n)*100 + (n.startswith('hello.'))*90 + ('hello' in n)*50 + ('build' in path)*10, p.stat().st_size)

candidate=sorted(candidates,key=score,reverse=True)[0]
print(f'candidate_fapp={candidate}')
print(f'candidate_size={candidate.stat().st_size}')

uefi=expected.replace('\\','/').lstrip('/')
parts=[x for x in uefi.split('/') if x]
if len(parts)<2:
    raise SystemExit(f'unexpected loader FAPP path: {expected}')
cur='::'
for d in parts[:-1]:
    cur += '/' + d
    subprocess.run(['mmd','-i',str(esp),cur],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
dest='::/'+'/'.join(parts)
subprocess.check_call(['mcopy','-o','-i',str(esp),str(candidate),dest])
subprocess.check_call(['mdir','-i',str(esp),'::/'+'/'.join(parts[:-1])])
print(f'wired_fapp={dest}')
