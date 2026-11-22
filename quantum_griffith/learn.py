"""Optional PyTorch differentiable logic-gate and wiring learner.

Unlike gate-count heuristics, the exported hard network is checked against the
entire truth table, and lowered with exact clean CCX operations. NN training
only proposes candidates; it cannot silently relax oracle correctness.

Requires torch: pip install torch. All other quantum_griffith modules are
dependency-free and can be tested without GPUs.
"""
from __future__ import annotations
from dataclasses import dataclass

import torch
from torch import nn
import torch.nn.functional as F

from .logic_dag import LogicDAG, LogicGate, lower_logic_dag
from .synthesis import synthesize, search_affine
from .reversible import Circuit


def _st(logits: torch.Tensor, tau: float, *, hard: bool, gumbel: bool) -> torch.Tensor:
    if gumbel and hard:
        return F.gumbel_softmax(logits, tau=tau, hard=True, dim=-1)
    if gumbel:
        return F.gumbel_softmax(logits, tau=tau, hard=False, dim=-1)
    probabilities = F.softmax(logits / tau, dim=-1)
    if not hard:
        return probabilities
    indices = probabilities.argmax(dim=-1)
    discrete = F.one_hot(indices, num_classes=logits.shape[-1]).to(probabilities.dtype)
    return discrete - probabilities.detach() + probabilities


class LearnableLogicDAG(nn.Module):
    """A small learned 2-input LUT DAG with trainable wiring and hard collapse."""

    def __init__(self, n_inputs: int, n_gates: int, n_outputs: int = 1):
        super().__init__()
        if n_inputs < 1 or n_gates < 1 or n_outputs < 1:
            raise ValueError("Invalid network dimensions")
        self.n_inputs = n_inputs
        self.n_gates = n_gates
        self.n_outputs = n_outputs
        self.gate_logits = nn.Parameter(torch.randn(n_gates, 16) * 0.05)
        self.edge_a = nn.ParameterList(
            [nn.Parameter(torch.randn(n_inputs + i) * 0.05) for i in range(n_gates)]
        )
        self.edge_b = nn.ParameterList(
            [nn.Parameter(torch.randn(n_inputs + i) * 0.05) for i in range(n_gates)]
        )
        self.readout_logits = nn.Parameter(torch.randn(n_outputs, n_inputs + n_gates) * 0.05)
        table = torch.tensor(
            [[(op >> index) & 1 for index in range(4)] for op in range(16)],
            dtype=torch.float32,
        )
        nonlinear = torch.tensor(
            [sum((op >> index) & 1 for index in range(4)) % 2 for op in range(16)],
            dtype=torch.float32,
        )
        self.register_buffer("table", table)
        self.register_buffer("nonlinear", nonlinear)

    def forward(self, x: torch.Tensor, *, tau: float = 1.0,
                mode: str = "soft", gumbel: bool = False) -> torch.Tensor:
        if x.ndim != 2 or x.shape[-1] != self.n_inputs:
            raise ValueError("Expected [batch,n_inputs]")
        if tau <= 0 or mode not in ("soft", "ste", "hard"):
            raise ValueError("Invalid relaxation parameters")
        states = [x[:, i] for i in range(self.n_inputs)]
        for i in range(self.n_gates):
            # A hard forward can be paired with STE backward. The hard mode
            # is deterministic at evaluation and uses exactly one gate/edge.
            hard = mode in ("ste", "hard")
            a_weights = _st(self.edge_a[i], tau, hard=hard,
                            gumbel=gumbel and mode != "hard")
            b_weights = _st(self.edge_b[i], tau, hard=hard,
                            gumbel=gumbel and mode != "hard")
            current = torch.stack(states, dim=1)
            a = current @ a_weights
            b = current @ b_weights
            basis = torch.stack(((1-a)*(1-b), a*(1-b), (1-a)*b, a*b), dim=-1)
            op_weights = _st(self.gate_logits[i], tau, hard=hard,
                             gumbel=gumbel and mode != "hard")
            output = (basis @ self.table.to(dtype=x.dtype).T) @ op_weights
            states.append(output)
        all_nodes = torch.stack(states, dim=-1)
        readout_weights = _st(self.readout_logits, tau, hard=mode != "soft",
                              gumbel=gumbel and mode != "hard")
        return all_nodes @ readout_weights.T

    def expected_ccx_proxy(self) -> torch.Tensor:
        """Soft proxy: each nonaffine LUT costs two CCX with uncompute.

        Not a final circuit cost: liveness, CSE and gate sharing are ignored.
        Only the exported exact circuit resource report is authoritative.
        """
        return 2 * (F.softmax(self.gate_logits, dim=-1) @ self.nonlinear).sum()

    def hard_graph(self) -> LogicDAG:
        gates = tuple(
            LogicGate(
                int(self.edge_a[i].argmax().item()),
                int(self.edge_b[i].argmax().item()),
                int(self.gate_logits[i].argmax().item()),
            )
            for i in range(self.n_gates)
        )
        outputs = tuple(int(i) for i in self.readout_logits.argmax(dim=-1).tolist())
        return LogicDAG(self.n_inputs, gates, outputs)


