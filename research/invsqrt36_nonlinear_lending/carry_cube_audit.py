"""Reproduce the PR71 frozen finite-certificate audit (no circuit changes).
Run: python research/invsqrt36_nonlinear_lending/carry_cube_audit.py
"""
import itertools
import json
import re
from pathlib import Path

SOURCE = Path(__file__).parent / "lean" / "V20CarryReuse.lean"
CUBE = [5, 7, 35, 85, 97, 98, 105, 109]
AFFECTED = [42, 49, 54, 55, 61, 62, 74, 77]

def load_columns():
    rows = [int(x) for x in re.search(r"def rows : List Nat := \[([^\]]+)\]", SOURCE.read_text()).group(1).split(",")]
    assert len(rows) == 117
    cols = [sum(((r >> j) & 1) << i for i, r in enumerate(rows)) for j in range(117)]
    return rows, cols

def build_basis(vs):
    b = {}
    for j, v in enumerate(vs):
        coeff = 1 << j
        while v:
            p = v.bit_length() - 1
            if p not in b:
                b[p] = (v, coeff)
                break
            w, c = b[p]
            v ^= w
            coeff ^= c
    return b

def coordinates(v, basis):
    out = 0
    while v:
        w, c = basis[v.bit_length()-1]
        v ^= w
        out ^= c
    return out

def verify_nand_bdd(*, legal, wires, one, zero, band, bxor):
    """Full-domain proof hook for canonical symbolic BDD values from a native replay.
    Does NOT run without the actual PR68 parent and verifier. Caller must establish
    wire indexing, cut identity, legal mask, and canonical equality for all HMRs.
    """
    diff = bxor(wires[36], bxor(one, band(wires[19], wires[25])))
    return band(legal, diff) == zero

def main():
    rows, c = load_columns()
    full = build_basis(c)
    assert len(full) == 117
    dual = sum(1 << i for i in CUBE)
    odd = lambda v: (v & dual).bit_count() & 1
    assert all(not odd(c[i] & c[j]) for i in range(37) for j in range(37))
    assert [i for i in range(80) if odd(c[37+i])] == AFFECTED
    low = [rows[i] & ((1<<37)-1) for i in CUBE]
    diffs = {x ^ low[0] for x in low}
    assert len(diffs) == 8 and all(a^b in diffs for a in diffs for b in diffs)
    q2 = [c[i]&c[j] for i,j in itertools.combinations(range(1,37),2)]
    cubic = [t for t in itertools.combinations(range(1,36),3) if odd(c[t[0]]&c[t[1]]&c[t[2]])]
    assert len(cubic) == 14
    assert len(build_basis(c[:37]+q2)) == 116
    assert len(build_basis(c[:37]+q2+[c[2]&c[3]&c[5]])) == 117
    nands = [(i-1,j-1,k) for i,j in itertools.combinations(range(1,36),2)
             for k in range(2) if c[36] == (c[i]&c[j]) ^ (c[0] if k else 0)]
    assert nands == [(19,25,1)]
    # All 666 nonzero affine factors with support <=2 (constant omitted,
    # since complement adds only an affine correction). No native synthesis.
    forms = c[1:37]+[c[i]^c[j] for i,j in itertools.combinations(range(1,37),2)]
    assert len(forms) == 666
    residues = set()
    hits = {0:0,1:0,2:0}
    total=0
    for a,b in itertools.combinations(forms,2):
        q = coordinates(a&b,full)>>37
        total += 1
        if q: residues.add(q)
        w=q.bit_count()
        if w in hits: hits[w]+=1
    receipt = {
      "scope":"PR71 117-row finite certificate only",
      "candidate_pairs":total,"nonzero_distinct_residues":len(residues),
      "zero_hits":hits[0],"single_hits":hits[1],"pair_hits":hits[2],
      "distinct_single":sum(x.bit_count()==1 for x in residues),
      "distinct_pair":sum(x.bit_count()==2 for x in residues),
      "cube_rows_zero_based":CUBE,"third_difference_product_columns":AFFECTED,
      "degree_ranks":[37,116,117],"nand_candidate":nands,
      "full_domain_nand_proven":False,"native_gate_change":False,
      "official_score_gain":False}
    assert (total,len(residues),hits[0],hits[1],hits[2])==(221445,30307,44434,6168,10528)
    print(json.dumps(receipt,indent=2))
if __name__=="__main__":
    main()
