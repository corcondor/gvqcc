#!/usr/bin/env python3
"""Read-only scan of repeated 42-CCX DQI windows; input-space GF(2) ranks.
Requires numpy and the adjacent dqi_kernel_motif_audit.py from this repo.
Only mathematical local quadratic windows are certified, NOT HMR/full-circuit.
"""
import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path

import numpy as np
from dqi_kernel_motif_audit import arrays_from_kmb, canonical_ccx


def rank(vectors):
    basis = {}
    for x in vectors:
        x = int(x)
        while x:
            k = x.bit_length()-1
            if k in basis:
                x ^= basis[k]
            else:
                basis[k] = x
                break
    return len(basis)


def overlap(a, b):
    return rank(a) + rank(b) - rank(a+b)


def scan(path, limit=None):
    h, z = arrays_from_kmb(Path(path))
    op, a3, b3, t3, a2, b2, *_ = z
    p3 = np.flatnonzero((op & 48) == 48)
    iscc = (op[p3] == 49)
    pc = p3[iscc]
    aa, bb, tt = a3[iscc], b3[iscc], t3[iscc]
    cand = np.arange(len(pc)-41, dtype=np.int32)
    cand = cand[(tt[cand]==tt[cand+1]) &
        (aa[cand]==aa[cand+3]) & (bb[cand]==bb[cand+3]) &
        (aa[cand]==aa[cand+4]) & (bb[cand]==bb[cand+4])]
    ref = canonical_ccx(0, aa, bb, tt)
    hits = np.array([j for j in cand if
        canonical_ccx(int(j),aa,bb,tt)==ref], dtype=np.int32)
    p2 = np.flatnonzero((op & 48) == 32)
    counts = Counter()
    cases = []
    seen = 0
    for j in np.flatnonzero(np.diff(hits)==42):
        first, second = int(pc[hits[j]]),int(pc[hits[j+1]])
        if not np.all(op[first+1293:second]==33):
            continue
        affine = [1 << j for j in range(h['qubits'])]
        dep = [0]*h['qubits']
        atoms = []
        pos2,pos3 = int(np.searchsorted(p2,first)),int(np.searchsorted(p3,first))
        higher = False
        for ix in range(first, second+1293):
            kind = int(op[ix])
            if kind == 33:
                a,b = int(a2[pos2]),int(b2[pos2])
                pos2 += 1
                affine[b] ^= affine[a]
                dep[b] ^= dep[a]
            elif kind == 49:
                a,b,t = int(a3[pos3]),int(b3[pos3]),int(t3[pos3])
                pos3 += 1
                higher |= bool(dep[a] or dep[b])
                atoms.append((affine[a],affine[b]))
                dep[t] ^= 1 << (len(atoms)-1)
            else:
                raise ValueError(f'Non-CX/CCX opcode: {kind}')
        if higher:
            counts['higher_degree_pairs'] += 1
            continue
        assert len(atoms)==84
        x1=[p for p,q in atoms[:42]]
        y1=[q for p,q in atoms[:42]]
        x2=[p for p,q in atoms[42:]]
        y2=[q for p,q in atoms[42:]]
        directions=[0]*84
        for wire,word in enumerate(dep):
            while word:
                bit = word & -word
                directions[bit.bit_length()-1] ^= 1<<wire
                word ^= bit
        input_rank=rank(x1+y1+x2+y2)
        output_rank=rank(directions)
        intersections=[overlap(x1,x2),overlap(y1,y2),
                       overlap(x1,y2),overlap(y1,x2)]
        counts[f'input_rank_{input_rank}_output_rank_{output_rank}'] += 1
        counts[f'intersections_{tuple(intersections)}'] += 1
        seen += 1
        if (12 in intersections or output_rank==12) and len(cases)<24:
            cases.append(dict(first_op=first,second_op=second,
                input_rank=input_rank,output_rank=output_rank,
                intersections=intersections))
        if limit is not None and seen>=limit:
            break
    digest=hashlib.sha256()
    with Path(path).open('rb') as f:
        while chunk:=f.read(8*1024*1024):
            digest.update(chunk)
    return dict(file_sha256=digest.hexdigest(),motifs=len(hits),
        adjacent=int(sum(np.diff(hits)==42)),quadratic_pairs=seen,
        counts=dict(counts),examples=cases,
        status='READ_ONLY; NOT A FULL-CIRCUIT EQUIVALENCE CERTIFICATE')


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('kmb',type=Path)
    p.add_argument('-o','--output',type=Path)
    p.add_argument('--limit',type=int)
    args=p.parse_args()
    report=scan(args.kmb,args.limit)
    output=json.dumps(report,indent=2,ensure_ascii=False)+'\n'
    if args.output:
        args.output.write_text(output,encoding='utf8')
    print(output)
