"""Synthetic exhaustive state-vector-bitset tests for generic ANGLE KMX oracle."""
import sys
import unittest
from pathlib import Path
import numpy as np

sys.path.insert(0,str(Path(__file__).resolve().parent))
from generic_angle_loader import compile_slot, delta_table, bitparallel_proof


class GenericAngleLoaderTest(unittest.TestCase):
    def test_each_boundary_and_arbitrary_dirty_target(self):
        words=np.random.default_rng(72).integers(0,128,size=(35,75),dtype=np.int64)
        for slot in [0,1,14]:
            lines,stat=compile_slot(words,slot)
            self.assertEqual(stat["num_qubits"],82)
            self.assertGreater(stat["CCX"],0)
            for dirty_seed in [0,19]:
                result=bitparallel_proof(lines,delta_table(words,slot),dirty_seed)
                self.assertTrue(result["exact_all_addresses"])
                self.assertTrue(result["scratch_clean"])
                self.assertTrue(result["relative_phase_zero_by_gate_set"])

    def test_all_zero_delta_and_partial_last_block(self):
        words=np.zeros((33,75),dtype=np.int64)
        lines,stat=compile_slot(words,2)
        self.assertEqual(stat["active_rows"],0)
        self.assertTrue(bitparallel_proof(lines,delta_table(words,2))["tags_unchanged"])

    def test_invalid_table_rejected(self):
        with self.assertRaises(ValueError):
            compile_slot(np.zeros((35,70),dtype=np.int64),1)
        with self.assertRaises(ValueError):
            compile_slot(np.full((35,75),128,dtype=np.int64),1)


if __name__=="__main__":
    unittest.main()
