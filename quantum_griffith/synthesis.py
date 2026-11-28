"""Exact ANF baselines, globally shared prefix DAGs, and affine-basis search.

The compiler intentionally optimizes CCX count instead of number of generic
two-input gates. Affine remapping is an invertible CNOT-only change of basis,
undone after the Boolean oracle, so the logical oracle is unchanged.
"""
from __future__ import annotations
import itertools
import random
from dataclasses import dataclass
from typing import Sequence

from .reversible import Circuit, Gate, verify_oracle

Tables = tuple[tuple[int, ...], ...]


def _validate(tables: Sequence[Sequence[int]], n_inputs: int) -> Tables:
    if not 1 <= n_inputs <= 10:
        raise ValueError("Supported test-oriented input size is 1..10")
    if not tables or any(len(t) != (1 << n_inputs) for t in tables):
        raise ValueError("Expected nonempty output tables, each with 2^n entries")
    if any(v not in (0, 1) for t in tables for v in t):
        raise ValueError("Output values must be Boolean")
    return tuple(tuple(int(v) for v in t) for t in tables)


def anf_terms(table: Sequence[int], n_inputs: int) -> tuple[int, ...]:
    """Möbius transform: f(x) = XOR_{mask in result} AND_{i in mask} x_i."""
    if len(table) != (1 << n_inputs):
        raise ValueError("Incorrect truth-table length")
    vals = [int(v) for v in table]
    if any(v not in (0, 1) for v in vals):
        raise ValueError("Non-Boolean truth-table value")
    for bit in range(n_inputs):
        for mask in range(1 << n_inputs):
            if mask & (1 << bit):
                vals[mask] ^= vals[mask ^ (1 << bit)]
    return tuple(mask for mask, v in enumerate(vals) if v)


def _term_index(tables: Tables, n: int) -> dict[int, tuple[int, ...]]:
    terms: dict[int, list[int]] = {}
    for out, table in enumerate(tables):
        for monomial in anf_terms(table, n):
            terms.setdefault(monomial, []).append(out)
    return {term: tuple(outputs) for term, outputs in terms.items()}


def _bits(mask: int, order: tuple[int, ...]) -> list[int]:
    return [i for i in order if mask & (1 << i)]


def _baseline(tables: Tables, n: int) -> Circuit:
    terms = _term_index(tables, n)
    degree = max((t.bit_count() for t in terms), default=0)
    work = max(0, degree - 2)
    anc0 = n + len(tables)
    ops: list[Gate] = []
    for mask, outputs in sorted(terms.items()):
        variables = [b for b in range(n) if mask & (1 << b)]
        degree_now = len(variables)
        for out in outputs:
            dest = n + out
            if degree_now == 0:
                ops.append(Gate("x", (dest,)))
            elif degree_now == 1:
                ops.append(Gate("cx", (variables[0], dest)))
            elif degree_now == 2:
                ops.append(Gate("ccx", (variables[0], variables[1], dest)))
            else:
                computes = [Gate("ccx", (variables[0], variables[1], anc0))]
                for j in range(2, degree_now - 1):
                    computes.append(Gate("ccx", (anc0 + j - 2, variables[j], anc0 + j - 1)))
                ops.extend(computes)
                ops.append(Gate("ccx", (anc0 + degree_now - 3, variables[-1], dest)))
                ops.extend(reversed(computes))
    return Circuit(n, len(tables), work, tuple(ops))


def _required_prefixes(terms: dict[int, tuple[int, ...]], order: tuple[int, ...]) -> set[int]:
    result: set[int] = set()
    for mask in terms:
        bits = _bits(mask, order)
        if len(bits) >= 3:
            pref = (1 << bits[0]) | (1 << bits[1])
            result.add(pref)
            for bit in bits[2:-1]:
                pref |= 1 << bit
                result.add(pref)
    return result


def _shared_estimate(terms: dict[int, tuple[int, ...]], order: tuple[int, ...]) -> tuple[int, int]:
    prefix_count = len(_required_prefixes(terms, order))
    terminals = sum(min(len(outs), 2) for t, outs in terms.items() if t.bit_count() >= 2)
    scratch = int(any(t.bit_count() >= 2 and len(outs) >= 3 for t, outs in terms.items()))
    return 2 * prefix_count + terminals, prefix_count + scratch


