#!/usr/bin/env python3
"""Check row-specific low permutations compatible with all current affine word codes."""
from __future__ import annotations
import argparse
from collections import Counter
from itertools import permutations
import hashlib
import json
from pathlib import Path
import numpy as np


def linear_mask(function):
    """Return the coefficient of a four-bit affine Boolean truth table."""
    a = int(function[0])
    mask = sum((int(function[1 << i]) ^ a) << i for i in range(4))
    if any(int(value) != (a ^ ((l & mask).bit_count() & 1))
           for l, value in enumerate(function)):
        return None
    return mask


def rank(vectors):
    basis={}
    for v in vectors:
        while v:
            h=v.bit_length()
            if h not in basis:
                basis[h]=v
                break
            v ^= basis[h]
    return len(basis)


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--words', type=Path, required=True)
    p.add_argument('--out', type=Path, required=True)
    a=p.parse_args()
    words=np.load(a.words,allow_pickle=False)[:1220].astype(np.uint8)
    digest=hashlib.sha256(words.tobytes()).hexdigest()
    assert digest == "8caf7416de79102103757e3ab7ab4b6bbebfad9b1bf1ecd564c20eb948dbfcea"
    pairs=((0,1),(0,2),(1,2),(0,3),(1,3))
    tags=[tuple(((l >> x) & (l >> y) & 1) for x,y in pairs) for l in range(16)]
    classes=Counter(tags)
    zero=[l for l in range(16) if not any(tags[l])]
    nonzero=[l for l in range(16) if any(tags[l])]
    assert sorted(classes.values()) == [1] * 10 + [6]
    assert len(nonzero)>8
    rows=[]
    for h in range(76):
        block=words[16*h:16*h+16]
        entries=[]
        for j in range(75):
            bits=block[:,j]&1
            coeff=linear_mask(bits)
            if coeff is not None:
                entries.append((j,coeff))
        rr=rank([coeff for _, coeff in entries])
        # If existing affine columns span all four coordinate functions, a
        # permutation preserving them must itself be affine.  Preserving each
        # borrowed tag fixes its ten singleton fibers pointwise.  An affine
        # permutation on F2^4 with >8 fixed points is the identity.
        if rr == 4:
            allowed=1
        else:
            allowed=0
            for reorder in permutations(zero):
                perm=list(range(16))
                for x,y in zip(zero,reorder):
                    perm[x]=y
                def rho(l):
                    address=16*h+l
                    return 0 if address <76 else 1+(address-76)//143
                if any(rho(l)!=rho(perm[l]) for l in range(16)):
                    continue
                if all(linear_mask(block[perm,j]&1) is not None for j,_ in entries):
                    allowed += 1
        rows.append(dict(h=h, affine_existing_columns=len(entries), gradient_rank=rr,
                         group_tag_and_affine_preserving_permutations=allowed))

    assert words.shape == (1220,75)
    actual_tags = ((words >> 6) ^ (words >> 7)) & 1
    for j in range(75):
        assert np.array_equal(actual_tags[:,j],
                np.array([tags[l&15][j%5] for l in range(1220)],dtype=np.uint8))

    partial_zero = [l for l in range(4) if not any(tags[l])]
    assert partial_zero == [0, 1, 2]
    partial_results = []
    for reorder in permutations(partial_zero):
        reordered = words.copy()
        for l, old in zip(partial_zero, reorder):
            reordered[1216+l] = words[1216+old]
        cur = reordered.reshape(1220,15,5)
        prev = np.concatenate([np.zeros_like(cur[:,:1]),cur[:,:-1]],axis=1)
        delta = prev ^ cur
        ranks=[]
        for k in range(15):
            # All 77 high rows have the last row's four valid low states
            # available. Check rank over those 3 nonanchor directions.
            points=(delta[:,k,:].astype(np.uint64)
                    << np.arange(0,40,8,dtype=np.uint64)).sum(axis=1)
            pivots=[]
            for h in range(1,77):
                row=0
                for l in range(1,4):
                    mixed=points[h*16+l] ^ points[h*16] ^ points[l] ^ points[0]
                    row |= int(mixed) << (40*(l-1))
                pivots.append(row)
            ranks.append(rank(pivots))
        partial_results.append(dict(permutation=reorder, cofactor_high_ranks=ranks,
                                   batches_requiring_extra_high_rank=sum(v>75 for v in ranks)))
    report=dict(status='FIXED_TAG_AND_EXISTING_AFFINE_CODE_ROW_PERMUTATIONS',
                source_uint8_sha256=digest,
                gradient_rank_histogram=dict(Counter(row['gradient_rank'] for row in rows)),
                non_identity_complete_row_choices=sum(row['group_tag_and_affine_preserving_permutations'] - 1 for row in rows),
                complete_rows=rows,
                partial_row_allowed_upper_bound=6,
                partial_row_permutation_results=partial_results,
                scope='Relabeling low slots inside each complete high row and group, preserving existing affine bit0 columns and the five borrowed tag functions. Dropping a code, changing tag conventions, or mixing high rows with low coordinates is outside this test.')
    a.out.write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({k:v for k,v in report.items() if k!='complete_rows'}))


if __name__=='__main__':
    main()
