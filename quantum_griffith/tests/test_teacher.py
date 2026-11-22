"""Provably exact teacher seeding for small differentiable circuit searches."""
import random
import unittest

from quantum_griffith.teacher import make_teacher
from quantum_griffith.logic_dag import lower_logic_dag
from quantum_griffith.reversible import verify_oracle


class TeacherTests(unittest.TestCase):
    def test_affine_teacher_factorizes_bilinear_function(self):
        table = tuple(
            (((x >> 0 ^ x >> 1) & 1) & ((x >> 2 ^ x >> 3) & 1))
            for x in range(16)
        )
        teacher = make_teacher((table,), 4, affine=True)
        self.assertEqual(teacher.truth_tables(), (table,))
        self.assertLessEqual(len(teacher.gates), 4)
        circuit = lower_logic_dag(teacher)
        verify_oracle(circuit, (table,))

    def test_random_teacher_is_exact_with_and_without_affine(self):
        rng = random.Random(2340)
        for n in (2, 3, 4):
            for output_count in (1, 2):
                for _ in range(5):
                    tables = tuple(
                        tuple(rng.randrange(2) for x in range(1 << n))
                        for _ in range(output_count)
                    )
                    for affine in (False, True):
                        graph = make_teacher(tables, n, affine=affine)
                        self.assertEqual(graph.truth_tables(), tables)
                        verify_oracle(lower_logic_dag(graph), tables)


class OptionalTorchSeedTests(unittest.TestCase):
    def test_hard_seed_keeps_exact_function(self):
        try:
            import torch
            from quantum_griffith.learn import LearnableLogicDAG, fit_truth_tables
        except ImportError:
            self.skipTest("PyTorch optional dependency not installed")
        torch.set_num_threads(1)
        table = tuple(
            (((x >> 0 ^ x >> 1) & 1) & ((x >> 2 ^ x >> 3) & 1))
            for x in range(16)
        )
        teacher = make_teacher((table,), 4, affine=True)
        net = LearnableLogicDAG(4, max(6, len(teacher.gates)), 1)
        net.initialize_from_teacher(teacher)
        self.assertEqual(net.hard_graph().truth_tables(), (table,))
        report = fit_truth_tables((table,), 4, gates=6, steps=2, restarts=1,
                                  seed=3, warm_start=True)
        self.assertIsNotNone(report.seeded_teacher_circuit)
        self.assertEqual(report.best_classical_errors, 0)
        verify_oracle(report.seeded_teacher_circuit, (table,))


if __name__ == "__main__":
    unittest.main()
