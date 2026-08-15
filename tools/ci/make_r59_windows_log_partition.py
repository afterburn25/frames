#!/usr/bin/env python3
from pathlib import Path
import subprocess, sys

p=Path(sys.argv[1])
here=Path(__file__).resolve().parent
subprocess.check_call([sys.executable, str(here/'make_r58_input_flight_recorder_fixed.py'), str(p)])
s=p.read_text()

# r59: the persistent pointer log lives on GPT partition #2 (FRAMESLOG), not
# on the EFI System Partition. GPT entries are 128 bytes; partition #2 begins
# at byte 128 in the entry array, and its first-LBA field is +32 bytes.
old='let part_lba=volatile_read64(pe+32); if part_lba<34 { return 0; }'
new='let part_lba=volatile_read64(pe+160); if part_lba<34 { return 0; } // R59 FRAMESLOG GPT partition 2'
if s.count(old)!=1:
    raise SystemExit(f'r59 partition selector: expected 1 site, found {s.count(old)}')
s=s.replace(old,new,1)

# Change the visible diagnostic revision from R58 to R59.
old_title='pointer_diag_draw_tag4(surface,(78*65536)+18,82+(53*256)+(56*65536)+(32*16777216),green);    // R58'
new_title='pointer_diag_draw_tag4(surface,(78*65536)+18,82+(53*256)+(57*65536)+(32*16777216),green);    // R59'
if s.count(old_title)!=1:
    raise SystemExit(f'r59 title: expected 1 R58 title site, found {s.count(old_title)}')
s=s.replace(old_title,new_title,1)

p.write_text(s)
