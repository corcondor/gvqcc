import math
import unittest
from research_20261116.frontier_cost_gate import (
    PUBLIC, LOCAL, score, matrix, eligible_chemistry, dqi_tradeoff
)

class TestCostGate(unittest.TestCase):
    def test_public_gm(self):
        self.assertAlmostEqual(score(PUBLIC), 28.09487171868039, places=8)
    def test_own_dqi_improves_public(self):
        ours={**PUBLIC, 'dqi': LOCAL['dqi']}
        self.assertLess(LOCAL['dqi'], PUBLIC['dqi'])
        self.assertGreater(score(ours), score(PUBLIC))
    def test_c41_43_are_scenarios_not_receipts(self):
        scenario=matrix({**PUBLIC, 'dqi': LOCAL['dqi']}, 28.3)
        self.assertEqual([x['C'] for x in scenario['rows']], [44,43,42,41])
        self.assertTrue(all('NOT_A_CIRCUIT' in x['verification'] for x in scenario['rows']))
        self.assertAlmostEqual(scenario['rows'][-1]['score_if_feasible_and_same_lambda'], 28.24611650, places=6)
        self.assertAlmostEqual(scenario['rows'][-1]['lambda_eff_needed_for_target'], 46.65411064, places=6)
    def test_toffoli_can_increase_when_q_decreases(self):
        for row in dqi_tradeoff():
            self.assertGreater(row['extra_T_allowance'], 0)
            self.assertTrue(math.isclose(row['max_T_at_same_DQI_cost']*row['Q']**2,
                                         368137.8485742187*890**2, rel_tol=1e-14))
    def test_no_error2_only_shortcut(self):
        self.assertFalse(eligible_chemistry({'status':'PASS','metrics':{'error_2':.014}}))
    def test_complete_official_receipt(self):
        rec={'status':'PASS','verified_shots':78080,'score':2e8,'num_qubits':427,
             'metrics':{'error_1':.019,'error_2':.018,'Lambda':300,'E_gap':3.915}}
        self.assertTrue(eligible_chemistry(rec))
        rec['metrics']['error_2']=.021
        self.assertFalse(eligible_chemistry(rec))
    def test_nonfinite_cost_rejected(self):
        with self.assertRaises(ValueError): score({**PUBLIC, 'dqi': float('inf')})

if __name__ == '__main__': unittest.main()
