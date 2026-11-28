"""Z3 exact all-state pre/post-HMR physical-wire nonlinear splice controls.

The positive identity is an algebraically exact 2 CCX -> 1 CCX rewrite:
    CCX(a,b,t); CX(t,u); CCX(a,b,t)
==  CX(t,u); CCX(a,b,u)
for ALL dirty bits a,b,t,u. Here it occurs after an HMR, proving
that a replacement need not stop at the first measurement if its *unitary*
subcircuit is certified for arbitrary input states.
"""
import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from native_kmb.real_kmb import KMB,Op
from native_kmb.smt_splice import (
    UnprovedRewrite, prove_all_inputs, splice_kmb, main,
)


class SMTNativeProofTests(unittest.TestCase):
    def setUp(self):
        self.hmr=Op(0x50,(11,),(0,))
        self.a=Op(0x31,(0,1,2))
        self.cx=Op(0x21,(2,3))
        self.cz=Op(0xa0,(0,3),(),(0,))
        self.original=KMB(
            "synthetic",2,128,1,0,b"",
            [self.hmr,self.a,self.cx,self.a,self.cz],b"\x00"*8,
        )
        self.short=[self.cx,Op(0x31,(0,1,3))]

    def test_exact_post_hmr_ccx_replacement_with_dirty_targets(self):
        revised,proof=splice_kmb(self.original,1,4,self.short)
        self.assertEqual(proof["paid_CCX_saved"],1)
        self.assertTrue(proof["post_HMR_cut"])
        self.assertEqual(proof["formal_proof"]["smt_result"],"UNSAT")
        self.assertEqual(proof["formal_proof"]["physical_qubits"],128)
        self.assertEqual(revised.paid(),1)
        self.assertEqual(revised.nq,128)
        self.assertEqual(revised.ops[0],self.hmr)
        self.assertEqual(revised.ops[-1],self.cz)
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/"candidate.kmb"
            revised.write(p)
            after=KMB.read(p)
            self.assertEqual(after.render(),p.read_bytes())
            self.assertEqual(after.ops,revised.ops)

    def test_wrong_replacement_hard_refused_with_counterexample(self):
        with self.assertRaisesRegex(UnprovedRewrite,"SAT counterexample"):
            splice_kmb(self.original,1,4,[self.cx])

    def test_non_cnot_phase_in_candidate_forbidden(self):
        with self.assertRaises(UnprovedRewrite):
            splice_kmb(self.original,1,4,[self.cx,self.cz])

    def test_hmr_inside_candidate_cut_forbidden(self):
        with self.assertRaises(UnprovedRewrite):
            splice_kmb(self.original,0,4,self.short)

    def test_equal_paid_cost_not_promoted(self):
        with self.assertRaises(UnprovedRewrite):
            splice_kmb(self.original,1,4,[self.a,self.cx,self.a])

    def test_unconditional_ops_require_distinct_qubits(self):
        with self.assertRaises(UnprovedRewrite):
            prove_all_inputs([Op(0x31,(0,1,1))],[],128)

    def test_plain_noncommuting_boolean_permutations_fail(self):
        with self.assertRaisesRegex(UnprovedRewrite,"SAT counterexample"):
            prove_all_inputs([Op(0x21,(0,1)),Op(0x11,(0,))],
                             [Op(0x11,(0,)),Op(0x21,(0,1))],128)

    def test_sha_bound_cli_writes_only_valid_candidate(self):
        with tempfile.TemporaryDirectory() as td:
            folder=Path(td)
            original=folder/"parent.kmb"
            self.original.write(original)
            proposal=folder/"proposal.json"
            payload={"expected_source_sha256":"0"*64,"start":1,"stop":4,
                     "replace":[{"opcode":"CX","wires":[2,3]},
                                {"opcode":"CCX","wires":[0,1,3]}]}
            proposal.write_text(json.dumps(payload))
            cmd=["--original-kmb",str(original),"--proposal",str(proposal),
                 "--output-kmb",str(folder/"out.kmb"),
                 "--receipt",str(folder/"proof.json")]
            with self.assertRaisesRegex(UnprovedRewrite,"SHA256"):
                main(cmd)
            self.assertFalse((folder/"out.kmb").exists())
            payload["expected_source_sha256"]=hashlib.sha256(original.read_bytes()).hexdigest()
            proposal.write_text(json.dumps(payload))
            proof=main(cmd)
            self.assertEqual(proof["paid_CCX_saved"],1)
            self.assertEqual(KMB.read(folder/"out.kmb").paid(),1)
            with self.assertRaises(FileExistsError):
                main(cmd)


if __name__=="__main__":
    unittest.main()
