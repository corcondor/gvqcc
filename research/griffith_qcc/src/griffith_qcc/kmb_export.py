"""Minimal KickMix v2 KMB serializer for self-contained X/CX/CCX blocks.

No measurements, conditional operations, or phase synthesis are supported.
Unsupported instructions fail closed. The serializer's binary layout follows
the existing user's qhdl_kmb.py reader and is checked against it in the
standalone reproducibility bundle; NOT an official verifier.
"""
import struct
from pathlib import Path

MAGIC=bytes.fromhex("d750c7d5c329d326e3cc9f6834f2b8bf")
STREAMS=("qqq0","qqq1","qqq2","qq0","qq1","q0","b0","bc")


def encode_kmb(gates,registers):
    streams={key:[] for key in STREAMS}
    types=[]
    for gate in gates:
        name,*q=gate
        if name=="CX" and len(q)==2:
            types.append(0x21)
            streams["qq0"].append(q[0])
            streams["qq1"].append(q[1])
        elif name=="CCX" and len(q)==3:
            types.append(0x31)
            for i in range(3):
                streams[f"qqq{i}"].append(q[i])
        elif name=="X" and len(q)==1:
            types.append(0x11)
            streams["q0"].append(q[0])
        else:
            raise ValueError(f"unsupported KMB operation: {gate}")
    all_qubits=[v for ids in registers.values() for v in ids]
    all_qubits.extend(q for op in gates for q in op[1:])
    if not all_qubits or min(all_qubits)<0:
        raise ValueError("nonnegative qubit ids required")
    nq=max(all_qubits)+1
    data=bytearray(MAGIC)
    data+=struct.pack("<4I",2,nq,0,len(registers))
    data+=struct.pack("<9Q",len(types),len(streams["qqq0"]),
                      len(streams["qq0"]),len(streams["q0"]),0,0,0,0,0)
    for name,ids in registers.items():
        nm=name.encode()
        data+=struct.pack("<2Q",0,len(nm)+8+4*len(ids))
        data+=struct.pack("<2I",len(nm),len(ids))+nm
        for q in ids:
            data+=struct.pack("<I",int(q)|0x80000000)
    data+=struct.pack("<2Q",1,len(types))+bytes(types)
    for j,key in enumerate(STREAMS):
        payload=b"".join(struct.pack("<I",int(v)) for v in streams[key])
        data+=struct.pack("<2Q",2+j,len(payload))+payload
    data+=struct.pack("<2Q",10,0)
    data+=struct.pack("<2Q",11,8)+struct.pack("<Q",0)
    return bytes(data)


def write_kmb(gates,registers,path):
    path=Path(path)
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_bytes(encode_kmb(gates,registers))
    return path
