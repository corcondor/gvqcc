"""Standalone synthetic witness for the exact GF(2) tensor rank proof.

This is an invariant test of the rank-certificate implementation, not a claim
about the real Goodpjw V8 KMB. Real bank runs require an external public V8 ZIP.
"""
import unittest

from native_kmb.real_kmb import KMB,Op
from native_kmb.tensor_obstruction import prove_restart, gf2_rank


class ExactTensorLowerBoundTests(unittest.TestCase):
    def test_rank_helper(self):
        self.assertEqual(gf2_rank([0,3,5,6]),2)
        self.assertEqual(gf2_rank([1,2,4,8]),4)

    def make_fixture(self,with_causal=False):
        ops=[Op(0x50,(126,),(0,)),Op(0x31,(0,1,2))]
        for j in range(37):
            a=3+2*j
            b=4+2*j
            if with_causal and j==1:
                # First 'later' product influences a still later control,
                # violating the independent-P0-only hypothesis.
                a=77
            ops.append(Op(0x31,(a,b,77+j)))
        ops.append(Op(0x50,(127,),(0,)))
        return KMB("synthetic",2,128,1,0,b"",ops,b"\x00"*8)

    def test_rank74_saturates_37_later_and_bound(self):
        cert=prove_restart(self.make_fixture(),1)
        self.assertEqual(cert["flattening_rank"],74)
        self.assertEqual(cert["minimum_later_AND_with_independent_P0"],37)
        self.assertTrue(cert["fixed_P0_architecture_saturates_bound"])
        self.assertEqual(cert["native_paid_CCX_saved"],0)

    def test_reject_later_product_dependency(self):
        with self.assertRaisesRegex(ValueError,"non-first product"):
            prove_restart(self.make_fixture(with_causal=True),1)


if __name__=="__main__":
    unittest.main()
