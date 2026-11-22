"""Unit/full-domain symbolic quantum phase proof for new partition families."""
import io,sys,unittest
from pathlib import Path
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parent))
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'gvqcc_multiform'))
from partition_patterns import METHODS,compile_partition,convert_hmr
from permutation_patterns import compile_perm,estimate,select_bits
from hmr_patterns import prove as prove_hmr,MeasuredCircuit
from multi_angle_synthesis import prove as prove_plain,delta_table

class PartitionTests(unittest.TestCase):
    def test_permutations_coverage(self):
        for bits in [(0,1,2,3,4,5),(0,1,2,3,4,7),(0,2,4,6,8,10),(1,3,7,8,9,10)]:
            low,high=select_bits(bits)
            self.assertEqual(len(low),6)
            self.assertEqual(len(high),5)
            self.assertEqual(set(low)|set(high),set(range(11)))
    def test_complete_truth_random_dirty_and_phase(self):
        for n in (17,36,79):
            words=np.random.default_rng(177+n).integers(0,128,size=(n,75),dtype=np.int64)
            for slot in (0,1,14):
                delta=delta_table(words,slot)
                for mode in METHODS:
                    c,s=compile_partition(words,slot,mode)
                    self.assertLessEqual(c.alloc,128)
                    for seed in (5,23):prove_plain(c,delta,seed)
                    h,hs=convert_hmr(c,s)
                    self.assertEqual(s['CCX'],2*hs['CCX'])
                    self.assertEqual(hs['HMR'],hs['CCX'])
                    for seed in (5,23):
                        self.assertTrue(prove_hmr(h,delta,seed)['all_HMR_phase_symbols_cancel'])
                for bits in [(0,1,2,3,4,5),(0,2,4,6,8,10)]:
                    c,s=compile_perm(words,slot,bits)
                    h,hs=convert_hmr(c,s)
                    self.assertEqual(hs['CCX'],estimate(words,slot,bits)['total_ccx_after_hmr'])
                    prove_hmr(h,delta,5)
    def test_missing_conditional_cz_caught_by_phase_proof(self):
        words=np.random.default_rng(88).integers(0,128,(33,75),dtype=np.int64)
        orig,s=compile_partition(words,2,'partition6-basis')
        h,_=convert_hmr(orig,s)
        # Deliberate failure injection: remove one phase correction CZ while
        # keeping the HMR. The verifier must reject any uncorrected symbol.
        bad=list(h.operations)
        i=next(i for i,(name,q,flag) in enumerate(bad) if name=='CZ')
        del bad[i]
        with self.assertRaises(AssertionError):prove_hmr(MeasuredCircuit(h.num_qubits,bad),delta_table(words,2))
    def test_native_kmx_hmr_parser_if_installed(self):
        try:
            import kickmix as km
        except ImportError:
            self.skipTest('native KickMix only in CI Python3.12')
        words=np.random.default_rng(88).integers(0,128,(17,75),dtype=np.int64)
        for mode in ('partition5-basis','partition6-basis'):
            c,s=compile_partition(words,2,mode)
            h,_=convert_hmr(c,s)
            parsed=km.Circuit.from_file(io.BytesIO(('\n'.join(h.kmx_lines())+'\n').encode()),format='kmx')
            self.assertEqual(parsed.num_qubits,h.num_qubits)
            out=io.BytesIO();parsed.to_file(out,format='kmb');out.seek(0)
            self.assertEqual(km.Circuit.from_file(out,format='kmb').num_qubits,h.num_qubits)

if __name__=='__main__': unittest.main()
