import unittest,os
from griffith_qcc.chemistry import load_words,helper_report,bank_delta_tables,rank_gf2
from griffith_qcc.xag import synthesize_shared_one_and,anf_nonlinear_terms
from griffith_qcc.kickmix_proof import prove_oracle

DATA=os.environ.get('GVQCC_V8_NPZ')
GAUGE=os.environ.get('GVQCC_GAUGE_NPZ')

@unittest.skipUnless(DATA, 'GVQCC_V8_NPZ not provided; no upstream data copied into Git')
class TestRealChemistry(unittest.TestCase):
    def test_conserved_helpers(self):
        base=helper_report(load_words(DATA))
        self.assertEqual(base['helper_time_invariance_violations'],0)
        self.assertEqual(base['helper_low_address_violations'],0)
        self.assertEqual(base['low_helper_augmented_rank'],10)
        self.assertTrue(base['usable_in_six_extra_AND_cache'])
        if GAUGE:
            g=helper_report(load_words(GAUGE))
            self.assertGreater(g['helper_time_invariance_violations'],0)

    def test_one_real_v8_fourbit_cone(self):
        w=load_words(DATA)
        d=bank_delta_tables(w,high_block=0)
        f=d[4][8]
        baseline=anf_nonlinear_terms(f,4)
        circuit=synthesize_shared_one_and([f],4)
        self.assertIsNotNone(circuit)
        self.assertEqual(baseline,5)
        self.assertEqual(len(circuit.products),1)
        circuit.assert_exact([f])
        proof=prove_oracle(circuit.emit_kmx(),4,1,expected_tables=(f,))
        for a in range(16):
            for t in [0,1]:
                self.assertEqual(proof['output_map'](a,t), ((f>>a)&1)^t)

if __name__=='__main__': unittest.main()