def _candidate_orders(n: int):
    if n <= 6:
        yield from itertools.permutations(range(n))
    else:
        rng = random.Random(20261122)
        default = tuple(range(n))
        seen = {default}
        yield default
        for _ in range(192):
            order = list(range(n))
            rng.shuffle(order)
            t = tuple(order)
            if t not in seen:
                seen.add(t)
                yield t


def _compile_shared(tables: Tables, n: int, order: tuple[int, ...]) -> Circuit:
    terms = _term_index(tables, n)
    prefixes = sorted(_required_prefixes(terms, order), key=lambda t: (t.bit_count(), t))
    first_anc = n + len(tables)
    registers = {mask: first_anc + j for j, mask in enumerate(prefixes)}
    ops: list[Gate] = []
    computes: list[Gate] = []
    for mask in prefixes:
        variables = _bits(mask, order)
        if len(variables) == 2:
            gate = Gate("ccx", (variables[0], variables[1], registers[mask]))
        else:
            parent = mask ^ (1 << variables[-1])
            gate = Gate("ccx", (registers[parent], variables[-1], registers[mask]))
        computes.append(gate)
    ops.extend(computes)

    scratch_needed = any(t.bit_count() >= 2 and len(outs) >= 3 for t, outs in terms.items())
    scratch = first_anc + len(prefixes)
    for mask, outputs in sorted(terms.items()):
        variables = _bits(mask, order)
        degree = len(variables)
        if degree <= 1:
            for out in outputs:
                if degree == 0:
                    ops.append(Gate("x", (n + out,)))
                else:
                    ops.append(Gate("cx", (variables[0], n + out)))
            continue
        if degree == 2:
            a, b = variables
        else:
            prefix = mask ^ (1 << variables[-1])
            a, b = registers[prefix], variables[-1]
        if len(outputs) > 2:
            ccx = Gate("ccx", (a, b, scratch))
            ops.append(ccx)
            for out in outputs:
                ops.append(Gate("cx", (scratch, n + out)))
            ops.append(ccx)
        else:
            for out in outputs:
                ops.append(Gate("ccx", (a, b, n + out)))
    ops.extend(reversed(computes))
    return Circuit(n, len(tables), len(prefixes) + int(scratch_needed), tuple(ops))


def _score(circuit: Circuit) -> float:
    r = circuit.resources()
    # The dominant currency is Toffoli count. Penalize clean work lines and
    # CNOT/depth modestly; no "free arbitrary Boolean gate" abstraction.
    return r.ccx + 0.18 * r.ancillas + 0.015 * r.cx + 0.0001 * r.depth


@dataclass(frozen=True)
class SynthesisResult:
    circuit: Circuit
    method: str
    basis_cnots: tuple[tuple[int, int], ...] = ()

    def as_dict(self) -> dict:
        return {
            "method": self.method,
            "basis_cnots": [list(v) for v in self.basis_cnots],
            "resources": self.circuit.resources().as_dict(),
            "circuit": self.circuit.to_json(),
        }


def synthesize(tables: Sequence[Sequence[int]], n_inputs: int, *,
               method: str = "best", max_ancillas: int | None = None) -> SynthesisResult:
    """Compile ANF into an exact quantum oracle. No approximation of f is made."""
    targets = _validate(tables, n_inputs)
    if method not in ("best", "baseline", "shared"):
        raise ValueError("method must be best/baseline/shared")
    baseline = SynthesisResult(_baseline(targets, n_inputs), "anf-baseline")
    if method == "baseline":
        return baseline
    terms = _term_index(targets, n_inputs)
    orders = sorted(
        _candidate_orders(n_inputs),
        key=lambda o: (_shared_estimate(terms, o)[0] +
                       0.18 * _shared_estimate(terms, o)[1], o),
    )
    best_shared = None
    for order in orders:
        estimate = _shared_estimate(terms, order)
        if max_ancillas is not None and estimate[1] > max_ancillas:
            continue
        candidate = SynthesisResult(_compile_shared(targets, n_inputs, order),
                                    "shared-prefix-dag")
        if best_shared is None or _score(candidate.circuit) < _score(best_shared.circuit):
            best_shared = candidate
        # Candidate-order score captures the only significant variation:
        # prefix count, so a tie cannot improve CCX/width. 1st is enough.
        break
    if method == "shared":
        if best_shared is None:
            raise ValueError("No shared DAG fits the ancilla budget")
        return best_shared
    if max_ancillas is not None and baseline.circuit.n_ancillas > max_ancillas:
        if best_shared is None:
            raise ValueError("No circuit fits the ancilla budget")
        return best_shared
    if best_shared is None:
        return baseline
    return min((baseline, best_shared), key=lambda r: _score(r.circuit))


