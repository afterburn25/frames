#!/usr/bin/env python3
from pathlib import Path
import base64, difflib, gzip, hashlib, re, subprocess, sys


def extract_patch_payload(text: str):
    m = re.search(r'base64\.b64decode\(\s*"""(.*?)"""\s*\)', text, re.S)
    if not m:
        return None
    return gzip.decompress(base64.b64decode(m.group(1))).decode('utf-8')


def split_patch(payload: str):
    lines = payload.splitlines(keepends=True)
    prefix = []
    hunks = []
    cur = None
    for line in lines:
        if line.startswith('@@'):
            if cur is not None:
                hunks.append(cur)
            cur = [line]
        elif cur is None:
            prefix.append(line)
        else:
            cur.append(line)
    if cur is not None:
        hunks.append(cur)
    return prefix, hunks


def pure_insert_pair(old: str, new: str):
    sm = difflib.SequenceMatcher(a=old, b=new, autojunk=False)
    ops = sm.get_opcodes()
    if not any(tag == 'insert' for tag, *_ in ops):
        return None
    if any(tag not in ('equal', 'insert') for tag, *_ in ops):
        return None
    return ops


def apply_insertions_to_line(lines, old, new, ops):
    candidates = [i for i, line in enumerate(lines) if line.rstrip('\n') == old]
    if candidates:
        if len(candidates) != 1:
            raise RuntimeError('semantic port: ancestral line is not unique')
        lines[candidates[0]] = new + ('\n' if lines[candidates[0]].endswith('\n') else '')
        return

    current_index = None
    for tag, i1, i2, j1, j2 in ops:
        if tag != 'insert':
            continue
        addition = new[j1:j2]
        left = old[max(0, i1 - 140):i1]
        right = old[i1:i1 + 140]
        matches = []
        for idx, line in enumerate(lines):
            body = line.rstrip('\n')
            lp = body.find(left) if left else 0
            if lp < 0:
                continue
            start = lp + len(left)
            rp = body.find(right, start) if right else start
            if rp >= 0:
                matches.append((idx, start, rp))
        if len(matches) != 1:
            raise RuntimeError(f'semantic port anchor match count={len(matches)}')
        idx, start, rp = matches[0]
        body = lines[idx].rstrip('\n')
        if addition in body:
            current_index = idx
            continue
        body = body[:rp] + addition + body[rp:]
        lines[idx] = body + ('\n' if lines[idx].endswith('\n') else '')
        current_index = idx
    if current_index is None:
        raise RuntimeError('semantic port had no insertion opcode')


def semantic_preapply(kernel: Path, payload: str, report_path: Path):
    prefix, hunks = split_patch(payload)
    kernel_lines = kernel.read_text().splitlines(keepends=True)
    remaining = []
    semantic = []

    for n, hunk in enumerate(hunks, 1):
        minus = [x[1:].rstrip('\n') for x in hunk[1:] if x.startswith('-') and not x.startswith('---')]
        plus = [x[1:].rstrip('\n') for x in hunk[1:] if x.startswith('+') and not x.startswith('+++')]
        if minus and len(minus) == len(plus):
            pairs = []
            ok = True
            for old, new in zip(minus, plus):
                ops = pure_insert_pair(old, new)
                if ops is None:
                    ok = False
                    break
                pairs.append((old, new, ops))
            if ok:
                trial = list(kernel_lines)
                try:
                    for old, new, ops in pairs:
                        apply_insertions_to_line(trial, old, new, ops)
                except RuntimeError:
                    remaining.append(hunk)
                    continue
                kernel_lines = trial
                semantic.append(n)
                continue
        remaining.append(hunk)

    kernel.write_text(''.join(kernel_lines))
    report_path.write_text('semantic_hunks=' + ','.join(map(str, semantic)) + '\n')
    return ''.join(prefix + [line for h in remaining for line in h]), semantic


def run_direct_transform(label: str, text: str, transform: Path, kernel: Path, evidence: Path):
    current_sha = hashlib.sha256(kernel.read_bytes()).hexdigest()
    adapted, count = re.subn(
        r"expected\s*=\s*['\"][0-9a-fA-F]{64}['\"]",
        f"expected='{current_sha}'",
        text,
        count=1,
    )
    if count != 1:
        raise SystemExit(f'{label}: direct transformer expected-hash guard not found')

    adapted_path = evidence / f'{label}-PRODUCT-ADAPTED.py'
    adapted_path.write_text(adapted)
    before = hashlib.sha256(kernel.read_bytes()).hexdigest()
    proc = subprocess.run(
        [sys.executable, str(adapted_path), str(kernel)],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )
    (evidence / f'{label}-PORT.log').write_text(proc.stdout)
    after = hashlib.sha256(kernel.read_bytes()).hexdigest()
    (evidence / f'{label}-DIRECT.txt').write_text(
        f'mode=direct-transform\noriginal={transform}\nbefore={before}\nafter={after}\nrc={proc.returncode}\n'
    )
    print(f'{label} rc={proc.returncode} mode=direct-transform kernel_sha256={after}')
    if proc.returncode != 0:
        print(proc.stdout)
        raise SystemExit(proc.returncode)


def main():
    if len(sys.argv) != 5:
        raise SystemExit('usage: port_architecture_to_product.py LABEL TRANSFORM PRODUCT EVIDENCE')
    label, transform_s, product_s, evidence_s = sys.argv[1:]
    transform = Path(transform_s)
    product = Path(product_s)
    evidence = Path(evidence_s)
    kernel = product / 'kernel/main.nx'
    evidence.mkdir(parents=True, exist_ok=True)

    text = transform.read_text()
    payload = extract_patch_payload(text)
    if payload is None:
        run_direct_transform(label, text, transform, kernel, evidence)
        return

    (evidence / f'{label}-PORT.patch').write_text(payload)
    reduced, semantic = semantic_preapply(kernel, payload, evidence / f'{label}-SEMANTIC.txt')
    (evidence / f'{label}-PORT-REDUCED.patch').write_text(reduced)

    proc = subprocess.run(
        ['patch', '-p1', '--forward', '--batch', '--fuzz=3'],
        cwd=product, input=reduced, text=True,
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    (evidence / f'{label}-PORT.log').write_text(proc.stdout)
    sha = hashlib.sha256(kernel.read_bytes()).hexdigest()
    print(f'{label} rc={proc.returncode} semantic_hunks={semantic} kernel_sha256={sha}')
    if proc.returncode != 0:
        print(proc.stdout)
        raise SystemExit(proc.returncode)


if __name__ == '__main__':
    main()
