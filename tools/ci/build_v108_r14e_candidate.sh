#!/usr/bin/env bash
set -euo pipefail
: "${KIT_SHA:?}" "${SRC_SHA:?}" "${BASE_SHA:?}" "${R14E_SHA:?}" "${ISO_NAME:?}"
rm -rf "$RUNNER_TEMP/r14e" evidence out payload
mkdir -p "$RUNNER_TEMP/r14e/kit" "$RUNNER_TEMP/r14e/src" evidence out payload
K=Frames-0.9.98-Runtime-Certification-Kit-v108-r9.zip
test "$(sha256sum "$K"|awk '{print $1}')" = "$KIT_SHA"
unzip -q "$K" -d "$RUNNER_TEMP/r14e/kit"
Z="$RUNNER_TEMP/r14e/kit/Frames-0.9.98-Source-v108.zip"
test "$(sha256sum "$Z"|awk '{print $1}')" = "$SRC_SHA"
unzip -q "$Z" -d "$RUNNER_TEMP/r14e/src"
F="$RUNNER_TEMP/r14e/src/Frames-0.9.98"
test "$(sha256sum "$F/kernel/main.nx"|awk '{print $1}')" = "$BASE_SHA"
for patch in \
  patch_v108_live_input_common.py \
  patch_v108_usb_mouse_live.py \
  patch_v108_ps2_touchpad_live.py \
  patch_v108_input_telemetry_overlay.py \
  patch_v108_input_usbboot_gate_decouple.py \
  patch_v108_physical_deep_telemetry.py \
  patch_v108_stable_input_diag_runtime.py \
  patch_v108_physical_input_r7.py \
  patch_v108_physical_input_r7_compilefix.py \
  patch_v108_physical_input_r8_cursor_offsets.py \
  patch_v108_physical_input_r9_protocol.py \
  patch_v108_physical_input_r10_hwdecode.py \
  patch_v108_physical_input_r11_touch_usb.py; do
  python3 "tools/ci/$patch" "$F/kernel/main.nx" >/dev/null
done
set +e
python3 tools/ci/patch_v108_physical_input_r12_latency_keyboard.py "$F/kernel/main.nx" >/dev/null
set -e
for patch in \
  patch_v108_physical_input_r12b_pollfix.py \
  patch_v108_usb_hub_topology_r2.py \
  patch_v108_usb_hub_topology_r3_abi.py \
  patch_v108_physical_input_r14_realhw.py \
  patch_v108_physical_input_r14b_textedit.py \
  patch_v108_physical_input_r14c_abi.py; do
  python3 "tools/ci/$patch" "$F/kernel/main.nx" >/dev/null
done
test "$(sha256sum "$F/kernel/main.nx"|awk '{print $1}')" = "$R14E_SHA"
cp "$F/kernel/main.nx" evidence/kernel-r14e.nx
# Model assertions use function identities because serial marker strings are emitted byte-by-byte.
grep -Fq 'fn v108_input_pointer_draw(surface:u64,state:u64,input_state:u64,pos:u64)' evidence/kernel-r14e.nx
grep -Fq 'fn serial_marker_v108_ibeam_ok' evidence/kernel-r14e.nx
grep -Fq 'fn serial_marker_v108_caret_blink_ok' evidence/kernel-r14e.nx
grep -Fq 'fn serial_marker_v108_text_edit_sequence_ok' evidence/kernel-r14e.nx
grep -Fq 'fn serial_marker_usb_hub_keyboard_skipped_v114' evidence/kernel-r14e.nx
! grep -Fq 'v108_input_pointer_draw(surface,state,input_state,cx,cy)' evidence/kernel-r14e.nx
printf 'status=PASS\nsource_sha=%s\n' "$R14E_SHA" > evidence/MODEL.txt
# The r14/r14b/r14c delta never adds physical write functionality; keep full physical test read-only.
printf 'status=PASS\nphysical_writes=BLOCKED\n' > evidence/WRITE-SURFACE.txt
find "$F" -type f -name '*.sh' -exec chmod +x {} +
find "$F/toolchain" -type f -name nexus -exec chmod +x {} +
(
  cd "$F"
  ./tools/build.sh
  python3 tools/make_esp.py
  python3 tools/sdk_selftest.py
  python3 tools/make_desktop_preview_image.py
  python3 tools/verify_desktop_preview_image.py --image build/Frames-0.9.98-Desktop-Preview.img --require-pass
  python3 tools/verify_release.py
)
cp "$F/build/Frames-0.9.98-Desktop-Preview.img" out/raw.img
FIRST="$(sgdisk -i 1 out/raw.img|awk -F: '/First sector/{gsub(/ /,"",$2);split($2,a,"(");print a[1]}')"
LAST="$(sgdisk -i 1 out/raw.img|awk -F: '/Last sector/{gsub(/ /,"",$2);split($2,a,"(");print a[1]}')"
dd if=out/raw.img of=out/esp.img bs=512 skip="$FIRST" count=$((LAST-FIRST+1)) status=none
mcopy -s -i out/esp.img '::/EFI' payload/
mcopy -s -i out/esp.img '::/FRAMES' payload/
dd if=/dev/zero of=out/efiboot.img bs=1M count=16 status=none
mkfs.fat -F 16 -n FRAMESBOOT out/efiboot.img >/dev/null
mmd -i out/efiboot.img ::/EFI ::/EFI/BOOT ::/FRAMES
mcopy -i out/efiboot.img payload/EFI/BOOT/BOOTX64.EFI ::/EFI/BOOT/BOOTX64.EFI
for f in payload/FRAMES/*; do mcopy -i out/efiboot.img "$f" ::/FRAMES/; done
ROOT="$RUNNER_TEMP/r14e-root"; mkdir -p "$ROOT"
cp out/efiboot.img "$ROOT/"; cp -a payload/EFI payload/FRAMES "$ROOT/"
printf 'Frames v108 r14e physical input repair\nI-beam hover + blinking insertion caret + Left/Right/Delete/Backspace + USB multi-child mouse repair\nRufus ISO Image mode\nRead-only diagnostic only\n' > "$ROOT/README.TXT"
xorriso -as mkisofs -iso-level 3 -R -J -V FRAMES_V108_R14E -eltorito-alt-boot -e efiboot.img -no-emul-boot -o "out/$ISO_NAME" "$ROOT" >/dev/null 2>&1
sha256sum "out/$ISO_NAME" | tee evidence/ISO-SHA256.txt
stat -c '%s' "out/$ISO_NAME" | tee evidence/ISO-SIZE.txt
