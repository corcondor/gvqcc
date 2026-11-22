"""Tests for genuine PyTorch policy gradients on *compiled* quantum costs."""
import unittest


class QuantumCostPolicyTests(unittest.TestCase):
    def test_stochastic_policy_gradient_and_exact_oracle(self):
        import torch
        from quantum_griffith.policy import QuantumAffinePolicy, learn_affine_policy
        from quantum_griffith.reversible import verify_oracle

        torch.manual_seed(17)
        policy = QuantumAffinePolicy(3, 2, depth=2)
        ids, log_probs = policy.sample(5)
        self.assertEqual(tuple(ids.shape), (5, 2))
        objective = (torch.tensor([0., 1., -2., 3., -1.]) * log_probs).mean()
        objective.backward()
        self.assertIsNotNone(policy.logits.grad)
        self.assertGreater(float(policy.logits.grad.abs().sum()), 0)

        table_a = tuple((x & 1) & ((x >> 1) & 1) for x in range(8))
        table_b = tuple(((x >> 1) & 1) & ((x >> 2) & 1) for x in range(8))
        target = (table_a, table_b)
        result = learn_affine_policy(target, 3, depth=2, steps=10, batch_size=8, seed=53)
        self.assertEqual(result.training_episodes, 80)
        self.assertEqual(result.random_episodes, 80)
        self.assertGreater(result.policy_unique_circuits, 1)
        verify_oracle(result.circuit, target, all_y=True)
        verify_oracle(result.random_circuit, target, all_y=True)
        self.assertLessEqual(
            result.circuit.resources().ccx,
            result.baseline_circuit.resources().ccx
        )

    def test_action_semantics_wires_and_registers(self):
        from quantum_griffith.policy import QuantumAffinePolicy
        policy = QuantumAffinePolicy(3, 2, depth=1)
        self.assertEqual(policy.actions[0], ("noop", -1, -1))
        self.assertIn(("input", 0, 2), policy.actions)
        self.assertIn(("output", 1, 0), policy.actions)
        self.assertEqual(policy.logits.shape[1], 1 + 3*2 + 2*1)


if __name__ == "__main__":
    unittest.main()
