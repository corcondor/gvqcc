"""Exhaustive small-function tests: exact truth tables, clean ancillas, phase-safe alphabet."""
import json
import random
import unittest

from quantum_griffith.logic_dag import LogicDAG, LogicGate, lower_logic_dag
from quantum_griffith.reversible import Circuit, Gate, verify_oracle
from quantum_griffith.synthesis import anf_terms, synthesize, search_affine, search_joint_affine


def make_table(n, f):
    return tuple(f(x) & 1 for x in range(1 << n))


class AnfAndOracleTests(unittest.TestCase):
    def test_mobius_all_three_input_functions(self):
        for tt in range(256):
            table = tuple((tt >> i) & 1 for i in range(8))
            terms = anf_terms(table, 3)
            reconstructed = tuple(
                sum(int((x & mask) == mask) for mask in terms) % 2 for x in range(8)
            )
            self.assertEqual(table, reconstructed)

    def test_all_two_input_boolean_functions_three_compilers(self):
        for table_int in range(16):
            table = tuple((table_int >> x) & 1 for x in range(4))
            for method in ("baseline", "shared", "best"):
                circuit = synthesize((table,), 2, method=method).circuit
                receipt = verify_oracle(circuit, (table,))
                self.assertEqual(receipt["basis_cases_checked"], 8)
                self.assertEqual(Circuit.from_json(circuit.to_json()), circuit)

    def test_random_multiple_outputs_three_and_four_inputs(self):
        rng = random.Random(811)
        for n in (3, 4):
            for count in (1, 2, 3):
                for _ in range(12):
                    tables = tuple(
                        tuple(rng.randrange(2) for _ in range(1 << n))
                        for _ in range(count)
                    )
                    for method in ("baseline", "shared", "best"):
                        circuit = synthesize(tables, n, method=method).circuit
                        verify_oracle(circuit, tables)

    def test_global_prefix_sharing_reduces_toffoli(self):
        # t0=x0*x1*x2, t1=x0*x1*x3, q=x2*x3.
        tables = (
            make_table(4, lambda x: (((x >> 0 & 1) & (x >> 1 & 1)) &
                                    ((x >> 2 & 1) ^ (x >> 3 & 1)))),
            make_table(4, lambda x: (
                (((x >> 0 & 1) & (x >> 1 & 1)) &
                 ((x >> 2 & 1) ^ (x >> 3 & 1))) ^
                ((x >> 2 & 1) & (x >> 3 & 1))
            )),
        )
        baseline = synthesize(tables, 4, method="baseline").circuit
        shared = synthesize(tables, 4, method="shared").circuit
        self.assertGreater(baseline.resources().ccx, shared.resources().ccx)
        verify_oracle(shared, tables)

    def test_shared_full_product_for_three_outputs(self):
        shared_term = make_table(3, lambda x: (x & 1) & (x >> 1 & 1))
        tables = (shared_term,) * 3
        baseline = synthesize(tables, 3, method="baseline").circuit
        shared = synthesize(tables, 3, method="shared").circuit
        self.assertEqual(baseline.resources().ccx, 3)
        self.assertEqual(shared.resources().ccx, 2)
        self.assertEqual(shared.resources().ancillas, 1)
        verify_oracle(shared, tables)

    def test_affine_basis_remapping_reduces_toffoli_four_to_one(self):
        # f(x)=(x0 XOR x1)*(x2 XOR x3). ANF contains four
        # distinct quadratic products. A two-CNOT basis change yields one.
        table = make_table(
            4, lambda x: (((x >> 0) ^ (x >> 1)) & 1) &
                         (((x >> 2) ^ (x >> 3)) & 1)
        )
        baseline = synthesize((table,), 4, method="baseline").circuit
        learned_basis = search_affine((table,), 4, max_depth=2, beam_width=12)
        self.assertEqual(baseline.resources().ccx, 4)
        self.assertEqual(learned_basis.circuit.resources().ccx, 1)
        self.assertTrue(learned_basis.basis_cnots)
        verify_oracle(learned_basis.circuit, (table,))

    def test_joint_output_basis_reduces_nonlinear_cost(self):
        # f=(q1 XOR q2, q1, q2), where q1=x0*x1, q2=x1*x2.
        # One output-basis row can eliminate q1, then another eliminates q2
        # from f0, reducing four CCX to two, with exact y-conjugation.
        q1 = make_table(3, lambda x: (x & 1) & (x >> 1 & 1))
        q2 = make_table(3, lambda x: (x >> 1 & 1) & (x >> 2 & 1))
        mixed = tuple(a ^ b for a, b in zip(q1, q2))
        tables = (mixed, q1, q2)
        baseline = synthesize(tables, 3, method="baseline").circuit
        result = search_joint_affine(tables, 3, max_depth=2, beam_width=24)
        self.assertEqual(baseline.resources().ccx, 4)
        self.assertLessEqual(result.circuit.resources().ccx, 2)
        self.assertTrue(result.output_basis_cnots)
        self.assertEqual(result.circuit.n_ancillas, 0)
        verify_oracle(result.circuit, tables, all_y=True)

    def test_joint_search_random_multioutput_equivalence(self):
        rng = random.Random(2981)
        for _ in range(8):
            tables = tuple(
                tuple(rng.randrange(2) for _ in range(8)) for _ in range(3)
            )
            result = search_joint_affine(tables, 3, max_depth=2, beam_width=10)
            verify_oracle(result.circuit, tables, all_y=True)

    def test_budget_limits(self):
        table = make_table(3, lambda x: ((x & 1) & (x >> 1 & 1) & (x >> 2 & 1)))
        with self.assertRaises(ValueError):
            synthesize((table,), 3, method="best", max_ancillas=0)
        self.assertEqual(synthesize((table,), 3, max_ancillas=1).circuit.n_ancillas, 1)

    def test_reject_invalid_gate_or_table(self):
        with self.assertRaises(ValueError):
            Gate("ccx", (0, 0, 2))
        with self.assertRaises(ValueError):
            synthesize(((1, 0),), 2)
        with self.assertRaises(ValueError):
            synthesize(((1, 0, 2, 0),), 2)


