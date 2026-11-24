"""Lossless KickMix KMB v2 reader/writer for exact structural search.
Source methodology from user's earlier native_kmb.py; no official verification.
"""
from dataclasses import dataclass
import struct,hashlib
HEADER=struct.Struct('<4I9Q')
SECTION=struct.Struct('<QQ')
WC={0:(),1:(7,),2:(5,6),3:(2,3,4)}
@dataclass(frozen=True)
class Op:
    raw:int
    wires:tuple
    measurement:int|None=None
    condition:int|None=None
    def __post_init__(self):
        if len(self.wires)!=len(WC[(self.raw>>4)&3]):raise ValueError("arity")
@dataclass
class NativeKMB:
    prefix16:bytes
    header:tuple
    sections:list
    ops:list
    @classmethod
    def parse(cls,data):
        h=HEADER.unpack_from(data,16)
        if h[0]!=2:raise ValueError("KMB v2 required")
        sections=[];pos=16+HEADER.size
        while pos<len(data):
            kind,size=SECTION.unpack_from(data,pos);pos+=16
            sections.append((kind,data[pos:pos+size]));pos+=size
        cols={k:raw for k,raw in sections if 1<=k<=9}
        if len(cols)!=9:raise ValueError("KMB op sections")
        idx={k:0 for k in range(2,10)}
        ints={k:memoryview(cols[k]).cast('I') for k in range(2,10)}
        def pop(k):
            j=idx[k];idx[k]=j+1
            return int(ints[k][j])
        ops=[]
        for raw in cols[1]:
            wires=tuple(pop(k) for k in WC[(raw>>4)&3])
            measurement=pop(8) if raw&64 else None
            condition=pop(9) if raw&128 else None
            ops.append(Op(raw,wires,measurement,condition))
        assert len(ops)==h[4]
        assert all(idx[k]==len(ints[k]) for k in range(2,10))
        return cls(data[:16],h,sections,ops)
    def to_bytes(self):
        cols={k:bytearray() for k in range(1,10)}
        for o in self.ops:
            cols[1].append(o.raw)
            for k,wire in zip(WC[(o.raw>>4)&3],o.wires):
                cols[k]+=struct.pack('<I',wire)
            if o.raw&64:cols[8]+=struct.pack('<I',o.measurement)
            if o.raw&128:cols[9]+=struct.pack('<I',o.condition)
        h=list(self.header)
        h[4]=len(self.ops)
        h[5]=sum((o.raw&127)==49 for o in self.ops)
        for j,k in enumerate([5,7,8,9],6):h[j]=len(cols[k])//4
        out=bytearray(self.prefix16)
        out.extend(HEADER.pack(*h))
        for kind,raw in self.sections:
            if kind in cols:raw=bytes(cols[kind])
            out.extend(SECTION.pack(kind,len(raw)));out.extend(raw)
        return bytes(out)
    def stats(self):
        return {'T':sum((o.raw&127)==49 for o in self.ops),
                'Q':self.header[1],'sha256':hashlib.sha256(self.to_bytes()).hexdigest()}
