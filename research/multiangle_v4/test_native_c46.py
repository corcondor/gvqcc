"""Real C46 ANGLE words: generated KMX and native KickMix parser/roundtrip.

This test runs only when kickmix installed; it does NOT call the full
FeMoCo/sampled official circuit verifier.
"""
from __future__ import annotations
import io,hashlib,sys,unittest
from pathlib import Path
import numpy as np
H=Path(__file__).resolve().parent
sys.path.insert(0,str(H))
sys.path.insert(0,str((H.parents[0]/'gvqcc_multiform_v3' if (H.parents[0]/'gvqcc_multiform_v3').exists() else H.parents[0]/'multiangle_v3')))
sys.path.insert(0,str((H.parents[0]/'gvqcc_multiform' if (H.parents[0]/'gvqcc_multiform').exists() else H.parents[0])))
from pinned_c46_words import words
from global_cofactor import compile_global
from high_pair import compile_pairs
from high_pair_general import compile_general,full_domain_prove
from multi_angle_synthesis import delta_table
from hmr_patterns import prove as prove_hmr

class RealC46Native(unittest.TestCase):
 def test_kmx_native_parser_and_kmb_roundtrip(self):
  try:import kickmix as km
  except ImportError:self.skipTest('native kickmix unavailable in local CPython3.13')
  w=words()
  cases=[('global-invariant',0,lambda:compile_global(w,0,'global6-canonical')),
         ('pair-exact',2,lambda:compile_pairs(w,2,'exact-paid','canonical')),
         ('general-two-CZ',6,lambda:compile_general(w,6,'exact','canonical'))]
  for name,k,builder in cases:
   with self.subTest(name=name):
    c,s=builder()
    if name=='general-two-CZ':
     self.assertGreater(s['general_selector_count'],0)
     self.assertGreater(full_domain_prove(c,delta_table(w,k),41)['multi_CZ_measurements'],0)
    else:prove_hmr(c,delta_table(w,k),41)
    kmx= ('\n'.join(c.kmx_lines())+'\n').encode()
    parsed=km.Circuit.from_file(io.BytesIO(kmx),format='kmx')
    self.assertEqual(parsed.num_qubits,s['qubits'])
    buf=io.BytesIO();parsed.to_file(buf,format='kmb');buf.seek(0)
    recovered=km.Circuit.from_file(buf,format='kmb')
    self.assertEqual(recovered.num_qubits,s['qubits'])
    print(name,'slot',k,'Q',s['qubits'],'CCX',s['CCX'],'SHA256',hashlib.sha256(kmx).hexdigest(),flush=True)

if __name__=='__main__':unittest.main()
