#!/usr/bin/env python3
from pathlib import Path
import hashlib, sys

product = Path(sys.argv[1])
p = product / 'boot/uefi/frames_boot.c'
logo = product / 'assets/branding/FramesLogo-48.rgba'
if not p.is_file():
    raise SystemExit(f'loader source missing: {p}')
if not logo.is_file():
    raise SystemExit(f'canonical logo missing: {logo}')
raw = logo.read_bytes()
if len(raw) != 48 * 48 * 4:
    raise SystemExit(f'unexpected FramesLogo-48.rgba size: {len(raw)}')
logo_sha = hashlib.sha256(raw).hexdigest()
logo_bytes = ','.join(f'0x{x:02x}' for x in raw)

s = p.read_text()
helper_anchor = 'static void print16(CHAR16 *s) { if (gConOut && gConOut->OutputString) gConOut->OutputString(gConOut,s); }\n'
if helper_anchor not in s:
    raise SystemExit('print16 helper anchor missing')

helpers = f'''static EFI_GRAPHICS_OUTPUT_PROTOCOL *gFramesGop;\nstatic const char gFramesCanonicalLogoIdentity[] __attribute__((used)) = "FRAMES_CANONICAL_LOGO_48_RGBA_SHA256={logo_sha}";\nstatic const uint8_t gFramesCanonicalLogo48[48*48*4] = {{{logo_bytes}}};\n\nstatic inline void frames_out8(uint16_t port,uint8_t value){{ __asm__ __volatile__("outb %0,%1"::"a"(value),"Nd"(port)); }}\nstatic inline uint8_t frames_in8(uint16_t port){{ uint8_t v; __asm__ __volatile__("inb %1,%0":"=a"(v):"Nd"(port)); return v; }}\nstatic void frames_serial_init(void){{\n    frames_out8(0x3f8+1,0x00); frames_out8(0x3f8+3,0x80); frames_out8(0x3f8+0,0x03); frames_out8(0x3f8+1,0x00);\n    frames_out8(0x3f8+3,0x03); frames_out8(0x3f8+2,0xc7); frames_out8(0x3f8+4,0x0b);\n}}\nstatic void frames_serial_putc(char c){{ for(uint32_t i=0;i<100000;i++){{ if(frames_in8(0x3f8+5)&0x20){{ frames_out8(0x3f8,c); return; }} }} }}\nstatic void frames_serial_write(const char *q){{ if(!q)return; while(*q)frames_serial_putc(*q++); }}\nstatic uint32_t frames_rgb(uint8_t r,uint8_t g,uint8_t b){{\n    if(!gFramesGop || !gFramesGop->Mode || !gFramesGop->Mode->Info) return 0;\n    return gFramesGop->Mode->Info->PixelFormat==1 ? ((uint32_t)b<<16)|((uint32_t)g<<8)|r : ((uint32_t)r<<16)|((uint32_t)g<<8)|b;\n}}\nstatic void frames_rect(uint32_t x,uint32_t y,uint32_t w,uint32_t h,uint32_t c){{\n    if(!gFramesGop || !gFramesGop->Mode || !gFramesGop->Mode->Info || !gFramesGop->Mode->FrameBufferBase)return;\n    uint32_t sw=gFramesGop->Mode->Info->HorizontalResolution, sh=gFramesGop->Mode->Info->VerticalResolution, stride=gFramesGop->Mode->Info->PixelsPerScanLine;\n    if(x>=sw||y>=sh)return; if(x+w>sw)w=sw-x; if(y+h>sh)h=sh-y;\n    volatile uint32_t *fb=(volatile uint32_t*)(uintptr_t)gFramesGop->Mode->FrameBufferBase;\n    for(uint32_t yy=0;yy<h;yy++) for(uint32_t xx=0;xx<w;xx++) fb[(uint64_t)(y+yy)*stride+x+xx]=c;\n}}\nstatic void frames_logo(uint32_t cx,uint32_t cy,uint32_t scale){{\n    if(!gFramesGop || !gFramesGop->Mode || !gFramesGop->Mode->Info || !gFramesGop->Mode->FrameBufferBase)return;\n    if(scale<1)scale=1; if(scale>6)scale=6;\n    uint32_t sw=gFramesGop->Mode->Info->HorizontalResolution, sh=gFramesGop->Mode->Info->VerticalResolution, stride=gFramesGop->Mode->Info->PixelsPerScanLine;\n    int32_t ox=(int32_t)cx-(int32_t)(48*scale)/2, oy=(int32_t)cy-(int32_t)(48*scale)/2;\n    volatile uint32_t *fb=(volatile uint32_t*)(uintptr_t)gFramesGop->Mode->FrameBufferBase;\n    for(uint32_t sy=0;sy<48;sy++) for(uint32_t sx=0;sx<48;sx++){{\n        const uint8_t *q=&gFramesCanonicalLogo48[(sy*48+sx)*4]; uint8_t a=q[3]; if(a<8)continue;\n        uint32_t c=frames_rgb(q[0],q[1],q[2]);\n        for(uint32_t yy=0;yy<scale;yy++) for(uint32_t xx=0;xx<scale;xx++){{\n            int32_t dx=ox+(int32_t)(sx*scale+xx), dy=oy+(int32_t)(sy*scale+yy);\n            if(dx>=0 && dy>=0 && (uint32_t)dx<sw && (uint32_t)dy<sh) fb[(uint64_t)(uint32_t)dy*stride+(uint32_t)dx]=c;\n        }}\n    }}\n}}\nstatic void frames_splash(uint32_t pct){{\n    if(!gFramesGop || !gFramesGop->Mode || !gFramesGop->Mode->Info)return;\n    uint32_t w=gFramesGop->Mode->Info->HorizontalResolution, h=gFramesGop->Mode->Info->VerticalResolution; if(w<320||h<240)return;\n    frames_rect(0,0,w,h,frames_rgb(8,13,24));\n    uint32_t scale=h>=900?5:(h>=700?4:3); frames_logo(w/2,h*38/100,scale);\n    uint32_t bw=w*44/100, bh=h/70; if(bh<8)bh=8; if(bh>18)bh=18; uint32_t bx=(w-bw)/2, by=h*68/100;\n    frames_rect(bx-2,by-2,bw+4,bh+4,frames_rgb(39,48,66)); frames_rect(bx,by,bw,bh,frames_rgb(17,24,37));\n    if(pct>100)pct=100; frames_rect(bx,by,(bw*pct)/100,bh,frames_rgb(52,142,255));\n}}\nstatic void frames_stage(uint32_t pct,const char *marker,CHAR16 *fallback){{ frames_serial_write(marker); if(gFramesGop)frames_splash(pct); else if(fallback)print16(fallback); }}\n'''
s = s.replace(helper_anchor, helper_anchor + helpers, 1)

