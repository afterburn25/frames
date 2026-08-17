#!/usr/bin/env python3
import argparse
import hashlib
import pathlib
import re
import sys


def sha256(path: pathlib.Path) -> str:
    h = hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def expected_hash(checksum_file: pathlib.Path, target_name: str) -> str:
    for line in checksum_file.read_text(errors='replace').splitlines():
        m = re.match(r'^([0-9a-fA-F]{64})\s+\*?(.+)$', line.strip())
        if m and pathlib.Path(m.group(2)).name == target_name:
            return m.group(1).lower()
    raise RuntimeError(f'no checksum entry for {target_name} in {checksum_file.name}')


def require(cond: bool, msg: str):
    if not cond:
        raise RuntimeError(msg)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--final', default='final')
    args = ap.parse_args()
    root = pathlib.Path(args.final)
    require(root.is_dir(), f'missing final handoff directory: {root}')

    isos = sorted(root.glob('*-Rufus-UEFI.iso'))
    require(len(isos) == 1, f'expected exactly one Rufus UEFI ISO, found {len(isos)}')
    iso = isos[0]
    iso_sum = root / 'ISO-SHA256.txt'
    cert = root / 'CERTIFICATION.txt'
    require(iso_sum.is_file(), 'missing ISO-SHA256.txt')
    require(cert.is_file(), 'missing CERTIFICATION.txt')
    expected = expected_hash(iso_sum, iso.name)
    actual = sha256(iso)
    require(actual == expected, f'ISO SHA-256 mismatch: expected {expected}, got {actual}')

    imgs = sorted(root.glob('*.img'))
    if imgs:
        img_sum = root / 'LOGGING-USB-SHA256.txt'
        require(img_sum.is_file(), 'writable/diagnostic IMG present but LOGGING-USB-SHA256.txt is missing')
        for img in imgs:
            expected_img = expected_hash(img_sum, img.name)
            actual_img = sha256(img)
            require(actual_img == expected_img, f'IMG SHA-256 mismatch for {img.name}')

    print(f'PHYSICAL_HANDOFF_PASS iso={iso.name} sha256={actual} images={len(imgs)} certification={cert.name}')


if __name__ == '__main__':
    try:
        main()
    except Exception as exc:
        print(f'PHYSICAL_HANDOFF_FAIL {exc}', file=sys.stderr)
        raise
