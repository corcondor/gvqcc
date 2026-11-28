"""Finalize generated raw KMB output. Safe to rerun on either file."""
from pathlib import Path
import struct,hashlib
trailer=struct.pack("<QQQQQ",10,0,11,8,0)
for name in ('forward.kmb','half.kmb'):
    path=Path(name);data=bytearray(path.read_bytes())
    if name=='forward.kmb':
        h=struct.unpack_from("<II",data,20)
        assert h in ((851,49142),(840,49140))
        struct.pack_into("<II",data,20,840,49140)
    if not data.endswith(trailer):data.extend(trailer)
    path.write_bytes(data)
    print(name,hashlib.sha256(data).hexdigest())
