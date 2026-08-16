#!/usr/bin/env python3
from pathlib import Path
import sys

if len(sys.argv) != 2:
    raise SystemExit('usage: instrument_full_product_fapp_verifier.py PATH_TO_frames_boot.c')

p = Path(sys.argv[1])
s = p.read_text(errors='replace')
needle = 'fapp_extract_verify('
pos = s.find(needle)
if pos < 0:
    raise SystemExit('fapp_extract_verify not found')

# Find the function body that owns the first fapp_extract_verify definition.
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

# Idempotent: do not double-instrument an already patched source.
if '[FAPP-DIAG]' in body:
    print('fapp_extract_verify already instrumented')
    raise SystemExit(0)

# Give each fail-closed branch a unique serial marker. This preserves every
# original predicate and return value while making the exact verifier rejection
# visible in headless QEMU and physical-test evidence.
parts = body.split('return 0;')
out = parts[0]
for idx, tail in enumerate(parts[1:], 1):
    out += f'print16(L"[FAPP-DIAG] fail-{idx:02d}\\r\\n"); return 0;' + tail

# Mark successful verification too, if the verifier has an explicit success return.
out = out.replace('return 1;', 'print16(L"[FAPP-DIAG] verify-ok\\r\\n"); return 1;')

s = s[:brace+1] + '\n    print16(L"[FAPP-DIAG] verifier-enter\\r\\n");' + out + s[end:]
p.write_text(s)
print(f'instrumented fapp_extract_verify fail_sites={len(parts)-1}')
if len(parts) <= 1:
    raise SystemExit('no return 0 verifier fail sites found')
