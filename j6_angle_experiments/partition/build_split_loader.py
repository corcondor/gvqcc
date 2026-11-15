#!/usr/bin/env python3
"""Synthesize a two-stage, exact J=6 angle loader at the 128-qubit cap.

A ten-bit lower-page function is followed by a top-bit-masked correction.
Each stage has its own complete monomial banks. Linear forms borrow two
independent feature pivots, which are immediately restored.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import sys
from pathlib import Path

import kickmix as km
import numpy as np

J = 6
WORD_BITS = J * 8
BASE = 11 + WORD_BITS
SIZE = 1220
TOP = 1024
WORDS_SHA = "8caf7416de79102103757e3ab7ab4b6bbebfad9b1bf1ecd564c20eb948dbfcea"


def bits(mask: int):
    while mask:
        bit = mask & -mask
        yield bit.bit_length() - 1
        mask ^= bit


def mobius(values):
    assert len(values) != 0 and len(values) & (len(values) - 1) == 0
    out = np.array(values, copy=True)
    for bit in range((len(out) - 1).bit_length()):
        span = 1 << bit
        shaped = out.reshape(-1, span * 2)
        shaped[:, span:] ^= shaped[:, :span]
    return out[:len(values)]


def basis_factor(columns):
    basis = {}
    left = []
    right = []
    for h, column in enumerate(columns):
        mask = 0
        while column:
            pivot = column.bit_length() - 1
            if pivot in basis:
                row, idx = basis[pivot]
                column ^= row
                mask ^= 1 << idx
            else:
                idx = len(left)
                basis[pivot] = (column, idx)
                left.append(column)
                right.append(0)
                mask ^= 1 << idx
                break
        for idx in bits(mask):
            right[idx] ^= 1 << h
    return list(zip(left, right))


def complete_columns(columns, low_masks, high_masks, care):
    """Minimum rank completion in a nested mask care-domain."""
    basis = []
    completed = []
    for h, column in zip(high_masks, columns):
        mask = sum(1 << i for i, low in enumerate(low_masks)
                   if i and (low | h) < care)
        rows = {}
        for independent in basis:
            reduced = independent & mask
            original = independent
            while reduced:
                pivot = reduced.bit_length() - 1
                if pivot not in rows:
                    rows[pivot] = reduced, original
                    break
                down, full = rows[pivot]
                reduced ^= down
                original ^= full
        reduced = column
        combo = 0
        while reduced:
            pivot = reduced.bit_length() - 1
            if pivot not in rows:
                break
            down, full = rows[pivot]
            reduced ^= down
            combo ^= full
        if reduced:
            basis.append(column)
            combo = column
        assert combo & mask == column
        completed.append(combo)
    return completed


def terms_of_cross_tensor(deltas, lo, hi, completion=True):
    """Pair residual rank-one outer products and share odd slices."""
    care = len(deltas)
    canvas = np.zeros(1024, np.uint64)
    canvas[:care] = deltas
    coeff = mobius(canvas)
    coeff[care:] = 0
    columns = [
        [0] + [sum((1 << d) for d, l in enumerate(lo) if d and (h|l)<care
                   and int(coeff[h|l])>>o&1) for h in hi[1:]]
        for o in range(WORD_BITS)
    ]
    if completion and care != 1024:
        columns = [complete_columns(c, lo, hi, care) for c in columns]
    factors = [basis_factor(c) for c in columns]
    ranks = [len(f) for f in factors]
    terms = []
    # If two output slices have maximal odd rank, delete one input row from
    # each via a shared rank-two update. For incomplete-rank slices a
    # rank-safe choice of two independent directions is handled below.
    odd = [o for o, rank in enumerate(ranks) if rank % 2]
    while len(odd) >= 2:
        a = odd.pop(0)
        ca = columns[a]
        best = None
        for b in odd:
            cb = columns[b]
            for ia in range(1, len(lo)):
                if not any(c>>ia&1 for c in ca):
                    continue
                ra = [c^((c>>ia&1)<<ia) for c in ca]
                if len(basis_factor(ra)) != ranks[a]-1:
                    continue
                ha = sum((1<<h) for h,c in enumerate(ca) if c>>ia&1)
                for ib in range(1, len(lo)):
                    if ia == ib or not any(c>>ib&1 for c in cb):
                        continue
                    hb = sum((1<<h) for h,c in enumerate(cb) if c>>ib&1)
                    cross = [((ha>>h&1)<<ia)^((hb>>h&1)<<ib) for h in range(len(hi))]
                    fa = basis_factor([c^s for c,s in zip(ca,cross)])
                    if len(fa) != ranks[a]-1:
                        continue
                    fb = basis_factor([c^s for c,s in zip(cb,cross)])
                    if len(fb) == ranks[b]-1:
                        best = (b, ia, ib, ha, hb, fa, fb)
                        break
                if best:
                    break
            if best:
                break
        if best:
            b, ia, ib, ha, hb, factors[a], factors[b] = best
            odd.remove(b)
            terms.append((1<<ia, hb, 1<<ib, ha, (1<<a)|(1<<b)))
    for o, factor in enumerate(factors):
        for i in range(0, len(factor), 2):
            a, ha = factor[i]
            if i+1 < len(factor):
                b, hb = factor[i+1]
                terms.append((a, hb, b, ha, 1<<o))
            else:
                terms.append((a, 0, 0, ha, 1<<o))
    return terms, ranks


def marks(variables, care):
    return [sum(1 << q for bit, q in enumerate(variables) if mask >> bit & 1)
            for mask in range(1 << len(variables))
            if sum(1 << q for bit, q in enumerate(variables) if mask>>bit&1) < care]


def pack_words(words):
    converted = words.astype(np.uint64).copy()
    converted ^= (converted & 64) << 1
    return sum(converted[:, j] << (8*j) for j in range(J))


def bitpacked(arr):
    return int.from_bytes(np.packbits(np.asarray(arr, dtype=np.uint8), bitorder="little").tobytes(), "little")


def synthesize(delta, low=(0,1,2,3), correction_low=None):
    lines = []
    groups = [("selection", range(11))]
    groups.extend((f"word_{j}", range(11+8*j, 19+8*j)) for j in range(J))
    for r, (name, wires) in enumerate(groups):
        lines.extend(f"APPEND_TO_REGISTER q{q} r{r}" for q in wires)
        lines.append(f'REGISTER r{r} "{name}"')
    coding = [f"CX q{17+8*j} q{18+8*j}" for j in range(J)]
    lines += coding
    desired = pack_words(delta)
    addresses = np.arange(SIZE)
    statistics = []

    def stage(correction, low):
        high = tuple(q for q in range(10) if q not in low)
        care = SIZE - TOP if correction else TOP
        lo, hi = marks(low, care), marks(high, care)
        wanted = desired[TOP:] ^ desired[:care] if correction else desired[:TOP]
        terms, ranks = terms_of_cross_tensor(wanted, lo, hi)
        cursor = BASE
        nodes = []

        def product(a, b):
            nonlocal cursor
            target = cursor
            cursor += 1
            nodes.append((a, b, target))
            lines.append(f"CCX q{a} q{b} q{target}")
            return target

        def bank(masks, masked):
            if masked:
                wires = {0: 10}
            else:
                wires = {}
            for mask in masks[1:]:
                unit = mask & -mask
                q = unit.bit_length() - 1
                if mask == unit and not masked:
                    wires[mask] = q
                else:
                    wires[mask] = product(q, wires[mask^unit])
            return wires

        lw = bank(lo, False)
        hw = bank(hi, correction)
        assert cursor <= 128, cursor
        residual = (np.r_[np.zeros(TOP, np.uint64), wanted]
                    if correction else wanted[addresses % TOP]).copy()
        lv = [((addresses & m) == m) for m in lo]
        hv = [((addresses & m) == m) & ((addresses >= TOP) if correction else True) for m in hi]

        def form(lmask, hmask):
            wires = {lw[lo[i]] for i in bits(lmask)} | {hw[hi[i]] for i in bits(hmask)}
            vectors = [lv[i] for i in bits(lmask)] + [hv[i] for i in bits(hmask)]
            assert vectors
            return wires, np.bitwise_xor.reduce(vectors, axis=0)

        def emit_term(c1, c2, targets):
            if not c1-c2:
                c1, c2 = c2, c1
            assert c1-c2
            p = min(c1-c2)
            q = min(c2)
            first = [f"CX q{c} q{p}" for c in sorted(c1-{p})]
            second = [f"CX q{c} q{q}" for c in sorted(c2-{q})]
            target = 11 + targets[0]
            fan = [f"CX q{target} q{11+o}" for o in targets[1:]]
            lines.extend(fan + first + second + [f"CCX q{p} q{q} q{target}"]
                         + second[::-1] + first[::-1] + fan[::-1])

        for a, ha, b, hb, output in terms:
            ca, av = form(a, ha)
            cb, bv = form(b, hb)
            emit_term(ca, cb, list(bits(output)))
            residual ^= (av & bv).astype(np.uint64) * np.uint64(output)

        # On the lower page any mixed term is forbidden. On the guarded
        # page pure low terms generated by the pairing identity can be
        # emitted globally, after which the guarded residual is separable.
        if correction:
            lower = mobius(residual[:TOP])
            for m in range(TOP):
                if not lower[m]:
                    continue
                assert m in lo, ("unexpected low residue", m)
                for o in bits(int(lower[m])):
                    lines.append(f"CX q{lw[m]} q{11+o}" if m else f"X q{11+o}")
            target = residual[TOP:] ^ residual[:care]
        else:
            target = residual[:TOP]
        canvas = np.zeros(TOP, np.uint64)
        canvas[:len(target)] = target
        coeff = mobius(canvas)
        gated_low_cost = 0
        for m in range(care):
            if not coeff[m]:
                continue
            assert m in hi or m in lo, ("unexpected residual", m)
            if correction and m and m in lw:
                emit_term({10}, {lw[m]}, list(bits(int(coeff[m]))))
                gated_low_cost += 1
                continue
            for o in bits(int(coeff[m])):
                if m in hw:
                    lines.append(f"CX q{hw[m]} q{11+o}")
                elif m in lw:
                    lines.append(f"CX q{lw[m]} q{11+o}")
                else:
                    assert m == 0 and not correction
                    lines.append(f"X q{11+o}")
        for a,b,c in reversed(nodes):
            lines.extend((f"HMR q{c} b0", f"CZ q{a} q{b} if b0"))
        statistics.append(dict(correction=correction, low_bits=low, hi_bits=high,
                               qubits=cursor, bank_ccx=len(nodes), core_ccx=len(terms)+gated_low_cost,
                               gated_low_ccx=gated_low_cost,
                               ranks=ranks))

    stage(False, low)
    stage(True, correction_low or low)
    lines.extend(coding)
    circuit = km.Circuit("\n".join(lines) + "\n")
    assert circuit.num_qubits <= 128
    assert circuit.operation_statistics().num_toffoli_like == sum(
        s["bank_ccx"] + s["core_ccx"] for s in statistics)
    return circuit, statistics


def prove(circuit, delta):
    """Symbolic tensor of the 1,220 addresses × 48 arbitrary input bits."""
    one = (1 << SIZE) - 1
    original_address = [bitpacked(np.arange(SIZE)>>q&1) for q in range(11)]
    original_words = [one << (SIZE*(o+1)) for o in range(WORD_BITS)]
    state = original_address + original_words + [0] * (circuit.num_qubits - BASE)
    phase = 0
    measurements = 0
    for line in str(circuit).splitlines():
        op, *operands = line.split()
        if op in ("REGISTER", "APPEND_TO_REGISTER"):
            continue
        q = [int(word[1:]) for word in operands if word.startswith("q")]
        if op == "X":
            state[q[0]] ^= one
        elif op == "CX":
            a,b = q
            state[b] ^= state[a]
        elif op == "CCX":
            a,b,c = q
            assert state[a] >> SIZE == state[b] >> SIZE == 0
            state[c] ^= state[a] & state[b]
        elif op == "HMR":
            assert phase == 0 and operands[-1] == "b0"
            phase = state[q[0]]
            state[q[0]] = 0
            measurements += 1
        elif op == "CZ":
            assert operands[-2:] == ["if","b0"]
            phase ^= state[q[0]] & state[q[1]]
        else:
            raise ValueError(line)
    assert not phase and state[:11] == original_address and not any(state[BASE:])
    for o, initial in enumerate(original_words):
        j,b = divmod(o,8)
        assert state[11+o] == initial ^ bitpacked(delta[:,j]>>b&1), o
    return dict(valid_addresses=SIZE, arbitrary_target_bits=WORD_BITS,
                exact_hmr_branches=measurements)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--words", type=Path, required=True)
    p.add_argument("--source", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    p.add_argument("--verifiers", type=Path, required=True)
    p.add_argument("--order", type=Path)
    p.add_argument("--correction-low", type=int, nargs="+")
    p.add_argument("--batches", type=int, nargs="+", default=list(range(13)))
    args = p.parse_args()
    base = np.load(args.words, allow_pickle=False)
    assert base.shape == (1220,75) and base.dtype == np.uint8
    assert hashlib.sha256(base.tobytes()).hexdigest() == WORDS_SHA
    if args.order:
        order = json.loads(args.order.read_text())["order"]
        assert sorted(order) == list(range(75))
        base = base[:, order]
    words = np.pad(base, ((0,0),(0,3)))
    args.output.mkdir(parents=True, exist_ok=False)
    rows = []
    circuits = []
    for k in args.batches:
        delta = words[:,k*J:(k+1)*J].copy()
        if k:
            delta ^= words[:,(k-1)*J:k*J]
        circuit, detail = synthesize(delta, correction_low=tuple(args.correction_low) if args.correction_low else None)
        proof = prove(circuit, delta)
        path = args.output / f"angle_k_{k}.kmb"
        circuit.to_file(path, format="kmb")
        circuit = km.Circuit.from_file(path)
        prove(circuit, delta)
        row = dict(batch=k, qubits=circuit.num_qubits, detail=detail,
                   toffoli=circuit.operation_statistics().num_toffoli_like, proof=proof,
                   sha256=hashlib.sha256(path.read_bytes()).hexdigest())
        print(json.dumps({s:row[s] for s in ("batch","qubits","toffoli","proof")}),flush=True)
        rows.append(row)
        circuits.append(circuit)
    if args.batches == list(range(13)):
        sys.path.insert(0,str(args.verifiers))
        from dfthcsos.scoreinfra.circuits import recover_words_from_circuits
        recovered, layout, t = recover_words_from_circuits(
            circuits, num_vectors=SIZE, num_angles=75, shots_per_address=1, seed=202611152)
        assert np.array_equal(recovered,base) and layout.batch_size == J and layout.brot == 8
        assert t == 2*sum(r["toffoli"] for r in rows)
        if not args.order:
            shutil.copyfile(args.source,args.output/"submission.npz")
        extra = dict(native_angles=True, valid_addresses=SIZE, shots_per_address=1,
                     reordered=bool(args.order), native_toffoli=t, separate_numeric_verify=False)
    else:
        extra = dict(native_angles=False)
    result = dict(rows=rows, **extra, cap=128, max_loader_qubits=max(r["qubits"] for r in rows),
                  loader_toffoli_per_pass=sum(r["toffoli"] for r in rows))
    (args.output/"result.json").write_text(json.dumps(result,indent=2)+"\n")
    print(json.dumps({k:v for k,v in result.items() if k != "rows"}))


if __name__=="__main__":
    main()
