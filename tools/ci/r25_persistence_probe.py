#!/usr/bin/env python3
import hashlib,json,pathlib,shutil,subprocess,tempfile
import r25_cert_driver as d
ROOT=pathlib.Path.cwd()
R21_SHA=d.R21_SHA; R24_SHA=d.R24_SHA
R25H_SHA='3d2e3a968043db2bf4c4bd2633f7a2263e4ce41167430db71a7db8ea1cdf9f87'
ISO_NAME=d.ISO_NAME; IMG_NAME=d.IMG_NAME

def req(x,m):
    if not x: raise RuntimeError(m)
def run(cmd,cwd=None,check=True,stdout=None,stderr=None):
    print('+',cmd,flush=True); return subprocess.run(cmd,cwd=cwd,shell=isinstance(cmd,str),check=check,text=True,stdout=stdout,stderr=stderr)
def sha(p): return d.sha(p)

def main():
    r21=ROOT/'r21-candidate/evidence/kernel-r21.nx'; req(r21.is_file() and sha(r21)==R21_SHA,'exact r21 source missing')
    kit=ROOT/'Frames-0.9.98-Runtime-Certification-Kit-v108-r9.zip'; req(kit.is_file() and sha(kit)==d.KIT_SHA,'kit identity')
    for x in ('probe-evidence','probe-out','probe-payload'):
        shutil.rmtree(ROOT/x,ignore_errors=True); (ROOT/x).mkdir(parents=True,exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='r25probe-') as td:
        td=pathlib.Path(td); kd=td/'kit'; sd=td/'src'; kd.mkdir(); sd.mkdir(); run(['unzip','-q',kit,'-d',kd]); z=kd/'Frames-0.9.98-Source-v108.zip'; req(sha(z)==d.SRC_SHA,'source identity'); run(['unzip','-q',z,'-d',sd]); F=sd/'Frames-0.9.98'; shutil.copy2(r21,F/'kernel/main.nx')
        r24=td/'r24.nx'; shutil.copy2(r21,r24); run(['python3',ROOT/'tools/ci/patch_v108_physical_input_r24b_fixbrace.py',r24],stdout=subprocess.PIPE); req(sha(r24)==R24_SHA,'r24 identity')
        rr=run(['python3',ROOT/'tools/ci/patch_v108_r25h_restore_bulk_dci.py',F/'kernel/main.nx'],stdout=subprocess.PIPE); req(sha(F/'kernel/main.nx')==R25H_SHA,'r25h identity'); shutil.copy2(F/'kernel/main.nx',ROOT/'probe-evidence/kernel-r25h.nx'); (ROOT/'probe-evidence/R25H-SHA.txt').write_text(rr.stdout)
        for x in ('out','payload'):
            shutil.rmtree(ROOT/x,ignore_errors=True)
        (ROOT/'out').symlink_to(ROOT/'probe-out',target_is_directory=True); (ROOT/'payload').symlink_to(ROOT/'probe-payload',target_is_directory=True)
        try: d.build_iso(F,ROOT/'probe-out'/ISO_NAME)
        finally:
            (ROOT/'out').unlink(); (ROOT/'payload').unlink()
        iso=ROOT/'probe-out'/ISO_NAME; iso_sha=sha(iso); (ROOT/'probe-evidence/ISO-SHA256.txt').write_text(f'{iso_sha}  {ISO_NAME}\n')
        (ROOT/'payload').symlink_to(ROOT/'probe-payload',target_is_directory=True)
        try: run(['python3','tools/ci/make_r25_logging_usb.py','--payload','payload','--out',ROOT/'probe-out'/IMG_NAME,'--evidence','probe-evidence'],cwd=ROOT)
        finally: (ROOT/'payload').unlink()
        ovmfs=list(pathlib.Path('/usr/share/OVMF').rglob('OVMF_CODE_4M.fd'))+list(pathlib.Path('/usr/share/OVMF').rglob('OVMF_CODE.fd')); req(ovmfs,'OVMF'); gate=ROOT/'probe-evidence/flight-log'; gate.mkdir()
        run(['python3','tools/ci/qemu_r25_flight_log_gate.py','--ovmf',ovmfs[0],'--iso',iso,'--log-image',ROOT/'probe-out'/IMG_NAME,'--manifest',ROOT/'probe-evidence/R25-LOG-IMAGE.json','--out',gate,'--expected-iso-sha',iso_sha],cwd=ROOT)
        result=json.loads((gate/'R25-FLIGHT-LOG.json').read_text()); req(result['status']=='PASS','flight log probe failed'); print('R25 PERSISTENCE PROBE PASS',json.dumps(result,sort_keys=True))
if __name__=='__main__': main()
