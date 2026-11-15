#!/usr/bin/env python3
"""Turn the borrowed ANGLE word tags into real clean inputs at width 128."""
import argparse
from hashlib import sha256
from itertools import combinations
import json
from pathlib import Path
from shutil import copyfile

import kickmix as km
import numpy as np


TAGS = {18: (0, 1), 26: (0, 2), 34: (1, 2), 42: (0, 3), 50: (1, 3)}
SIZE = 1220
ONES = (1 << SIZE) - 1
ADDR = [sum(1 << a for a in range(SIZE) if a & (1 << q)) for q in range(11)]
WORD = [ONES << (q * SIZE) for q in range(1, 41)]
INPUT = ADDR + WORD + [0] * 82
EXPECTED_WORDS_SHA = "8caf7416de79102103757e3ab7ab4b6bbebfad9b1bf1ecd564c20eb948dbfcea"


def step(lines, state):
    state = list(state)
    phase = 0
    for line in lines:
        op, *parts = line.split()
        if op in {"REGISTER", "APPEND_TO_REGISTER"}:
            continue
        if phase:
            assert op == "CZ"
        qs = [int(s[1:]) for s in parts if s.startswith("q")]
        if op == "X":
            state[qs[0]] ^= ONES
        elif op == "CX":
            a, b = qs
            state[b] ^= state[a]
        elif op == "CCX":
            a, b, c = qs
            assert not (state[a] >> SIZE or state[b] >> SIZE)
            state[c] ^= state[a] & state[b]
        elif op == "R":
            assert not state[qs[0]]
        elif op == "HMR":
            assert not phase and parts[-1] == "b0"
            phase = state[qs[0]]
            assert not phase >> SIZE
            state[qs[0]] = 0
        elif op == "CZ":
            a, b = qs
            assert parts[-2:] == ["if", "b0"] and not (state[a] >> SIZE or state[b] >> SIZE)
            assert phase == state[a] & state[b]
            phase = 0
        else:
            raise ValueError(line)
    assert not phase
    return state


def parse_tag_line(line, mapped, omitted):
    parts = line.split()
    control_only = parts[0] == "CX" and int(parts[1][1:]) in omitted
    for i, token in enumerate(parts):
        if token.startswith("q") and int(token[1:]) in omitted:
            assert control_only and i == 1, (line, omitted)
        if token.startswith("q") and int(token[1:]) in mapped:
            parts[i] = "q" + str(mapped[int(token[1:])])
    return " ".join(parts)


def beta_basis(residuals, care):
    """Factor function/target incidence, with the constant-on-care row for free."""
    basis = {care.bit_length() - 1: (care, 1)}
    functions = [care]
    directions = [0]
    for output, fn in enumerate(residuals):
        fn &= care
        mask = 0
        while fn:
            pivot = fn.bit_length() - 1
            if pivot not in basis:
                mask ^= 1 << len(functions)
                basis[pivot] = (fn, 1 << len(functions))
                functions.append(fn)
                directions.append(0)
                break
            row, coeff = basis[pivot]
            fn ^= row
            mask ^= coeff
        while mask:
            low = mask & -mask
            directions[low.bit_length()-1] ^= 1 << output
            mask ^= low
    return zip(functions, directions, strict=True)


def affine_basis(state, care, excluded):
    basis = {}
    for q in [-1, *range(11), *range(51, 128)]:
        if q == excluded:
            continue
        assert not (state[q] >> SIZE) if q >= 0 else True
        row = care if q == -1 else state[q] & care
        mask = 1 << (q+1)
        while row:
            pivot = row.bit_length()-1
            if pivot not in basis:
                basis[pivot] = (row, mask)
                break
            head, coeff = basis[pivot]
            row ^= head
            mask ^= coeff
    return basis


def affine_expr(basis, fn):
    comb = 0
    while fn:
        pivot = fn.bit_length() - 1
        if pivot not in basis:
            return
        row, mask = basis[pivot]
        fn ^= row
        comb ^= mask
    return [q-1 for q in range(129) if (comb >> q) & 1]


def source_product_rewrite(omega, recipe, direction):
    pivot = next(q for q in recipe if q >= 0)
    load = [f'X q{pivot}' if q == -1 else f'CX q{q} q{pivot}'
            for q in recipe if q != pivot]
    destinations = [q+11 for q in range(40) if (direction >> q) & 1]
    t = destinations[0]
    fan = [f'CX q{t} q{q}' for q in destinations[1:]]
    return [*load, *fan, f'CCX q{omega} q{pivot} q{t}', *fan, *load]


