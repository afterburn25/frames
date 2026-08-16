#!/usr/bin/env bash
set -euo pipefail
lane="$1"; cand="$2"; ovmf="${3:-}"
if [[ "$lane" != model && -z "$ovmf" ]]; then ovmf="$(find /usr/share/OVMF -type f \( -name OVMF_CODE_4M.fd -o -name OVMF_CODE.fd \) | head -n1)"; test -s "$ovmf"; fi
ISO_NAME=Frames-0.9.98-v108-Physical-Input-Repair-r18-USB-xHCI-Menu-Stability-Rufus-UEFI.iso
R18_SHA=dd0386720bba6dce4c1fd0576e995dd6a2932638633147914589b342cc3dfe22
mkdir -p gate; ISO="$(find "$cand" -name "$ISO_NAME" -type f -print -quit)"; test -s "$ISO"; EXPECT="$(awk '{print $1}' "$cand/evidence/ISO-SHA256.txt")"; test "$(sha256sum "$ISO"|awk '{print $1}')" = "$EXPECT"
case "$lane" in
 usb-direct) python3 tools/ci/qemu_usb_hub_topology_gate_r3.py --ovmf "$ovmf" --iso "$ISO" --out gate --expected-iso-sha "$EXPECT" --topology direct; grep -q '"status": "PASS"' gate/TOPOLOGY.json;;
 usb-hub) python3 tools/ci/qemu_usb_hub_topology_gate_r3.py --ovmf "$ovmf" --iso "$ISO" --out gate --expected-iso-sha "$EXPECT" --topology hub; grep -q '"status": "PASS"' gate/TOPOLOGY.json;;
 usb-hub-multi) python3 tools/ci/qemu_usb_hub_multichild_gate_r17.py --ovmf "$ovmf" --iso "$ISO" --out gate --expected-iso-sha "$EXPECT"; grep -q '"status": "PASS"' gate/MULTICHILD-R17.json;;
 usb-multicontroller) python3 tools/ci/qemu_usb_multicontroller_gate_r16.py --ovmf "$ovmf" --iso "$ISO" --out gate --expected-iso-sha "$EXPECT"; grep -q '"status": "PASS"' gate/USB-MULTICONTROLLER.json;;
 usb-keyboard) python3 tools/ci/qemu_usb_keyboard_gate_r17.py --ovmf "$ovmf" --iso "$ISO" --out gate --expected-iso-sha "$EXPECT"; grep -q '"status": "PASS"' gate/USB-KEYBOARD.json;;
 ps2) python3 tools/ci/qemu_ps2_delivery_gate_r17.py --ovmf "$ovmf" --iso "$ISO" --out gate --expected-iso-sha "$EXPECT"; grep -q '"status": "PASS"' gate/PS2-DELIVERY.json;;
 smoothness) python3 tools/ci/qemu_ps2_cursor_smoothness_r10.py --ovmf "$ovmf" --iso "$ISO" --out gate --expected-iso-sha "$EXPECT"; grep -q '"status": "PASS"' gate/SMOOTHNESS.json;;
 text-edit) python3 tools/ci/qemu_text_edit_gate_r15.py --ovmf "$ovmf" --iso "$ISO" --out gate --expected-iso-sha "$EXPECT"; grep -q '"status": "PASS"' gate/TEXT-EDIT.json;;
 focus-persistence) python3 tools/ci/qemu_focus_persistence_gate_r17.py --ovmf "$ovmf" --iso "$ISO" --out gate --expected-iso-sha "$EXPECT"; grep -q '"status": "PASS"' gate/FOCUS-PERSISTENCE.json;;
 context-menu) python3 tools/ci/qemu_context_menu_gate_r18.py --ovmf "$ovmf" --iso "$ISO" --out gate --expected-iso-sha "$EXPECT"; grep -q '"status": "PASS"' gate/CONTEXT-MENU.json;;
 desktop-interaction) python3 tools/ci/qemu_desktop_interaction_gate_r17.py --ovmf "$ovmf" --iso "$ISO" --out gate --expected-iso-sha "$EXPECT"; grep -q '"status": "PASS"' gate/DESKTOP-INTERACTION.json;;
 model)
  K="$cand/evidence/kernel-r18.nx"; test "$(sha256sum "$K"|awk '{print $1}')" = "$R18_SHA"
  for pat in 'fn xhci_legacy_handoff_v118' 'scratch_count=scratch_lo+(scratch_hi*32)' 'volatile_write64(xhci_state+1240,3)' 'volatile_write64(xhci_state+1240,6)' 'fn v108_context_hit_v118(state:u64,x:u64,y:u64)' 'fn v108_desktop_context_draw_v118' 'serial_marker_v108_context_outside_ok' 'fn v108_text_menuitem_v118' 'volatile_write64(input_state+4056,read_tsc())' 'now_idle-moved>180000000'; do grep -Fq "$pat" "$K"; done;;
 safety)
  truncate -s 32M gate/sentinel.img; before="$(sha256sum gate/sentinel.img|awk '{print $1}')"; set +e; timeout 90 qemu-system-x86_64 -machine q35 -m 768M -smp 2 -cpu max -accel tcg,thread=single -display none -no-reboot -no-shutdown -nic none -serial file:gate/serial.log -drive if=pflash,format=raw,readonly=on,file="$ovmf" -cdrom "$ISO" -boot d -drive file=gate/sentinel.img,if=none,format=raw,readonly=on,id=s -device nvme,drive=s,serial=R18_SENTINEL >/dev/null 2>gate/stderr; rc=$?; set -e; after="$(sha256sum gate/sentinel.img|awk '{print $1}')"; test "$before" = "$after"; grep -q FRAMES_V108_INPUT_TEST_RUNTIME_READY gate/serial.log; printf 'qemu_rc=%s\nbefore=%s\nafter=%s\n' "$rc" "$before" "$after" > gate/SAFETY.txt;;
 *) exit 2;;
esac
echo PASS > gate/RESULT.status; sha256sum gate/* 2>/dev/null > gate/SHA256SUMS.txt || true
