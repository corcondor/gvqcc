"""Read real 15-bank angle-word targets and audit nonlinear helper contracts.

Data is never downloaded or committed. Supply a local .npz with angle_words.
For V8, words have 7 active bits and 75 columns, grouped 5 per bank.
The conserved five helper functions are bit5 XOR bit6 of each word.
"""
from __future__ import annotations
from dataclasses import dataclass, asdict
from pathlib import Path
import json


def rank_gf2(values) -> int:
    basis = {}
    for y in values:
        x = int(y)
        while x:
            j = x.bit_length()-1
            if j in basis:x ^= basis[j]
            else:basis[j] = x;break
    return len(basis)


def load_words(path):
    import numpy as np
    with np.load(path,allow_pickle=False) as z:
        w=np.asarray(z['angle_words'],dtype=np.int16)
    if w.ndim!=2 or w.shape[1] != 75 or not 0 <= w.min() or w.max() >= 128:
        raise ValueError('requires shape [addresses,75] and 7-bit words')
    return w


def bank_delta_tables(words, *, high_block: int=0) -> list[list[int]]:
    """Packed 16-row low-address truth tables, all 35 outputs in all 15 banks.

    Last partial block is invalid for this simple demonstration; full synthesis
    must treat these as don't-care rows with an explicit valid-address mask.
    """
    lo=16*high_block
    if lo+16>len(words):raise ValueError('need 16 legal addresses for this block')
    delta=[]
    for k in range(15):
        table=[]
        for j in range(5):
            for b in range(7):
                v=0
                for a in range(16):
                    w=int(words[lo+a,5*k+j]);v0=int(words[lo+a,5*(k-1)+j]) if k else 0
                    v|=(((w ^ v0)>>b)&1)<<a
                table.append(v)
        delta.append(table)
    return delta


def helper_report(words) -> dict:
    n=len(words)
    violations=0;nonlow=0
    low_helpers=[]
    for j in range(5):
        helper=[((int(words[a,j])>>5)^(int(words[a,j])>>6))&1 for a in range(n)]
        low_helpers.append(helper)
        for k in range(1,15):
            for a in range(n):
                other=((int(words[a,5*k+j])>>5)^(int(words[a,5*k+j])>>6))&1
                violations+=int(helper[a] != other)
        for a in range(n):
            if helper[a] != helper[a%16]:nonlow+=1
    basic=[(1<<16)-1]+[sum(((a>>i)&1)<<a for a in range(16)) for i in range(4)]
    h=[sum(x[a]<<a for a in range(16)) for x in low_helpers]
    return {'addresses':n,'banks':15,'helper_positions':5,'helper_time_invariance_violations':violations,
            'helper_low_address_violations':nonlow,'low_affine_rank':rank_gf2(basic),
            'low_helper_augmented_rank':rank_gf2(basic+h),
            'helper_tt_hex':[hex(x) for x in h],
            'usable_in_six_extra_AND_cache': violations == 0 and nonlow == 0 and rank_gf2(basic+h)==10}


def audit(path: str) -> dict:
    words=load_words(path)
    helpers=helper_report(words)
    deltas=bank_delta_tables(words)
    full_rank=[rank_gf2([x for bank in deltas for x in bank])]
    return {'input':str(path),'helpers':helpers,'low_block_crossbank_rank':full_rank[0],
            'disclaimer':'No native KickMix score was measured.'}


def main():
    import argparse
    p=argparse.ArgumentParser()
    p.add_argument('submission_npz',type=Path)
    p.add_argument('--json',type=Path)
    a=p.parse_args()
    rep=audit(str(a.submission_npz))
    s=json.dumps(rep,indent=2,ensure_ascii=False)
    if a.json:a.json.write_text(s+'\n')
    print(s)

if __name__=='__main__': main()