def _map_tables(tables: Tables, n: int, rows: tuple[int, ...]) -> Tables:
    # u=A*x. Since A is generated by CNOT row operations it is invertible.
    result = [[0] * (1 << n) for _ in tables]
    for x in range(1 << n):
        u = sum(((x & row).bit_count() & 1) << i for i, row in enumerate(rows))
        for out, table in enumerate(tables):
            result[out][u] = table[x]
    return tuple(tuple(v) for v in result)


def _wrap_basis(core: SynthesisResult, n: int,
                moves: tuple[tuple[int, int], ...]) -> SynthesisResult:
    gates = tuple(Gate("cx", move) for move in moves)
    wrapped = Circuit(
        n, core.circuit.n_outputs, core.circuit.n_ancillas,
        gates + core.circuit.gates + tuple(reversed(gates)),
    )
    return SynthesisResult(wrapped, "affine-" + core.method, moves)


def search_affine(tables: Sequence[Sequence[int]], n_inputs: int, *,
                  max_depth: int = 2, beam_width: int = 16,
                  max_ancillas: int | None = None,
                  verify: bool = True) -> SynthesisResult:
    """Cost-guided beam search over invertible GF(2) changes of input basis.

    This is an actual discrete structure search, NOT yet an NN trainer. Every
    explored transformation has exact inverse CNOTs, so the full oracle is exact.
    """
    targets = _validate(tables, n_inputs)
    if max_depth < 0 or beam_width < 1:
        raise ValueError("Invalid beam-search parameters")
    if max_depth > 5:
        raise ValueError("Limit search depth to 5 for bounded experimentation")
    initial = synthesize(targets, n_inputs, max_ancillas=max_ancillas)
    best = initial
    ident = tuple(1 << i for i in range(n_inputs))
    visited = {ident}
    frontier: list[tuple[tuple[int, ...], tuple[tuple[int, int], ...]]] = [(ident, ())]
    for _depth in range(max_depth):
        next_states: list[tuple[float, tuple[int, ...], tuple[tuple[int, int], ...]]] = []
        for rows, path in frontier:
            for c in range(n_inputs):
                for t in range(n_inputs):
                    if c == t:
                        continue
                    new_rows = list(rows)
                    new_rows[t] ^= new_rows[c]
                    key = tuple(new_rows)
                    if key in visited:
                        continue
                    visited.add(key)
                    new_path = path + ((c, t),)
                    mapped = _map_tables(targets, n_inputs, key)
                    try:
                        core = synthesize(mapped, n_inputs, max_ancillas=max_ancillas)
                    except ValueError:
                        continue
                    candidate = _wrap_basis(core, n_inputs, new_path)
                    score = _score(candidate.circuit)
                    next_states.append((score, key, new_path))
                    if score < _score(best.circuit):
                        best = candidate
        next_states.sort(key=lambda item: (item[0], item[1]))
        frontier = [(rows, path) for _, rows, path in next_states[:beam_width]]
        if not frontier:
            break
    if verify:
        verify_oracle(best.circuit, targets)
    return best


@dataclass(frozen=True)
class JointSynthesisResult:
    """A fully conjugated oracle: input basis A and output basis B."""
    circuit: Circuit
    method: str
    input_basis_cnots: tuple[tuple[int, int], ...]
    output_basis_cnots: tuple[tuple[int, int], ...]

    def as_dict(self) -> dict:
        return {
            "method": self.method,
            "input_basis_cnots": [list(g) for g in self.input_basis_cnots],
            "output_basis_cnots": [list(g) for g in self.output_basis_cnots],
            "resources": self.circuit.resources().as_dict(),
        }


