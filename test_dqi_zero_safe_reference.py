#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Unseeded exact algebra tests plus independent deterministic adversarial fixtures."""
import random
import unittest
from dqi_zero_safe_reference import (
    gmul, ginv, absolute_trace, qrem, qmul, norm_inv_quadratic,
    pmul, add, divrem, step, trim, extract_zero_safe
)

BASIS = (6, 20, 72, 272)
KAPPAS = [2048 ^ (6 if i & 1 else 0) ^ (20 if i & 2 else 0) ^
          (72 if i & 4 else 0) ^ (272 if i & 8 else 0) for i in range(16)]
# The published 2026-11-15 weight31 slot13 failing quantum decoder fixture.
N13 = [1575,511,3039,1239,1384,1941,1863,2028,2122,166,703,2445,1984,3853,2001,316,1639,2186]
D13 = [1791,1861,1515,3980,3674,3700,3609,3772,3580,804,1643,3795,2549,2683,357,197,1499,1951,1433]

class TestZeroSafe(unittest.TestCase):
    def test_field_irreducibility(self):
        self.assertEqual(len(set(KAPPAS)), 16)
        self.assertTrue(all(absolute_trace(k) == 1 for k in KAPPAS))
        for k in KAPPAS:
            for a in ((1,0),(0,1),(123,456),(4095,4095)):
                self.assertEqual(qmul(a, norm_inv_quadratic(a,k),k),(1,0))
        for a in (1, 2, 3, 127, 2048, 4095): self.assertEqual(gmul(a, ginv(a)),1)

    def test_real_nonterminal_zero_pivot_13(self):
        k13, k14 = KAPPAS[13], KAPPAS[14]
        self.assertEqual(k13,2398)
        self.assertEqual(qrem(N13,k13),(0,0))
        self.assertEqual(qrem(D13,k13),(1013,2476))
        # Two-pivot S M14 M13 S chart already discovered in old research.
        first_n, first_d, h13 = step(D13,N13,k13)
        self.assertEqual(h13,(0,0))
        self.assertEqual(qrem(first_n,k14),(1067,2334))
        second_n, second_d, h14 = step(first_n,first_d,k14)
        self.assertLessEqual(len(second_d),len(N13)-2)
        self.assertLessEqual(len(second_n),len(D13)-2)
        # Reverse S M14 M13 S exactly.
        inverse_n, inverse_d = second_d, second_n  # final chart after S
        inverse_n, inverse_d = inverse_d, inverse_n  # undo S
        inverse_n, inverse_d = inverse_d, add(pmul([k14,1,1],inverse_n),pmul(h14,inverse_d))
        inverse_n, inverse_d = inverse_d, add(pmul([k13,1,1],inverse_n),pmul(h13,inverse_d))
        inverse_n, inverse_d = inverse_d, inverse_n
        self.assertEqual((inverse_n,inverse_d),(N13,D13))

    def test_full_adaptive_recovery_with_nonterminal_zero(self):
        # A genuine nonterminal zero in the first pivot of a 9-step extraction.
        rng = random.Random(202611170910)
        ks = KAPPAS[6:15]
        n = pmul([ks[0],1,1],[rng.randrange(4096) for _ in range(6)])
        d = [rng.randrange(4096) for _ in range(10)]
        d[-1] = 1
        self.assertEqual(qrem(n,ks[0]),(0,0))
        result = extract_zero_safe(n,d,ks)
        self.assertEqual(result.reverse(),(n,d))
        self.assertGreaterEqual(result.skipped_initial_zeros,1)
        self.assertNotEqual(result.steps[0].index,0)
        self.assertEqual(result.numerator,[])
        self.assertEqual(len(result.denominator),1)

    def test_4096_random_and_adversarial_pairs(self):
        rng=random.Random(202611170911)
        for j in range(4096):
            r=rng.randrange(1,17)
            ks=KAPPAS[:r]
            n=[rng.randrange(4096) for _ in range(r)]
            d=[rng.randrange(4096) for _ in range(r+1)]
            # Force thousands of q-divisible (but nonzero) numerators.
            if j%2==0 and r>=3:
                n=pmul([ks[0],1,1],[rng.randrange(4096) for _ in range(r-2)])
                self.assertEqual(qrem(n,ks[0]),(0,0))
            if not n or not any(n): n=[1]
            if not d or not any(d): d=[1]
            # Require exactly 4096 coprime-domain cases, not just attempts.
            n=trim(n); d=trim(d)
            for repair in range(100):
                x,y=n[:],d[:]
                while y: x,y=y,divrem(x,y)[1]
                if len(x) == 1: break
                d[0] ^= rng.randrange(1,4096)
            else: self.fail('Could not construct coprime denominator')
            result=extract_zero_safe(n,d,ks)
            self.assertEqual(result.reverse(),(n,d))
            self.assertEqual(result.numerator,[])
            self.assertEqual(len(result.denominator),1)

    def test_repeated_public_node_is_not_silently_accepted(self):
        with self.assertRaisesRegex(ValueError,'Repeated public quadratic'):
            extract_zero_safe([1],[1,1],[2048,2048])

if __name__=='__main__': unittest.main(verbosity=2)