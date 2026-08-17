#!/usr/bin/env python3
import argparse, pathlib, subprocess, tempfile, struct, hashlib

def run(cmd):
    print('+', ' '.join(map(str,cmd)), flush=True); subprocess.run(list(map(str,cmd)),check=True)

def fat_info(path, target11):
    b=path.read_bytes(); bps=struct.unpack_from('<H',b,11)[0]; spc=b[13]; reserved=struct.unpack_from('<H',b,14)[0]; nf=b[16]; fatsz=struct.unpack_from('<I',b,36)[0]; root=struct.unpack_from('<I',b,44)[0]
    assert bps==512 and spc and reserved>=16 and nf>=1 and fatsz
    fat_off=reserved*bps; data_sector=reserved+nf*fatsz
    def fat_next(c): return struct.unpack_from('<I',b,fat_off+c*4)[0] & 0x0fffffff
    def chain(start):
        out=[]; c=start; seen=set()
        while 2<=c<0x0ffffff8:
            if c in seen: raise RuntimeError('FAT loop')
            seen.add(c); out.append(c); c=fat_next(c)
        return out
    found=None
    for dc in chain(root):
        off=(data_sector+(dc-2)*spc)*bps
        for i in range(0,spc*bps,32):
            e=b[off+i:off+i+32]
            if e[0] in (0,0xe5):
                if e[0]==0: break
                continue
            if e[11]==0x0f: continue
            if e[:11]==target11:
                hi=struct.unpack_from('<H',e,20)[0]; lo=struct.unpack_from('<H',e,26)[0]; found=((hi<<16)|lo,struct.unpack_from('<I',e,28)[0]); break
        if found: break
    if not found: raise RuntimeError('target file not found')
    ch=chain(found[0]); needed=(found[1]+spc*bps-1)//(spc*bps)
    if len(ch)<needed or any(ch[i]+1!=ch[i+1] for i in range(needed-1)): raise RuntimeError('log file not contiguous')
    rel_start=data_sector+(ch[0]-2)*spc; rel_end=rel_start+needed*spc-1
    return dict(bps=bps,spc=spc,reserved=reserved,data_sector=data_sector,start_cluster=ch[0],size=found[1],rel_start=rel_start,rel_end=rel_end,clusters=needed)

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--payload',required=True); ap.add_argument('--out',required=True); ap.add_argument('--evidence',required=True); a=ap.parse_args()
    payload=pathlib.Path(a.payload); out=pathlib.Path(a.out); ev=pathlib.Path(a.evidence); ev.mkdir(parents=True,exist_ok=True)
    if not (payload/'EFI/BOOT/BOOTX64.EFI').is_file() or not (payload/'FRAMES').is_dir(): raise SystemExit('payload missing')
    total_sectors=524288; p1_start=2048; p1_sectors=131072; p2_start=133120; p2_sectors=262144; marker_rel=12; marker_lba=p2_start+marker_rel
    with tempfile.TemporaryDirectory(prefix='r25logimg-') as td:
        td=pathlib.Path(td); p1=td/'p1.img'; p2=td/'p2.img'; log=td/'FRAMES.LOG'; readme=td/'README.TXT'
        with open(out,'wb') as f: f.truncate(total_sectors*512)
        run(['sgdisk','-o',out]); run(['sgdisk','-n',f'1:{p1_start}:{p1_start+p1_sectors-1}','-t','1:EF00','-c','1:FRAMESBOOT',out]); run(['sgdisk','-n',f'2:{p2_start}:{p2_start+p2_sectors-1}','-t','2:0700','-c','2:FRAMESLOG',out])
        with open(p1,'wb') as f:f.truncate(p1_sectors*512)
        with open(p2,'wb') as f:f.truncate(p2_sectors*512)
        run(['mkfs.fat','-F','32','-n','FRAMESBOOT',p1]); run(['mkfs.fat','-F','32','-n','FRAMESLOG',p2])
        run(['mmd','-i',p1,'::/EFI','::/EFI/BOOT','::/FRAMES']); run(['mcopy','-i',p1,payload/'EFI/BOOT/BOOTX64.EFI','::/EFI/BOOT/BOOTX64.EFI'])
        for f in sorted((payload/'FRAMES').iterdir()): run(['mcopy','-i',p1,f,'::/FRAMES/'])
        with open(log,'wb') as f:
            header=b'Frames r25 System Flight Recorder\r\nFixed-size diagnostic log; trailing spaces are unused.\r\n'; f.write(header); remaining=4*1024*1024-len(header); chunk=b' '*1024*1024
            while remaining: n=min(remaining,len(chunk)); f.write(chunk[:n]); remaining-=n
        readme.write_text('FRAMES.LOG is the Frames System Flight Recorder diagnostic stream.\r\nThe file is preallocated; Frames only writes inside its certified data clusters.\r\nInternal system disks remain read-only.\r\n')
        run(['mcopy','-i',p2,log,'::/FRAMES.LOG']); run(['mcopy','-i',p2,readme,'::/README.TXT'])
        info=fat_info(p2,b'FRAMES  LOG'); abs_start=p2_start+info['rel_start']; abs_end=p2_start+info['rel_end']
        if abs_start<p2_start+32 or abs_end>=p2_start+p2_sectors: raise RuntimeError('bad log range')
        marker=bytearray(512); vals=[2391787741383512646,1,total_sectors,512,p2_start,abs_start,abs_end,marker_lba,3545795563478602310,4*1024*1024]
        for i,v in enumerate(vals): struct.pack_into('<Q',marker,i*8,v)
        with open(p2,'r+b') as f: f.seek(marker_rel*512); f.write(marker)
        with open(out,'r+b') as d: d.seek(p1_start*512); d.write(p1.read_bytes()); d.seek(p2_start*512); d.write(p2.read_bytes())
    sha=hashlib.sha256(out.read_bytes()).hexdigest(); manifest={'total_sectors':total_sectors,'bytes':out.stat().st_size,'sha256':sha,'p1_start':p1_start,'p1_sectors':p1_sectors,'p2_start':p2_start,'p2_sectors':p2_sectors,'marker_lba':marker_lba,'log_lba_start':abs_start,'log_lba_end':abs_end,'log_bytes':4*1024*1024,'cluster_sectors':info['spc'],'nonce':3545795563478602310}
    import json; (ev/'R25-LOG-IMAGE.json').write_text(json.dumps(manifest,indent=2)+'\n'); (ev/'R25-LOG-IMAGE-SHA256.txt').write_text(f'{sha}  {out.name}\n'); print(json.dumps(manifest,sort_keys=True))
if __name__=='__main__': main()
