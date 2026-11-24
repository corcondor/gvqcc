#!/usr/bin/env python3
"""Lossless KMB v2 column splice for an independently verified local window.

Never overwrites the source. Retains register bytes, untouched ops, angles,
classical-control columns and INFO_TAG data byte-for-byte. Revalidates output.
Lean and native full-circuit acceptance remain separate mandatory gates.
"""
from __future__ import annotations
import argparse, hashlib, json, struct
from pathlib import Path
from scan import KMB, GATES, ARITY, PKT, HDR, eval_ops, Op

CODE={name:code for code,name in GATES.items()}
SRC={1:(7,),2:(5,6),3:(2,3,4)}
BYTES={1:1,2:4,3:4,4:4,5:4,6:4,7:4,8:4,9:4,10:16}


def used_counts(raw: bytes):
    def cnt(pred):
        return raw.translate(bytes(int(bool(pred(x))) for x in range(256))).count(1)
    n3=cnt(lambda x:(x&0x30)==0x30)
    n2=cnt(lambda x:(x&0x30)==0x20)
    n1=cnt(lambda x:(x&0x30)==0x10)
    return {1:len(raw),2:n3,3:n3,4:n3,5:n2,6:n2,7:n1,8:cnt(lambda x:x&0x40),9:cnt(lambda x:x&0x80),10:cnt(lambda x:(x&0x7f)==0x13),11:0}


def encode(objs):
    out={k:bytearray() for k in range(1,12)}
    for obj in objs:
        name=obj['op'];qs=obj['q'];opcode=CODE[name]
        if len(qs)!=ARITY[name] or len(qs)!=len(set(qs)):
            raise ValueError('invalid arity or duplicate operand')
        out[1].append(opcode)
        for col,q in zip(SRC[len(qs)],qs):out[col]+=struct.pack('<I',q)
    return {k:bytes(v) for k,v in out.items()}


def copy_range(mm,f,lo,hi):
    for a in range(lo,hi,1<<20):f.write(mm[a:min(a+(1<<20),hi)])


def emit(src:Path, hit:dict, dest:Path):
    if dest.resolve()==src.resolve() or dest.exists():raise FileExistsError('output exists or source would be overwritten')
    k=KMB(src)
    try:
        begin,end=hit['begin'],hit['end']
        if not (0<=begin<end<=k.nops):raise ValueError('bad source range')
        before=hit['before'];after=hit['after']
        if len(before)!=end-begin:raise ValueError('nonconsecutive original window')
        for j,obj in enumerate(before):
            if obj['idx']!=begin+j:raise ValueError('bad index list')
        support=sorted({q for obj in before for q in obj['q']})
        if len(support)>6:raise ValueError('exhaustive check limit')
        bops=[Op(i,obj['op'],tuple(obj['q'])) for i,obj in enumerate(before)]
        aops=[Op(i,obj['op'],tuple(obj['q'])) for i,obj in enumerate(after)]
        if eval_ops(bops,support)!=eval_ops(aops,support):raise ValueError('phase or output mismatch')
        old=encode(before);new=encode(after)
        op_off=k.packets[1][0]
        prefix=used_counts(k.mm[op_off:op_off+begin]);
        window=used_counts(k.mm[op_off+begin:op_off+end]);
        if any(window[i]*BYTES[i]!=len(old[i]) for i in range(1,11)):
            raise ValueError('source window has barriers or wrong arity')
        # Exact operand-column identity: guard against a stale or reindexed receipt.
        for col in range(1,11):
            base,length=k.packets[col];lo=prefix[col]*BYTES[col];hi=lo+len(old[col]);
            if k.mm[base+lo:base+hi]!=old[col]:raise ValueError(f'KMB operand mismatch in column {col}')
        oldh=list(HDR.unpack_from(k.mm,0));newh=oldh[:]
        newh[5]+=len(after)-len(before)
        for field,col in [(6,2),(7,5),(8,7),(9,8),(10,9),(11,10)]:
            newh[field]+=(len(new[col])-len(old[col]))//BYTES[col]
        # All source KMB header counts must agree with its original packets.
        if len(before)==0 or newh[5]<=0:raise ValueError('empty replacement')
        try:
            with dest.open('xb') as f:
                f.write(HDR.pack(*newh))
                copy_range(k.mm,f,HDR.size,op_off-PKT.size)
                for col in range(1,12):
                    base,length=k.packets[col]
                    pos=prefix[col]*BYTES.get(col,1)
                    low=pos;high=low+len(old[col])
                    replacement=new[col] if col<=10 else None
                    if col==11:low=high=0
                    size=length+(len(replacement)-len(old[col]) if col<=10 else 0)
                    f.write(PKT.pack(col,size))
                    copy_range(k.mm,f,base,base+low)
                    if replacement is not None:f.write(replacement)
                    copy_range(k.mm,f,base+high,base+length)
            ck=KMB(dest)
            try:
                if ck.nops!=newh[5] or ck.q!=k.q:raise ValueError('invalid emitted KMB')
                sha=ck.sha()
            finally:ck.close()
        except BaseException:
            dest.unlink(missing_ok=True)
            raise
        return dict(source_sha256=k.sha(),output_sha256=sha,source_ops=k.nops,output_ops=newh[5],
                    source_qubits=k.q,output_qubits=k.q,saved_nonclifford=hit['saved_nonclifford'],
                    status='LOCAL_EXACT_LEAN_AND_NATIVE_FULL_VERIFICATION_PENDING')
    finally:k.close()


def main():
    p=argparse.ArgumentParser();p.add_argument('--source',type=Path,required=True)
    p.add_argument('--receipt',type=Path,required=True)
    p.add_argument('--index',type=int,default=0)
    p.add_argument('--out',type=Path,required=True)
    a=p.parse_args()
    receipt=json.loads(a.receipt.read_text());k=KMB(a.source)
    try:
        if k.sha()!=receipt['sha256']:raise ValueError('source SHA does not match receipt')
    finally:k.close()
    out=emit(a.source,receipt['hits'][a.index],a.out)
    print(json.dumps(out,indent=2))

if __name__=='__main__':main()
