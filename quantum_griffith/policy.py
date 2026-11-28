"""PyTorch policy-gradient search over exact reversible quantum synthesis.

Unlike a LUT-classification loss with a loose expected-AND proxy, each sampled
action sequence is synthesized into an ACTUAL X/CX/CCX quantum oracle before
its resource cost is used for REINFORCE. The simulator strictly verifies the
best found circuit against every clean-ancilla basis input and every output
register value (when n_outputs <= 5).

The action policy is intentionally small: a sequence of invertible elementary
GF(2) input/output CNOT basis moves, or NOOP. Its action space is therefore
much narrower than unrestricted neural quantum architecture search. This is a
reproducible proof-of-concept, not a trained replacement for classical logic
synthesis, and no neural advantage over random/beam search is assumed.
"""
from __future__ import annotations

import random
from dataclasses import dataclass
from typing import Sequence

import torch
from torch import nn
from torch.distributions import Categorical

from .reversible import Circuit, verify_oracle
from .synthesis import (
    JointSynthesisResult,
    _map_tables,
    _mix_outputs,
    _score,
    _validate,
    _wrap_joint,
    synthesize,
)


class QuantumAffinePolicy(nn.Module):
    """Trainable categorical distribution over reversible basis rewrites."""

    def __init__(self, n_inputs: int, n_outputs: int, depth: int):
        super().__init__()
        if n_inputs < 1 or n_outputs < 1 or depth < 1:
            raise ValueError("Dimensions and policy depth must be positive")
        self.actions: tuple[tuple[str, int, int], ...] = (
            ("noop", -1, -1),
            *((("input", c, t)
               for c in range(n_inputs) for t in range(n_inputs) if c != t)),
            *((("output", c, t)
               for c in range(n_outputs) for t in range(n_outputs) if c != t)),
        )
        self.logits = nn.Parameter(torch.zeros(depth, len(self.actions)))

    def sample(self, batch_size: int) -> tuple[torch.Tensor, torch.Tensor]:
        dist = Categorical(logits=self.logits)
        ids = dist.sample((batch_size,))
        return ids, dist.log_prob(ids).sum(dim=1)

    def entropy(self) -> torch.Tensor:
        return Categorical(logits=self.logits).entropy().sum()


@dataclass
class PolicyResult:
    circuit: Circuit
    method: str
    best_actions: tuple[tuple[str, int, int], ...]
    baseline_circuit: Circuit
    random_circuit: Circuit
    training_episodes: int
    random_episodes: int
    policy_unique_circuits: int
    final_entropy: float
    input_basis_cnots: tuple[tuple[int, int], ...]
    output_basis_cnots: tuple[tuple[int, int], ...]

    def as_dict(self) -> dict:
        return {
            "method": self.method,
            "baseline": self.baseline_circuit.resources().as_dict(),
            "policy_best": self.circuit.resources().as_dict(),
            "random_best": self.random_circuit.resources().as_dict(),
            "policy_found_improvement_over_baseline":
                _score(self.circuit) < _score(self.baseline_circuit),
            "policy_beats_equal_budget_random":
                _score(self.circuit) < _score(self.random_circuit),
            "training_episodes": self.training_episodes,
            "random_episodes": self.random_episodes,
            "distinct_evaluated_action_sequences": self.policy_unique_circuits,
            "final_entropy": self.final_entropy,
            "best_actions": [list(a) for a in self.best_actions],
            "input_basis_cnots": [list(v) for v in self.input_basis_cnots],
            "output_basis_cnots": [list(v) for v in self.output_basis_cnots],
            "strict_validation": True,
        }


