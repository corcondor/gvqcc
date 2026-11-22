"""Bit-for-bit KickMix binary-v2 parser/writer for the published ANGLE family.

Handles opcodes in the current public ANGLE circuits and rejects unsupported
angle payloads and info tags. Register declarations and all unrelated gate
operands are faithfully preserved. No external KickMix Python package required.
"""
from __future__ import annotations
from dataclasses import dataclass
from array import array
from pathlib import Path
import struct,sys

MAGIC=bytes.fromhex("d750c7d5c329d326e3cc9f6834f2b8bf")
HDR=struct.Struct("<16s4I9Q")
PK=struct.Struct("<QQ")


@dataclass(frozen=True)
class Op:
    code:int
    wires:tuple[int,...]
    bits:tuple[int,...]=()
    cond:tuple[int,...]=()
    angle:bytes=b""


class KMB:
    def __init__(self,origin,version,nq,nb,nregs,registers,ops,tag=b""):
        self.origin=origin;self.version=version;self.nq=nq;self.nb=nb
        self.nregs=nregs;self.registers=registers;self.ops=ops;self.tag=tag

    @classmethod
    def read(cls,path):
        data=Path(path).read_bytes()
        if len(data)<HDR.size:raise ValueError("truncated binary")
        h=HDR.unpack_from(data)
        magic,v,nq,nb,nregs,*counts=h
        if magic!=MAGIC or v!=2:raise ValueError("unsupported KMB header")
        pos=HDR.size;regstart=pos
        for _ in range(nregs):
            kind,length=PK.unpack_from(data,pos)
            if kind!=0 or pos+16+length>len(data):
                raise ValueError("invalid register declaration")
            pos+=16+length
        regs=data[regstart:pos]
        streams=[]
        for typ in range(1,12):
            kind,sz=PK.unpack_from(data,pos)
            if kind!=typ or pos+16+sz>len(data):
                raise ValueError("KMB payload packet mismatch")
            pos+=PK.size
            streams.append(data[pos:pos+sz]);pos+=sz
        if pos!=len(data):raise ValueError("extraneous binary data")
        expected=[counts[0],counts[1]*4,counts[1]*4,counts[1]*4,
                  counts[2]*4,counts[2]*4,counts[3]*4,counts[4]*4,
                  counts[5]*4,counts[6]*16]
        if [len(s) for s in streams[:10]]!=expected:
            raise ValueError("KMB column size mismatch")
        if counts[7] or counts[8]:raise ValueError("info tags unsupported")
        if len(streams[10])<8:raise ValueError("truncated tag packet")
        def u32(blob):
            a=array("I");a.frombytes(blob)
            if sys.byteorder!="little":a.byteswap()
            return a
        cols=[u32(s) for s in streams[1:9]]
        used=[0]*8;ops=[]
        for op in streams[0]:
            kind=op&0x70
            if op in (0x50,0xd0):kind=0x10
            if kind==0x30:
                wires=tuple(cols[j][used[j]] for j in range(3))
                for j in range(3):used[j]+=1
            elif kind==0x20:
                wires=tuple(cols[3+j][used[3+j]] for j in range(2))
                for j in range(3,5):used[j]+=1
            elif kind==0x10:
                wires=(cols[5][used[5]],);used[5]+=1
            else:
                wires=()
            bits=();cond=()
            if op in (0x50,0xd0) or (op&0x70)==0x40:
                bits=(cols[6][used[6]],);used[6]+=1
            if op&0x80:
                cond=(cols[7][used[7]],);used[7]+=1
            if op in (0x13,0x93):
                raise ValueError("generic Z_POW not supported in this loader-only adapter")
            if op not in (0x11,0x21,0x31,0x50,0x10,0x20,0x90,0xa0):
                raise ValueError(f"loader opcode unsupported: {op:#x}")
            if any(not 0<=x<nq for x in wires):
                raise ValueError("qubit wire index out of range")
            ops.append(Op(op,wires,bits,cond))
        if used!=list(map(len,cols)):
            raise ValueError("unconsumed KMB operand bytes")
        return cls(path,v,nq,nb,nregs,regs,ops,streams[10])

    def render(self):
        b3=[array("I") for _ in range(3)]
        b2=[array("I") for _ in range(2)]
        b1=array("I");bits=array("I");cond=array("I");opcodes=bytearray()
        for o in self.ops:
            if o.code not in (0x11,0x21,0x31,0x50,0x10,0x20,0x90,0xa0):
                raise ValueError("cannot emit unsupported opcode")
            opcodes.append(o.code)
            if len(o.wires)==3:
                for dst,v in zip(b3,o.wires):dst.append(v)
            elif len(o.wires)==2:
                for dst,v in zip(b2,o.wires):dst.append(v)
            elif len(o.wires)==1:b1.append(o.wires[0])
            elif o.wires:raise ValueError("wrong arity")
            bits.extend(o.bits);cond.extend(o.cond)
            if o.angle:raise ValueError("rotation angle unsupported")
        for a in (*b3,*b2,b1,bits,cond):
            if sys.byteorder!="little":a.byteswap()
        streams=[bytes(opcodes)]+[v.tobytes() for v in
                 (*b3,*b2,b1,bits,cond)]+[b"",self.tag]
        counts=(len(opcodes),len(b3[0]),len(b2[0]),len(b1),
                len(bits),len(cond),0,0,0)
        header=HDR.pack(MAGIC,self.version,self.nq,self.nb,self.nregs,*counts)
        return header+self.registers+b"".join(
            PK.pack(index,len(s))+s for index,s in enumerate(streams,1)
        )

    def write(self,path):
        Path(path).write_bytes(self.render())

    def paid(self):
        return sum(op.code==0x31 for op in self.ops)

    def cx(self):
        return sum(op.code==0x21 for op in self.ops)
