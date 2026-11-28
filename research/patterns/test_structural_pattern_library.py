import copy
import tempfile
import unittest
from pathlib import Path
import numpy as np

from structural_pattern_library import (
    Ledger, apply, cheapest_output_basis, dead_givens_mask,
    delta_table, fingerprint, gf2_rank, mixed_rank_profile, mixed_rows,
    generate_run, padding_completions)


class PatternLibraryTest(unittest.TestCase):
    def setUp(self):
        self.z = {'angle_words': np.random.default_rng(1).integers(0,128,(76+2*20,75),dtype=np.int64),
                  'W':np.random.default_rng(2).normal(size=(2,20,4)),
                  'H2_I':np.random.default_rng(3).normal(size=(2,4)),
                  'U':np.random.default_rng(4).normal(size=(2,20,76))}

    def test_exact_gf2(self):
        self.assertEqual(gf2_rank([[1,1,0],[0,1,1],[1,0,1]]),2)
        self.assertEqual(gf2_rank(np.zeros((3,9),np.uint8)),0)

    def test_word_run_changes_only_two_boundary_deltas(self):
        a=self.z['angle_words']
        before=[delta_table(a,k) for k in range(15)]
        op={'type':'run_length','row':99,'columns':[7,12,17],'xor':1}
        b=apply(self.z,op)['angle_words']
        after=[delta_table(b,k) for k in range(15)]
        changed=[k for k in range(15) if not np.array_equal(before[k],after[k])]
        self.assertEqual(changed,[1,4])
        for k in changed:
            self.assertEqual(int(np.count_nonzero(after[k]^before[k])),1)

    def test_permutation_must_swap_W_and_U(self):
        z=self.z
        op={'type':'row_swap','rank':1,'a':2,'b':7}
        changed=apply(z,op)
        self.assertTrue(np.array_equal(changed['W'][1,2],z['W'][1,7]))
        self.assertTrue(np.array_equal(changed['U'][1,7],z['U'][1,2]))
        i,j=76+20+2,76+20+7
        self.assertTrue(np.array_equal(changed['angle_words'][i],z['angle_words'][j]))
        self.assertTrue(np.array_equal(changed['H2_I'],z['H2_I']))
        self.assertTrue(np.array_equal(z['angle_words'][i],apply(changed,op)['angle_words'][i]))

    def test_dead_word_sufficient_condition(self):
        # Identity-like tree: after first mixing one coordinate can be nonzero.
        words=np.zeros((2,75),np.int64)
        edges=np.array([(0,i) for i in range(1,76)])
        dead,v=dead_givens_mask(words,edges)
        self.assertFalse(dead.any())
        # Rotation of two all-zero coordinates is unobservable.
        edges=np.array([(i,i+1) for i in range(75)])
        dead,v=dead_givens_mask(words,edges)
        self.assertTrue(dead[:,1:].all())
        self.assertFalse(dead[:,0].any())

    def test_output_basis_joint_rank_invariant(self):
        rows=np.random.default_rng(13).integers(0,128,(48,75),dtype=np.int64)
        p=mixed_rows(rows,3,0)
        pre=gf2_rank(p.reshape(75,-1))
        p[1]^=p[4]
        self.assertEqual(gf2_rank(p.reshape(75,-1)),pre)

    def test_padding_previous_same_low_position(self):
        words=np.zeros((35,75),dtype=np.int64)
        for low in range(16):words[16+low,0]=low
        words[32:35,0]=[3,4,5]
        # Previous block low addresses 3..15: values 3..15.
        d=delta_table(words,0)
        n=len(d);missing=(-n)%16
        extra=d[-16:-16+missing]
        self.assertEqual(extra[:,0].tolist(),list(range(3,16)))
        got=padding_completions(words)
        self.assertIsInstance(got,list)
        self.assertEqual(mixed_rows(words,0,0,'previous').shape,(5,15,3))

    def test_journal_dedup_by_seed_and_action(self):
        with tempfile.TemporaryDirectory() as d:
            file=Path(d)/'ledger.jsonl'
            a={'type':'dead_word','row':80,'col':7,'xor':1}
            seed='a'*64
            x=Ledger(file)
            self.assertTrue(x.append(seed,'null_givens',a,{'evidence':'structural_screen'}))
            self.assertFalse(x.append(seed,'null_givens',a,{'evidence':'structural_screen'}))
            y=Ledger(file)
            self.assertFalse(y.append(seed,'null_givens',a,{}))
            self.assertTrue(y.append('b'*64,'null_givens',a,{}))
            self.assertEqual(len(file.read_text().splitlines()),2)

if __name__=='__main__': unittest.main()
