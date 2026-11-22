"""Exact reversible pebble proof on 2- and 3-clean-ancilla AND DAGs."""
import itertools
import unittest

from griffith_qcc.pebble_schedule import plan_and_dag
from griffith_qcc.reversible_blocks import simulate


class PebbleProofTest(unittest.TestCase):
    def test_chain_time_space_trade(self):
        nodes=[(-1,-2),(0,-3),(1,-4)]
        narrow=plan_and_dag(4,nodes,[2],2)
        wide=plan_and_dag(4,nodes,[2],3)
        self.assertEqual((narrow.ccx,narrow.cx,narrow.max_live),(8,1,2))
        self.assertEqual((wide.ccx,wide.cx,wide.max_live),(6,1,3))
        for p in (narrow,wide):
            for a,b,c,d,t in itertools.product((0,1),repeat=5):
                x=[a,b,c,d]+[0]*p.clean_budget+[t]
                y=simulate(p.gates,x)
                self.assertEqual(y[:4],x[:4])
                self.assertEqual(y[4:4+p.clean_budget],[0]*p.clean_budget)
                self.assertEqual(y[-1],t^(a&b&c&d))
                self.assertEqual(simulate(p.gates[::-1],y),x)

    def test_shared_intermediate_reuse(self):
        nodes=[(-1,-2),(0,-3),(0,-4)]
        narrow=plan_and_dag(4,nodes,[1,2],2)
        wide=plan_and_dag(4,nodes,[1,2],3)
        self.assertEqual(narrow.ccx,6)
        self.assertEqual(wide.ccx,6)
        for p in (narrow,wide):
            for a,b,c,d,u,v in itertools.product((0,1),repeat=6):
                x=[a,b,c,d]+[0]*p.clean_budget+[u,v]
                y=simulate(p.gates,x)
                self.assertEqual(y[:4],x[:4])
                self.assertEqual(y[4:4+p.clean_budget],[0]*p.clean_budget)
                self.assertEqual(y[-2:],[u^(a&b&c),v^(a&b&d)])
                self.assertEqual(simulate(p.gates[::-1],y),x)

    def test_infeasible_budget_fails_closed(self):
        with self.assertRaises(ValueError):
            plan_and_dag(3,[(-1,-2),(0,-3)],[1],1)


if __name__=="__main__":
    unittest.main()
