"""Combine repeated arithmetic updates across intervening affine routing."""

import argparse
from collections import Counter, defaultdict
from dataclasses import dataclass
from hashlib import file_digest
import json
from pathlib import Path

import numpy as np

import dqi_ccx_peephole as kmb
from theory_bilinear_patch import source_ordered_gf12
from theory_bilinear_verify import parse

PIN = "e4e110436080b8538f50511dc7064185e1708c2bd386ea0e36322d7791311355"
LINEAR = {0x21, 0x22}
CX, CCX = 0x21, 0x31


@dataclass(frozen=True)
class Template:
    name: str
    ops: tuple
    bases: tuple
    terms: tuple


@dataclass(frozen=True)
class Site:
    start: int
    stop: int
    template: Template
    mapping: dict

    def directions(self):
        return tuple(tuple(self.mapping[q] for q in part) for part in self.template.bases)


def support(mask):
    while mask:
        bit = mask & -mask
        yield bit.bit_length() - 1
        mask ^= bit


def remap(form, virtual):
    out = 0
    for q in support(form):
        out ^= virtual[q]
    return out


def instantiate(template, mapping):
    base = [[1 << mapping[q] for q in part] for part in template.bases]
    return [tuple(remap(form, axis) for form, axis in zip(t, base)) for t in template.terms]


def load_templates(repo):
    c = json.loads((repo / "inverse_v2_actual_eea_product_certificate.json").read_text())
    gf24_bases = tuple(c[k] for k in ("input_left", "input_right", "output_qubits_in_field_order"))
    gf24 = parse(repo / "inverse_v2_actual_eea_product.kmx")
    raw = json.loads((repo / "inverse_v2_actual_tensor99.json").read_text())
    # Peel the input conjugation layers so the corresponding plain tensor
    # also matches sites that place conjugations in the intervening routing.
    assert gf24[:12] == gf24[-12:]
    gf24_terms = [(a ^ ((a & 4095) << 12), b, w) for a, b, w in raw]
    gf12_notes = json.loads((repo / "theory_bilinear_input_certificate.json").read_text())["records"][0]
    gc12 = gf12_notes["terms"]
    return [Template("GF12", tuple(source_ordered_gf12(gc12)), tuple(range(q, q + 12) for q in (0, 12, 24)), tuple(gc12)),
            Template("GF24", tuple(gf24[12:-12]), gf24_bases, tuple(gf24_terms))]


def match(circuit, template):
    operands = []
    for count, columns in ((3, 3), (2, 2)):
        group = [op.qubits for op in template.ops if len(op.qubits) == count]
        for j in range(columns):
            operands.extend(q[j] for q in group)
    original, first, inv = np.unique(np.array(operands), return_index=True, return_inverse=True)
    packet_cols = {}
    for k in range(2, 7):
        packet = circuit.packets[k]
        packet_cols[k] = np.frombuffer(circuit.data, dtype="<u4", count=packet["payload_bytes"] // 4,
                                       offset=packet["payload_offset"])
    pattern = bytes(op.opcode for op in template.ops)
    n3, n2 = pattern.count(bytes([CCX])), pattern.count(bytes([CX]))
    assert n3 + n2 == len(pattern)
    start = -1
    while (start := circuit.opcodes.find(pattern, start + 1)) >= 0:
        q3, q2 = [circuit.rank(f"q{m}", start) for m in (3, 2)]
        parts = [packet_cols[k][q3:q3 + n3] for k in (2, 3, 4)] + [packet_cols[k][q2:q2 + n2] for k in (5, 6)]
        observed = np.concatenate(parts)
        rows = observed[first]
        if len(np.unique(rows)) == len(rows) and np.array_equal(rows[inv], observed):
            yield Site(start, start + len(pattern), template, dict(zip(map(int, original), map(int, rows))))


def route(terms, gap, n):
    forms = [1 << q for q in range(n)]
    for op in gap:
        a, b = op.qubits
        if op.opcode == CX:
            forms[b] ^= forms[a]
        else:
            forms[a], forms[b] = forms[b], forms[a]
    moved = []
    for a, b, w in terms:
        for op in reversed(gap):
            ctrl, target = op.qubits
            if op.opcode == CX:
                w ^= ((w >> ctrl) & 1) << target
            else:
                diff = ((w >> ctrl) ^ (w >> target)) & 1
                w ^= (diff << ctrl) | (diff << target)
        moved.append((remap(a, forms), remap(b, forms), w))
    return moved


def can_combine(a, b):
    updates = {u for _, _, u in a}
    reads = {r for x, y, _ in b for r in (x, y)}
    return not any((u & r).bit_count() & 1 for u in updates for r in reads)


