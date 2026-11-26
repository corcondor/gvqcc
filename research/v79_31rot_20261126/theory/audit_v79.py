"""Exact full-cube or explicitly restricted-domain native V79 audits.

The phase-site audit detects equal/complement Boolean functions. The optional
CCX audit replaces a control product by 0, 1, a wire, or XOR of two wires only
after equality on every one of the 2**22 input states is established. Work
wires start at zero. The old target is deliberately excluded from candidates.
With --legal, the identities are proved only for x=1..3,133,452, and each
new affine identity receives an out-of-domain witness when one exists.
HMR semantics are checked with the same one-debt invariant as V79's verifier.
This is an independent diagnostic/rewriter, not an official KickMix run.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import hashlib
import json
from pathlib import Path
import sys
import time


def input_tables(width=22):
    length = 1 << width
    result = []
    for q in range(width):
        if q < 3:
            raw = bytes([[0xaa, 0xcc, 0xf0][q]]) * (length // 8)
        else:
            n = 1 << (q - 3)
            raw = (bytes(n) + b'\xff' * n) * (length // (16*n))
        result.append(int.from_bytes(raw, 'little'))
    return result


def low_weight_representation(product, state, target, ones):
    """Return (constant, wires), minimizing nonconstant terms up to weight 2."""
    if not product:
        return False, ()
    if product == ones:
        return True, ()
    available = {}
    for q, table in enumerate(state):
        if q != target:
            available.setdefault(table, q)
    if product in available:
        return False, (available[product],)
    complement = product ^ ones
    if complement in available:
        return True, (available[complement],)
    for q, table in enumerate(state):
        if q == target:
            continue
        difference = product ^ table
        if difference in available:
            r = available[difference]
            if r != q:
                return False, tuple(sorted((q, r)))
    return None


def full_span_representation(product, state, target, ones):
    """Exact affine-span membership using full truth tables and GF(2) elimination."""
    basis = {}
    qcount = len(state)
    values = [(q, value) for q, value in enumerate(state) if q != target]
    values.append((qcount, ones))
    for q, value in values:
        coefficients = 1 << q
        while value:
            pivot = value.bit_length() - 1
            if pivot not in basis:
                basis[pivot] = (value, coefficients)
                break
            row, combination = basis[pivot]
            value ^= row
            coefficients ^= combination
    value, coefficients = product, 0
    while value:
        pivot = value.bit_length() - 1
        if pivot not in basis:
            return None, len(basis)
        row, combination = basis[pivot]
        value ^= row
        coefficients ^= combination
    return (bool(coefficients >> qcount & 1),
            tuple(q for q in range(qcount) if coefficients >> q & 1)), len(basis)


def run(args):
    sys.path.insert(0, str(args.helpers.resolve()))
    from native_kmb import NativeKMB, Op
    started = time.time()
    circuit = NativeKMB.read(args.circuit)
    length = 1 << 22
    ones = ((1 << (3133452+1))-2) if args.legal else (1 << length) - 1
    full_inputs = input_tables()
    inputs = [value & ones for value in full_inputs]
    state = inputs + [0] * (circuit.header[1] - 22)
    full_state = full_inputs + [0] * (circuit.header[1] - 22)
    full_ones = (1 << length)-1
    phase_bytes = dict(circuit.sections)[10]
    angles = [int.from_bytes(phase_bytes[i:i+16], 'little')
              for i in range(0, len(phase_bytes), 16)]
    fingerprints = defaultdict(list)
    const_rotations, rewrites, output = [], [], []
    span_candidates, span_ranks = [], Counter()
    phase_index, debt, hmr_count, ccx_count = 0, None, 0, 0
    for index, op in enumerate(circuit.ops):
        wires, gate = op.wires, op.raw
        assert max(wires) < len(state)
        # This shadow replay is the unmodified source, used only to find a
        # counterexample to extending a legal identity outside its domain.
        full_product = None
        if args.legal:
            if gate == 17: full_state[wires[0]] ^= full_ones
            elif gate == 33: full_state[wires[1]] ^= full_state[wires[0]]
            elif gate == 49:
                full_product = full_state[wires[0]] & full_state[wires[1]]
                full_state[wires[2]] ^= full_product
            elif gate == 80: full_state[wires[0]] = 0
        def witness(constant, controls):
            if not args.legal:
                return None
            affine = full_ones if constant else 0
            for q in controls:
                assert q != wires[2]
                affine ^= full_state[q]
            difference = full_product ^ affine
            assert not difference & ones
            if not difference: return None
            x=(difference & -difference).bit_length()-1
            assert not 1 <= x <= 3133452
            return dict(x=x, control_product=(full_product>>x)&1,
                        affine_replacement=(affine>>x)&1,
                        original_controls=[(full_state[q]>>x)&1 for q in wires[:2]],
                        replacement_wires=[(full_state[q]>>x)&1 for q in controls])
        if gate == 17:
            state[wires[0]] ^= ones
        elif gate == 33:
            state[wires[1]] ^= state[wires[0]]
        elif gate == 49:
            ccx_count += 1
            product = state[wires[0]] & state[wires[1]]
            if args.ccx:
                representation = low_weight_representation(
                    product, state, wires[2], ones)
                if args.span:
                    span_representation, rank = full_span_representation(
                        product, state, wires[2], ones)
                    span_ranks[rank] += 1
                    if span_representation is not None:
                        const, controls = span_representation
                        span_candidates.append(dict(index=index,
                            old_wires=wires, constant=const, controls=controls,
                            out_of_domain_witness=witness(const,controls)))
                        if representation is None:
                            representation = span_representation
                if representation is not None:
                    constant, controls = representation
                    replacement = ([Op(17, (wires[2],))] if constant else [])
                    replacement += [Op(33, (q, wires[2])) for q in controls]
                    if len(replacement) <= args.max_replacement_ops:
                        rewrites.append(dict(index=index, old_wires=wires,
                                             constant=constant, controls=controls,
                                             new_ops=len(replacement),
                                             out_of_domain_witness=witness(constant,controls)))
                        output.extend(replacement)
                        state[wires[2]] ^= product
                        continue
            state[wires[2]] ^= product
        elif gate == 80:
            assert debt is None and op.measurement == 0
            debt = state[wires[0]]
            state[wires[0]] = 0
            hmr_count += 1
        elif gate in (144, 160):
            assert debt is not None and op.condition == 0
            correction = state[wires[0]]
            if gate == 160:
                correction &= state[wires[1]]
            assert correction == debt, (index, wires)
            debt = None
        elif gate == 19:
            if args.rotations:
                value = state[wires[0]]
                flipped = bool(value >> (1 if args.legal else 0) & 1)
                canonical = value ^ ones if flipped else value
                digest = hashlib.sha256(
                    canonical.to_bytes(length//8, 'little')).hexdigest()
                fingerprints[digest].append(dict(rotation_index=phase_index,
                                                instruction_index=index,
                                                complemented=flipped))
                if value in (0, ones):
                    const_rotations.append(dict(rotation_index=phase_index,
                                                value=bool(value)))
            phase_index += 1
        else:
            raise ValueError(f'Unsupported opcode {gate} at {index}')
        output.append(op)
        if args.ccx and index and index % 15000 == 0:
            print(json.dumps(dict(progress=index, ccx_seen=ccx_count,
                                  rewrites=len(rewrites),
                                  seconds=round(time.time()-started, 2))), flush=True)
    assert debt is None
    assert state == inputs + [0] * (circuit.header[1]-22)
    assert phase_index == len(angles)
    before, after = Counter(o.raw for o in circuit.ops), Counter(o.raw for o in output)
    repeated = [items for items in fingerprints.values() if len(items)>1]
    report = dict(source=str(args.circuit.resolve()),
                  source_sha256=hashlib.sha256(args.circuit.read_bytes()).hexdigest(),
                  inputs=3133452 if args.legal else length, width=circuit.header[1],
                  domain='legal_1_to_3133452' if args.legal else 'full_22_bit_cube',
                  rotations=phase_index, hmr_phase_debts_checked=hmr_count,
                  restoration='PASS', official_kickmix=False,
                  counts_before=dict(before), counts_after=dict(after),
                  instruction_count_before=len(circuit.ops),
                  instruction_count_after=len(output), ccx_rewrites=rewrites,
                  elapsed_seconds=time.time()-started)
    if args.span:
        report['full_affine_span_audit'] = dict(
            examined_ccx=ccx_count, candidates=span_candidates,
            available_span_rank_histogram=dict(span_ranks),
            scope='Current other wires and constant at each original CCX site; target excluded. No rescheduling or nonlinear-basis change.')
    if args.rotations:
        report['rotation_audit'] = dict(
            distinct_functions_up_to_complement=len(fingerprints),
            repeated_groups=len(repeated),
            removable_duplicate_count=sum(len(x)-1 for x in repeated),
            constant_rotations=const_rotations, examples=repeated[:20],
            note='No duplicate does not rule out a different phase basis or resynthesis.')
    if args.output_kmb:
        circuit.ops = output
        args.output_kmb.write_bytes(circuit.to_bytes())
        report['output_kmb'] = str(args.output_kmb.resolve())
        report['output_sha256'] = hashlib.sha256(args.output_kmb.read_bytes()).hexdigest()
    args.report.write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--helpers', type=Path, required=True)
    parser.add_argument('--circuit', type=Path, required=True)
    parser.add_argument('--report', type=Path, required=True)
    parser.add_argument('--rotations', action='store_true')
    parser.add_argument('--ccx', action='store_true')
    parser.add_argument('--span', action='store_true')
    parser.add_argument('--legal', action='store_true',help='Restrict identities to legal benchmark inputs.')
    parser.add_argument('--max-replacement-ops', type=int, default=2)
    parser.add_argument('--output-kmb', type=Path)
    run(parser.parse_args())
