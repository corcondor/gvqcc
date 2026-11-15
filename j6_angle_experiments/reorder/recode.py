#!/usr/bin/env python3
"""Find exact Givens sign gauges and compile input for a six-word schedule search."""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path

import numpy as np

WORD_SHA = "8caf7416de79102103757e3ab7ab4b6bbebfad9b1bf1ecd564c20eb948dbfcea"
NPZ_SHA = "42be33687903988f5d09e8c2f7fefc093896d841d4648fde32186f499794d347"


def reconstruct(words, edges):
    state = np.zeros((len(words), len(edges) + 1))
    state[:, 0] = 1
    angles = (np.pi / 128) * words
    for i, (p, c) in enumerate(edges):
        previous = state[:, p].copy()
        assert not state[:, c].any()
        state[:, p] = previous * np.cos(angles[:, i])
        state[:, c] = previous * np.sin(angles[:, i])
    return state


def gauge(words, edges, mode, final):
    last = {int(v): i for i, pair in enumerate(edges) for v in pair}
    signs = np.zeros((len(words), len(edges) + 1), dtype=np.int16)
    result = np.zeros_like(words)
    for i, (p, c) in enumerate(edges):
        best_rank = np.full(len(words), 1000, dtype=np.int16)
        chosen_p = np.zeros(len(words), dtype=np.int16)
        chosen_c = np.zeros(len(words), dtype=np.int16)
        for sign_p in ([final] if last[p] == i else [0, 1]):
            for sign_c in ([final] if last[c] == i else [0, 1]):
                reflection = sign_p ^ sign_c
                turns = signs[:, p] ^ sign_p
                candidate = ((1 - 2 * reflection) * words[:, i].astype(np.int16) + 128 * turns) & 255
                if mode == "minimum":
                    merit = candidate
                elif mode == "tag":
                    tag = ((candidate >> 7) ^ (candidate >> 6)) & 1
                    merit = 256 * tag + candidate
                elif mode == "near_original":
                    distance = candidate ^ words[:, i]
                    merit = ((candidate >> 6) & 1) * 128
                    merit += sum(((distance >> j) & 1) * 16 for j in range(6))
                    merit += (candidate >> 7)
                else:
                    raise ValueError(mode)
                use = merit < best_rank
                result[use, i] = candidate[use]
                best_rank[use] = merit[use]
                chosen_p[use] = sign_p
                chosen_c[use] = sign_c
        signs[:, p] = chosen_p
        signs[:, c] = chosen_c
    assert (signs == final).all()
    return result


def mobius_axis(array, axis):
    z = np.swapaxes(array.copy(), axis, 0)
    for bit in range((len(z) - 1).bit_length()):
        i = np.arange(len(z))
        targets = i[(i & (1 << bit)) != 0]
        z[targets] ^= z[targets ^ (1 << bit)]
    return np.swapaxes(z, axis, 0)


def matrices(words, high_has_selector, code):
    values = words.copy()
    if code == "tag":
        values ^= (values & 64) << 1
    coef = mobius_axis(mobius_axis(values.reshape(-1, 16, 75), 1), 0)
    cross = coef[0 if high_has_selector else 1:, 1:]
    cross = cross.transpose(2, 1, 0)
    return [
       [[int.from_bytes(np.packbits((row >> b) & 1, bitorder="little").tobytes(), "little")
         for row in cross[j]]
        for b in range(8)] for j in range(75)
    ] + [[[0] * 15 for _ in range(8)]]


def pair_rank(a, b):
    basis = {}
    for x, y in zip(a, b, strict=True):
        row = x ^ y
        while row:
            i = row.bit_length() - 1
            if i not in basis:
                basis[i] = row
                break
            row ^= basis[i]
    return len(basis)


def banks(words, code):
    return [
        matrices(words[:1024], False, code),
        matrices(words[1024:] ^ words[:208], True, code),
    ]


def entry_cost(parts, a, b):
    return sum((pair_rank(m[a][i], m[b][i]) + 1) // 2 for m in parts for i in range(8))


def schedule_pairs(permutation):
    padded = [75] * 6 + list(permutation) + [75] * 3
    return zip(padded, padded[6:])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--words", type=Path, required=True)
    parser.add_argument("--npz", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    raw = np.load(args.words, allow_pickle=False).astype(np.uint8)
    assert raw.shape == (1232, 75)
    assert hashlib.sha256(raw[:1220].tobytes()).hexdigest() == WORD_SHA
    assert hashlib.sha256(args.npz.read_bytes()).hexdigest() == NPZ_SHA
    with np.load(args.npz, allow_pickle=False) as z:
        edges = z["tree_edges"]
    reference = reconstruct(raw, edges)
    args.out.mkdir(parents=True, exist_ok=True)
    variants = [("fixed", raw, 0, 0.)]
    for mode in ("minimum", "tag", "near_original"):
        for final in (0, 1):
            table = gauge(raw, edges, mode, final)
            residual = float(np.max(np.abs(reconstruct(table, edges) - (1-2*final)*reference)))
            assert residual < 4e-15
            variants.append((f"{mode}_{final}", table, final, residual))
    results = []
    points = list(schedule_pairs(range(75)))
    for name, words, final, residual in variants:
        for code in ("ordinary", "tag"):
            parts = banks(words, code)
            score = sum(entry_cost(parts, a, b) for a, b in points)
            row = dict(name=name, code=code, final_sign=final, exact_reconstruction_error=residual,
                       changed_legal_words=int(np.count_nonzero(raw[:1220] != words[:1220])),
                       fixed_order_ccx_rank_sum=score,
                       near_quadrant_edges=int(np.sum(np.max(words[:1220], axis=0) <=64)))
            results.append(row)
            print(json.dumps(row),flush=True)
    best = min((r for r in results if r["name"]!="fixed"), key=lambda r:r["fixed_order_ccx_rank_sum"])
    fixed = min((r for r in results if r["name"]=="fixed"), key=lambda r:r["fixed_order_ccx_rank_sum"])
    for row in (fixed,best):
        name, words, final, _ = next(v for v in variants if v[0]==row["name"])
        parts = banks(words, row["code"])
        matrix = [[entry_cost(parts, i,j) for j in range(76)] for i in range(76)]
        np.save(args.out/f"{name}_words.npy",words,allow_pickle=False)
        # All incident-edge pairs keep their original order. Using consecutive
        # incident pairs gives the same dependency relation after closure.
        previous = {}
        predecessor = []
        for i, (p,c) in enumerate(edges):
            pred = sum(1 << j for j in {previous[v] for v in (p,c) if v in previous})
            predecessor.append(pred)
            previous[p] = previous[c] = i
        with (args.out / f"{name}_schedule.txt").open("w") as f:
            f.write("75\n")
            for mask in predecessor:
                f.write(f"{mask & ((1<<64)-1)} {mask>>64}\n")
            for costs in matrix:
                f.write(" ".join(map(str,costs))+"\n")
    (args.out/"gauge_recode_costs.json").write_text(json.dumps({"rows":results,"best_gauge":best,"best_fixed":fixed},indent=2)+"\n")

if __name__ == "__main__":
    main()