def combine_directions(terms):
    shared = defaultdict(int)
    for a, b, w in terms:
        shared[min(a, b), max(a, b)] ^= w
    candidates = [(a, b, w) for (a, b), w in shared.items() if w]
    for axis in (0, 1):
        stars = defaultdict(list)
        for a, b, w in candidates:
            fixed, other = (a, b) if axis == 0 else (b, a)
            stars[fixed].append((other, w))
        candidates = [(min(fixed, other), max(fixed, other), w)
                      for fixed, star in stars.items() for other, w in compress(star)]
    return candidates


def eliminate(rows):
    """Re-express a sum of outer products along independent first factors."""
    basis = {}
    for v, w in rows:
        while v:
            pivot = v.bit_length()
            if pivot not in basis:
                basis[pivot] = v, w
                break
            other, weight = basis[pivot]
            v ^= other
            basis[pivot] = other, weight ^ w
    return [(v, w) for v, w in basis.values() if w]


def compress(star):
    after = eliminate(star)
    return [(v, w) for w, v in eliminate((w, v) for v, w in after)]


def reified(a, b, w):
    assert a and b and a != b and w
    pivot = next(support(a))
    ax = a ^ (1 << pivot)
    p1 = [kmb.Operation(CX, (i, pivot)) for i in support(ax)]
    if b >> pivot & 1:
        b ^= ax
    second = next(i for i in support(b) if i != pivot)
    p2 = [kmb.Operation(CX, (i, second)) for i in support(b ^ (1 << second))]
    setup = p1 + p2
    for op in setup:
        c, t = op.qubits
        w ^= ((w >> c) & 1) << t
    assert not ((w >> pivot | w >> second) & 1)
    target = next(support(w))
    fan = [kmb.Operation(CX, (target, i)) for i in support(w ^ (1 << target))]
    return setup + fan + [kmb.Operation(CCX, (pivot, second, target))] + fan[::-1] + setup[::-1]


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("source", type=Path)
    p.add_argument("profile", type=Path)
    p.add_argument("repo", type=Path)
    p.add_argument("report", type=Path)
    p.add_argument("--candidate", type=Path)
    p.add_argument("--test-templates", action="store_true")
    p.add_argument("--max-group", type=int, default=5)
    arg = p.parse_args()
    with arg.source.open("rb") as source:
        assert file_digest(source, "sha256").hexdigest() == PIN
    prof = json.loads(arg.profile.read_text())
    assert prof["raw_kmb_sha256"] == PIN
    circuit = kmb.BinaryCircuit(arg.source, prof)
    templates = load_templates(arg.repo)
    if arg.test_templates:
        from dqi_ccx_input_factor import exact_polynomial_check
        for template in templates:
            identity = {q: q for op in template.ops for q in op.qubits}
            rebuilt = [op for term in instantiate(template, identity) for op in reified(*term)]
            print(template.name, exact_polynomial_check(list(template.ops), rebuilt), flush=True)
    counts = {}
    selected = []
    overwrites = []
    for template in templates:
        occurrences = list(match(circuit, template))
        tally = Counter(matches=len(occurrences))
        for start, left in enumerate(occurrences):
            opening = instantiate(template, left.mapping)
            previous, gap = left, []
            for length, right in enumerate(occurrences[start + 1 : start + arg.max_group], 2):
                if previous.stop > right.start or right.start - previous.stop > 4096:
                    break
                raw = circuit.opcodes[previous.stop:right.start]
                if any(op not in LINEAR for op in set(raw)):
                    break
                if length == 2:
                    tally["affine_gap"] += 1
                gap += list(circuit.operations(previous.stop, right.start))
                closing = route(instantiate(template, right.mapping), gap, prof["header"]["num_qubits"])
                independent = can_combine(opening, closing)
                reverse = can_combine(closing, opening)
                if length == 2:
                    tally["independent_forward"] += independent
                    tally["independent_reverse"] += reverse
                if not independent or not reverse:
                    break
                tally[f"cross_independent_{length}"] += 1
                opening.extend(closing)
                transformed = combine_directions(opening)
                saved = len(opening) - len(transformed)
                previous = right
                if not saved:
                    continue
                tally["saving_groups"] += 1
                if any(left.start < end and right.stop > lo for lo, end, *_ in overwrites):
                    continue
                new = [op for term in transformed for op in reified(*term)] + gap
                overwrites.append((left.start, right.stop, list(circuit.operations(left.start, right.stop)), new))
                selected.append({"field": template.name, "start": left.start, "stop": right.stop, "saving": saved})
        counts[template.name] = dict(tally)
        print(template.name, counts[template.name], flush=True)
    if arg.candidate is not None and overwrites:
        if arg.candidate.exists():
            raise FileExistsError(arg.candidate)
        kmb.write_rewritten(circuit, arg.candidate, sorted(overwrites))
    circuit.close()
    arg.report.write_text(json.dumps({"baseline": PIN, "counts": counts, "selected": selected,
                                      "static_saving": sum(x["saving"] for x in selected)}, indent=2) + "\n")


if __name__ == "__main__":
    main()
