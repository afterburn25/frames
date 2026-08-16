#!/usr/bin/env python3
from pathlib import Path
import hashlib, sys

if len(sys.argv) != 2:
    raise SystemExit('usage: patch_v108_uefi_approved_splash.py PATH_TO_frames_boot.c')
p = Path(sys.argv[1])
raw = p.read_bytes()
expected = 'c6a373548d4db2cdb62a9c3c5d375ed7677929a4aeb12dc1b1d5bee29a350882'
actual = hashlib.sha256(raw).hexdigest()
if actual != expected:
    raise SystemExit(f'unexpected v108 loader hash: {actual}')
s = raw.decode('utf-8')

gop_anchor = '''typedef struct {\n    void *QueryMode;\n    void *SetMode;\n    void *Blt;\n    EFI_GRAPHICS_OUTPUT_PROTOCOL_MODE *Mode;\n} EFI_GRAPHICS_OUTPUT_PROTOCOL;\n'''
if s.count(gop_anchor) != 1:
    raise SystemExit('GOP type anchor mismatch')
asset_struct = r'''
#pragma pack(push,1)
typedef struct {
    uint8_t magic[8];
    uint32_t width;
    uint32_t height;
    uint32_t stride;
    uint32_t flags;
} FRAMES_SPLASH_ASSET_V1;
#pragma pack(pop)
_Static_assert(sizeof(FRAMES_SPLASH_ASSET_V1)==24, "Frames splash asset header mismatch");
'''
s = s.replace(gop_anchor, gop_anchor + asset_struct, 1)

console_anchor = '''static EFI_SIMPLE_TEXT_OUTPUT_PROTOCOL *gConOut;\nstatic void print16(CHAR16 *s) { if (gConOut && gConOut->OutputString) gConOut->OutputString(gConOut,s); }\nstatic void fatal(CHAR16 *s, EFI_STATUS st) {\n    (void)st;\n    print16(L"\\r\\nFRAMES BOOT ERROR: "); print16(s); print16(L"\\r\\nSystem halted.\\r\\n");\n    for (;;) __asm__ __volatile__("hlt");\n}\n'''
if s.count(console_anchor) != 1:
    raise SystemExit('console anchor mismatch')
render_code = r'''static EFI_SIMPLE_TEXT_OUTPUT_PROTOCOL *gConOut;
static uint64_t gSplashQuiet;
static void print16(CHAR16 *s) { if (!gSplashQuiet && gConOut && gConOut->OutputString) gConOut->OutputString(gConOut,s); }
static uint32_t frames_splash_pixel(uint8_t r,uint8_t g,uint8_t b,uint32_t pixel_format) {
    if(pixel_format==0) return ((uint32_t)b<<16)|((uint32_t)g<<8)|(uint32_t)r;
    return ((uint32_t)r<<16)|((uint32_t)g<<8)|(uint32_t)b;
}
static int frames_splash_render(EFI_GRAPHICS_OUTPUT_PROTOCOL *gop,const void *asset,UINTN asset_size) {
    static const uint8_t magic[8]={'F','S','P','L','1',0,0,0};
    if(!gop || !gop->Mode || !gop->Mode->Info || !gop->Mode->FrameBufferBase || !asset) return 0;
    if(gop->Mode->Info->PixelFormat>1) return 0;
    if(asset_size<sizeof(FRAMES_SPLASH_ASSET_V1)) return 0;
    const FRAMES_SPLASH_ASSET_V1 *h=(const FRAMES_SPLASH_ASSET_V1*)asset;
    if(!mem_equal(h->magic,magic,8) || h->width==0 || h->height==0 || h->stride!=h->width*4 || h->flags!=1) return 0;
    UINTN need=sizeof(*h)+(UINTN)h->stride*(UINTN)h->height;
    if(need>asset_size) return 0;
    uint32_t sw=gop->Mode->Info->HorizontalResolution, sh=gop->Mode->Info->VerticalResolution, stride=gop->Mode->Info->PixelsPerScanLine;
    if(sw==0 || sh==0 || stride<sw || h->width>sw || h->height>sh) return 0;
    uint32_t pf=gop->Mode->Info->PixelFormat;
    volatile uint32_t *fb=(volatile uint32_t*)(uintptr_t)gop->Mode->FrameBufferBase;
    const uint8_t br=8,bg=17,bb=31;
    uint32_t bgpx=frames_splash_pixel(br,bg,bb,pf);
    for(uint32_t y=0;y<sh;y++) for(uint32_t x=0;x<sw;x++) fb[(UINTN)y*stride+x]=bgpx;
    uint32_t ox=(sw-h->width)/2, oy=(sh-h->height)/2;
    const uint8_t *px=(const uint8_t*)asset+sizeof(*h);
    for(uint32_t y=0;y<h->height;y++){
        const uint8_t *row=px+(UINTN)y*h->stride;
        for(uint32_t x=0;x<h->width;x++){
            const uint8_t *q=row+(UINTN)x*4;
            uint32_t a=q[3];
            if(a==0) continue;
            uint8_t r=(uint8_t)(((uint32_t)q[0]*a+(uint32_t)br*(255-a))/255);
            uint8_t g=(uint8_t)(((uint32_t)q[1]*a+(uint32_t)bg*(255-a))/255);
            uint8_t b=(uint8_t)(((uint32_t)q[2]*a+(uint32_t)bb*(255-a))/255);
            fb[(UINTN)(oy+y)*stride+(ox+x)]=frames_splash_pixel(r,g,b,pf);
        }
    }
    uint32_t barw=sw/9; if(barw<64) barw=64; if(barw>160) barw=160;
    uint32_t barx=(sw-barw)/2, bary=oy+h->height+24;
    if(bary+3<sh){
        uint32_t accent=frames_splash_pixel(62,142,255,pf);
        for(uint32_t y=0;y<3;y++) for(uint32_t x=0;x<barw;x++) fb[(UINTN)(bary+y)*stride+barx+x]=accent;
    }
    return 1;
}
static void fatal(CHAR16 *s, EFI_STATUS st) {
    (void)st;
    gSplashQuiet=0;
    if(gConOut && gConOut->ClearScreen) gConOut->ClearScreen(gConOut);
    print16(L"\r\nFRAMES BOOT ERROR: "); print16(s); print16(L"\r\nSystem halted.\r\n");
    for (;;) __asm__ __volatile__("hlt");
}
'''
s = s.replace(console_anchor, render_code, 1)

