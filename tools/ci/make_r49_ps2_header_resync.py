#!/usr/bin/env python3
from pathlib import Path
import sys

p=Path(sys.argv[1]); s=p.read_text()

def rep(old,new,label):
    n=s.count(old)
    if n!=1:
        raise SystemExit(f'{label}: expected 1 site, found {n}')
    return s.replace(old,new)

# r48 diagnostic title -> r49.
s=rep(
    '''pointer_diag_draw_tag4(surface,(78*65536)+18,82+(52*256)+(56*65536)+(32*16777216),green);    // R48''',
    '''pointer_diag_draw_tag4(surface,(78*65536)+18,82+(52*256)+(57*65536)+(32*16777216),green);    // R49''',
    'title')

# Physical PS/2 resynchronization fix.
# In the 3-byte locked path, only a byte with mandatory PS/2 header bit 3 set
# may become packet byte 0. Any non-header byte is discarded while index stays 0,
# allowing the stream to recover from a one- or two-byte phase error without
# disturbing the already-proven packet decoder or Generic Pointer path.
s=rep(
'''        if index==0 {
            // r47 hybrid IRQ/poll transport + post-STI ACK barrier + fixed-cadence policy: after a deterministic F4/FA barrier,
            // every third byte is packet byte 0. Never abandon cadence merely
            // because this byte's fixed-header bit is damaged/missing. Store
            // it, consume the remaining two bytes, then discard the complete
            // frame if the header is invalid. This prevents one corrupt byte
            // from shifting all subsequent packet boundaries.
            unsafe { volatile_write64(input_state+2808,data); volatile_write64(input_state+2800,1); volatile_write64(input_state+3152,read_tsc()); }
            return 1;
        }''',
'''        if index==0 {
            // r49 physical PS/2 header resynchronization. Bit 3 is mandatory in
            // every standard PS/2 packet header. If the physical stream arrives
            // out of phase, discard bytes until a valid header candidate appears;
            // do not advance packet index on a non-header byte.
            if (data/8)%2==0 {
                unsafe { volatile_write64(input_state+2960,volatile_read64(input_state+2960)+1); }
                let r49_diag=volatile_read64(input_state+3976);
                if r49_diag!=0 { unsafe { volatile_write64(r49_diag+352,0); volatile_write64(r49_diag+360,volatile_read64(r49_diag+360)+1); } }
                return 1;
            }
            unsafe { volatile_write64(input_state+2808,data); volatile_write64(input_state+2800,1); volatile_write64(input_state+3152,read_tsc()); }
            return 1;
        }''',
    'three-byte header acquisition')

p.write_text(s)
