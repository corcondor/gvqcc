"""Finalize raw native writer output for KickMix 1.0.0 (run exactly once)."""
import struct,sys
from pathlib import Path
for path in map(Path,sys.argv[1:]):
    with path.open('r+b') as f:
        f.seek(24);f.write(struct.pack('<I',49140));f.seek(0,2);f.write(struct.pack('<QQQQQ',10,0,11,8,0))