entry_anchor = '''EFI_STATUS EFIAPI efi_main(EFI_HANDLE image, EFI_SYSTEM_TABLE *st) {\n    EFI_BOOT_SERVICES *bs=st->BootServices; gConOut=st->ConOut;\n    if (gConOut && gConOut->ClearScreen) gConOut->ClearScreen(gConOut);\n    print16(L"FRAMES 0.9.98\\r\\n");\n    print16(L"Independent Nexus Operating System Bootstrap\\r\\n\\r\\n");\n    print16(L"[1/8] UEFI loader started\\r\\n");\n'''
if s.count(entry_anchor) != 1:
    raise SystemExit('efi_main entry anchor mismatch')
entry_repl = r'''EFI_STATUS EFIAPI efi_main(EFI_HANDLE image, EFI_SYSTEM_TABLE *st) {
    EFI_BOOT_SERVICES *bs=st->BootServices; gConOut=st->ConOut;
    if (gConOut && gConOut->ClearScreen) gConOut->ClearScreen(gConOut);
    EFI_GRAPHICS_OUTPUT_PROTOCOL *gop=0; bs->LocateProtocol(&gGraphicsOutputProtocolGuid,0,(void**)&gop);
    void *splash_file=0; UINTN splash_file_size=0;
    EFI_STATUS splash_status=load_file(bs,image,L"\\Frames\\SPLASH.FSP",&splash_file,&splash_file_size);
    if(!EFI_ERROR(splash_status) && frames_splash_render(gop,splash_file,splash_file_size)){
        gSplashQuiet=1;
        if(bs->Stall){ typedef EFI_STATUS (EFIAPI *EFI_STALL_FN)(UINTN); ((EFI_STALL_FN)bs->Stall)(600000); }
    }
    print16(L"FRAMES 0.9.98\r\n");
    print16(L"Independent Nexus Operating System Bootstrap\r\n\r\n");
    print16(L"[1/8] UEFI loader started\r\n");
'''
s = s.replace(entry_anchor, entry_repl, 1)

late_gop = '    EFI_GRAPHICS_OUTPUT_PROTOCOL *gop=0; bs->LocateProtocol(&gGraphicsOutputProtocolGuid,0,(void**)&gop);\n'
if s.count(late_gop) != 2:
    raise SystemExit(f'late GOP anchor mismatch count={s.count(late_gop)}')
pos=s.rfind(late_gop)
s=s[:pos]+'    if(!gop) bs->LocateProtocol(&gGraphicsOutputProtocolGuid,0,(void**)&gop);\n'+s[pos+len(late_gop):]

p.write_text(s)
print('patched exact v108 loader with approved Boot Splash Phase 1 renderer')
print('base_sha256='+actual)
print('patched_sha256='+hashlib.sha256(p.read_bytes()).hexdigest())
