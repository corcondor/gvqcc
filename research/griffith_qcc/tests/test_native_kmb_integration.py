"""Native KMB v2 binary, all-state linear proof and in-place splice guard."""
import random
import tempfile
import unittest
from pathlib import Path

from native_kmb.real_kmb import KMB,Op
from native_kmb.linear_opt import (
    matrix_run, synthesize_rows, optimize_run, certify_source_candidate,
    optimize_bank, partition,
)
from native_kmb.native_splice import splice_pre_hmr,initial_legal_states


def make_kmb(ops,nq=4,nb=1):
    return KMB("synthetic",2,nq,nb,0,b"",list(ops),b"\x00"*8)


def full_small_bitsets(nq=4):
    return [
        sum(((x>>q)&1)<<x for x in range(1<<nq))
        for q in range(nq)
    ]


class NativeKMBTests(unittest.TestCase):
    def test_binary_roundtrip_with_real_loader_opcode_types(self):
        c=make_kmb([
            Op(0x11,(0,)),
            Op(0x21,(0,1)),
            Op(0x31,(0,1,2)),
            Op(0x50,(2,),(0,)),
            Op(0x90,(0,),(),(0,)),
            Op(0xa0,(0,1),(),(0,)),
        ])
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/"fixture.kmb"
            c.write(p)
            loaded=KMB.read(p)
            self.assertEqual(loaded.ops,c.ops)
            self.assertEqual(loaded.render(),p.read_bytes())

    def test_gaussian_synthesis_is_exact_for_random_reversible_maps(self):
        rng=random.Random(3041907)
        for width in (2,3,5,9):
            for _ in range(35):
                controls=[]
                for j in range(rng.randrange(1,45)):
                    a,b=rng.sample(range(width),2)
                    controls.append(Op(0x21,(a,b)))
                wires,rows=matrix_run(controls)
                for order in (list(range(len(wires))),list(reversed(range(len(wires))))) :
                    generated=synthesize_rows(rows,order)
                    transformed=[Op(0x21,(wires[a],wires[b])) for a,b in generated]
                    self.assertEqual(matrix_run(transformed,wires)[1],rows)

    def test_whole_native_file_splicing_preserves_non_cx_ops(self):
        cx=Op(0x21,(0,1))
        old=make_kmb([cx,cx,cx,cx,Op(0x31,(0,1,2)),Op(0x50,(2,),(0,)),
                      Op(0xa0,(0,1),(),(0,))])
        with tempfile.TemporaryDirectory() as d:
            src=Path(d)/"old.kmb"
            dst=Path(d)/"new.kmb"
            old.write(src)
            proof=optimize_bank(src,dst,attempts=0)
            self.assertEqual(proof["saved_CX"],4)
            self.assertEqual(proof["old_CCX"],1)
            self.assertEqual(proof["new_CCX"],1)
            new=KMB.read(dst)
            self.assertEqual(old.ops[-3:],new.ops)
            self.assertEqual(new.render(),dst.read_bytes())
            self.assertEqual(certify_source_candidate(old,new)["saved_CX"],4)

    def test_wrong_cnot_matrix_fails_closed(self):
        old=make_kmb([Op(0x21,(0,1)),Op(0x31,(0,1,2))])
        bad=make_kmb([Op(0x21,(0,2)),Op(0x31,(0,1,2))])
        with self.assertRaises(AssertionError):
            certify_source_candidate(old,bad)

    def test_nonlinear_splice_can_remove_exactly_cancelling_toffolis(self):
        gate=Op(0x31,(0,1,2))
        old=make_kmb([gate,gate,Op(0x50,(2,),(0,))])
        new,proof=splice_pre_hmr(
            old,0,2,[],full_small_bitsets(),16)
        self.assertEqual(old.paid(),2)
        self.assertEqual(new.paid(),0)
        self.assertEqual(proof["strict_paid_saving"],2)
        self.assertEqual(proof["full_basis_states_checked"],16)
        self.assertEqual(new.ops[-1],old.ops[-1])
        # This artificial positive control is not claimed as a V8 saving.

    def test_incorrect_nonlinear_splice_is_rejected(self):
        gate=Op(0x31,(0,1,2))
        old=make_kmb([gate,Op(0x50,(2,),(0,))])
        with self.assertRaises(AssertionError):
            splice_pre_hmr(old,0,1,[],full_small_bitsets(),16)

    def test_post_hmr_splice_is_rejected(self):
        gate=Op(0x31,(0,1,2))
        old=make_kmb([Op(0x50,(3,),(0,)),gate])
        with self.assertRaises(ValueError):
            splice_pre_hmr(old,1,2,[],full_small_bitsets(),16)

    def test_no_paid_saving_cannot_be_promoted(self):
        gate=Op(0x31,(0,1,2))
        old=make_kmb([gate,gate])
        with self.assertRaises(ValueError):
            splice_pre_hmr(old,0,2,[gate,gate],full_small_bitsets(),16)

    def test_formal_equivalence_of_original_and_optimized_runs(self):
        rng=random.Random(11)
        for _ in range(60):
            run=[Op(0x21,tuple(rng.sample(range(9),2)))
                 for _ in range(rng.randrange(6,50))]
            replacement,_=optimize_run(run,attempts=2)
            all_wires=list(range(9))
            self.assertEqual(matrix_run(run,all_wires)[1],
                             matrix_run(replacement,all_wires)[1])
            self.assertLessEqual(len(replacement),len(run))


if __name__=="__main__":
    unittest.main()