class LogicDagTests(unittest.TestCase):
    def test_lower_all_sixteen_boolean_gates(self):
        for tt in range(16):
            graph = LogicDAG(2, (LogicGate(0, 1, tt),), (2,))
            circuit = lower_logic_dag(graph)
            verify_oracle(circuit, graph.truth_tables())
            nonlinear = (tt.bit_count() % 2) == 1
            self.assertEqual(circuit.resources().ccx, 2 if nonlinear else 0)

    def test_liveness_and_cse(self):
        # Duplicate copies of AND; one dead gate; output XOR.
        graph = LogicDAG(2, (
            LogicGate(0, 1, 0b1000),  # AND
            LogicGate(0, 1, 0b1000),  # duplicate
            LogicGate(0, 0, 0b1111),  # unreachable constant one
            LogicGate(2, 3, 0b0110),  # XOR duplicate outputs: zero
        ), (2, 3, 5))
        circuit = lower_logic_dag(graph)
        self.assertEqual(circuit.n_ancillas, 2)
        self.assertEqual(circuit.resources().ccx, 2)
        verify_oracle(circuit, graph.truth_tables())

    def test_unary_reduction(self):
        for tt in range(16):
            graph = LogicDAG(1, (LogicGate(0, 0, tt),), (1,))
            c = lower_logic_dag(graph)
            self.assertEqual(c.resources().ccx, 0)
            verify_oracle(c, graph.truth_tables())

    def test_noncommuting_swapped_parent_order_is_preserved(self):
        # f(a,b)=a AND (NOT b), and g(b,a)=b AND (NOT a).
        graph = LogicDAG(2, (
            LogicGate(0, 1, 0b0010),
            LogicGate(1, 0, 0b0010),
            LogicGate(0, 1, 0b0100),
        ), (2, 3, 4))
        circuit = lower_logic_dag(graph)
        # The swapped g shares the identical function with one of the
        # other outputs, and truly distinct functions are not merged.
        self.assertEqual(circuit.n_ancillas, 2)
        verify_oracle(circuit, graph.truth_tables())

    def test_graph_rejects_forward_reference(self):
        with self.assertRaises(ValueError):
            LogicDAG(2, (LogicGate(0, 3, 8),), (2,))


class OptionalPyTorchTests(unittest.TestCase):
    def test_hard_forward_matches_export_and_ste_has_gradients(self):
        try:
            import torch
            from quantum_griffith.learn import LearnableLogicDAG
        except ImportError:
            self.skipTest("PyTorch optional dependency not installed")
        torch.manual_seed(43)
        net = LearnableLogicDAG(3, 5, 2)
        x = torch.tensor(
            [[(i >> j) & 1 for j in range(3)] for i in range(8)],
            dtype=torch.float32,
        )
        hard = net(x, mode="hard")
        graph = net.hard_graph()
        expected = torch.tensor([graph.evaluate(i) for i in range(8)], dtype=torch.float32)
        self.assertTrue(torch.equal(hard, expected))
        verify_oracle(lower_logic_dag(graph), graph.truth_tables())
        prediction = net(x, mode="ste")
        loss = torch.mean((prediction - (1 - expected)) ** 2)
        loss.backward()
        gradients = [p.grad for p in net.parameters() if p.grad is not None]
        self.assertTrue(gradients)
        self.assertTrue(any(torch.isfinite(g).all() and g.abs().sum() > 0 for g in gradients))


if __name__ == "__main__":
    unittest.main()
