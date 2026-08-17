#!/usr/bin/env python3
import argparse, pathlib, subprocess, tempfile, struct, hashlib, json

MAGIC=b'FRMSTAG1'
NONCE=3545795563478602310
LOG_BYTES=4*1024*1024

def run(cmd):
    print('+',' '.join(map(str,cmd)),flush=True)
    subprocess.run(list(map(str,cmd)),check=True)

def file_sha(path):
    h=hashlib.sha256()
    with open(path,'rb') as f:
        for b in iter(lambda:f.read(1024*1024),b''): h.update(b)
    return h.hexdigest()

def fat_info(path,target11):
    b=path.read_bytes(); bps=struct.unpack_from('<H',b,11)[0]; spc=b[13]; reserved=struct.unpack_from('<H',b,14)[0]; nf=b[16]; fatsz=struct.unpack_from('<I',b,36)[0]; root=struct.unpack_from('<I',b,44)[0]
    if bps!=512 or not spc or not reserved or not nf or not fatsz: raise RuntimeError('invalid FAT32 BPB')
    fat_off=reserved*bps; data_sector=reserved+nf*fatsz
    def fat_next(c): return struct.unpack_from('<I',b,fat_off+c*4)[0]&0x0fffffff
    def chain(start):
        out=[]; c=start; seen=set()
        while 2<=c<0x0ffffff8:
            if c in seen: raise RuntimeError('FAT loop')
            seen.add(c);out.append(c);c=fat_next(c)
        return out
    found=None
    for dc in chain(root):
        off=(data_sector+(dc-2)*spc)*bps
        for i in range(0,spc*bps,32):
            e=b[off+i:off+i+32]
            if e[0]==0: break
            if e[0]==0xe5 or e[11]==0x0f: continue
            if e[:11]==target11:
                hi=struct.unpack_from('<H',e,20)[0];lo=struct.unpack_from('<H',e,26)[0]
                found=((hi<<16)|lo,struct.unpack_from('<I',e,28)[0]);break
        if found:break
    if not found: raise RuntimeError('target file not found')
    ch=chain(found[0]); needed=(found[1]+spc*bps-1)//(spc*bps)
    if len(ch)<needed or any(ch[i]+1!=ch[i+1] for i in range(needed-1)): raise RuntimeError('FRAMES.LOG not contiguous')
    rel_start=data_sector+(ch[0]-2)*spc; rel_end=rel_start+needed*spc-1
    return {'spc':spc,'reserved':reserved,'fatsz':fatsz,'root':root,'data_sector':data_sector,'start_cluster':ch[0],'size':found[1],'rel_start':rel_start,'rel_end':rel_end}

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--out',required=True);ap.add_argument('--evidence',required=True);a=ap.parse_args()
    out=pathlib.Path(a.out);ev=pathlib.Path(a.evidence);ev.mkdir(parents=True,exist_ok=True)
    total_sectors=524288; pstart=2048; psectors=total_sectors-pstart
    with tempfile.TemporaryDirectory(prefix='r25l-fat-') as td:
        td=pathlib.Path(td);part=td/'part.img';log=td/'FRAMES.LOG';tag=td/'FRAMES.TAG'
        with open(part,'wb') as f:f.truncate(psectors*512)
        run(['mkfs.fat','-F','32','-n','FRAMESUSB',part])
        header=b'Frames r25l System Flight Recorder\r\nPersistent records begin below; trailing spaces are unused.\r\n'
        with open(log,'wb') as f:
            f.write(header); remaining=LOG_BYTES-len(header); chunk=b' '*1024*1024
            while remaining:
                n=min(remaining,len(chunk));f.write(chunk[:n]);remaining-=n
        tag.write_bytes(MAGIC+struct.pack('<QQQ',1,NONCE,LOG_BYTES))
        run(['mcopy','-i',part,log,'::/FRAMES.LOG']);run(['mcopy','-i',part,tag,'::/FRAMES.TAG'])
        info=fat_info(part,b'FRAMES  LOG')
        with open(out,'wb') as f:f.truncate(total_sectors*512)
        # CI-only MBR + one FAT32 LBA partition: mirrors the single-volume layout expected after Rufus ISO mode.
        mbr=bytearray(512);e=446;mbr[e]=0x00;mbr[e+4]=0x0c;struct.pack_into('<I',mbr,e+8,pstart);struct.pack_into('<I',mbr,e+12,psectors);mbr[510]=0x55;mbr[511]=0xaa
        with open(out,'r+b') as f:f.write(mbr);f.seek(pstart*512);f.write(part.read_bytes())
    abs_start=pstart+info['rel_start'];abs_end=pstart+info['rel_end'];h=file_sha(out)
    manifest={'total_sectors':total_sectors,'bytes':out.stat().st_size,'sha256':h,'partition_start':pstart,'partition_sectors':psectors,'log_lba_start':abs_start,'log_lba_end':abs_end,'log_bytes':LOG_BYTES,'cluster_sectors':info['spc'],'nonce':NONCE,'tag_magic':'FRMSTAG1','purpose':'CI-only Rufus-style FAT32 persistence target; not a physical handoff image'}
    (ev/'R25L-RUFUS-LOG-VOLUME.json').write_text(json.dumps(manifest,indent=2)+'\n');(ev/'R25L-RUFUS-LOG-VOLUME-SHA256.txt').write_text(f'{h}  {out.name}\n')
    print(json.dumps(manifest,sort_keys=True))
if __name__=='__main__':main()
