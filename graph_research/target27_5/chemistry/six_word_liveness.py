#!/usr/bin/env python3
"""Exact storage test for a simultaneous separable feature bank at J=6."""
from __future__ import annotations
import argparse
from itertools import permutations
import hashlib
import json
from pathlib import Path
import numpy as np


def basis(vectors, cap=None):
    echelon={}
    for x in vectors:
        while x:
            pivot=x.bit_length()-1
            if pivot not in echelon:
                echelon[pivot]=x
                break
            x^=echelon[pivot]
        if len(echelon)==cap:
            break
    return list(echelon.values())


def pack(values):
    bits=np.packbits(values.astype(np.uint8),bitorder='little')
    return int.from_bytes(bits.tobytes(),'little')


def profile(difference):
    bits=((difference[:,None]>>np.arange(8)[None,:])&1).astype(np.uint8)
    col_bits=[pack(bits[:,j]) for j in range(8)]
    # h=0 and l=0 are fixed by the cofactor reference.
    grid=bits.reshape(76,16,8)
    cof=grid ^ grid[:,:1] ^ grid[:1,:] ^ grid[:1,:1]
    highs=basis(pack(col) for col in cof.reshape(76,128).T)
    lows=basis(pack(row) for row in cof.transpose(0,2,1).reshape(-1,16))
    return col_bits, highs, lows


def inspect(prev,cur):
    pair_profiles={(i,j):profile(prev[:,i]^cur[:,j]) for i in range(6) for j in range(6)}
    best=None
    natural=None
    min_q=128+48
    for arrangement in permutations(range(6)):
        factors=[pair_profiles[i,j] for i,j in enumerate(arrangement)]
        d=len(basis(x for c,_,_ in factors for x in c))
        h=len(basis((x for _,h,_ in factors for x in h), cap=75))
        l=len(basis((x for _,_,l in factors for x in l), cap=15))
        optimistic_borrow=48-d
        # A full high/low bank in this model requires h+l+1 independent
        # functions including the implicit constant. 11 selection bits and
        # the constant contribute at most 12. Credit ALL stable parities
        # as reusable slots, even nonseparable functions and zero values.
        optimistic_needed=max(0,h+l+1-12-optimistic_borrow)
        result=dict(slot_permutation=arrangement,transition_rank=d,high_cofactor_rank=h,
                    low_cofactor_rank=l,stable_output_parity_dimension=optimistic_borrow,
                    min_extra_qubits_for_simultaneous_bank=optimistic_needed,
                    min_total_Q=11+48+optimistic_needed)
        if arrangement==tuple(range(6)):
            natural=result
        if result['min_total_Q']<min_q:
            min_q=result['min_total_Q'];best=result
    assert best is not None and natural is not None
    return dict(natural=natural, optimistic_slot_assignment=best,
                all_slot_assignments_tested=720)


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--words',type=Path,required=True)
    p.add_argument('--out',type=Path,required=True)
    a=p.parse_args()
    raw=np.load(a.words,allow_pickle=False)[:1220].astype(np.uint8)
    digest=hashlib.sha256(raw.tobytes()).hexdigest()
    assert digest=="8caf7416de79102103757e3ab7ab4b6bbebfad9b1bf1ecd564c20eb948dbfcea"
    w=np.pad(raw[:1216],((0,0),(0,3))).reshape(1216,13,6)
    rows=[]
    for k in range(13):
        prev=(w[:,k-1,:] if k else np.zeros_like(w[:,0,:]))
        row=dict(batch=k,**inspect(prev,w[:,k,:]))
        rows.append(row)
        print(json.dumps(row),flush=True)
    a.out.write_text(json.dumps(dict(status='SIMULTANEOUS_BANK_STORAGE_BOUND',
          actual_words_sha256=digest,
          addresses=1216,layout_max_qubits=128,
          rows=rows,scope='Fixed six-word batches and 4/7 partition. All inter-slot matching permutations granted without checking the Givens order. Lower bounds for simultaneously resident independently spanning pure high and pure low feature banks, with address selections preserved and input endpoint dependence removed from borrowed output parities. Does not bound time multiplexing, new partition, or different nonlinear control functions.'),indent=2)+'\n')


if __name__=='__main__':
    main()
