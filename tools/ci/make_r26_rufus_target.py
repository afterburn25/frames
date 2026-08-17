#!/usr/bin/env python3
import argparse, pathlib, subprocess, tempfile, struct, hashlib, json, sys
from r26_log_format import build_log, LOG_BYTES, NONCE, MAGIC, HEADER_BYTES

def run(cmd):
    print('+',' '.join(map(str,cmd)),flush=True); subprocess.run(list(map(str,cmd)),check=True)

def sha(path):
    h=hashlib.sha256()
    with open(path,'rb') as f:
        for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
    return h.hexdigest()

def fat_info(path,target11):
    b=path.read_bytes(); bps=struct.unpack_from('<H',b,11)[0]; spc=b[13]; reserved=struct.unpack_from('<H',b,14)[0]; nf=b[16]; fatsz=struct.unpack_from('<I',b,36)[0]; root=struct.unpack_from('<I',b,44)[0]
    if bps!=512 or not spc or not reserved or not nf or not fatsz or root<2: raise RuntimeError('invalid FAT32 BPB')
    fat_off=reserved*bps; data_sector=reserved+nf*fatsz
    def fat_next(c): return struct.unpack_from('<I',b,fat_off+c*4)[0]&0x0fffffff
    def chain(start,limit=20000):
        out=[];c=start;seen=set()
        while 2<=c<0x0ffffff8 and len(out)<limit:
            if c in seen:raise RuntimeError('FAT loop')
            seen.add(c);out.append(c);c=fat_next(c)
        return out,c
    roots,_=chain(root)
    found=None
    for dc in roots:
        base=(data_sector+(dc-2)*spc)*bps
        for i in range(0,spc*bps,32):
            e=b[base+i:base+i+32]
            if e[0]==0: break
            if e[0]==0xe5 or e[11]==0x0f: continue
            if e[:11]==target11:
                hi=struct.unpack_from('<H',e,20)[0];lo=struct.unpack_from('<H',e,26)[0]
                found=((hi<<16)|lo,struct.unpack_from('<I',e,28)[0]);break
        if found:break
    if not found:raise RuntimeError('FRAMES.LOG not found')
    ch,eoc=chain(found[0]);needed=(found[1]+spc*bps-1)//(spc*bps)
    if len(ch)!=needed or eoc<0x0ffffff8:raise RuntimeError('unexpected FRAMES.LOG chain length')
    if any(ch[i]+1!=ch[i+1] for i in range(len(ch)-1)):raise RuntimeError('FRAMES.LOG fragmented in CI Rufus target')
    rel_first=data_sector+(ch[0]-2)*spc; rel_last=rel_first+(needed*spc)-1
    return {'spc':spc,'reserved':reserved,'fatsz':fatsz,'root':root,'start_cluster':ch[0],'size':found[1],'rel_first':rel_first,'rel_last':rel_last}

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--payload',required=True);ap.add_argument('--out',required=True);ap.add_argument('--evidence',required=True);a=ap.parse_args()
    payload=pathlib.Path(a.payload);out=pathlib.Path(a.out);ev=pathlib.Path(a.evidence);ev.mkdir(parents=True,exist_ok=True)
    if not (payload/'EFI/BOOT/BOOTX64.EFI').is_file() or not (payload/'FRAMES').is_dir():raise SystemExit('payload missing')
    total_sectors=1048576 # 512 MiB CI-only target
    pstart=2048;psectors=total_sectors-pstart
    with tempfile.TemporaryDirectory(prefix='r26-rufus-') as td:
        td=pathlib.Path(td);part=td/'part.img';log=td/'FRAMES.LOG'
        with part.open('wb') as f:f.truncate(psectors*512)
        run(['mkfs.fat','-F','32','-n','FRAMESUSB',part])
        build_log(log)
        # Create the log first on a fresh FAT volume so the test media models a bounded preallocated file.
        run(['mcopy','-i',part,log,'::/FRAMES.LOG'])
        run(['mmd','-i',part,'::/EFI','::/EFI/BOOT','::/FRAMES'])
        run(['mcopy','-i',part,payload/'EFI/BOOT/BOOTX64.EFI','::/EFI/BOOT/BOOTX64.EFI'])
        for f in sorted((payload/'FRAMES').iterdir()): run(['mcopy','-i',part,f,'::/FRAMES/'])
        info=fat_info(part,b'FRAMES  LOG')
        with out.open('wb') as f:f.truncate(total_sectors*512)
        mbr=bytearray(512);e=446;mbr[e+4]=0x0c;struct.pack_into('<I',mbr,e+8,pstart);struct.pack_into('<I',mbr,e+12,psectors);mbr[510]=0x55;mbr[511]=0xaa
        with out.open('r+b') as f:f.write(mbr);f.seek(pstart*512);f.write(part.read_bytes())
    first=pstart+info['rel_first'];last=pstart+info['rel_last'];authorized_first=first+1
    manifest={'status':'PASS','purpose':'CI-only Rufus ISO-mode FAT32 target; never a physical handoff','bytes':out.stat().st_size,'sha256':sha(out),'partition_start':pstart,'partition_sectors':psectors,'log_first_lba':first,'log_last_lba':last,'authorized_lba_start':authorized_first,'authorized_lba_end':last,'log_lba_start':authorized_first,'log_lba_end':last,'log_bytes':LOG_BYTES,'header_bytes':HEADER_BYTES,'cluster_sectors':info['spc'],'nonce':NONCE,'magic':MAGIC.decode()}
    (ev/'R26-RUFUS-TARGET.json').write_text(json.dumps(manifest,indent=2)+'\n');(ev/'R26-RUFUS-TARGET-SHA256.txt').write_text(f"{manifest['sha256']}  {out.name}\n")
    print(json.dumps(manifest,sort_keys=True))
if __name__=='__main__':main()
