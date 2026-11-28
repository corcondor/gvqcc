import unittest
import os
from griffith_qcc.helper_code_search import helper_rank,original_helpers,instantiate,tensor_rank_proxy
from griffith_qcc.chemistry import helper_report

DATA=os.environ.get('GVQCC_V8_NPZ')

class TestHelperCode(unittest.TestCase):
    def test_rank_bad(self):
        self.assertLess(helper_rank([0,0,0,0,0]),10)

    @unittest.skipUnless(DATA, 'Requires external V8 candidate NPZ')
    def test_project_mutated_lut4_code(self):
        import numpy as np
        with np.load(DATA) as z:w=z['angle_words'];edges=z['tree_edges']
        h=list(original_helpers(w))
        self.assertEqual(helper_rank(h),10)
        new=instantiate(w,edges,h)
        self.assertTrue(np.array_equal(new,w))
        for j in range(5):
            h1=h.copy();h1[j]^=1<<5
            if helper_rank(h1) != 10:continue
            new=instantiate(w,edges,h1)
            self.assertNotEqual(np.count_nonzero(new!=w),0)
            rep=helper_report(new)
            self.assertEqual(rep['helper_time_invariance_violations'],0)
            self.assertEqual(rep['helper_low_address_violations'],0)
            self.assertTrue(rep['usable_in_six_extra_AND_cache'])
            # Changing a LUT code changes the *representation*, not orbital vector.
            self.assertEqual(new.shape,w.shape)
            break
        else:self.fail('could not mutate any full-rank helper bit')

if __name__=='__main__':unittest.main()