@dataclass
class TrainingReport:
    best_graph: LogicDAG | None
    best_learned_circuit: Circuit | None
    best_classical_errors: int
    baseline_circuit: Circuit
    optimized_circuit: Circuit
    steps: int
    restarts: int

    def as_dict(self) -> dict:
        return {
            "exact_neural_candidate_found": self.best_learned_circuit is not None,
            "best_classical_errors": self.best_classical_errors,
            "baseline": self.baseline_circuit.resources().as_dict(),
            "affine_or_shared": self.optimized_circuit.resources().as_dict(),
            "learned": None if self.best_learned_circuit is None else
                       self.best_learned_circuit.resources().as_dict(),
            "steps": self.steps,
            "restarts": self.restarts,
        }


def fit_truth_tables(tables: tuple[tuple[int, ...], ...], n_inputs: int, *,
                     gates: int = 12, steps: int = 400, restarts: int = 3,
                     lr: float = 0.04, cost_weight: float = 0.002,
                     seed: int = 20261122) -> TrainingReport:
    """Train with continuous relaxation; accept only *exact* discrete oracles.

    This experimental small-network learner is an optional candidate generator.
    The deterministic ANF/affine compiler remains a guaranteed exact fallback.
    """
    if n_inputs > 6 or n_inputs < 1 or steps < 1 or restarts < 1:
        raise ValueError("Use 1..6 inputs and positive steps/restarts")
    desired = torch.tensor(tables, dtype=torch.float32).T.contiguous()
    if desired.shape != (1 << n_inputs, len(tables)):
        raise ValueError("Invalid target table shape")
    x = torch.tensor(
        [[(i >> j) & 1 for j in range(n_inputs)] for i in range(1 << n_inputs)],
        dtype=torch.float32,
    )
    baseline = synthesize(tables, n_inputs, method="baseline").circuit
    optimized = search_affine(tables, n_inputs, max_depth=2, beam_width=12).circuit
    best_errors = desired.numel() + 1
    best_graph = None
    best_circuit = None
    for restart in range(restarts):
        torch.manual_seed(seed + restart)
        network = LearnableLogicDAG(n_inputs, gates, len(tables))
        optimizer = torch.optim.Adam(network.parameters(), lr=lr)
        for step in range(steps):
            optimizer.zero_grad()
            tau = max(0.45, 1.5 * (1 - step / steps))
            predicted = network(x, tau=tau, mode="ste", gumbel=True)
            # Straight-through hard values are exactly 0/1; clamped BCE
            # would zero the gradient at mistakes. MSE retains a gradient.
            task_loss = F.mse_loss(predicted, desired)
            loss = task_loss + cost_weight * network.expected_ccx_proxy()
            loss.backward()
            optimizer.step()
            if step % 20 != 0 and step != steps - 1:
                continue
            graph = network.hard_graph()
            truth = graph.truth_tables()
            errors = sum(
                int(truth[o][v] != int(tables[o][v]))
                for o in range(len(tables)) for v in range(1 << n_inputs)
            )
            if errors < best_errors:
                best_errors = errors
            if errors == 0:
                candidate = lower_logic_dag(graph, verify=True)
                if (best_circuit is None or
                    candidate.resources().ccx < best_circuit.resources().ccx or
                    (candidate.resources().ccx == best_circuit.resources().ccx and
                     candidate.width < best_circuit.width)):
                    best_graph, best_circuit = graph, candidate
    return TrainingReport(best_graph, best_circuit, best_errors,
                          baseline, optimized, steps, restarts)