def _mix_outputs(tables: Tables, rows: tuple[int, ...]) -> Tables:
    """Apply an invertible output GF(2) basis B to the function vector."""
    length = len(tables[0])
    return tuple(
        tuple(
            sum(tables[k][x] for k in range(len(tables)) if (row >> k) & 1) % 2
            for x in range(length)
        )
        for row in rows
    )


def _wrap_joint(core: SynthesisResult, n_inputs: int,
                input_moves: tuple[tuple[int, int], ...],
                output_moves: tuple[tuple[int, int], ...]) -> JointSynthesisResult:
    # x <- A*x, y <- B*y, y <- y XOR (B*f(A^-1*x)),
    # y <- B^-1*y, x <- A^-1*x.
    # As both transforms are exact CNOTs, all y values and all phases agree.
    pre_x = tuple(Gate("cx", move) for move in input_moves)
    pre_y = tuple(Gate("cx", (n_inputs + c, n_inputs + t))
                  for c, t in output_moves)
    circuit = Circuit(
        n_inputs, core.circuit.n_outputs, core.circuit.n_ancillas,
        pre_x + pre_y + core.circuit.gates + tuple(reversed(pre_y)) + tuple(reversed(pre_x))
    )
    return JointSynthesisResult(circuit, "joint-affine-" + core.method,
                                input_moves, output_moves)


def search_joint_affine(tables: Sequence[Sequence[int]], n_inputs: int, *,
                        max_depth: int = 2, beam_width: int = 24,
                        max_ancillas: int | None = None,
                        verify: bool = True) -> JointSynthesisResult:
    """Search joint input/output GF(2) bases with exact conjugation.

    Output encoding is an important overlooked degree of freedom. Since the
    output register may contain arbitrary y initially, one cannot simply
    optimize f by taking linear combinations of its components: one must
    conjugate the output register with the same invertible transform.
    """
    targets = _validate(tables, n_inputs)
    if not 0 <= max_depth <= 5 or beam_width < 1:
        raise ValueError("Invalid joint search parameters")
    nout = len(targets)
    ident_x = tuple(1 << i for i in range(n_inputs))
    ident_y = tuple(1 << i for i in range(nout))
    first = synthesize(targets, n_inputs, max_ancillas=max_ancillas)
    best = _wrap_joint(first, n_inputs, (), ())
    visited = {(ident_x, ident_y)}
    frontier = [(ident_x, ident_y, (), ())]
    for _depth in range(max_depth):
        proposed = []
        for rows_x, rows_y, path_x, path_y in frontier:
            for group in ("input", "output"):
                nbits = n_inputs if group == "input" else nout
                for control in range(nbits):
                    for target in range(nbits):
                        if control == target:
                            continue
                        new_x, new_y = rows_x, rows_y
                        new_path_x, new_path_y = path_x, path_y
                        if group == "input":
                            tmp = list(rows_x)
                            tmp[target] ^= tmp[control]
                            new_x = tuple(tmp)
                            new_path_x = path_x + ((control, target),)
                        else:
                            tmp = list(rows_y)
                            tmp[target] ^= tmp[control]
                            new_y = tuple(tmp)
                            new_path_y = path_y + ((control, target),)
                        state = (new_x, new_y)
                        if state in visited:
                            continue
                        visited.add(state)
                        transformed = _mix_outputs(
                            _map_tables(targets, n_inputs, new_x), new_y
                        )
                        try:
                            core = synthesize(
                                transformed, n_inputs, max_ancillas=max_ancillas
                            )
                        except ValueError:
                            continue
                        candidate = _wrap_joint(core, n_inputs, new_path_x, new_path_y)
                        merit = _score(candidate.circuit)
                        proposed.append((merit, new_x, new_y, new_path_x, new_path_y))
                        if merit < _score(best.circuit):
                            best = candidate
        proposed.sort(key=lambda z: (z[0], z[1], z[2]))
        frontier = [(x, y, px, py) for _, x, y, px, py in proposed[:beam_width]]
        if not frontier:
            break
    if verify:
        verify_oracle(best.circuit, targets)
    return best
