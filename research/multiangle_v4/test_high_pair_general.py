import unittest,sys
from pathlib import Path
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parent))
sys.path.insert(0,str((Path(__file__).resolve().parents[1]/'gvqcc_multiform') if (Path(__file__).resolve().parents[1]/'gvqcc_multiform').exists() else Path(__file__).resolve().parents[1]))
sys.path.insert(0,str((Path(__file__).resolve().parents[1]/'gvqcc_multiform_v3') if (Path(__file__).resolve().parents[1]/'gvqcc_multiform_v3').exists() else Path(__file__).resolve().parents[1]/'multiangle_v3'))
from high_pair_general import compile_general,full_domain_prove
from multi_angle_synthesis import delta_table
class T(unittest.TestCase):
 def test_all_cases(self):
  for n in (68,195):
   w=np.random.default_rng(n).integers(0,128,(n,75),dtype=np.int64)
   for k in (0,3,14):
    for mode in ('greedy','exact'):
     c,s=compile_general(w,k,mode)
     self.assertLessEqual(c.num_qubits,128)
     for seed in (1,5):
      p=full_domain_prove(c,delta_table(w,k),seed)
      self.assertTrue(p['all_HMR_symbols_cancel'])
if __name__=='__main__':unittest.main()
