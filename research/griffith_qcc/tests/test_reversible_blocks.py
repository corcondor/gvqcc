"""Proof-by-exhaustion for the new reversible arithmetic library.

NOT a native KickMix or Kaggle score test. These X/CX/CCX blocks are exact
permutations, hence classical full-input proof extends to superpositions.
"""
import itertools
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from griffith_qcc.reversible_blocks import (
    add_three_mod, csa_three, and_fanout, and_clean_cache, simulate, costs
)


class ReversibleArithmeticTest(unittest.TestCase):
    def test_three_sum_and_reversal(self):
        for n in range(1,5):
            ops,regs=add_three_mod(n)
            self.assertEqual(costs(ops,regs)["CCX"],4*(n-1))
            self.assertEqual(costs(ops,regs)["qubits"],4*n+1)
            for a,b,c in itertools.product(range(1<<n),repeat=3):
                x=[(z>>i)&1 for z in (a,b,c,0) for i in range(n)]+[0]
                y=simulate(ops,x)
                self.assertEqual(y[:3*n],x[:3*n])
                self.assertEqual(y[4*n],0)
                self.assertEqual(sum(y[3*n+i]<<i for i in range(n)),(a+b+c)%(1<<n))
                self.assertEqual(simulate(list(reversed(ops)),y),x)

    def test_carry_save_contract(self):
        for n in range(1,5):
            ops,regs=csa_three(n)
            self.assertEqual(costs(ops,regs)["CCX"],2*n)
            self.assertEqual(costs(ops,regs)["qubits"],5*n)
            for a,b,c in itertools.product(range(1<<n),repeat=3):
                x=[(z>>i)&1 for z in (a,b,c,0,0) for i in range(n)]
                y=simulate(ops,x)
                self.assertEqual(y[:3*n],x[:3*n])
                s=sum(y[3*n+i]<<i for i in range(n))
                k=sum(y[4*n+i]<<i for i in range(n))
                self.assertEqual(s+2*k,a+b+c)
                self.assertEqual(simulate(list(reversed(ops)),y),x)

    def test_and_fanout_preserves_dirty_targets(self):
        for m in range(1,7):
            ops=and_fanout(0,1,list(range(2,m+2)))
            for v in range(1<<(m+2)):
                x=[(v>>i)&1 for i in range(m+2)]
                y=simulate(ops,x)
                self.assertEqual(y[:2],x[:2])
                self.assertEqual(y[2:],[z^(x[0]&x[1]) for z in x[2:]])
                self.assertEqual(simulate(list(reversed(ops)),y),x)

    def test_cache_clean(self):
        for m in range(1,7):
            ops=and_clean_cache(0,1,2,list(range(3,m+3)))
            for v in range(1<<(m+2)):
                x=[(v>>i)&1 for i in range(m+3)]
                x[2]=0
                y=simulate(ops,x)
                self.assertEqual(y[:3],x[:3])
                self.assertEqual(y[3:],[z^(x[0]&x[1]) for z in x[3:]])
                self.assertEqual(simulate(list(reversed(ops)),y),x)


if __name__=="__main__":
    unittest.main()
