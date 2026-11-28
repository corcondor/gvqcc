import unittest,sys
from pathlib import Path
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parent))
sys.path.insert(0,str((Path(__file__).resolve().parents[1]/'gvqcc_multiform') if (Path(__file__).resolve().parents[1]/'gvqcc_multiform').exists() else Path(__file__).resolve().parents[1]))
sys.path.insert(0,str((Path(__file__).resolve().parents[1]/'gvqcc_multiform_v3') if (Path(__file__).resolve().parents[1]/'gvqcc_multiform_v3').exists() else Path(__file__).resolve().parents[1]/'multiangle_v3'))
from high_pair import compile_pairs,pair_options,choose_pairs
from multi_angle_synthesis import delta_table
from hmr_patterns import prove as prove_hmr
class TestHighPair(unittest.TestCase):
 def test_matching_no_overlapping(self):
  groups=[[0]*64 for _ in range(9)]
  pairs=choose_pairs([(4,0,1,0,0,0),(3,1,2,0,0,0),(2,3,4,0,0,0)],'exact')
  self.assertEqual(len(set(x for pair in pairs for x in pair)),2*len(pairs))
 def test_complete_small_random_dirty_and_phase(self):
  for n in (70,129):
   w=np.random.default_rng(n+31).integers(0,128,(n,75),dtype=np.int64)
   for slot in (0,2,14):
    for strategy in ('greedy','exact','random-1'):
     h,stat=compile_pairs(w,slot,strategy)
     self.assertLessEqual(h.num_qubits,128)
     self.assertTrue(prove_hmr(h,delta_table(w,slot),2)['all_HMR_phase_symbols_cancel'])
     self.assertTrue(prove_hmr(h,delta_table(w,slot),8)['all_valid_addresses'])
if __name__=='__main__':unittest.main()