start_anchor = '''EFI_STATUS EFIAPI efi_main(EFI_HANDLE image, EFI_SYSTEM_TABLE *st) {
    EFI_BOOT_SERVICES *bs=st->BootServices; gConOut=st->ConOut;
    if (gConOut && gConOut->ClearScreen) gConOut->ClearScreen(gConOut);
    print16(L"FRAMES 0.9.91\\r\\n");
    print16(L"Independent Nexus Operating System Bootstrap\\r\\n\\r\\n");
    print16(L"[1/8] UEFI loader started\\r\\n");
    if (bs->SetWatchdogTimer) bs->SetWatchdogTimer(0,0,0,0);
'''
start_replacement = '''EFI_STATUS EFIAPI efi_main(EFI_HANDLE image, EFI_SYSTEM_TABLE *st) {
    EFI_BOOT_SERVICES *bs=st->BootServices; gConOut=st->ConOut;
    if (bs->SetWatchdogTimer) bs->SetWatchdogTimer(0,0,0,0);
    frames_serial_init(); frames_serial_write("FRAMES_HANDOFF_LOADER_START\\n");
    EFI_GRAPHICS_OUTPUT_PROTOCOL *gop=0;
    if(bs->LocateProtocol && !EFI_ERROR(bs->LocateProtocol(&gGraphicsOutputProtocolGuid,0,(void**)&gop)) && gop && gop->Mode && gop->Mode->Info){ gFramesGop=gop; frames_splash(5); }
    else { if (gConOut && gConOut->ClearScreen) gConOut->ClearScreen(gConOut); print16(L"FRAMES 0.9.91\\r\\nIndependent Nexus Operating System Bootstrap\\r\\n\\r\\n[1/8] UEFI loader started\\r\\n"); }
'''
if start_anchor not in s:
    raise SystemExit('efi_main structural start anchor missing')
s = s.replace(start_anchor, start_replacement, 1)

