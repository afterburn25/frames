#!/usr/bin/env python3
from pathlib import Path
import re, sys

if len(sys.argv) != 2:
    raise SystemExit('usage: instrument_full_product_fapp_verifier.py PATH_TO_frames_boot.c')

p = Path(sys.argv[1])
s = p.read_text(errors='replace')
needle = 'fapp_extract_verify('
pos = s.find(needle)
if pos < 0:
    raise SystemExit('fapp_extract_verify not found')

brace = s.find('{', pos)
if brace < 0:
    raise SystemExit('fapp_extract_verify opening brace not found')

def find_body_end(text, start):
    depth = 0
    i = start
    quote = None
    line_comment = False
    block_comment = False
    esc = False
    while i < len(text):
        c = text[i]
        n = text[i+1] if i+1 < len(text) else ''
        if line_comment:
            if c == '\n': line_comment = False
            i += 1; continue
        if block_comment:
            if c == '*' and n == '/': block_comment = False; i += 2; continue
            i += 1; continue
        if quote:
            if esc: esc = False
            elif c == '\\': esc = True
            elif c == quote: quote = None
            i += 1; continue
        if c == '/' and n == '/': line_comment = True; i += 2; continue
        if c == '/' and n == '*': block_comment = True; i += 2; continue
        if c in ('\"', "'"): quote = c; i += 1; continue
        if c == '{': depth += 1
        elif c == '}':
            depth -= 1
            if depth == 0: return i
        i += 1
    return -1

end = find_body_end(s, brace)
if end < 0:
    raise SystemExit('fapp_extract_verify closing brace not found')
body = s[brace+1:end]

if '[FAPP-DIAG]' in body:
    print('fapp_extract_verify already instrumented')
    raise SystemExit(0)

# Preserve control flow exactly. The source uses compact one-line forms such as
#   if(condition)return 0;
# so inserting text before `return 0` would make that return unconditional.
# Instead, wrap each fail branch in braces and keep the return inside the if.
pat = re.compile(r'if\s*\((.*?)\)\s*return\s+0\s*;', re.S)
count = 0

def repl(m):
    global count
    count += 1
    cond = m.group(1)
    return f'if({cond}){{print16(L"[FAPP-DIAG] fail-{count:02d}\\r\\n"); return 0;}}'

new_body = pat.sub(repl, body)
if count == 0:
    raise SystemExit('no conditional return 0 verifier fail sites found')

# Success marker; use a callable replacement so Python regex replacement-string
# escape processing cannot turn the intended C "\\r\\n" into literal CR/LF.
success_pat = re.compile(r'(?<![A-Za-z0-9_])return\s+1\s*;')
new_body, success_count = success_pat.subn(
    lambda _m: 'print16(L"[FAPP-DIAG] verify-ok\\r\\n"); return 1;',
    new_body,
    count=1,
)
if success_count != 1:
    raise SystemExit('expected one explicit verifier success return')

s = s[:brace+1] + '\n    print16(L"[FAPP-DIAG] verifier-enter\\r\\n");' + new_body + s[end:]
p.write_text(s)
print(f'instrumented fapp_extract_verify fail_sites={count} semantics=preserved escapes=preserved')
