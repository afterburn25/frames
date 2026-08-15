#!/usr/bin/env python3
from pathlib import Path
import sys

product = Path(sys.argv[1])
p = product / 'boot/uefi/frames_boot.c'
if not p.is_file():
    raise SystemExit(f'loader source missing: {p}')
s = p.read_text()

helper_anchor = 'static void print16(CHAR16 *s) { if (gConOut && gConOut->OutputString) gConOut->OutputString(gConOut,s); }\n'
if helper_anchor not in s:
    raise SystemExit('print16 helper anchor missing')
helpers = r'''
static inline void frames_diag_out8(uint16_t port,uint8_t value){ __asm__ __volatile__("outb %0,%1"::"a"(value),"Nd"(port)); }
static inline uint8_t frames_diag_in8(uint16_t port){ uint8_t v; __asm__ __volatile__("inb %1,%0":"=a"(v):"Nd"(port)); return v; }
static void frames_diag_serial_init(void){
    frames_diag_out8(0x3f8+1,0x00); frames_diag_out8(0x3f8+3,0x80); frames_diag_out8(0x3f8+0,0x03); frames_diag_out8(0x3f8+1,0x00);
    frames_diag_out8(0x3f8+3,0x03); frames_diag_out8(0x3f8+2,0xc7); frames_diag_out8(0x3f8+4,0x0b);
}
static void frames_diag_putc(char c){ for(uint32_t i=0;i<100000;i++){ if(frames_diag_in8(0x3f8+5)&0x20){ frames_diag_out8(0x3f8,c); return; } } }
static void frames_diag_write(const char *q){ if(!q)return; while(*q)frames_diag_putc(*q++); }
static void frames_diag_box(EFI_GRAPHICS_OUTPUT_PROTOCOL *gop,uint32_t slot,uint32_t rgb){
    if(!gop || !gop->Mode || !gop->Mode->Info || !gop->Mode->FrameBufferBase)return;
    uint32_t sw=gop->Mode->Info->HorizontalResolution, sh=gop->Mode->Info->VerticalResolution, stride=gop->Mode->Info->PixelsPerScanLine;
    if(sw<80 || sh<24)return;
    volatile uint32_t *fb=(volatile uint32_t*)(uintptr_t)gop->Mode->FrameBufferBase;
    uint32_t x=8+slot*22, y=8;
    for(uint32_t yy=0;yy<16;yy++) for(uint32_t xx=0;xx<16;xx++) fb[(uint64_t)(y+yy)*stride+x+xx]=rgb;
}
'''
s = s.replace(helper_anchor, helper_anchor + helpers, 1)

start = 'EFI_STATUS EFIAPI efi_main(EFI_HANDLE image, EFI_SYSTEM_TABLE *st) {\n    EFI_BOOT_SERVICES *bs=st->BootServices; gConOut=st->ConOut;\n'
repl = 'EFI_STATUS EFIAPI efi_main(EFI_HANDLE image, EFI_SYSTEM_TABLE *st) {\n    EFI_BOOT_SERVICES *bs=st->BootServices; gConOut=st->ConOut;\n    frames_diag_serial_init(); frames_diag_write("FRAMES_FREEZE_LOADER_ENTRY\\n");\n'
if start not in s:
    raise SystemExit('efi_main anchor missing')
s = s.replace(start, repl, 1)

pairs = [
('    print16(L"[2/8] FramesKernel.fkrn loaded\\r\\n");','    print16(L"[2/8] FramesKernel.fkrn loaded\\r\\n"); frames_diag_write("FRAMES_FREEZE_KERNEL_FILE_LOADED\\n");'),
('    print16(L"[3/8] FKRN64 header and SHA-256 verified\\r\\n");','    print16(L"[3/8] FKRN64 header and SHA-256 verified\\r\\n"); frames_diag_write("FRAMES_FREEZE_KERNEL_VERIFIED\\n");'),
('    print16(L"[4/8] System.fex loaded and FEX64 SHA-256 verified\\r\\n");','    print16(L"[4/8] System.fex loaded and FEX64 SHA-256 verified\\r\\n"); frames_diag_write("FRAMES_FREEZE_SYSTEM_VERIFIED\\n");'),
('    print16(L"[5/8] Nexus kernel code loaded into executable memory\\r\\n");','    print16(L"[5/8] Nexus kernel code loaded into executable memory\\r\\n"); frames_diag_write("FRAMES_FREEZE_KERNEL_EXEC_READY\\n");'),
('    print16(L"[7/8] BootInfoV4, verified boot modules, ACPI, framebuffer, and memory-map buffers prepared\\r\\n");','    print16(L"[7/8] BootInfoV4, verified boot modules, ACPI, framebuffer, and memory-map buffers prepared\\r\\n"); frames_diag_write("FRAMES_FREEZE_BOOTINFO_READY\\n");'),
('    print16(L"[8/8] Exiting UEFI boot services and entering Nexus kernel...\\r\\n");','    print16(L"[8/8] Exiting UEFI boot services and entering Nexus kernel...\\r\\n"); frames_diag_write("FRAMES_FREEZE_PRE_EBS\\n"); frames_diag_box(gop,0,0x00ffff00u);')
]
for old,new in pairs:
    if old not in s:
        raise SystemExit('stage anchor missing: '+old)
    s=s.replace(old,new,1)

old_tail='''    if(EFI_ERROR(s)) for(;;)__asm__ __volatile__("hlt");

    /* Frames Kernel ABI 4 transition contract: RCX = FramesBootInfoV4*. Nexus 5.10 consumes this as a typed &FramesBootInfoV4 parameter. */
    kernel_entry(bi);
'''
new_tail='''    if(EFI_ERROR(s)) { frames_diag_write("FRAMES_FREEZE_EBS_FAILED\\n"); for(;;)__asm__ __volatile__("hlt"); }
    frames_diag_write("FRAMES_FREEZE_POST_EBS\\n"); frames_diag_box(gop,1,0x0000ffffu);

    /* Frames Kernel ABI 4 transition contract: RCX = FramesBootInfoV4*. Nexus 5.10 consumes this as a typed &FramesBootInfoV4 parameter. */
    frames_diag_write("FRAMES_FREEZE_KERNEL_CALL\\n"); frames_diag_box(gop,2,0x00ff00ffu);
    kernel_entry(bi);
'''
if old_tail not in s:
    raise SystemExit('handoff tail anchor missing')
s=s.replace(old_tail,new_tail,1)

p.write_text(s)
print('freeze-isolation loader breadcrumbs applied')