def learn_affine_policy(tables: Sequence[Sequence[int]], n_inputs: int, *,
                        depth: int = 2, steps: int = 140,
                        batch_size: int = 12, seed: int = 20261122,
                        lr: float = 0.14,
                        entropy_weight: float = 0.01) -> PolicyResult:
    """Train on actual compiled quantum resources using REINFORCE.

    Each episode samples a sequence of input/output CNOT basis moves. A
    supervised truth-table loss is never used: the exact oracle is obtained
    constructively and the sole trainable objective is its physical resource
    proxy. Negative improvements are kept in the report, not hidden.

    For a fair comparison with uninformed search, uniformly random sequences
    get the *same number of samples* and the same resource evaluator.
    """
    if not 1 <= n_inputs <= 6 or depth < 1 or depth > 4:
        raise ValueError("Supported small function sizes: n_inputs <= 6, 1 <= depth <= 4")
    if steps < 1 or batch_size < 1 or lr <= 0 or entropy_weight < 0:
        raise ValueError("Training budget and optimizer settings invalid")
    target = _validate(tables, n_inputs)
    n_outputs = len(target)
    torch.manual_seed(seed)
    policy = QuantumAffinePolicy(n_inputs, n_outputs, depth)
    optimizer = torch.optim.Adam(policy.parameters(), lr=lr)
    actions = policy.actions
    noop = (0,) * depth
    cache: dict[tuple[int, ...], JointSynthesisResult] = {}

    def compile_actions(action_ids: tuple[int, ...]) -> JointSynthesisResult:
        if action_ids in cache:
            return cache[action_ids]
        rows_x = [1 << i for i in range(n_inputs)]
        rows_y = [1 << i for i in range(n_outputs)]
        input_moves: list[tuple[int, int]] = []
        output_moves: list[tuple[int, int]] = []
        for key in action_ids:
            kind, c, t = actions[key]
            if kind == "input":
                rows_x[t] ^= rows_x[c]
                input_moves.append((c, t))
            elif kind == "output":
                rows_y[t] ^= rows_y[c]
                output_moves.append((c, t))
        mapped = _map_tables(target, n_inputs, tuple(rows_x))
        transformed = _mix_outputs(mapped, tuple(rows_y))
        core = synthesize(transformed, n_inputs, method="best")
        result = _wrap_joint(core, n_inputs, tuple(input_moves), tuple(output_moves))
        cache[action_ids] = result
        return result

    reference = compile_actions(noop)
    best_key = noop
    best_cost = _score(reference.circuit)
    running_baseline: float | None = None

    for _ in range(steps):
        sampled, log_probs = policy.sample(batch_size)
        keys = [tuple(map(int, row)) for row in sampled.tolist()]
        values = []
        for key in keys:
            candidate = compile_actions(key)
            cost = _score(candidate.circuit)
            values.append(cost)
            if cost < best_cost:
                best_key = key
                best_cost = cost
                # Because the action sequence is a composition of exact CNOT
                # conjugations, this check is an independent guard.
                verify_oracle(candidate.circuit, target)
        rewards = torch.tensor(values, dtype=torch.float32)
        if running_baseline is None:
            running_baseline = float(rewards.mean().item())
        advantages = rewards - running_baseline
        optimizer.zero_grad()
        objective = (advantages.detach() * log_probs).mean()
        objective = objective - entropy_weight * policy.entropy()
        objective.backward()
        optimizer.step()
        running_baseline = 0.9 * running_baseline + 0.1 * rewards.mean().item()

    # Equal episode budget, same action set, independent seeded RNG, no training.
    rng = random.Random(seed + 100003)
    best_random_key = noop
    best_random_cost = _score(reference.circuit)
    for _ in range(steps * batch_size):
        key = tuple(rng.randrange(len(actions)) for _ in range(depth))
        candidate = compile_actions(key)
        cost = _score(candidate.circuit)
        if cost < best_random_cost:
            best_random_key, best_random_cost = key, cost
    best = compile_actions(best_key)
    rand_best = compile_actions(best_random_key)
    verify_oracle(best.circuit, target)
    verify_oracle(rand_best.circuit, target)
    return PolicyResult(
        circuit=best.circuit,
        method="reinforce-exact-quantum-cost",
        best_actions=tuple(actions[i] for i in best_key),
        baseline_circuit=reference.circuit,
        random_circuit=rand_best.circuit,
        training_episodes=steps * batch_size,
        random_episodes=steps * batch_size,
        policy_unique_circuits=len(cache),
        final_entropy=float(policy.entropy().item()),
        input_basis_cnots=best.input_basis_cnots,
        output_basis_cnots=best.output_basis_cnots,
    )
