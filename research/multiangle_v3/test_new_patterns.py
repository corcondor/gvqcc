"""Algebraic, all-address dirty-target, and every-HMR-branch phase tests."""
from __future__ import annotations
import sys,unittest,io
from pathlib import Path
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parent))
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'gvqcc_multiform'))
from hmr_patterns import ALGORITHMS as HMRS,compile_hmr,prove as proof_hmr
from affine_patterns import (METHODS,synthesize_affine,hmr_from_reversible,
                             transform_maps,chosen_factorization,transform_catalog)
from multi_angle_synthesis import prove as proof_plain,delta_table,word_masks


class NewPatternTests(unittest.TestCase):
    def test_shear_translation_all_functions(self):
        for shear in [None,(0,1),(3,0),(2,1)]:
            for s in range(16):
                inv,forms=transform_maps(shear,s)
                self.assertEqual(len(set(inv)),16)
                self.assertEqual(forms[0],1)
    def test_all_algorithms_all_dirty_and_phase_symbols(self):
        for n in (19,35,63):
            words=np.random.default_rng(912+n).integers(0,128,(n,75),dtype=np.int64)
            for slot in (0,1,14):
                delta=delta_table(words,slot)
                for alg in HMRS:
                    circuit,st=compile_hmr(words,slot,alg)
                    for dirty in (3,27):
                        certificate=proof_hmr(circuit,delta,dirty)
                        self.assertTrue(certificate['all_HMR_phase_symbols_cancel'])
                    self.assertEqual(st['HMR'],st['conditional_CZ'])
                    self.assertEqual(st['qubits'],circuit.num_qubits)
                for method in METHODS:
                    c,st=synthesize_affine(words,slot,method)
                    for dirty in (3,27):
                        self.assertTrue(proof_plain(c,delta,dirty)['scratch_clean'])
                    measured,mst=hmr_from_reversible(c,st,'all-clean')
                    for dirty in (3,27):
                        self.assertTrue(proof_hmr(measured,delta,dirty)['all_HMR_phase_symbols_cancel'])
                    self.assertEqual(mst['CCX']+mst['HMR'],st['CCX'])
                    self.assertLessEqual(mst['qubits'],128)

    def test_native_kmx_parser_if_installed(self):
        try:
            import kickmix as km
        except ImportError:
            self.skipTest('native kickmix unavailable in this Python')
        words=np.random.default_rng(7).integers(0,128,(17,75),dtype=np.int64)
        for method in (HMRS[2],HMRS[5],HMRS[8]):
            c,stat=compile_hmr(words,1,method)
            src=io.BytesIO(('\n'.join(c.kmx_lines())+'\n').encode())
            parsed=km.Circuit.from_file(src,format='kmx')
            self.assertEqual(parsed.num_qubits,c.num_qubits)
            data=io.BytesIO()
            parsed.to_file(data,format='kmb')
            data.seek(0)
            restored=km.Circuit.from_file(data,format='kmb')
            self.assertEqual(restored.num_qubits,c.num_qubits)
        c,_=synthesize_affine(words,1,'affine-mix')
        m,_=hmr_from_reversible(c,{'method':'affine-mix','slot':1},'all-clean')
        parsed=km.Circuit.from_file(io.BytesIO(('\n'.join(m.kmx_lines())+'\n').encode()),format='kmx')
        self.assertEqual(parsed.num_qubits,m.num_qubits)

if __name__=='__main__':unittest.main()
