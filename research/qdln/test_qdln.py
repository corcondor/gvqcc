#!/usr/bin/env python3
"""Self-contained regression tests; invoke: python research/qdln/test_qdln.py."""
from pathlib import Path
from itertools import combinations
import sys
sys.path.insert(0,str(Path(__file__).parent))
from solver import synthesize
from reversible import compile_oracle,verify_clean_xor

# Pinned from public goodpjw2008 3,375T chemistry angle_words:
# batch 2, high row 58 (16 low-address values), quadratic/affine outputs.
ANGLE_BATCH2_HIGH58=[23205,36873,36873,13107,42405,36174,36174,42330,39321]


def main():
    for quadratic in range(64):
        truth=0
        for x in range(16):
            y=0
            for j,(i,k) in enumerate(combinations(range(4),2)):
                if (quadratic>>j)&1:y ^= ((x>>i)&1)&((x>>k)&1)
            truth|=y<<x
        sol=synthesize([truth])
        assert sol.verify()
        assert verify_clean_xor(sol)
    sample=synthesize(ANGLE_BATCH2_HIGH58)
    assert sample.verify()
    assert sample.cost()["naive_shared_ANF_AND"]==6
    assert sample.cost()["qdln_AND"]==2
    assert verify_clean_xor(sample,all_y=True)  # 16 * 512 possible input/output states
    oracle=compile_oracle(sample)
    assert oracle.resource_count()["paid_Toffolis"]==4
    assert oracle.width==15
    print("EXACT_PASS",sample.cost(),oracle.resource_count())
    try:
        import torch
    except ImportError:
        print("SKIP differentiable training: torch not installed")
    else:
        from learn import train
        learned,receipt=train(ANGLE_BATCH2_HIGH58,number_of_ands=2,
                              epochs=800,restarts=8,seed=42)
        assert learned is not None,receipt
        assert learned.verify()
        assert verify_clean_xor(learned)
        print("NEURAL_CERTIFIED_PASS",receipt)


if __name__=="__main__":main()