stage_pairs = [
('    print16(L"[2/8] FramesKernel.fkrn loaded\\r\\n");','    frames_stage(16,"FRAMES_SPLASH_KERNEL_LOADED\\n",L"[2/8] FramesKernel.fkrn loaded\\r\\n");'),
('    print16(L"[3/8] FKRN64 header and SHA-256 verified\\r\\n");','    frames_stage(30,"FRAMES_SPLASH_KERNEL_VERIFIED\\n",L"[3/8] FKRN64 header and SHA-256 verified\\r\\n");'),
('    print16(L"[4/8] System.fex loaded and FEX64 SHA-256 verified\\r\\n");','    frames_stage(44,"FRAMES_SPLASH_SYSTEM_VERIFIED\\n",L"[4/8] System.fex loaded and FEX64 SHA-256 verified\\r\\n");'),
('    print16(L"[5/8] Nexus kernel code loaded into executable memory\\r\\n");','    frames_stage(60,"FRAMES_SPLASH_KERNEL_EXEC_READY\\n",L"[5/8] Nexus kernel code loaded into executable memory\\r\\n");'),
]
for old,new in stage_pairs:
    if old not in s: raise SystemExit('stage anchor missing: '+old)
    s=s.replace(old,new,1)

late_gop='    EFI_GRAPHICS_OUTPUT_PROTOCOL *gop=0; bs->LocateProtocol(&gGraphicsOutputProtocolGuid,0,(void**)&gop);'
if late_gop not in s: raise SystemExit('late GOP anchor missing')
s=s.replace(late_gop,'    if(!gop) bs->LocateProtocol(&gGraphicsOutputProtocolGuid,0,(void**)&gop); if(gop) gFramesGop=gop;',1)

last_pair='''    print16(L"[7/8] BootInfoV4, verified boot modules, ACPI, framebuffer, and memory-map buffers prepared\\r\\n");
    print16(L"[8/8] Exiting UEFI boot services and entering Nexus kernel...\\r\\n");'''
last_repl='''    frames_stage(82,"FRAMES_SPLASH_BOOTINFO_READY\\n",L"[7/8] BootInfoV4, verified boot modules, ACPI, framebuffer, and memory-map buffers prepared\\r\\n");
    frames_stage(88,"FRAMES_HANDOFF_PRE_EBS\\n",L"[8/8] Exiting UEFI boot services and entering Nexus kernel...\\r\\n");'''
if last_pair not in s: raise SystemExit('final stage anchors missing')
s=s.replace(last_pair,last_repl,1)

old_tail='''    if(EFI_ERROR(s)) for(;;)__asm__ __volatile__("hlt");

    /* Frames Kernel ABI 4 transition contract: RCX = FramesBootInfoV4*. Nexus 5.10 consumes this as a typed &FramesBootInfoV4 parameter. */
    kernel_entry(bi);
'''
new_tail='''    if(EFI_ERROR(s)) { frames_serial_write("FRAMES_HANDOFF_EBS_FAILED\\n"); for(;;)__asm__ __volatile__("hlt"); }
    frames_serial_write("FRAMES_HANDOFF_POST_EBS\\n"); frames_splash(94);

    /* Frames Kernel ABI 4 transition contract: RCX = FramesBootInfoV4*. Nexus 5.10 consumes this as a typed &FramesBootInfoV4 parameter. */
    frames_serial_write("FRAMES_HANDOFF_KERNEL_CALL\\n"); frames_splash(96);
    kernel_entry(bi);
'''
if old_tail not in s: raise SystemExit('handoff tail anchor missing')
s=s.replace(old_tail,new_tail,1)

old_fatal='''static void fatal(CHAR16 *s, EFI_STATUS st) {
    (void)st;
    print16(L"\\r\\nFRAMES BOOT ERROR: "); print16(s); print16(L"\\r\\nSystem halted.\\r\\n");
'''
new_fatal='''static void fatal(CHAR16 *s, EFI_STATUS st) {
    (void)st; frames_serial_write("FRAMES_BOOT_FATAL\\n");
    if(gConOut && gConOut->ClearScreen) gConOut->ClearScreen(gConOut);
    print16(L"\\r\\nFRAMES BOOT ERROR: "); print16(s); print16(L"\\r\\nSystem halted.\\r\\n");
'''
if old_fatal not in s: raise SystemExit('fatal anchor missing')
s=s.replace(old_fatal,new_fatal,1)

p.write_text(s)
print('patched', p)
print('canonical_logo_sha256', logo_sha)
