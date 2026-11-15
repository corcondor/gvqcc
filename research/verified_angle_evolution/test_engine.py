"""Small exact tests including deliberate reject and native KMB bytes roundtrip."""
from pathlib import Path
import tempfile,unittest
from kmb_v2 import load,Circuit,Gate
from exact_angle import verify
from rewrite import candidate_moves,apply_move
from evaluator import evaluate,BASE_L,BASE_SCORE,calculate_score
ROOT=Path(__file__).resolve().parent

class EvolutionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.cs=[load(ROOT/'inputs'/f'angle_k_{i}.kmb') for i in range(15)]
    def test_full_baseline(self):
        receipt,words=verify(self.cs)
        self.assertEqual(receipt.ccx,4030)
        self.assertEqual(receipt.transitions,36600)
        self.assertEqual(receipt.measurement_phases,2230)
    def test_kmb_roundtrip(self):
        with tempfile.TemporaryDirectory() as tmp:
            for i,c in enumerate(self.cs):
                output=Path(tmp)/f'{i}.kmb'
                data=c.write(output)
                self.assertEqual(data,(ROOT/'inputs'/f'angle_k_{i}.kmb').read_bytes())
    def test_rewrite_rule_basis(self):
        # 2 CCX with same controls, commute to 1 CCX with 2 CX.
        ops=[Gate(0x31,(0,1,2)),Gate(0x31,(0,1,3))]
        moves=candidate_moves(ops,window=20)
        self.assertTrue(any(x.saved==1 for x in moves))
        new=apply_move(ops,moves[0])
        self.assertEqual(sum(g.name=='CCX' for g in new),1)
        for x in range(16):
            def apply(ops):
                s=[(x>>j)&1 for j in range(4)]
                for g in ops:
                    if g.name=='CCX':a,b,t=g.q;s[t]^=s[a]&s[b]
                    if g.name=='CX':a,b=g.q;s[b]^=s[a]
                return s
            self.assertEqual(apply(ops),apply(new))
    def test_baseline_evaluator(self):
        result=evaluate(str(ROOT/'candidate.py'))
        self.assertTrue(result['valid'])
        self.assertEqual(result['combined_score'],1.)
    def test_fake_improvement_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'wrong.py'
            p.write_text('''from kmb_v2 import Circuit\ndef synthesize(circuits):\n c=circuits[0]; i=next(j for j,g in enumerate(c.ops) if g.name=='CCX'); c.ops=[g for j,g in enumerate(c.ops) if j!=i]; return circuits\n''')
            r=evaluate(str(p))
            self.assertFalse(r['valid'])
    def test_cost_derivative(self):
        score,chem=calculate_score(4030)
        self.assertLess(abs(score-BASE_SCORE),1e-8)
        self.assertGreater(calculate_score(4029)[0],score)
if __name__=='__main__':unittest.main()
