#!/usr/bin/env python3
"""Find structurally identical 42-CCX/1251-CX kernels in a v2 Kickmix KMB.

All 1293 gates, including each CX/CCX operand, must match modulo an
injective wire renaming. This reports syntax equivalence, not semantic
common-input values, execution probability, or a verified T reduction.

Usage: python dqi_kernel_motif_audit.py dqi.kmb -o motif_audit.json
Requirements: numpy
"""
from __future__ import annotations
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import struct
import numpy as np

MAGIC = bytes.fromhex("d750c7d5c329d326e3cc9f6834f2b8bf")
HEADER = struct.Struct('<4I9Q')

def arrays_from_kmb(path: Path):
    with path.open('rb') as f:
        if f.read(16) != MAGIC:
            raise ValueError('Bad KMB magic')
        version,nq,nb,nreg,nops,n3,n2,n1,nbit,ncond,nangle,ntags,nchars=HEADER.unpack(f.read(HEADER.size))
        if version != 2:
            raise ValueError('Only version 2 supported')
        for _ in range(nreg):
            typ,n=struct.unpack('<QQ',f.read(16))
            if typ != 0:raise ValueError('Bad register packet')
            f.seek(n,1)
        sizes=(nops,n3*4,n3*4,n3*4,n2*4,n2*4,n1*4,nbit*4,ncond*4,nangle*16,(ntags+1)*8+nchars)
        offsets=[]
        for j,expected in enumerate(sizes,1):
            typ,n=struct.unpack('<QQ',f.read(16))
            if typ != j or n != expected:raise ValueError('Bad packet size/type')
            offsets.append(f.tell())
            f.seek(n,1)
        if f.tell()!=path.stat().st_size:raise ValueError('Trailing bytes')
    types=['u1']+['<u4']*8+['<u8','u1']
    arr=[np.memmap(path,dtype=dtype,offset=offset,mode='r',shape=length//np.dtype(dtype).itemsize)
         for offset,length,dtype in zip(offsets,sizes,types)]
    return {'qubits':nq,'ops':nops,'n3':n3,'n2':n2},arr

def canonical_ccx(idx,a,b,t,limit=42):
    ids={};out=[]
    for j in range(idx,idx+limit):
        triple=[]
        for value in (int(a[j]),int(b[j]),int(t[j])):
            if value not in ids:ids[value]=len(ids)
            triple.append(ids[value])
        out.append(tuple(triple))
    return tuple(out)

def analyze(path: Path):
    header,arr=arrays_from_kmb(path)
    op,q30,q31,q32,q20,q21,*_=arr
    p3=np.flatnonzero((op & 0x30)==0x30)
    isccx=np.asarray(op[p3]==0x31)
    pcc=p3[isccx]
    c0,c1,t=q30[isccx],q31[isccx],q32[isccx]
    n=len(pcc)
    if n<42:raise ValueError('Fewer than 42 CCX; no template')
    # A low-cost prefix discriminant, followed by the exact 42-gate signature.
    candidates=np.arange(n-41,dtype=np.int32)
    candidates=candidates[(t[candidates]==t[candidates+1]) &
                          (c0[candidates]==c0[candidates+3]) &
                          (c1[candidates]==c1[candidates+3]) &
                          (c0[candidates]==c0[candidates+4]) &
                          (c1[candidates]==c1[candidates+4])]
    ref=canonical_ccx(0,c0,c1,t)
    hits=np.array([i for i in candidates if canonical_ccx(int(i),c0,c1,t)==ref],dtype=np.int32)
    if not len(hits) or hits[0]!=0:raise ValueError('Expected motif anchored at first CCX absent')
    if len(hits)>1 and not np.all(np.diff(hits)>=42):raise ValueError('Overlapping motif matches')
    spans=pcc[hits+41]-pcc[hits]
    if not np.all(spans==1292):raise ValueError('Motif 42-CCX gates not always 1293 instructions wide')
    p2=np.flatnonzero((op & 0x30)==0x20)
    first=int(pcc[0]);base_types=np.asarray(op[first:first+1293]);
    i2=np.flatnonzero(base_types==0x21);i3=np.flatnonzero(base_types==0x31)
    if len(i2)!=1251 or len(i3)!=42:raise ValueError('Wrong prefix template arities')
    flat_indices=np.array([3*j+k for j,v in enumerate(base_types) for k in range(2 if v==0x21 else 3)],dtype=np.int32)
    def full_sig(s):
        s=int(s);j2=int(np.searchsorted(p2,s));j3=int(np.searchsorted(p3,s))
        three=np.zeros((1293,3),dtype=np.int32)
        three[i2,0]=q20[j2:j2+1251];three[i2,1]=q21[j2:j2+1251]
        three[i3,0]=q30[j3:j3+42];three[i3,1]=q31[j3:j3+42];three[i3,2]=q32[j3:j3+42]
        raw=three.reshape(-1)[flat_indices]
        _,fi,inverse=np.unique(raw,return_index=True,return_inverse=True)
        renumber=np.empty(len(fi),dtype=np.int32)
        renumber[np.argsort(fi)]=np.arange(len(fi),dtype=np.int32)
        return renumber[inverse]
    full_ref=full_sig(first)
    full_matches=0
    for start in pcc[hits]:
        if np.array_equal(op[start:start+1293],base_types) and np.array_equal(full_sig(start),full_ref):
            full_matches+=1
    adjacent=np.flatnonzero(np.diff(hits)==42)
    gap_counts=Counter()
    for j in adjacent:
        s=int(pcc[hits[j]]+1293);e=int(pcc[hits[j+1]])
        intermediate=op[s:e]
        kind='cx_only' if np.all(intermediate==0x21) else ('contains_hmr' if np.any(intermediate==0x50) else 'other')
        gap_counts[kind]+=1
    file_hash=hashlib.sha256()
    with path.open('rb') as f:
        while chunk:=f.read(8*1024*1024):file_hash.update(chunk)
    return {
        'file':path.name,'sha256':file_hash.hexdigest(),
        'scope':'read_only_static_syntactic_motif_audit_no_score_or_equivalence_claim',
        'qubits':header['qubits'],'total_instructions':int(header['ops']),
        'unconditional_ccx':int(n),
        'template':{'length_ops':1293,'cx':1251,'ccx':42,'wires':int(full_ref.max()+1),
                    'start_op_index':first,'end_op_index':first+1292},
        'matching_42ccx_skeletons':int(len(hits)),
        'matching_full_1293_gate_templates_modulo_wire_renaming':int(full_matches),
        'nonoverlapping_ccx_in_templates':int(len(hits)*42),
        'fraction_unconditional_ccx_in_templates':float(len(hits)*42/n),
        'adjacent_template_pairs_in_ccx_stream':int(len(adjacent)),
        'adjacent_template_gap_categories':dict(gap_counts),
        'idealized_static_ccx_savings':{'minus_1_per_template':int(len(hits)),
                                        'minus_2_per_template':int(2*len(hits))},
        'caveat':'Identical gate syntax need not imply same caller contract or reusable operands; ignores surrounding linear preparation/uncomputation, HMR phases, guard states, scratch lifetime and execution probabilities. No reduced KMB has been created.',
    }

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('kmb',type=Path)
    ap.add_argument('-o','--output',type=Path)
    args=ap.parse_args()
    report=analyze(args.kmb)
    s=json.dumps(report,ensure_ascii=False,indent=2,sort_keys=True)+'\n'
    if args.output:
        args.output.parent.mkdir(parents=True,exist_ok=True)
        args.output.write_text(s,encoding='utf-8')
    print(s,end='')
if __name__=='__main__':main()

