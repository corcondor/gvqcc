#!/usr/bin/env python3
"""Exhaustive mathematical checks and independent gate-stream tests for v5."""
import io
import itertools
import json
import sys
import tempfile
import unittest
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[1]
for folder in ('gvqcc_multiform','gvqcc_multiform_v3','gvqcc_multiform_v4','gvqcc_multiform_v5'):
 sys.path.insert(0,str(ROOT/folder))
from high_group_basis import (inverse_rows,group_candidates,select_basis,verify_group,
      compile_group,cf_cost)
from global_20_basis import factor_selector
from screen_global_axis import high_selector_rank
from multi_angle_synthesis import delta_table
from hmr_patterns import prove as generator_prove
from independent_kmx_verifier import verify as independent_verify

class GroupMatroidTests(unittest.TestCase):
 def test_random_m3_optimal_exhaustive(self):
  rng=np.random.default_rng(1729)
  for _ in range(25):
   rows=rng.integers(0,1<<9,size=(3,64),dtype=np.int64).tolist()
   candidates,_=group_candidates(rows,3)
   weights={x[3]:x[0] for x in candidates}
   opt=min(weights[a]+weights[b]+weights[c]
         for a,b,c in itertools.combinations(range(1,8),3) if (a^b)!=c)
   selected,sels,stat=select_basis(rows,3)
   self.assertEqual(stat['chosen_cost'],opt)
   self.assertTrue(verify_group(rows,selected,sels))

 def test_random_m8_inverse_and_no_worse(self):
  rng=np.random.default_rng(779)
  for m in (1,2,3,4,8):
   for _ in range(6):
    rows=rng.integers(0,1<<12,size=(m,64),dtype=np.int64).tolist()
    for sup in (2,3,8):
     basis,sels,stat=select_basis(rows,sup)
     self.assertEqual(stat['m'],m)
     self.assertLessEqual(stat['chosen_cost'],stat['baseline_cost'])
     self.assertTrue(verify_group(rows,basis,sels))
     mat=[x[3] for x in basis]
     inv=inverse_rows(mat,m)
     self.assertEqual(sels,[sum(((inv[i]>>j)&1)<<i for i in range(m)) for j in range(m)])

 def test_global_selector_matrix_rank_factorization(self):
  rng=np.random.default_rng(502)
  examples=[0,1,(1<<20)-1]+[int(rng.integers(0,1<<20)) for _ in range(300)]
  for selector in examples:
   terms=factor_selector(selector)
   self.assertEqual(len(terms),high_selector_rank(selector))
   actual=0
   for a,b in terms:
    for k in range(3):
     if b>>k&1:actual ^= a<<(8*k)
   self.assertEqual(actual,selector)

class FullOracleTests(unittest.TestCase):
 def test_mutated_kmx_phase_or_value_is_rejected(self):
  rng = np.random.default_rng(953)
  words = rng.integers(0,128,size=(71,75),dtype=np.int64)
  c,stat = compile_group(words,2,'fixed-upper',8,None)
  lines = list(c.kmx_lines())
  with tempfile.TemporaryDirectory() as temp:
   path = Path(temp)/'mutant.kmx'
   # Negative control: drop a target fanout; independent interpreter must fail.
   k = next(i for i,line in enumerate(lines) if line.startswith('CX ') and int(line.split()[2][1:]) in
            [11+8*j+b for j in range(5) for b in range(7)])
   path.write_text('\n'.join(lines[:k]+lines[k+1:])+'\n')
   with self.assertRaises(AssertionError):independent_verify(path,words,2,dirty_seed=11)
   # Negative control: corrupt the first conditional phase correction.
   k = next(i for i,line in enumerate(lines) if line.startswith('CZ '))
   mutant=lines.copy();mutant[k]='CZ q0 q1 if b0'
   path.write_text('\n'.join(mutant)+'\n')
   with self.assertRaises(AssertionError):independent_verify(path,words,2,dirty_seed=11)

 def test_synthetic_all_addresses_and_dirty_target(self):
  rng=np.random.default_rng(2468)
  for N in (65,129):
   words=rng.integers(0,128,size=(N,75),dtype=np.int64)
   for k in (0,2,14):
    for axis in ('fixed-upper','fixed-lower'):
     c,rec=compile_group(words,k,axis,8,None)
     self.assertLessEqual(rec['qubits'],128)
     self.assertTrue(generator_prove(c,delta_table(words,k),dirty_seed=17)['all_valid_addresses'])
     with tempfile.TemporaryDirectory() as temp:
      path=Path(temp)/'candidate.kmx'
      path.write_text('\n'.join(c.kmx_lines())+'\n')
      checked=independent_verify(path,words,k,dirty_seed=123)
      self.assertEqual(checked['all_legal_addresses_verified'],N)
      self.assertEqual(checked['CCX'],rec['CCX'])
      self.assertTrue(checked['phase_symbols_cancel'])

 def test_actual_pinned_C46_and_native_when_installed(self):
  from pinned_c46_words import words
  words=words()
  self.assertEqual(words.shape,(1219,75))
  for k in (2,8,13):
   c,rec=compile_group(words,k,'fixed-upper',8,'canonical')
   self.assertEqual(rec['qubits'],127)
   self.assertTrue(generator_prove(c,delta_table(words,k),dirty_seed=81)['all_HMR_phase_symbols_cancel'])
   with tempfile.TemporaryDirectory() as temp:
    path=Path(temp)/'candidate.kmx';path.write_text('\n'.join(c.kmx_lines())+'\n')
    checked=independent_verify(path,words,k,dirty_seed=511)
    self.assertEqual(checked['CCX'],rec['CCX'])
    try:
     import kickmix as km
    except ImportError:
     continue
    native=km.Circuit.from_file(io.BytesIO(path.read_bytes()),format='kmx')
    self.assertEqual(native.num_qubits,rec['qubits'])
    b=io.BytesIO();native.to_file(b,format='kmb');b.seek(0)
    new=km.Circuit.from_file(b,format='kmb')
    self.assertEqual(new.num_qubits,rec['qubits'])
    print(f'NATIVE_REAL_C46_PASS slot={k} CCX={rec["CCX"]} Q={rec["qubits"]}',flush=True)

if __name__=='__main__':unittest.main()
