"""Exact exhaustive tests: reversible state update blocks, no unverified score claim."""
import itertools
import unittest

from griffith_qcc.state_feedback import (
    d_latch, d_latch_via_ccx, lfsr_step,
    mux_factored, mux_naive, parity_control_factored,
    parity_control_naive, t_flip
)


def apply(ops, xs):
    x = list(xs)
    for g in ops:
        if g[0] == "X":
            x[g[1]] ^= 1
        elif g[0] == "CX":
            x[g[2]] ^= x[g[1]]
        elif g[0] == "CCX":
            x[g[3]] ^= x[g[1]] & x[g[2]]
        elif g[0] == "SWAP":
            x[g[1]], x[g[2]] = x[g[2]], x[g[1]]
        elif g[0] == "CSWAP":
            if x[g[1]]:
                x[g[2]], x[g[3]] = x[g[3]], x[g[2]]
        else:
            raise AssertionError(g)
    return x


class TestStateFeedback(unittest.TestCase):
    def test_d_latch(self):
        for x in itertools.product(range(2), repeat=3):
            expected = [x[0], x[2] if x[0] else x[1], x[1] if x[0] else x[2]]
            for circuit in (d_latch(0,1,2), d_latch_via_ccx(0,1,2)):
                self.assertEqual(apply(circuit,x), expected)
                self.assertEqual(apply(reversed(circuit), expected), list(x))

    def test_t_flip(self):
        for x in itertools.product(range(2),repeat=3):
            self.assertEqual(apply(t_flip(0,1,2),x),[x[0],x[1],x[2]^(x[0]&x[1])])

    def test_mux(self):
        for x in itertools.product(range(2),repeat=4):
            for f in (mux_naive,mux_factored):
                gates=f(0,1,2,3)
                expect=[x[0],x[1],x[2],x[3]^(x[2] if x[0] else x[1])]
                self.assertEqual(apply(gates,x),expect)
                self.assertEqual(apply(reversed(gates),expect),list(x))

    def test_parity(self):
        for n in range(1,7):
            for x in itertools.product(range(2),repeat=n+2):
                expect=list(x)
                expect[-1] ^= x[0] & (sum(x[1:-1])&1)
                for f in (parity_control_naive,parity_control_factored):
                    gates=f(0,list(range(1,n+1)),n+1)
                    self.assertEqual(apply(gates,x),expect)
                    self.assertEqual(apply(reversed(gates),expect),list(x))

    def test_lfsr(self):
        for n in range(2,9):
            gates=lfsr_step(list(range(n)))
            for x in itertools.product(range(2),repeat=n):
                expect=list(x[1:])+[x[0]^x[-1]]
                self.assertEqual(apply(gates,x),expect)
                self.assertEqual(apply(reversed(gates),expect),list(x))


if __name__ == "__main__":
    unittest.main()
