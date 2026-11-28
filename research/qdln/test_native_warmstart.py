"""Regression certificates for native QDLN warm-start and polar-rank bounds.

Run: python research/qdln/test_native_warmstart.py

The full 15-KMB + 2,438-input replay requires the user's public V8 archive
and is in the companion research reproducer, not in this CI fixture.
"""
from native_warmstart import (extract_pre_hmr, gf2_rank, polar_rank,
                              output_witness, lower_bound)


def run():
    # A cached AND is created, followed by one genuine output AND and a
    # fanout CX; no later output-product control depends on that result.
    ops=[(0x31,(0,1,4)),(0x21,(4,2)),(0x31,(2,3,5)),
         (0x21,(5,6)),(0x50,(4,))]
    d=extract_pre_hmr(ops,7,cache_ccx=1)
    assert d["pre_hmr_paid"]==2
    assert d["paid_tail"]==1
    assert d["terms"][0]["a"]==str(1<<2)
    assert d["terms"][0]["b"]==str(1<<3)
    assert int(d["terms"][0]["effect"])==(1<<5)|(1<<6)
    assert d["formal_parent_exact"]
    assert gf2_rank([1,2,3])==2

    # Four disjoint quadratic products selected by a single output XOR mask
    # have an alternating polar matrix of rank 8, hence >=4 ANDs.
    terms=[{"a":str(1<<(2*i)),"b":str(1<<(2*i+1)),
            "effect":str(1<<(11+i))} for i in range(4)]
    w=output_witness([int(t["effect"]) for t in terms])
    assert w is not None
    assert polar_rank(terms,w,8)==8
    a={"qubits":8,"terms":terms,"nonlinear_feedback_sites":[]}
    cert=lower_bound(a,list(range(4)))
    assert cert["min_AND"]==4 and cert["saturates_formal_bound"]

    # Bound applies to formal cached inputs, not restricted reachable words.
    assert "formal" in cert["scope"]
    print("NATIVE_QDLN_GF2_PASS",cert)


if __name__=="__main__":run()
