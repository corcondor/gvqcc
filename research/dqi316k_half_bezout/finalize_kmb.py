"""Finalize the two raw KMB files exactly as in the native Vercel experiment."""
from pathlib import Path
import struct, hashlib

EXPECTED = {
    "forward.kmb": "d26b9bab24c355d27c951e9339f0575a350d645e5d336d7d9cd17580e53d007e",
    "half.kmb": "72676a49be105adc303d0c4541b1beba09665aa9421c41f67649d4c064e5c6fa",
}
for name, expected in EXPECTED.items():
    path = Path(name)
    data = bytearray(path.read_bytes())
    if hashlib.sha256(data).hexdigest() != expected:
        if name == "forward.kmb":
            assert struct.unpack_from("<II", data, 20) == (851, 49142)
            struct.pack_into("<II", data, 20, 840, 49140)
        data.extend(struct.pack("<QQQQQ",10,0,11,8,0))
        assert hashlib.sha256(data).hexdigest() == expected, name
        path.write_bytes(data)
    print(name, expected)
