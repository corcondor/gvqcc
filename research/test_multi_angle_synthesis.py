"""Algebraic and oracle correctness across all constructive families."""
import unittest
import io
from pathlib import Path
import sys
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parent))
from multi_angle_synthesis import (ALGORITHMS,synthesize,delta_table,prove,rank_output_basis,mobius_low_anf,word_masks)

class TestMultiAngle(unittest.TestCase):
    def test_full_exact_oracles_dirty_and_partial(self):
        for n in (17,35,79):
            words=np.random.default_rng(141+n).integers(0,128,(n,75),dtype=np.int64)
            for method in ALGORITHMS:
                for slot in (0,1,14):
                    c,stats=synthesize(words,slot,method)
                    for seed in (0,11):
                        status=prove(c,delta_table(words,slot),seed)
                        self.assertTrue(status['all_valid_addresses'])
                    self.assertLessEqual(stats['qubits'],128)
    def test_zero_table_and_boundary(self):
        for method in ALGORITHMS:
            words=np.zeros((35,75),dtype=np.int64)
            c,stats=synthesize(words,14,method)
            self.assertTrue(prove(c,delta_table(words,14))['scratch_clean'])
    def test_native_kmx_parser_if_installed(self):
        try:
            import kickmix as km
        except ImportError:
            self.skipTest('native kickmix is not installed in this interpreter')
        words=np.random.default_rng(18).integers(0,128,(17,75),dtype=np.int64)
        for method in ALGORITHMS:
            c,stats=synthesize(words,0,method)
            blob=io.BytesIO(('\n'.join(c.kmx_lines())+'\n').encode())
            circuit=km.Circuit.from_file(blob,format='kmx')
            self.assertEqual(circuit.num_qubits,stats['qubits'])

    def test_mobius_and_rank_basis(self):
        rng=np.random.default_rng(3)
        for _ in range(8):
            masks=[int(x) for x in rng.integers(0,1<<16,16)]
            coeff=mobius_low_anf(masks)
            basis,forms=rank_output_basis(coeff)
            for s in range(16):
                recomposed=0
                for j,p in enumerate(basis):
                    low_form=0
                    for monomial in range(16):
                        if (forms[j]>>monomial)&1 and s&monomial==monomial:
                            low_form ^= 1
                    if low_form:recomposed ^= p
                self.assertEqual(recomposed,masks[s])

if __name__=='__main__':unittest.main()