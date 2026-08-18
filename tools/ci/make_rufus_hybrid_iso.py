#!/usr/bin/env python3
from pathlib import Path
import argparse
import hashlib
import shutil
import struct
import uuid
import zlib

SECTOR = 512
GPT_ENTRY_SIZE = 128
GPT_ENTRY_COUNT = 128
GPT_ARRAY_BYTES = GPT_ENTRY_SIZE * GPT_ENTRY_COUNT
ESP_TYPE = uuid.UUID('c12a7328-f81f-11d2-ba4b-00a0c93ec93b')


def find_embedded_esp(data: bytes):
    """Find a GPT disk image embedded in the ISO and return its ESP byte range."""
    candidates = []
    pos = 0
    while True:
        pos = data.find(b'EFI PART', pos)
        if pos < 0:
            break
        if pos >= SECTOR and pos % SECTOR == 0:
            base = pos - SECTOR
            hdr = data[pos:pos + SECTOR]
            if len(hdr) == SECTOR:
                hsz = struct.unpack_from('<I', hdr, 12)[0]
                current = struct.unpack_from('<Q', hdr, 24)[0]
                entries_lba = struct.unpack_from('<Q', hdr, 72)[0]
                count = struct.unpack_from('<I', hdr, 80)[0]
                esz = struct.unpack_from('<I', hdr, 84)[0]
                if 92 <= hsz <= SECTOR and current == 1 and esz >= 128 and count > 0:
                    entry_base = base + entries_lba * SECTOR
                    for i in range(min(count, 128)):
                        off = entry_base + i * esz
                        ent = data[off:off + esz]
                        if len(ent) < 128:
                            break
                        if ent[:16] == ESP_TYPE.bytes_le:
                            start, end = struct.unpack_from('<QQ', ent, 32)
                            abs_start = base + start * SECTOR
                            abs_end = base + (end + 1) * SECTOR
                            if 0 <= abs_start < abs_end <= len(data):
                                boot = data[abs_start:abs_start + SECTOR]
                                if boot[510:512] == b'\x55\xaa' and boot[82:90] == b'FAT32   ':
                                    candidates.append((base, start, end, abs_start, abs_end))
        pos += 8
    if len(candidates) != 1:
        raise SystemExit(f'expected exactly one embedded GPT ESP, found {len(candidates)}')
    return candidates[0]


def make_header(current, backup, first_usable, last_usable, disk_guid, entries_lba, entries_crc):
    h = bytearray(SECTOR)
    h[:8] = b'EFI PART'
    struct.pack_into('<I', h, 8, 0x00010000)
    struct.pack_into('<I', h, 12, 92)
    struct.pack_into('<I', h, 16, 0)
    struct.pack_into('<I', h, 20, 0)
    struct.pack_into('<Q', h, 24, current)
    struct.pack_into('<Q', h, 32, backup)
    struct.pack_into('<Q', h, 40, first_usable)
    struct.pack_into('<Q', h, 48, last_usable)
    h[56:72] = disk_guid.bytes_le
    struct.pack_into('<Q', h, 72, entries_lba)
    struct.pack_into('<I', h, 80, GPT_ENTRY_COUNT)
    struct.pack_into('<I', h, 84, GPT_ENTRY_SIZE)
    struct.pack_into('<I', h, 88, entries_crc)
    crc = zlib.crc32(h[:92]) & 0xffffffff
    struct.pack_into('<I', h, 16, crc)
    return h


