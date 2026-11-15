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


def repair(circuit, omitted):
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
    first = correct(corrected_a, fixed, omitted[0], temp)
    second = correct(corrected_b, fixed, omitted[1], temp)
    if first is None or second is None:
        return None
    clean = [gate for tag, q in physical.items() if tag != extra
             for gate in (f'HMR q{q} b0', f'CZ q{TAGS[tag][0]} q{TAGS[tag][1]} if b0')]
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
                          if (res := repair(orig, pair)) is not None]
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
            "batch": batch, "omitted_then_corrected_tags": pair, "added_CX_like_nonclifford": added,
            "overall_toffoli_like": candidate.operation_statistics().num_toffoli_like,
            "qubits": candidate.num_qubits, "proof": proof,
            "sha256": sha256(out.read_bytes()).hexdigest(),
        }
        proofs.append(row)
        print(row, flush=True)
    receipt = {"omission_correction_failures": failures, "batches": proofs,
               "scanned_TAGs": [18,26,42],
               "complete_proof": not failures,
               "proved_toffoli": sum(x["overall_toffoli_like"] for x in proofs)}
    (args.output/"repair_receipt.json").write_text(json.dumps(receipt,indent=2)+"\n")
    assert not failures


if __name__ == "__main__":
    main()
