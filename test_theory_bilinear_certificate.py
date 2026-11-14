"""Independent semantic regression of the shipped whole multiplication block."""
from collections import Counter
from pathlib import Path
import unittest

from dqi_ccx_input_factor import exact_polynomial_check
from theory_bilinear_verify import parse


class ExactBilinearCertificateTests(unittest.TestCase):
    def test_full_arbitrary_accumulator_map_and_resource_counts(self):
        root = Path(__file__).resolve().parent
        before = parse(root / 'inverse_v2_actual_eea_product.kmx')
        after = parse(root / 'theory_bilinear_actual_cpr.kmx')
        proof = exact_polynomial_check(before, after)
        self.assertEqual(proof['status'], 'PASS')
        self.assertEqual(proof['input_variables'], 72)
        self.assertEqual(proof['maximum_output_degree'], 2)
        self.assertEqual(Counter(x.opcode for x in before), {0x21: 6122, 0x31: 99})
        self.assertEqual(Counter(x.opcode for x in after), {0x21: 1535, 0x31: 99})

    def test_missing_nonlinear_product_is_rejected(self):
        root = Path(__file__).resolve().parent
        before = parse(root / 'inverse_v2_actual_eea_product.kmx')
        after = parse(root / 'theory_bilinear_actual_cpr.kmx')
        index = next(i for i, operation in enumerate(after) if operation.opcode == 0x31)
        del after[index]
        with self.assertRaises(AssertionError):
            exact_polynomial_check(before, after)


if __name__ == '__main__':
    unittest.main()
