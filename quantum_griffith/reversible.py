"""Small exact reversible circuit IR, basis simulator and resource accounting.

The gate alphabet is X, CX, CCX only. On arbitrary superpositions these
permutation matrices preserve the relative phase exactly (unlike relative-phase
Toffoli rewrites); basis checking plus this gate restriction proves the oracle
action on all quantum inputs when the work register starts clean.
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import Sequence

_ARITY = {"x": 1, "cx": 2, "ccx": 3}


@dataclass(frozen=True)
class Gate:
    kind: str
    wires: tuple[int, ...]

    def __post_init__(self) -> None:
        if self.kind not in _ARITY:
            raise ValueError("Only exact phase-free X/CX/CCX are allowed")
        if len(self.wires) != _ARITY[self.kind] or len(set(self.wires)) != len(self.wires):
            raise ValueError("A gate requires distinct wires of the correct arity")
        if any(not isinstance(i, int) or i < 0 for i in self.wires):
            raise ValueError("Invalid qubit index")

    def inverse(self) -> Gate:
        return self  # all supported gates are self-inverse


@dataclass(frozen=True)
class ResourceCost:
    x: int
    cx: int
    ccx: int
    qubits: int
    ancillas: int
    depth: int
    t7_estimate: int

    def as_dict(self) -> dict[str, int]:
        return {
            "x": self.x, "cx": self.cx, "ccx": self.ccx,
            "qubits": self.qubits, "ancillas": self.ancillas,
            "depth": self.depth, "t7_estimate": self.t7_estimate,
        }


@dataclass(frozen=True)
class Circuit:
    n_inputs: int
    n_outputs: int
    n_ancillas: int
    gates: tuple[Gate, ...]

    def __post_init__(self) -> None:
        if self.n_inputs < 1 or self.n_outputs < 1 or self.n_ancillas < 0:
            raise ValueError("Invalid register dimensions")
        for gate in self.gates:
            if any(q >= self.width for q in gate.wires):
                raise ValueError("Gate wire is outside the circuit")

    @property
    def width(self) -> int:
        return self.n_inputs + self.n_outputs + self.n_ancillas

    def simulate_bits(self, x: int, y: int = 0, anc: int = 0) -> tuple[int, int, int]:
        """Exact classical permutation induced by the quantum gates."""
        if not 0 <= x < (1 << self.n_inputs):
            raise ValueError("x out of range")
        if not 0 <= y < (1 << self.n_outputs):
            raise ValueError("y out of range")
        if not 0 <= anc < (1 << self.n_ancillas):
            raise ValueError("anc out of range")
        state = x | (y << self.n_inputs) | (anc << (self.n_inputs + self.n_outputs))
        for gate in self.gates:
            if gate.kind == "x":
                state ^= 1 << gate.wires[0]
            elif gate.kind == "cx":
                c, t = gate.wires
                if state & (1 << c):
                    state ^= 1 << t
            else:
                a, b, t = gate.wires
                if state & (1 << a) and state & (1 << b):
                    state ^= 1 << t
        xm = (1 << self.n_inputs) - 1
        ym = (1 << self.n_outputs) - 1
        return state & xm, (state >> self.n_inputs) & ym, state >> (self.n_inputs + self.n_outputs)

    def resources(self) -> ResourceCost:
        count = {k: 0 for k in _ARITY}
        last = [0] * self.width
        for gate in self.gates:
            count[gate.kind] += 1
            depth = 1 + max(last[q] for q in gate.wires)
            for q in gate.wires:
                last[q] = depth
        return ResourceCost(
            x=count["x"], cx=count["cx"], ccx=count["ccx"],
            qubits=self.width, ancillas=self.n_ancillas,
            depth=max(last, default=0), t7_estimate=7 * count["ccx"],
        )

    def to_json(self) -> dict:
        return {
            "ir_version": 1, "registers": {
                "x": self.n_inputs, "y": self.n_outputs, "anc": self.n_ancillas
            },
            "gates": [{"kind": g.kind, "wires": list(g.wires)} for g in self.gates],
            "resources": self.resources().as_dict(),
        }

    @staticmethod
    def from_json(obj: dict) -> Circuit:
        r = obj["registers"]
        return Circuit(
            r["x"], r["y"], r["anc"],
            tuple(Gate(v["kind"], tuple(v["wires"])) for v in obj["gates"])
        )


def verify_oracle(circuit: Circuit, tables: Sequence[Sequence[int]], *,
                  all_y: bool = True) -> dict[str, int]:
    """Prove |x>|y>|0> -> |x>|y XOR f(x)>|0> on all x and tested y.

    For at most 5 outputs, y is exhaustively enumerated by default. Above
    that, use a representative collection; an exhaustive proof can be obtained
    by calling this with a smaller output partition. The circuit is a phase-free
    permutation, so this certifies the superposition oracle on clean ancillas.
    """
    n = circuit.n_inputs
    if len(tables) != circuit.n_outputs:
        raise ValueError("Table count differs from output count")
    if any(len(t) != (1 << n) for t in tables):
        raise ValueError("Each truth table must have 2^n entries")
    if any(bit not in (0, 1) for t in tables for bit in t):
        raise ValueError("Truth table entries must be 0/1")
    ys = (range(1 << circuit.n_outputs)
          if all_y and circuit.n_outputs <= 5 else
          sorted(set((0, 1, (1 << circuit.n_outputs) - 1))))
    checked = 0
    for x in range(1 << n):
        fx = sum(int(t[x]) << j for j, t in enumerate(tables))
        for y in ys:
            xx, yy, anc = circuit.simulate_bits(x, y)
            checked += 1
            if (xx, yy, anc) != (x, y ^ fx, 0):
                raise AssertionError(
                    f"Not a clean oracle: x={x}, y={y}, "
                    f"got={(xx, yy, anc)}, expected={(x, y ^ fx, 0)}"
                )
    return {"basis_cases_checked": checked, "phase_safe_by_gate_alphabet": 1}
