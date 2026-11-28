"""Native KickMix binary v2 rewriter with exact byte-for-byte roundtrips.

Does not itself prove that a rewritten circuit is correct, nor that an official
KickMix score improves. Use `verify_family.py` and the native verifier.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import hashlib
import struct
from typing import Iterable

HEADER = struct.Struct('<4I9Q')
SECTION = struct.Struct('<QQ')
_PREFIX_LEN = 16 + HEADER.size
WIRE_COLS = {0: (), 1: (7,), 2: (5, 6), 3: (2, 3, 4)}

@dataclass(frozen=True)
class Op:
    raw: int
    wires: tuple[int, ...]
    measurement: int | None = None
    condition: int | None = None

    def __post_init__(self):
        cols = WIRE_COLS[(self.raw >> 4) & 3]
        if len(self.wires) != len(cols):
            raise ValueError(f'wrong arity for opcode {self.raw}')
        if (self.measurement is not None) != bool(self.raw & 64):
            raise ValueError('measurement flag mismatch')
        if (self.condition is not None) != bool(self.raw & 128):
            raise ValueError('conditional flag mismatch')

@dataclass
class NativeKMB:
    prefix16: bytes
    header: tuple[int, ...]
    sections: list[tuple[int, bytes]]
    ops: list[Op]

    @classmethod
    def parse(cls, data: bytes) -> 'NativeKMB':
        if len(data) < _PREFIX_LEN: raise ValueError('truncated KMB header')
        prefix16 = data[:16]
        header = HEADER.unpack_from(data, 16)
        if header[0] != 2: raise ValueError('unsupported KMB format version')
        sections = []
        offset = _PREFIX_LEN
        while offset < len(data):
            if offset + SECTION.size > len(data): raise ValueError('truncated section header')
            kind, length = SECTION.unpack_from(data, offset)
            offset += SECTION.size
            if offset + length > len(data): raise ValueError('truncated section body')
            sections.append((kind, data[offset:offset+length]))
            offset += length
        columns = {kind: b for kind, b in sections if 1 <= kind <= 9}
        if len(columns) != 9: raise ValueError('missing or repeated operation columns')
        pos = {i:0 for i in range(2,10)}
        nums = {i: memoryview(columns[i]).cast('I') for i in range(2,10)}
        def take(i):
            a=nums[i];j=pos[i];pos[i]+=1
            if j>=len(a): raise ValueError(f'underflow in column {i}')
            return int(a[j])
        ops=[]
        for op in columns[1]:
            wires=tuple(take(i) for i in WIRE_COLS[(op >> 4) & 3])
            measurement=take(8) if op&64 else None
            condition=take(9) if op&128 else None
            ops.append(Op(op,wires,measurement,condition))
        for i in range(2,10):
            if pos[i] != len(nums[i]):raise ValueError(f'unconsumed entries in column {i}')
        if len(ops) != header[4]:raise ValueError('incorrect header operation count')
        return cls(prefix16,header,sections,ops)

    @classmethod
    def read(cls, path: str | Path) -> 'NativeKMB':
        return cls.parse(Path(path).read_bytes())

    def to_bytes(self) -> bytes:
        columns={k:bytearray() for k in range(1,10)}
        for op in self.ops:
            columns[1].append(op.raw)
            for ci,wi in zip(WIRE_COLS[(op.raw >> 4) & 3], op.wires):
                columns[ci] += struct.pack('<I',wi)
            if op.raw&64:columns[8] += struct.pack('<I',op.measurement)
            if op.raw&128:columns[9] += struct.pack('<I',op.condition)
        old=self.header
        header=list(old)
        header[4]=len(self.ops)
        header[5]=sum((o.raw&127)==49 for o in self.ops)
        header[6]=len(columns[5])//4
        header[7]=len(columns[7])//4
        header[8]=len(columns[8])//4
        header[9]=len(columns[9])//4
        data=bytearray(self.prefix16)
        data.extend(HEADER.pack(*header))
        seen=set()
        for kind,raw in self.sections:
            if kind in columns:
                if kind in seen:raise ValueError('duplicate operation section')
                seen.add(kind)
                raw=bytes(columns[kind])
            data.extend(SECTION.pack(kind,len(raw)))
            data.extend(raw)
        if seen!=set(columns):raise ValueError('missing operation section')
        return bytes(data)

    def stats(self) -> dict:
        return {'instructions':len(self.ops), 'toffoli':sum((o.raw&127)==49 for o in self.ops),
                'cx':sum((o.raw&127)==33 for o in self.ops),'qubits':self.header[1],
                'hmr':sum((o.raw&127)==80 for o in self.ops),
                'sha256':hashlib.sha256(self.to_bytes()).hexdigest()}

def cancel_adjacent_cx(ops: Iterable[Op]) -> tuple[list[Op],int]:
    """Exactly cancel consecutive CX on the same control/target; no phase effects.

    This is a score-neutral serialization/control regression, NOT a Toffoli optimization.
    """
    result=[]
    pairs=0
    for op in ops:
        if result and op.raw==33 and result[-1].raw==33 and op.wires==result[-1].wires:
            result.pop()
            pairs+=1
        else:result.append(op)
    return result,pairs
