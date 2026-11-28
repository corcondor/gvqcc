"""Neural LUT netlist -> exact clean reversible quantum oracle.

A 2-input Boolean gate has algebraic form
    f(a,b) = c0 XOR (c1 & a) XOR (c2 & b) XOR (c12 & a & b).
A destination initialized to zero can therefore be computed by X/CX/CCX
without measuring or losing the source values. Computing all live DAG nodes,
copying selected outputs, then reversing the computation clears *every*
temporary qubit. This is a safe first lowering, not yet optimal pebbling.
"""
from __future__ import annotations
from dataclasses import dataclass

from .reversible import Circuit, Gate, verify_oracle


@dataclass(frozen=True)
class LogicGate:
    a: int
    b: int
    tt: int

    def __post_init__(self):
        if self.a < 0 or self.b < 0 or not 0 <= self.tt <= 15:
            raise ValueError("Invalid LUT gate")


@dataclass(frozen=True)
class LogicDAG:
    n_inputs: int
    gates: tuple[LogicGate, ...]
    outputs: tuple[int, ...]

    def __post_init__(self):
        if self.n_inputs < 1 or not self.outputs:
            raise ValueError("Invalid graph dimensions")
        for i, gate in enumerate(self.gates):
            bound = self.n_inputs + i
            if gate.a >= bound or gate.b >= bound:
                raise ValueError("Gate depends on itself or a future gate")
        if any(out < 0 or out >= self.n_inputs + len(self.gates) for out in self.outputs):
            raise ValueError("Output wire is not defined")

    def evaluate(self, x: int) -> tuple[int, ...]:
        if not 0 <= x < (1 << self.n_inputs):
            raise ValueError("Input out of range")
        values = [(x >> i) & 1 for i in range(self.n_inputs)]
        for g in self.gates:
            addr = values[g.a] | (values[g.b] << 1)
            values.append((g.tt >> addr) & 1)
        return tuple(values[i] for i in self.outputs)

    def truth_tables(self) -> tuple[tuple[int, ...], ...]:
        rows = [self.evaluate(x) for x in range(1 << self.n_inputs)]
        return tuple(tuple(row[out] for row in rows) for out in range(len(self.outputs)))


def _uses(graph: LogicDAG) -> set[int]:
    live: set[int] = set()
    def visit(ref: int) -> None:
        if ref < graph.n_inputs:
            return
        i = ref - graph.n_inputs
        if i in live:
            return
        live.add(i)
        gate = graph.gates[i]
        visit(gate.a)
        visit(gate.b)
    for ref in graph.outputs:
        visit(ref)
    return live


def _swap_tt(tt: int) -> int:
    return (tt & 0b1001) | ((tt & 0b0010) << 1) | ((tt & 0b0100) >> 1)


def _lower_gate(a: int, b: int, tt: int, target: int) -> list[Gate]:
    """XOR a 2-input LUT into a fresh clean target, preserving a and b."""
    if a == b:
        f0, f1 = tt & 1, (tt >> 3) & 1
        return ([Gate("x", (target,))] if f0 else []) + (
            [Gate("cx", (a, target))] if f0 ^ f1 else []
        )
    f00 = tt & 1
    f10 = (tt >> 1) & 1
    f01 = (tt >> 2) & 1
    f11 = (tt >> 3) & 1
    out = []
    if f00:
        out.append(Gate("x", (target,)))
    if f00 ^ f10:
        out.append(Gate("cx", (a, target)))
    if f00 ^ f01:
        out.append(Gate("cx", (b, target)))
    if f00 ^ f10 ^ f01 ^ f11:
        out.append(Gate("ccx", (a, b, target)))
    return out


def lower_logic_dag(graph: LogicDAG, *, verify: bool = True,
                    fuse_output_sinks: bool = True) -> Circuit:
    """Compile a learned hard Boolean DAG into a clean quantum oracle.

    Direct output fusion writes a sink gate's f(a,b) straight into its
    output y bit via XOR. Since y is an arbitrary *target*, not a fresh
    ancilla, the gate is not uncomputed. Every *internal* live gate is
    uncomputed in reverse. This can halve CCX count for terminal ANDs.
    """
    live = _uses(graph)
    n = graph.n_inputs
    first_work = n + len(graph.outputs)
    output_refs: dict[int, list[int]] = {}
    for out, ref in enumerate(graph.outputs):
        output_refs.setdefault(ref, []).append(out)
    internal_users: set[int] = set()
    for index in live:
        g = graph.gates[index]
        for ref in (g.a, g.b):
            if ref >= n:
                internal_users.add(ref)
    possible_sinks: dict[int, int] = {}
    if fuse_output_sinks:
        for index in live:
            ref = n + index
            if ref not in internal_users and len(output_refs.get(ref, ())) == 1:
                possible_sinks[index] = output_refs[ref][0]

    wire_for_node: dict[int, int] = {}
    dedup: dict[tuple, int] = {}
    forward: list[Gate] = []
    computes: list[Gate] = []
    fused_nodes: set[int] = set()
    work_count = 0
    for index, g in enumerate(graph.gates):
        if index not in live:
            continue
        a = g.a if g.a < n else wire_for_node[g.a]
        b = g.b if g.b < n else wire_for_node[g.b]
        tt = g.tt
        if a > b:
            a, b = b, a
            tt = _swap_tt(tt)
        if a == b:
            identity = ("unary", a, tt & 1, (tt >> 3) & 1)
        else:
            identity = ("binary", a, b, tt)
        if identity in dedup:
            wire_for_node[n + index] = dedup[identity]
            continue
        if index in possible_sinks:
            # No descendants and exactly one output use. Its dirty y target
            # must NOT enter CSE, as it may hold arbitrary initial y.
            dest = n + possible_sinks[index]
            fused_nodes.add(index)
            wire_for_node[n + index] = dest
            forward.extend(_lower_gate(a, b, tt, dest))
            continue
        dest = first_work + work_count
        work_count += 1
        wire_for_node[n + index] = dest
        dedup[identity] = dest
        actions = _lower_gate(a, b, tt, dest)
        computes.extend(actions)
        forward.extend(actions)

    copies = []
    for out, ref in enumerate(graph.outputs):
        if ref >= n and (ref - n) in fused_nodes:
            continue
        source = ref if ref < n else wire_for_node[ref]
        copies.append(Gate("cx", (source, n + out)))
    circuit = Circuit(n, len(graph.outputs), work_count,
                      tuple(forward + copies + list(reversed(computes))))
    if verify:
        verify_oracle(circuit, graph.truth_tables())
    return circuit
