#!/usr/bin/env bash
set -euo pipefail
: "${GITHUB_WORKSPACE:?}" "${RUNNER_TEMP:?}" "${ISO_NAME:?}"
R17_SHA=990a52e11163359e65307c25752504827398b288d4a1ef763675039b47103732
R18_SHA=dd0386720bba6dce4c1fd0576e995dd6a2932638633147914589b342cc3dfe22
KIT_SHA=61b0fc25513719fce554729724c7848647de9cffe54434d4ab5f7ba8af42a36a
SRC_SHA=5f8c13adac6d34e64bd47d9463a3e261cd0b51bb5ddb500aa9f7b87c2914a52d
test "$(sha256sum r17-candidate/evidence/kernel-r17.nx|awk '{print $1}')" = "$R17_SHA"
rm -rf "$RUNNER_TEMP/r18r5" evidence out payload; mkdir -p "$RUNNER_TEMP/r18r5/kit" "$RUNNER_TEMP/r18r5/src" evidence out payload
K=Frames-0.9.98-Runtime-Certification-Kit-v108-r9.zip; test "$(sha256sum "$K"|awk '{print $1}')" = "$KIT_SHA"; unzip -q "$K" -d "$RUNNER_TEMP/r18r5/kit"
Z="$RUNNER_TEMP/r18r5/kit/Frames-0.9.98-Source-v108.zip"; test "$(sha256sum "$Z"|awk '{print $1}')" = "$SRC_SHA"; unzip -q "$Z" -d "$RUNNER_TEMP/r18r5/src"
F="$RUNNER_TEMP/r18r5/src/Frames-0.9.98"; cp r17-candidate/evidence/kernel-r17.nx "$F/kernel/main.nx"; cp "$F/kernel/main.nx" evidence/kernel-r17.nx
python3 tools/ci/patch_v108_physical_input_r18_usb_xhci_menu.py "$F/kernel/main.nx" | tee evidence/R18-SHA.txt
test "$(sha256sum "$F/kernel/main.nx"|awk '{print $1}')" = "$R18_SHA"; cp "$F/kernel/main.nx" evidence/kernel-r18.nx
diff -u evidence/kernel-r17.nx evidence/kernel-r18.nx > evidence/R17-R18.patch || true
python3 - <<'PY'
from pathlib import Path
d=Path('evidence/R17-R18.patch').read_text(errors='replace').lower(); bad=['nvme_write','storage_write','write10','write(10)','scsi_write','fat_write','block_write','destructive_write','physical_write_enable']; hits=[x for x in bad if x in d]
Path('evidence/WRITE-SURFACE.txt').write_text('status='+('PASS' if not hits else 'FAIL')+'\nhits='+','.join(hits)+'\n')
if hits: raise SystemExit(hits)
PY
find "$F" -type f -name '*.sh' -exec chmod +x {} +; find "$F/toolchain" -type f -name nexus -exec chmod +x {} +
cd "$F"; ./tools/build.sh; python3 tools/make_esp.py; python3 tools/sdk_selftest.py; python3 tools/make_desktop_preview_image.py; python3 tools/verify_desktop_preview_image.py --image build/Frames-0.9.98-Desktop-Preview.img --require-pass; python3 tools/verify_release.py; cp build/Frames-0.9.98-Desktop-Preview.img "$GITHUB_WORKSPACE/out/raw.img"
cd "$GITHUB_WORKSPACE"; FIRST="$(sgdisk -i 1 out/raw.img|awk -F: '/First sector/{gsub(/ /,"",$2);split($2,a,"(");print a[1]}')"; LAST="$(sgdisk -i 1 out/raw.img|awk -F: '/Last sector/{gsub(/ /,"",$2);split($2,a,"(");print a[1]}')"
dd if=out/raw.img of=out/esp.img bs=512 skip="$FIRST" count=$((LAST-FIRST+1)) status=none; mcopy -s -i out/esp.img '::/EFI' payload/; mcopy -s -i out/esp.img '::/FRAMES' payload/
dd if=/dev/zero of=out/efiboot.img bs=1M count=16 status=none; mkfs.fat -F 16 -n FRAMESBOOT out/efiboot.img >/dev/null; mmd -i out/efiboot.img ::/EFI ::/EFI/BOOT ::/FRAMES; mcopy -i out/efiboot.img payload/EFI/BOOT/BOOTX64.EFI ::/EFI/BOOT/BOOTX64.EFI; for f in payload/FRAMES/*; do mcopy -i out/efiboot.img "$f" ::/FRAMES/; done
ROOT="$RUNNER_TEMP/r18r5-root"; rm -rf "$ROOT"; mkdir -p "$ROOT"; cp out/efiboot.img "$ROOT/"; cp -a payload/EFI payload/FRAMES "$ROOT/"; printf 'Frames v108 r18 xHCI/menu stability repair\nRufus ISO Image mode\nRead-only diagnostic only\n' > "$ROOT/README.TXT"
xorriso -as mkisofs -iso-level 3 -R -J -V FRAMES_V108_R18 -eltorito-alt-boot -e efiboot.img -no-emul-boot -o "out/$ISO_NAME" "$ROOT" >/dev/null 2>&1
sha256sum "out/$ISO_NAME" | tee evidence/ISO-SHA256.txt; stat -c '%s' "out/$ISO_NAME" | tee evidence/ISO-SIZE.txt
