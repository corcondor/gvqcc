import unittest,sys,tempfile
from pathlib import Path
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parent))
from independent_kmx_verifier import verify
from global_cofactor import compile_global
from high_pair_general import compile_general
class T(unittest.TestCase):
 def test_independent_parser_and_phase_failure(self):
  w=np.random.default_rng(9).integers(0,128,(87,75),dtype=np.int64)
  c,s=compile_global(w,1,'global6-rref-low')
  with tempfile.TemporaryDirectory() as tmp:
   f=Path(tmp)/'t.kmx';f.write_text('\n'.join(c.kmx_lines())+'\n')
   self.assertTrue(verify(f,w,1,42)['phase_symbols_cancel'])
   lines=f.read_text().splitlines()
   idx=next(i for i,x in enumerate(lines) if x.startswith('CZ '))
   del lines[idx];f.write_text('\n'.join(lines)+'\n')
   with self.assertRaises(AssertionError):verify(f,w,1,42)
 def test_general_pair_native_text(self):
  w=np.random.default_rng(3).integers(0,128,(88,75),dtype=np.int64)
  c,s=compile_general(w,0,'exact','canonical')
  with tempfile.TemporaryDirectory() as tmp:
   f=Path(tmp)/'t.kmx';f.write_text('\n'.join(c.kmx_lines())+'\n')
   self.assertTrue(verify(f,w,0,19)['phase_symbols_cancel'])
if __name__=='__main__':unittest.main()
