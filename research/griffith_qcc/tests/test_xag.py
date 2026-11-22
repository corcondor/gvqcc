import unittest
from griffith_qcc.xag import Affine, AndProduct, XAG, affine_functions, synthesize_shared_one_and, anf_nonlinear_terms
from griffith_qcc.kickmix_proof import prove_oracle
from griffith_qcc.joint import Physical, Hardware, JointCandidate, candidate_record


class TestXag(unittest.TestCase):
    def test_affine_enumeration(self):
        for n in range(1,6):
            self.assertEqual(len(affine_functions(n)),1<<(n+1))

    def test_multitarget_shared_oneand(self):
        # f0 = a & (b ^ c), f1 = f0 ^ d on four binary inputs
        target=[]
        for out in (0,1):
            bits=0
            for a in range(16):
                f=((a & 1)&(((a>>1)^(a>>2))&1)) ^ ( ((a>>3)&1) if out else 0)
                bits |= f << a
            target.append(bits)
        circuit=synthesize_shared_one_and(target,4)
        self.assertIsNotNone(circuit)
        self.assertEqual(len(circuit.products),1)
        self.assertEqual(circuit.assert_exact(target)['mismatch'],0)
        proof=prove_oracle(circuit.emit_kmx(),4,2,expected_tables=tuple(target))
        self.assertEqual(proof['hmr_count'],1)
        for a in range(16):
            want=sum(((target[i]>>a)&1)<<i for i in range(2))
            for t in [0,1,2,3]:
                self.assertEqual(proof['output_map'](a,t),want^t)
        self.assertLess(circuit.resources()['ccx_static'],XAG(4,circuit.products,circuit.outputs).resources(hmr=False)['ccx_static'])

    def test_nonfactorable_rejection(self):
        # n=4 monomial a*b*c has algebraic degree 3; one AND of affine forms cannot realize it.
        tt=sum((1 if (a & 7)==7 else 0) << a for a in range(16))
        self.assertIsNone(synthesize_shared_one_and([tt],4))

    def test_exact_phase_mutation_detected(self):
        target=sum(((a&1)&((a>>1)&1)) << a for a in range(4))
        circuit=synthesize_shared_one_and([target],2)
        self.assertIsNotNone(circuit)
        proof=prove_oracle(circuit.emit_kmx(),2,1,expected_tables=(target,))
        self.assertTrue(proof['basis_phase_workspace_cases'])
        broken='\n'.join(x for x in circuit.emit_kmx().splitlines() if not x.startswith('CZ '))
        with self.assertRaises((ValueError,AssertionError)):
            prove_oracle(broken,2,1)

    def test_joint_gate_never_scored_when_unverified(self):
        p=Physical(0.0199,0.0199,283.0,3.92,46.90)
        unver=JointCandidate('demo',p,Hardware(13250.0,427,True,False),'a'*64)
        self.assertEqual(candidate_record(unver)['status'],'RESEARCH_ONLY_NOT_SCORABLE')
        self.assertIsNone(candidate_record(unver)['score_comparable_cost'])
        ver=JointCandidate('demo',p,Hardware(13250.0,427,True,True),'a'*64)
        self.assertEqual(candidate_record(ver)['status'],'READY_FOR_OFFICIAL_SCORE')
        # A verified physical candidate below the strict Lambda floor is rejected.
        bad=JointCandidate('demo',Physical(.019,.019,48.0,3.92,46.8),Hardware(100,200,True,True),'a'*64)
        self.assertIsNone(candidate_record(bad)['score_comparable_cost'])

if __name__=='__main__': unittest.main()
