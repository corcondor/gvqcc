import unittest,sys
from pathlib import Path
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parent))
sys.path.insert(0,str((Path(__file__).resolve().parents[1]/'gvqcc_multiform') if (Path(__file__).resolve().parents[1]/'gvqcc_multiform').exists() else Path(__file__).resolve().parents[1]))
sys.path.insert(0,str((Path(__file__).resolve().parents[1]/'gvqcc_multiform_v3') if (Path(__file__).resolve().parents[1]/'gvqcc_multiform_v3').exists() else Path(__file__).resolve().parents[1]/'multiangle_v3'))
from global_cofactor import *
from multi_angle_synthesis import delta_table,word_masks
from hmr_patterns import prove as prove_hmr

class TestGlobalFactor(unittest.TestCase):
 def test_kernel_guarantee(self):
  import random
  rng=random.Random(5)
  for _ in range(30):
   rows=[rng.getrandbits(35) for _ in range(20)]
   kl=kernel([x^rows[0] for x in rows[1:]])
   self.assertTrue(all(parity(a,x^rows[0])==0 for a in kl for x in rows))
   for m in ('rref-high','rref-low'):
    basis=independent_rows(kl,order='low' if m=='rref-low' else 'high')
    self.assertEqual(len(basis),len(kl))
 def test_small_all_address_phase(self):
  for n in (70,135,193):
   z=np.random.default_rng(100+n).integers(0,128,(n,75),dtype=np.int64)
   for slot in (0,1,14):
    for alg in ('global5-canonical','global6-rref-high','global6-rref-low','global6-rref-best'):
     h,stat=compile_global(z,slot,alg)
     self.assertLessEqual(h.num_qubits,128)
     for seed in (17,33):
      result=prove_hmr(h,delta_table(z,slot),dirty_seed=seed)
      self.assertTrue(result['all_valid_addresses'])
      self.assertTrue(result['all_HMR_phase_symbols_cancel'])
 def test_canonical_decoding(self):
  n=130
  z=np.random.default_rng(9).integers(0,128,(n,75),dtype=np.int64)
  for j in range(5):
   alpha=3<<(7*j+5)
   for a in range(n):
    p=((a>>j)&1)
    for k in range(15):
     z[a,5*k+j] &= ~((1<<5)|(1<<6))
     z[a,5*k+j] |= p<<5
  for k in (0,1):
   d=word_masks(delta_table(z,k))
   low,st=discover_global(d,6,'canonical')
   self.assertEqual(st['invariant_dimension'],5)
   c,s=compile_global(z,k,'global6-canonical')
   self.assertTrue(prove_hmr(c,delta_table(z,k),1)['all_HMR_phase_symbols_cancel'])
if __name__=='__main__':unittest.main()
