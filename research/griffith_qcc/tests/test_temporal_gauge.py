import unittest
import random
import os
from griffith_qcc.temporal_gauge import tag,transformed_word,project_row,project_table,carrier_tree
from griffith_qcc.chemistry import load_words,helper_report

V8=os.environ.get('GVQCC_V8_NPZ')
JOINT=os.environ.get('GVQCC_JOINT_NPZ')

class TestTemporalGauge(unittest.TestCase):
    def test_tag_identity_exhaustive(self):
        for w in range(128):
            for sin in range(2):
                for sp in range(2):
                    for sc in range(2):
                        t=transformed_word(w,sin,sp,sc)
                        changed=(sin^sc) if w in (32,96) else (sin^sp)
                        self.assertEqual(tag(t)^tag(w),changed)

    def test_gauge_can_prescribe_any_tags(self):
        # Small fresh-child tree: e0 splits into e1, then e0 into e2.
        edges=[(0,1),(0,2)]
        left,right=carrier_tree(edges)
        rnd=random.Random(4)
        for _ in range(300):
            old=[rnd.randrange(128) for _ in edges]
            req=[rnd.randrange(2) for _ in edges]
            new,g=project_row(old,req,left,right)
            self.assertEqual([tag(x) for x in new],req)
            self.assertIn(g,(0,1))

    @unittest.skipUnless(V8 and JOINT,'Requires external V8 and joint NPZ files')
    def test_full_real_joint_projection(self):
        import numpy as np
        with np.load(V8) as x: target=x['angle_words'].copy();edges=x['tree_edges'].copy()
        with np.load(JOINT) as x: old=x['angle_words'].copy()
        new,gs=project_table(old,target,edges)
        self.assertTrue(np.array_equal(((new>>5)^(new>>6))&1,((target>>5)^(target>>6))&1))
        self.assertEqual(helper_report(new)['helper_time_invariance_violations'],0)
        self.assertEqual(int(np.count_nonzero(new!=old)),32)
        self.assertEqual(int(np.count_nonzero(np.any(new!=old,axis=1))),7)
        self.assertEqual(int(gs.sum()),0)
        again,g=project_table(new,target,edges)
        self.assertTrue(np.array_equal(new,again))

        def vectors(words):
            u=np.zeros((len(words),len(edges)+1));u[:,0]=1
            for k,(p,c) in enumerate(edges):
                angle=np.pi*words[:,k]/64
                cv=np.cos(angle);sv=np.sin(angle)
                a=u[:,p].copy();b=u[:,c].copy()
                u[:,p]=cv*a-sv*b;u[:,c]=sv*a+cv*b
            return u
        u0=vectors(old);u1=vectors(new)
        self.assertLess(np.max(abs(u0*(1-2*gs[:,None])-u1)),1e-12)

if __name__=='__main__': unittest.main()