def correct(residuals, state, tag, temp):
    a, b = TAGS[tag]
    assert state[a] == ADDR[a] and state[b] == ADDR[b]
    care = ADDR[a] & ADDR[b]
    basis = affine_basis(state, care, temp)
    lines = [f'R q{temp}', f'CCX q{a} q{b} q{temp}']
    ccx = 1
    for fn, direction in beta_basis(residuals, care):
        if not direction:
            continue
        if fn == care:
            lines.extend(f'CX q{temp} q{q+11}' for q in range(40) if (direction >> q) & 1)
            continue
        recipe = affine_expr(basis, fn)
        if recipe is None:
            return None
        assert any(x >= 0 for x in recipe)
        lines.extend(source_product_rewrite(temp, recipe, direction))
        ccx += 1
    return [*lines, f'HMR q{temp} b0', f'CZ q{a} q{b} if b0'], ccx


HIGH_MASK = [sum(1 << a for a in range(SIZE) if a >> 4 == h)
             for h in range((SIZE + 15) // 16)]
LOW_MASK = [sum(1 << a for a in range(SIZE) if a % 16 == l)
            for l in range(16)]


def high_low_parts(value):
    high = 0
    for h, region in enumerate(HIGH_MASK):
        if ((value >> (h * 16)) ^ value) & 1:
            high ^= region
    low = 0
    for l, region in enumerate(LOW_MASK):
        if (value ^ high) >> l & 1:
            low ^= region
    assert high ^ low == value
    return high, low


def projection(rows):
    basis = {}
    for q, row in rows:
        combo = 1 << (q + 1)
        while row:
            pivot = row.bit_length() - 1
            if pivot not in basis:
                basis[pivot] = (row, combo)
                break
            keep, previous = basis[pivot]
            row ^= keep
            combo ^= previous
    return basis


def evaluate_low(outputs):
    table = [sum(((value >> a) & 1) << o for o, value in enumerate(outputs))
             for a in range(16)]
    for i in (1, 2, 4, 8):
        for state in range(16):
            if state & i:
                table[state] ^= table[state ^ i]
    lines = []
    orders = []
    monomials = {1 << i: i for i in range(4)}
    def materialize(mask):
        if mask in monomials:
            return monomials[mask]
        lowest = mask & -mask
        source_a = monomials[lowest]
        source_b = materialize(mask ^ lowest)
        target = 51 + len(orders)
        orders.append((source_a, source_b, target))
        monomials[mask] = target
        lines.extend((f'R q{target}', f'CCX q{source_a} q{source_b} q{target}'))
        return target
    for term, direction in enumerate(table):
        if direction:
            pivot = materialize(term) if term else None
            lines.extend((f'CX q{pivot} q{o+11}' if term else f'X q{o+11}')
                         for o in range(40) if direction >> o & 1)
    for a,b,t in reversed(orders):
        lines.extend((f'HMR q{t} b0', f'CZ q{a} q{b} if b0'))
    return lines, len(orders)


def load_affine(wire, expression):
    return [f'CX q{src} q{wire}' if src >= 0 else f'X q{wire}' for src in expression]


def paired_corrections(first, second, base, omitted, spare, tail):
    early, late = tail[:12], tail[12:]
    assert all(early[i].startswith(("HMR ", "CZ ")) for i in range(12))
    assert {int(line.split()[1][1:]) for line in early[::2]} == set(range(119,125))
    if any(f"q{wire}" in line.split() for wire in (119, 120) for line in late):
        return None
    state = step(early, base)

    tag_functions = [ADDR[TAGS[t][0]] & ADDR[TAGS[t][1]] for t in omitted]
    hi, lo = zip(*(high_low_parts(fn) for fn in first))
    hj, lp = zip(*(high_low_parts(fn) for fn in second))
    # High-high and low-low entries are collected for the affine compensation.
    to_high = [0] * 40
    low_a, low_b = tag_functions
    to_low = [(low_a & p) ^ (low_b & q) for p,q in zip(lo, lp, strict=True)]
    span_high = [(q, state[q]) for q in (*range(4,11), *range(51,119))]
    assert all(not high_low_parts(row)[1] for _,row in span_high)
    high_basis = projection([(-1, ONES), *span_high])
    def high_expr(fn):
        return affine_expr(high_basis,fn)

    lanes = [(TAGS[tag][0], TAGS[tag][1], lane)
             for tag,lane in zip(omitted, (119,120), strict=True)]
    lines = list(early)
    for a,b,w in lanes:
        lines.extend((f'R q{w}', f'CCX q{a} q{b} q{w}'))
    ccx = 2

    missing = [h & k for h,k in zip(hi,hj,strict=True)
               if h and k and h != k and high_expr(h&k) is None]
    fill = None
    if missing:
        for (a,left), (b,right) in combinations(span_high,2):
            new = left & right
            if high_expr(new) is not None:
                continue
            trial = projection([(-1, ONES), *span_high, (spare,new)])
            if all(affine_expr(trial,fn) is not None for fn in missing):
                fill = a,b,spare
                high_basis = trial
                break
        if fill is None:
            return None
        a,b,t = fill
        lines.extend((f'R q{t}', f'CCX q{a} q{b} q{t}'))
        ccx += 1

    for o,(h,k) in enumerate(zip(hi,hj,strict=True),11):
        if not h and not k:
            continue
        if h and k and h != k:
            left = high_expr(k)
            right = high_expr(h)
            if left is None or right is None:
                return None
            a = load_affine(119,left)
            b = load_affine(120,right)
            lines.extend((*a,*b,f'CCX q119 q120 q{o}',*b,*a))
            to_high[o-11] ^= h & k
            to_low[o-11] ^= low_a & low_b
        else:
            expr = high_expr(h or k)
            if expr is None or not expr:
                return None
            high_wire = next(q for q in expr if q >= 0)
            change = load_affine(high_wire,[q for q in expr if q != high_wire])
            if h and k:
                change = ['CX q119 q120', *change]
            tag = 119 if h and not k else 120
            lines.extend((*change, f'CCX q{tag} q{high_wire} q{o}', *reversed(change)))
        ccx += 1
    for o,val in enumerate(to_high,11):
        exp = high_expr(val)
        assert exp is not None
        lines.extend(load_affine(o,exp))
    for a,b,t in [*lanes,*([fill] if fill is not None else [])]:
        lines.extend((f'HMR q{t} b0', f'CZ q{a} q{b} if b0'))

    # Restore the two original CCX/CZ-linked kept tags separately in the
    # existing suffix, then apply the low-only corrections with workspace free.
    low_code, low_ccx = evaluate_low(to_low)
    return lines, late, low_code, ccx + low_ccx

def repair(circuit, omitted, use_pairing=False):
    orig = str(circuit).splitlines()
    boundary = next(i for i, line in enumerate(orig) if line.startswith("HMR"))
    prefix, raw_core, raw_tail, suffix = orig[:62], orig[62:boundary], orig[boundary:-5], orig[-5:]
    kept = sorted(set(TAGS) - set(omitted))
    extra = next(tag for tag in kept if tag not in (34, 50))
    physical = {tag: q for q, tag in enumerate(kept, 125)}
    temp = physical[extra]
    a, b = TAGS[extra]
    virtual = {**physical, omitted[0]: 128, omitted[1]: 129}
    try:
        ghosts = [parse_tag_line(line, virtual, omitted) for line in raw_core]
        tail = [parse_tag_line(line, physical, omitted) for line in raw_tail]
    except AssertionError:
        return None
    if any(f'q{temp}' in line.split() for line in tail):
        return None
    prep = [op for t, q in physical.items()
            for op in (f'R q{q}', f'CCX q{TAGS[t][0]} q{TAGS[t][1]} q{q}')]
    core = [line for line in ghosts if not line.startswith(('CX q128 ', 'CX q129 '))]
    prefix = prefix + prep
    entry = step(prefix, INPUT)
    true_a = ADDR[TAGS[omitted[0]][0]] & ADDR[TAGS[omitted[0]][1]]
    def experiment(value_a, value_b):
        forced_entry = list(entry)
        forced_entry[128:130] = [value_a,value_b]
        return step(ghosts, forced_entry)
    base = experiment(0, 0)
    test_a = experiment(ONES, 0)
    true_a_only = experiment(true_a, 0)
    test_b = experiment(true_a, ONES)
    assert base[:128] == step(core, entry)[:128]
    finish_extra = [f'HMR q{temp} b0', f'CZ q{a} q{b} if b0']
    fixed = step(finish_extra, base)
    corrected_a = [x ^ y for x, y in zip(test_a[11:51], base[11:51], strict=True)]
    corrected_b = [x ^ y for x, y in zip(test_b[11:51], true_a_only[11:51], strict=True)]
    assert not any(f >> SIZE for f in corrected_a + corrected_b)
    clean = [gate for tag, q in physical.items() if tag != extra
             for gate in (f'HMR q{q} b0', f'CZ q{TAGS[tag][0]} q{TAGS[tag][1]} if b0')]
    if use_pairing:
        paired = paired_corrections(corrected_a, corrected_b, fixed, omitted, temp, tail)
        if paired is not None:
            simultaneous, late, low_only, count = paired
            sequence = prefix + core + finish_extra + simultaneous + late + clean + low_only + suffix
            result = km.Circuit("\n".join(sequence) + "\n")
            assert result.num_qubits <= 128
            return result, 3+count

    first = correct(corrected_a, fixed, omitted[0], temp)
    second = correct(corrected_b, fixed, omitted[1], temp)
    if first is None or second is None:
        return None
    result = km.Circuit("\n".join(prefix + core + finish_extra + first[0] + second[0] + tail + clean + suffix) + "\n")
    assert result.num_qubits <= 128
    return result, 3 + first[1] + second[1]



def prove(path, output_delta):
    circ = km.Circuit.from_file(path)
    values = step(str(circ).splitlines(), INPUT)
    assert values[:11] == ADDR and not any(values[51:])
    for o, value in enumerate(values[11:51]):
        bit = np.flatnonzero((output_delta[:, o//8] >> (o % 8)) & 1)
        expected = sum(1 << int(a) for a in bit)
        assert value == (WORD[o] ^ expected), (path.name, o)
    return {"addresses": SIZE, "arbitrary_word_bits": 40, "all_measurement_branches": True}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--references", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--pair-correction", action="store_true")
    args = parser.parse_args()
    with np.load(args.references, allow_pickle=False) as data:
        words = data["angle_words"].astype(np.uint8)
    assert sha256(words.tobytes()).hexdigest() == EXPECTED_WORDS_SHA
    args.output.mkdir(parents=True, exist_ok=False)
    copyfile(args.source/"submission.npz", args.output/"submission.npz")
    proofs = []
    failures = []
    for batch in range(15):
        name = f"angle_k_{batch}.kmb"
        source, out = args.source / name, args.output / name
        if not batch:
            copyfile(source, out)
            added, pair = 0, []
            candidate = km.Circuit.from_file(out)
        else:
            orig = km.Circuit.from_file(source)
            candidates = [(res[1], pair, res[0])
                          for pair in combinations((18,26,42), 2)
                          if (res := repair(orig, pair, args.pair_correction)) is not None]
            if not candidates:
                failures.append(batch)
                print(batch, "no omitted-tag corrections", flush=True)
                continue
            added, pair, candidate = min(candidates, key=lambda x:x[0])
            assert candidate.operation_statistics().num_toffoli_like == orig.operation_statistics().num_toffoli_like + added
            candidate.to_file(out, format="kmb")
        delta = words[:,5*batch:5*(batch+1)].copy()
        if batch:
            delta ^= words[:,5*(batch-1):5*batch]
        proof = prove(out, delta)
        row = {
            "batch": batch, "omitted_then_corrected_tags": pair, "added_CCX": added,
            "overall_toffoli_like": candidate.operation_statistics().num_toffoli_like,
            "qubits": candidate.num_qubits, "proof": proof,
            "sha256": sha256(out.read_bytes()).hexdigest(),
        }
        proofs.append(row)
        print(row, flush=True)
    receipt = {"omission_correction_failures": failures, "batches": proofs,
               "scanned_tags": [18,26,42], "paired_correction": args.pair_correction,
               "complete_proof": not failures,
               "proved_toffoli": sum(x["overall_toffoli_like"] for x in proofs)}
    (args.output/"repair_receipt.json").write_text(json.dumps(receipt,indent=2)+"\n")
    assert not failures


if __name__ == "__main__":
    main()
