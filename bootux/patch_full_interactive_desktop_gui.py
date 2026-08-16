#!/usr/bin/env python3
from pathlib import Path
import hashlib, sys

if len(sys.argv) != 2:
    raise SystemExit('usage: patch_full_interactive_desktop_gui.py PATH_TO_main.nx')

p = Path(sys.argv[1])
raw = p.read_bytes()
expected = 'df33322fc01b2fc25c5e46012dcd143b3d089a9a969409ad45e9a66650268896'
actual = hashlib.sha256(raw).hexdigest()
if actual != expected:
    raise SystemExit(f'unexpected GUI-test v116 kernel hash: {actual}')
text = raw.decode('utf-8')

anchor = 'fn appearance_system_phase1_compose(state:u64,surface:u64,process:u64,wm:u64) -> u64 {'
if text.count(anchor) != 1:
    raise SystemExit('appearance_system_phase1_compose anchor mismatch')

full_gui = r'''fn serial_marker_full_gui_windows_ok() -> void { serial_putc(70); serial_putc(82); serial_putc(65); serial_putc(77); serial_putc(69); serial_putc(83); serial_putc(95); serial_putc(70); serial_putc(85); serial_putc(76); serial_putc(76); serial_putc(95); serial_putc(71); serial_putc(85); serial_putc(73); serial_putc(95); serial_putc(87); serial_putc(73); serial_putc(78); serial_putc(68); serial_putc(79); serial_putc(87); serial_putc(83); serial_putc(95); serial_putc(79); serial_putc(75); serial_putc(10); return; }
fn serial_marker_full_gui_input_ok() -> void { serial_putc(70); serial_putc(82); serial_putc(65); serial_putc(77); serial_putc(69); serial_putc(83); serial_putc(95); serial_putc(70); serial_putc(85); serial_putc(76); serial_putc(76); serial_putc(95); serial_putc(71); serial_putc(85); serial_putc(73); serial_putc(95); serial_putc(73); serial_putc(78); serial_putc(80); serial_putc(85); serial_putc(84); serial_putc(95); serial_putc(79); serial_putc(75); serial_putc(10); return; }
fn serial_marker_full_gui_fileman_ok() -> void { serial_putc(70); serial_putc(82); serial_putc(65); serial_putc(77); serial_putc(69); serial_putc(83); serial_putc(95); serial_putc(70); serial_putc(85); serial_putc(76); serial_putc(76); serial_putc(95); serial_putc(71); serial_putc(85); serial_putc(73); serial_putc(95); serial_putc(70); serial_putc(73); serial_putc(76); serial_putc(69); serial_putc(77); serial_putc(65); serial_putc(78); serial_putc(95); serial_putc(79); serial_putc(75); serial_putc(10); return; }
fn serial_marker_full_gui_settings_ok() -> void { serial_putc(70); serial_putc(82); serial_putc(65); serial_putc(77); serial_putc(69); serial_putc(83); serial_putc(95); serial_putc(70); serial_putc(85); serial_putc(76); serial_putc(76); serial_putc(95); serial_putc(71); serial_putc(85); serial_putc(73); serial_putc(95); serial_putc(83); serial_putc(69); serial_putc(84); serial_putc(84); serial_putc(73); serial_putc(78); serial_putc(71); serial_putc(83); serial_putc(95); serial_putc(79); serial_putc(75); serial_putc(10); return; }
fn serial_marker_full_interactive_desktop_ok() -> void { serial_putc(70); serial_putc(82); serial_putc(65); serial_putc(77); serial_putc(69); serial_putc(83); serial_putc(95); serial_putc(70); serial_putc(85); serial_putc(76); serial_putc(76); serial_putc(95); serial_putc(73); serial_putc(78); serial_putc(84); serial_putc(69); serial_putc(82); serial_putc(65); serial_putc(67); serial_putc(84); serial_putc(73); serial_putc(86); serial_putc(69); serial_putc(95); serial_putc(68); serial_putc(69); serial_putc(83); serial_putc(75); serial_putc(84); serial_putc(79); serial_putc(80); serial_putc(95); serial_putc(79); serial_putc(75); serial_putc(10); return; }

fn full_interactive_desktop_compose(state:u64,surface:u64,process:u64,wm:u64) -> u64 {
    if state==0 || surface==0 || process==0 || wm==0 { return 0; }
    let w=volatile_read64(surface+16); let h=volatile_read64(surface+24); if w<1024 || h<700 { return 0; }
    let panel_y=volatile_read64(wm+72); if panel_y<560 || panel_y>=h { return 0; }
    let panel=appearance_color(state,40); let surfacec=appearance_color(state,48); let surface2=appearance_color(state,56);
    let textc=appearance_color(state,64); let muted=appearance_color(state,72); let focus=appearance_color(state,80); let accent=appearance_color(state,8); let accent2=appearance_color(state,16);
    if panel==0 || surfacec==0 || surface2==0 || textc==0 || accent==0 { return 0; }

    // Repaint only the desktop wallpaper and taskbar. Do not call appearance_home:
    // that dashboard view is what previously covered the real window manager.
    if appearance_wallpaper(surface,state)==0 { return 0; }
    if display_fill_rect(surface,(0*65536)+panel_y,(w*65536)+(h-panel_y),panel)==0 { return 0; }
    if display_fill_rect(surface,(0*65536)+panel_y,(w*65536)+2,accent)==0 { return 0; }
    if appearance_logo(surface,state,(16*65536)+(panel_y+5),1)==0 { return 0; }
    if gui_text_frames(surface,72,panel_y+19,textc)==0 { return 0; }
    if gui_draw_icon(surface,(170*65536)+(panel_y+14),2,accent)==0 { return 0; }
    if gui_draw_icon(surface,(214*65536)+(panel_y+14),3,accent2)==0 { return 0; }
    if gui_draw_icon(surface,(258*65536)+(panel_y+14),1,focus)==0 { return 0; }
    if display_fill_rect(surface,((w-164)*65536)+(panel_y+19),(54*65536)+6,muted)==0 { return 0; }
    if display_fill_rect(surface,((w-94)*65536)+(panel_y+19),(38*65536)+6,accent)==0 { return 0; }

    // Desktop shortcuts remain visible behind the windows.
    if gui_draw_icon(surface,(30*65536)+88,2,accent)==0 || gui_text_files(surface,24,122,textc)==0 { return 0; }
    if gui_draw_icon(surface,(30*65536)+164,3,accent2)==0 || gui_text_nexus(surface,24,198,textc)==0 { return 0; }
    if gui_draw_icon(surface,(30*65536)+240,1,focus)==0 || gui_text_settings(surface,18,274,textc)==0 { return 0; }

    // The existing certified desktop created five real windows. Re-layout those
    // exact records into a usable desktop and exercise focus/move/resize.
    var id:u64=1; while id<=5 { if wm_record(wm,id)==0 { return 0; } id=id+1; }
    if wm_move(wm,1,(590*65536)+70)==0 || wm_resize(wm,1,(560*65536)+360)==0 { return 0; }
    if wm_move(wm,2,(650*65536)+96)==0 || wm_resize(wm,2,(500*65536)+350)==0 { return 0; }
    if wm_move(wm,3,(430*65536)+82)==0 || wm_resize(wm,3,(650*65536)+420)==0 { return 0; }
    if wm_move(wm,4,(82*65536)+112)==0 || wm_resize(wm,4,(710*65536)+500)==0 { return 0; }
    if wm_move(wm,5,(770*65536)+172)==0 || wm_resize(wm,5,(430*65536)+410)==0 { return 0; }
    if wm_focus(wm,5)==0 { return 0; }
    let input=volatile_read64(process+1072); if input==0 || gui_input_focus(input,wm,5)==0 || gui_input_focus(input,wm,4)==0 { return 0; }
    serial_marker_full_gui_input_ok();
    if wm_focus(wm,4)==0 || volatile_read64(wm+16)!=4 { return 0; }
    let r5=wm_record(wm,5); if volatile_read64(r5+8)!=770 || volatile_read64(r5+24)!=430 { return 0; }
    serial_marker_full_gui_windows_ok();

    let dirty=volatile_read64(process+624); if dirty==0 { return 0; }
    if wm_render_all(wm,surface,dirty)<5 { return 0; }

    // Nexus / native app window content (window 3) behind the File Manager.
    let r3=wm_record(wm,3); let x3=volatile_read64(r3+8); let y3=volatile_read64(r3+16); let w3=volatile_read64(r3+24); let h3=volatile_read64(r3+32);
    if gui_text_nexus_ide(surface,x3+20,y3+14,textc)==0 { return 0; }
    if display_fill_rect(surface,((x3+14)*65536)+(y3+50),(150*65536)+(h3-66),surfacec)==0 { return 0; }
    if display_fill_rect(surface,((x3+178)*65536)+(y3+50),((w3-194)*65536)+(h3-190),surface2)==0 { return 0; }
    var cl:u64=0; while cl<12 { var cc=accent; if cl%3==1 { cc=focus; } if cl%3==2 { cc=muted; } if display_fill_rect(surface,((x3+198+(cl%4)*12)*65536)+(y3+72+(cl*20)),((150+(cl%5)*24)*65536)+4,cc)==0 { return 0; } cl=cl+1; }
    if display_fill_rect(surface,((x3+178)*65536)+(y3+h3-126),((w3-194)*65536)+110,surfacec)==0 || gui_text_terminal(surface,x3+194,y3+h3-108,textc)==0 { return 0; }

    // File Manager window 4: navigation rail, folders and file rows.
    let r4=wm_record(wm,4); let x4=volatile_read64(r4+8); let y4=volatile_read64(r4+16); let w4=volatile_read64(r4+24); let h4=volatile_read64(r4+32);
    if gui_text_files(surface,x4+18,y4+14,textc)==0 { return 0; }
    if display_fill_rect(surface,((x4+12)*65536)+(y4+48),(170*65536)+(h4-62),surfacec)==0 { return 0; }
    if gui_text_home(surface,x4+42,y4+72,textc)==0 || gui_text_documents(surface,x4+42,y4+112,textc)==0 || gui_text_downloads(surface,x4+42,y4+152,textc)==0 || gui_text_projects(surface,x4+42,y4+192,textc)==0 || gui_text_media(surface,x4+42,y4+232,textc)==0 || gui_text_archive(surface,x4+42,y4+272,textc)==0 { return 0; }
    if display_fill_rect(surface,((x4+194)*65536)+(y4+54),((w4-210)*65536)+42,surface2)==0 || gui_text_search_frames(surface,x4+214,y4+70,muted)==0 { return 0; }
    var fr:u64=0; while fr<6 { let ry=y4+118+(fr*52); if display_fill_rect(surface,((x4+198)*65536)+ry,((w4-220)*65536)+38,surfacec)==0 { return 0; } if gui_draw_icon(surface,((x4+210)*65536)+(ry+7),2,accent)==0 { return 0; } fr=fr+1; }
    serial_marker_full_gui_fileman_ok();

    // Settings window 5 remains visible beside the active File Manager.
    let x5=volatile_read64(r5+8); let y5=volatile_read64(r5+16); let w5=volatile_read64(r5+24); let h5=volatile_read64(r5+32);
    if gui_text_settings(surface,x5+18,y5+14,textc)==0 { return 0; }
    if display_fill_rect(surface,((x5+14)*65536)+(y5+50),(110*65536)+(h5-66),surfacec)==0 { return 0; }
    if gui_text_appearance(surface,x5+28,y5+72,accent)==0 || gui_text_themes(surface,x5+146,y5+72,textc)==0 { return 0; }
    if gui_text_wallpaper(surface,x5+146,y5+110,muted)==0 || gui_text_fonts(surface,x5+146,y5+146,muted)==0 || gui_text_cursor(surface,x5+146,y5+182,muted)==0 || gui_text_lock_screen(surface,x5+146,y5+218,muted)==0 { return 0; }
    if display_fill_rect(surface,((x5+146)*65536)+(y5+268),(64*65536)+42,accent)==0 || display_fill_rect(surface,((x5+222)*65536)+(y5+268),(64*65536)+42,accent2)==0 || display_fill_rect(surface,((x5+298)*65536)+(y5+268),(64*65536)+42,focus)==0 { return 0; }
    serial_marker_full_gui_settings_ok();

    // Visible notification toast and focused-window ring.
    if display_fill_rect(surface,((w-330)*65536)+42,(292*65536)+86,panel)==0 || gui_text_system_health(surface,w-308,58,textc)==0 { return 0; }
    if display_fill_rect(surface,((w-308)*65536)+88,(180*65536)+7,accent)==0 || display_fill_rect(surface,((w-308)*65536)+108,(132*65536)+6,focus)==0 { return 0; }
    if display_fill_rect(surface,((x4-3)*65536)+(y4-3),((w4+6)*65536)+3,focus)==0 || display_fill_rect(surface,((x4-3)*65536)+(y4+h4),((w4+6)*65536)+3,focus)==0 { return 0; }

    let timing=volatile_read64(process+664); let present=volatile_read64(process+672); let cursor=volatile_read64(process+640); if timing==0 || present==0 || cursor==0 { return 0; }
    if desktop_draw_cursor(surface,volatile_read64(cursor+16),volatile_read64(cursor+24))==0 { return 0; }
    if dirty_add(dirty,0,(w*65536)+h,16)==0 || present_enqueue(present,0,(w*65536)+h,16)==0 || present_flush(present,surface,timing)==0 { return 0; }
    serial_marker_full_interactive_desktop_ok();
    return 1;
}

'''
text = text.replace(anchor, full_gui + anchor, 1)

old = 'if gui_physical_test_mode!=0 { serial_marker_frames_integrated_gui_ok(); serial_marker_gui_physical_test_ready(); return; }'
new = 'if gui_physical_test_mode!=0 { if full_interactive_desktop_compose(appearance_state,display_state,process_state,window_manager_state)==0 { serial_marker_desktop_cert_fail(); return; } serial_marker_frames_integrated_gui_ok(); serial_marker_gui_physical_test_ready(); return; }'
if text.count(old) != 1:
    raise SystemExit('GUI physical-test completion anchor mismatch')
text = text.replace(old, new, 1)

p.write_text(text)
print('full_interactive_desktop_gui_patch=PASS')
print('base_kernel_sha256='+actual)
print('patched_kernel_sha256='+hashlib.sha256(p.read_bytes()).hexdigest())