def hybridize(src: Path, dst: Path):
    raw = src.read_bytes()
    if raw[32769:32774] != b'CD001':
        raise SystemExit('input is not an ISO9660 image')
    base, inner_start, inner_end, esp_abs_start, esp_abs_end = find_embedded_esp(raw)
    if esp_abs_start % SECTOR or esp_abs_end % SECTOR:
        raise SystemExit('embedded ESP is not 512-byte aligned')

    shutil.copyfile(src, dst)
    orig_bytes = dst.stat().st_size
    if orig_bytes % SECTOR:
        raise SystemExit('ISO size is not sector aligned')

    # Reserve 32 sectors for the backup GPT entry array plus one backup header.
    orig_sectors = orig_bytes // SECTOR
    new_sectors = orig_sectors + 33
    last_lba = new_sectors - 1
    backup_entries_lba = last_lba - 32
    first_usable = 34
    last_usable = backup_entries_lba - 1
    part_start = esp_abs_start // SECTOR
    part_end = esp_abs_end // SECTOR - 1
    if part_start < first_usable or part_end > last_usable:
        raise SystemExit('embedded ESP does not fit outer GPT usable range')

    disk_guid = uuid.uuid5(uuid.NAMESPACE_URL, 'privoralabs:frames:rufus-hybrid:' + hashlib.sha256(raw).hexdigest())
    part_guid = uuid.uuid5(disk_guid, 'Frames EFI System')

    entries = bytearray(GPT_ARRAY_BYTES)
    entry = bytearray(GPT_ENTRY_SIZE)
    entry[:16] = ESP_TYPE.bytes_le
    entry[16:32] = part_guid.bytes_le
    struct.pack_into('<QQQ', entry, 32, part_start, part_end, 0)
    name = 'Frames EFI System'.encode('utf-16le')
    entry[56:56 + len(name)] = name
    entries[:GPT_ENTRY_SIZE] = entry
    entries_crc = zlib.crc32(entries) & 0xffffffff

    primary = make_header(1, last_lba, first_usable, last_usable, disk_guid, 2, entries_crc)
    backup = make_header(last_lba, 1, first_usable, last_usable, disk_guid, backup_entries_lba, entries_crc)

    with dst.open('r+b') as f:
        f.truncate(new_sectors * SECTOR)
        mbr = bytearray(f.read(SECTOR))
        mbr[446:510] = b'\0' * 64
        protective_size = min(new_sectors - 1, 0xffffffff)
        mbr[446:462] = struct.pack('<B3sB3sII', 0, b'\x00\x02\x00', 0xEE, b'\xff\xff\xff', 1, protective_size)
        mbr[510:512] = b'\x55\xaa'
        f.seek(0); f.write(mbr)
        f.seek(SECTOR); f.write(primary)
        f.seek(2 * SECTOR); f.write(entries)
        f.seek(backup_entries_lba * SECTOR); f.write(entries)
        f.seek(last_lba * SECTOR); f.write(backup)

    verify(dst, expected_start=part_start, expected_end=part_end)
    print(f'hybrid_iso={dst}')
    print(f'outer_disk_guid={disk_guid}')
    print(f'esp_lba_start={part_start}')
    print(f'esp_lba_end={part_end}')
    print(f'iso_sha256={hashlib.sha256(dst.read_bytes()).hexdigest()}')


def verify(path: Path, expected_start=None, expected_end=None):
    data = path.read_bytes()
    if data[510:512] != b'\x55\xaa':
        raise SystemExit('missing protective MBR signature')
    if data[450] != 0xEE:
        raise SystemExit('protective MBR partition type is not 0xEE')
    hdr = bytearray(data[SECTOR:2 * SECTOR])
    if hdr[:8] != b'EFI PART':
        raise SystemExit('missing primary GPT header')
    stored = struct.unpack_from('<I', hdr, 16)[0]
    struct.pack_into('<I', hdr, 16, 0)
    if (zlib.crc32(hdr[:92]) & 0xffffffff) != stored:
        raise SystemExit('primary GPT header CRC mismatch')
    entries_lba = struct.unpack_from('<Q', hdr, 72)[0]
    entries_crc = struct.unpack_from('<I', hdr, 88)[0]
    entries = data[entries_lba * SECTOR:entries_lba * SECTOR + GPT_ARRAY_BYTES]
    if (zlib.crc32(entries) & 0xffffffff) != entries_crc:
        raise SystemExit('GPT partition-array CRC mismatch')
    first = entries[:GPT_ENTRY_SIZE]
    if first[:16] != ESP_TYPE.bytes_le:
        raise SystemExit('first GPT partition is not an EFI System Partition')
    start, end = struct.unpack_from('<QQ', first, 32)
    if expected_start is not None and (start != expected_start or end != expected_end):
        raise SystemExit('outer GPT ESP range mismatch')
    boot = data[start * SECTOR:(start + 1) * SECTOR]
    if boot[510:512] != b'\x55\xaa' or boot[82:90] != b'FAT32   ':
        raise SystemExit('outer GPT ESP does not point to FAT32 boot volume')
    last_lba = len(data) // SECTOR - 1
    backup = bytearray(data[last_lba * SECTOR:(last_lba + 1) * SECTOR])
    if backup[:8] != b'EFI PART':
        raise SystemExit('missing backup GPT header')
    stored_b = struct.unpack_from('<I', backup, 16)[0]
    struct.pack_into('<I', backup, 16, 0)
    if (zlib.crc32(backup[:92]) & 0xffffffff) != stored_b:
        raise SystemExit('backup GPT header CRC mismatch')
    print('rufus_hybrid_verify=PASS')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('input_iso', type=Path)
    ap.add_argument('output_iso', type=Path, nargs='?')
    ap.add_argument('--verify', action='store_true')
    args = ap.parse_args()
    if args.verify:
        verify(args.input_iso)
        return
    if args.output_iso is None:
        raise SystemExit('output_iso is required unless --verify is used')
    hybridize(args.input_iso, args.output_iso)


if __name__ == '__main__':
    main()
