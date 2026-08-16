#!/usr/bin/env python3
from pathlib import Path
import re, subprocess, sys, os

if len(sys.argv) != 3:
    raise SystemExit('usage: wire_v72_gui_fapp_into_esp.py SOURCE_ROOT ESP_IMAGE')
root = Path(sys.argv[1])
esp = Path(sys.argv[2])
loader = root / 'boot/uefi/frames_boot.c'
s = loader.read_text(errors='replace')

# Discover the exact optional FAPP path requested by this loader.  Do not
# assume a particular escaping style: inspect every wide-string literal.
literals = re.findall(r'L"([^"\n]+)"', s)
paths = [x for x in literals if '.fapp' in x.lower()]
if not paths:
    # Preserve useful evidence if this revision constructs the name indirectly.
    nearby = [line for line in s.splitlines() if 'hello_fapp' in line.lower() or 'fapp' in line.lower()]
    print('FAPP-related loader source:')
    for line in nearby:
        print(line)
    raise SystemExit('no literal loader .fapp path found')
expected = paths[0].replace('\\\\','\\')
print(f'loader_fapp_path={expected}')


def fapps():
    out=[]
    for p in root.rglob('*'):
        if p.is_file() and p.suffix.lower()=='.fapp' and p.stat().st_size>0:
            out.append(p)
    return out

# v72's ordinary kernel/System build does not necessarily package the sample
# application.  If no FAPP exists, discover the source tree's own FAPP builder
# and invoke the most specific HelloFrames/package target we can prove exists.
candidates=fapps()
if not candidates:
    print('no prebuilt FAPP; discovering supplied package tooling')
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
            if 'fapp' in hay:
                tool_hits.append(p)
                print(f'fapp_tool_hit={p.relative_to(root)}')

    # Prefer executable/package scripts explicitly named for FAPP.
    scripts=[]
    for p in tool_hits:
        n=p.name.lower()
        if p.suffix.lower() in ('.py','.sh') and ('fapp' in n or 'package' in n or 'pack' in n):
            scripts.append(p)

    # Find likely HelloFrames application source/manifest.
    hello=[]
    for p in root.rglob('*'):
        if p.is_file() and ('helloframes' in str(p).lower() or ('hello' in p.name.lower() and 'example' not in str(p).lower())):
            hello.append(p)
            print(f'hello_source_hit={p.relative_to(root)}')

    # Try only self-describing, supplied builders.  Capture --help first and
    # derive conservative invocations rather than inventing a package format.
    build_dir=root/'build'
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
        # Common source-provided CLI shapes; only attempted when help text
        # advertises matching concepts.
        if hello and ('output' in low or '-o' in low):
            src=hello[0]
            out=build_dir/'HelloFrames.fapp'
            attempts += [cmd0+[str(src),'-o',str(out)], cmd0+['--input',str(src),'--output',str(out)]]
        if 'helloframes' in low:
            attempts += [cmd0+['HelloFrames'], cmd0+['helloframes']]
        for cmd in attempts:
            try:
                print('trying='+' '.join(cmd))
                r=subprocess.run(cmd,cwd=root,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=60)
                print(r.stdout[:8000])
                print(f'exit={r.returncode}')
            except Exception as e:
                print(f'attempt_failed={e}')
            candidates=fapps()
            if candidates:
                break
        if candidates:
            break

if not candidates:
    raise SystemExit('no .fapp package could be produced by supplied v72 tooling')

def score(p: Path):
    n=p.name.lower(); path=str(p).lower()
    return (('helloframes' in n)*100 + ('hello' in n)*50 + ('build' in path)*10, p.stat().st_size)

candidate=sorted(candidates,key=score,reverse=True)[0]
print(f'candidate_fapp={candidate}')
print(f'candidate_size={candidate.stat().st_size}')

# Translate UEFI path (\\Frames\\Foo.fapp) to mtools ::/Frames/Foo.fapp.
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
