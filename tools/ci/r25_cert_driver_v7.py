#!/usr/bin/env python3
from pathlib import Path

base=Path(__file__).with_name('r25_cert_driver.py')
s=base.read_text()
repls={
    "R25_SHA='068ed900f8942ecec797e2f5fa5e79f95fce51ef817b2e3336af05d643528674'":"R25_SHA='af77b8f648dbb11fa6a31810e2150483818213635c92404dd956db892df9fdb0'",
    "patch_v108_r25_flightrec_usbwrite.py":"patch_v108_r25k_large_media_log_gate.py",
    "'FRAMES_FLIGHT_RECORDER_R25_READY','FRAMES_CONTROLLED_USB_LOG_R25_ARMED','fn v108_msc_snapshot_v125'":"'fn serial_marker_flight_recorder_r25','fn serial_marker_controlled_usb_log_r25','fn v108_msc_snapshot_v125'",
    "'XENU ST FL VID PID MSC LOG','FREC Q DROP ARM W ERR'":"'fn v108_text_xenu_v125','fn v108_text_frec_v125'",
    "volatile_read64(data+80)!=3545795563478602310":"volatile_read64(data+64)!=3545795563478602310",
    "volatile_read64(msc+688)!=524287":"volatile_read64(msc+688)<524287",
}
for old,new in repls.items():
    if s.count(old)!=1:
        raise SystemExit(f'r25 v7 anchor mismatch for {old!r}: {s.count(old)}')
    s=s.replace(old,new,1)
old="req(not miss,'r25 model missing '+repr(miss)); req('desktop_redraw=1' not in s,'full desktop repaint re-enabled')"
new="req(not miss,'r25 model missing '+repr(miss)); req('serial_usb_msc_diag(46' in s,'shared xHCI event dispatcher missing'); req('if eslot==slot && ep==dci' in s,'MSC completion routing missing'); req('volatile_read64(msc+688)<524287' in s,'larger-media bounded capacity gate missing'); req('desktop_redraw=1' not in s,'full desktop repaint re-enabled')"
if s.count(old)!=1: raise SystemExit('r25 v7 model-gate anchor mismatch')
s=s.replace(old,new,1)
old="lg=g/'flight-log';lg.mkdir();run(['python3','tools/ci/qemu_r25_flight_log_gate.py','--ovmf',ovmf,'--iso',ROOT/'out'/ISO_NAME,'--log-image',logimg,'--manifest',man,'--out',lg,'--expected-iso-sha',iso_sha],cwd=ROOT);jsonpass(lg/'R25-FLIGHT-LOG.json');status['flight-log']='PASS';(lg/'RESULT.status').write_text('PASS\\n')"
new="lg=g/'flight-log';lg.mkdir();run(['python3','tools/ci/qemu_r25_flight_log_gate.py','--ovmf',ovmf,'--iso',ROOT/'out'/ISO_NAME,'--log-image',logimg,'--manifest',man,'--out',lg,'--expected-iso-sha',iso_sha],cwd=ROOT);jsonpass(lg/'R25-FLIGHT-LOG.json');status['flight-log']='PASS';(lg/'RESULT.status').write_text('PASS\\n'); large=g/'flight-log-large-media.img';shutil.copy2(logimg,large);large.touch();run(['truncate','-s','512M',large]);lgg=g/'flight-log-large';lgg.mkdir();run(['python3','tools/ci/qemu_r25_flight_log_gate.py','--ovmf',ovmf,'--iso',ROOT/'out'/ISO_NAME,'--log-image',large,'--manifest',man,'--out',lgg,'--expected-iso-sha',iso_sha],cwd=ROOT);jsonpass(lgg/'R25-FLIGHT-LOG.json');status['flight-log-large']='PASS';(lgg/'RESULT.status').write_text('PASS\\n');large.unlink()"
if s.count(old)!=1: raise SystemExit('r25 v7 large-media gate anchor mismatch')
s=s.replace(old,new,1)
ns={'__name__':'__main__','__file__':str(base)}
exec(compile(s,str(base),'exec'),ns,ns)
