#!/usr/bin/env python3
from pathlib import Path
import struct
MAGIC=b'FRLOG126'
VERSION=1
NONCE=3545795563478602310
LOG_BYTES=4*1024*1024
HEADER_BYTES=512
HEADER_OFFSET=128

def build_log(path):
    path=Path(path)
    head=bytearray(b' '*HEADER_BYTES)
    text=(b'Frames r26 System Flight Recorder\r\n'
          b'Rufus ISO-native controlled diagnostic log. Internal disks remain read-only.\r\n'
          b'Record stream begins after this 512-byte header.\r\n')
    head[:len(text)]=text
    struct.pack_into('<8sQQQQ',head,HEADER_OFFSET,MAGIC,VERSION,NONCE,LOG_BYTES,HEADER_BYTES)
    with path.open('wb') as f:
        f.write(head)
        left=LOG_BYTES-HEADER_BYTES
        chunk=b' '*(1024*1024)
        while left:
            n=min(left,len(chunk)); f.write(chunk[:n]); left-=n
    return path
