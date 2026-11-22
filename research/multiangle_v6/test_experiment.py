#!/usr/bin/env python3
"""Exact algebraic tests and adversarial corrections for 20-high-state compiler."""
import sys,tempfile,unittest
from pathlib import Path
import numpy as np
sys.path.insert(0,str(Path(__file__).parent))
from basis_exchange import optimize,verify_transform,cost,xorcoefs
from global20_rank_hmr import compile_rank_r
from independent_interleaved import independent_verify
from global_20_basis import factor_selector

class TestMathematics(unittest.TestCase):
    def test_factors_rank_two_and_three(self):
        for mask in [0x101,0x10021,0x112201,0x8f5432,0x040709]:
            factors=factor_selector(mask)
            recovered=0
            for a,b in factors:
                for j in range(3):
                    if b>>j&1:recovered^=a<<(8*j)
            self.assertEqual(recovered,mask)

    def test_basis_exchange_preserves_values_and_cost(self):
        rng=np.random.default_rng(69)
        for n in [3,4,5]:
            c=[tuple(int(x) for x in rng.integers(0,2**10,size=64)) for i in range(n)]
            m=[1<<i for i in range(n)];s=m.copy()
            M,S,C,report=optimize(m,s,c,max_steps=50)
            verify_transform(M,S,C,n)
            self.assertEqual(report['cost'],sum(cost(a,b) for a,b in zip(C,S)))
            self.assertLessEqual(report['cost'],report['previous_cost'])
            for old in range(n):
                recovered=[0]*64
                for j in range(n):
                    if S[j]>>old&1:recovered=[a^b for a,b in zip(recovered,C[j])]
                self.assertEqual(tuple(recovered),c[old])

    def test_real_phase_and_wrong_cz_rejected(self):
        root=Path(__file__).resolve().parents[1]
        seed=root/'gvqcc_multiform/seeds/c46_public_v8.npz'
        if seed.exists():
            with np.load(seed,allow_pickle=False) as z:words=np.asarray(z['angle_words'],np.int64)
        else:
            from pinned_c46_words import words as pinned
            words=pinned()
        circ,stat=compile_rank_r(words,13,support=8,initial_basis='grouped',basis_exchange=True)
        self.assertGreater(stat['selector_rank_hist'].get(2,0),0)
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/'good.kmx';p.write_text('\n'.join(circ.kmx_lines())+'\n')
            result=independent_verify(p,words,13,dirty_seed=120)
            self.assertTrue(result['phase_symbols_cancel'])
            self.assertEqual(stat['CCX'],result['CCX'])
            bad=Path(td)/'bad.kmx'
            lines=p.read_text().splitlines()
            for i,line in enumerate(lines):
                if line.startswith('CZ ') and i>0 and lines[i-1].startswith('CX '):
                    lines.pop(i);break
            else:raise AssertionError('no generalized CZ correction')
            bad.write_text('\n'.join(lines)+'\n')
            with self.assertRaises(AssertionError): independent_verify(bad,words,13)

if __name__=='__main__':unittest.main(verbosity=2)
