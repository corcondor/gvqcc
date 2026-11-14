"""Independent regression proofs for input-side Toffoli factorization."""
import unittest

from dqi_ccx_input_factor import (identity_check, optimize_block,
                                  exact_polynomial_check, pair_operands)
from dqi_ccx_peephole import Operation


class InputFactorizationTests(unittest.TestCase):
    def test_identity_on_every_four_bit_input_and_condition(self):
        self.assertEqual(identity_check()["checks"], 32)

    def test_interleaved_three_product_banks_exactly(self):
        before = [Operation(0x31, (common, shared, 15+common), source_index=12*bank+common)
                  for bank, shared in enumerate((12, 13, 14)) for common in range(12)]
        after, certificate = optimize_block(before, 256)
        self.assertEqual(len(certificate), 24)
        self.assertEqual(sum(op.is_ccx for op in after), 12)
        proof = exact_polynomial_check(before, after)
        self.assertEqual(proof["input_variables"], 27)
        self.assertEqual(proof["all_basis_states_covered"], 134217728)

    def test_operand_order_does_not_matter(self):
        for first in ((0, 1, 3), (1, 0, 3)):
            for second in ((0, 2, 3), (2, 0, 3)):
                before = [Operation(0x31, first), Operation(0x31, second)]
                after, certificate = optimize_block(before, 256)
                self.assertEqual(len(certificate), 1)
                exact_polynomial_check(before, after)

    def test_barriers_and_different_classical_conditions(self):
        a, b = Operation(0x31, (0, 1, 3)), Operation(0x31, (0, 2, 3))
        for barrier in (Operation(0x11, (0,)), Operation(0x12, (4,)),
                        Operation(0x50, (4,), bit=0), Operation(0x81, condition=0),
                        Operation(0x01), Operation(0xC2, bit=0, condition=1)):
            original = [a, barrier, b]
            after, certificate = optimize_block(original, 256)
            self.assertEqual(certificate, [])
            self.assertEqual(after, original)
        self.assertIsNone(pair_operands(Operation(0xB1, (0, 1, 3), condition=0),
                                        Operation(0xB1, (0, 2, 3), condition=1)))

    def test_independent_polynomial_proof_rejects_wrong_rewrite(self):
        before = [Operation(0x31, (0, 1, 3)), Operation(0x31, (0, 2, 3))]
        wrong = [Operation(0x21, (1, 2)), Operation(0x31, (0, 2, 3))]
        with self.assertRaises(AssertionError):
            exact_polynomial_check(before, wrong)


if __name__ == "__main__":
    unittest.main()
