#!/usr/bin/env python3
"""Build and verify a six-word family for a commuting-edge permutation."""
import argparse
import hashlib
import json
import sys
from pathlib import Path

import kickmix as km
import numpy as np

from recode import NPZ_SHA, WORD_SHA, reconstruct


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--order", type=Path, required=True)
    p.add_argument("--words", type=Path, required=True)
    p.add_argument("--original-words", type=Path, required=True)
    p.add_argument("--npz", type=Path, required=True)
    p.add_argument("--compiler", type=Path, required=True)
    p.add_argument("--verifiers", type=Path, required=True)
    p.add_argument("--out", type=Path, required=True)
    p.add_argument("--correction-low", type=int, nargs="+", default=[6,7])
    args = p.parse_args()
    sys.path.insert(0,str(args.compiler))
    sys.path.insert(0,str(args.verifiers))
    from build_split_loader import prove, synthesize
    from dfthcsos.scoreinfra.circuits import recover_words_from_circuits

    assert hashlib.sha256(args.npz.read_bytes()).hexdigest() == NPZ_SHA
    base = np.load(args.original_words,allow_pickle=False)[:1220].astype(np.uint8)
    assert hashlib.sha256(base.tobytes()).hexdigest() == WORD_SHA
    with np.load(args.npz,allow_pickle=False) as z:
        params = dict(z)
    edges = params["tree_edges"]
    order = json.loads(args.order.read_text())["permutation"]
    assert sorted(order) == list(range(75))
    working = list(range(75))
    swaps = 0
    for i,next_edge in enumerate(order):
        at = working.index(next_edge)
        while at > i:
            assert not set(edges[working[at-1]]) & set(edges[working[at]])
            working[at-1], working[at] = working[at], working[at-1]
            swaps += 1
            at -= 1
    seen = {0}
    for par,child in edges[order]:
        assert par in seen and child not in seen
        seen.add(child)
    words = np.load(args.words,allow_pickle=False)[:1220].astype(np.uint8)[:,order]
    old, new = reconstruct(base,edges), reconstruct(words,edges[order])
    difference = np.minimum(np.max(np.abs(old-new),axis=1),np.max(np.abs(old+new),axis=1))
    assert np.max(difference) < 4e-15
    padded = np.pad(words,((0,0),(0,3)))
    args.out.mkdir(parents=True)
    circuits = []
    rows = []
    for k in range(13):
        delta = padded[:,6*k:6*k+6].copy()
        if k:
            delta ^= padded[:,6*k-6:6*k]
        circuit, layout = synthesize(delta, correction_low=tuple(args.correction_low))
        path = args.out/f"angle_k_{k}.kmb"
        circuit.to_file(path,format="kmb")
        circuit = km.Circuit.from_file(path)
        row = dict(batch=k, ccx=circuit.operation_statistics().num_toffoli_like,
                   qubits=circuit.num_qubits, proof=prove(circuit,delta),
                   sha256=hashlib.sha256(path.read_bytes()).hexdigest(), stage=layout)
        rows.append(row)
        circuits.append(circuit)
    recovered, layout, t = recover_words_from_circuits(
        circuits, num_vectors=1220, num_angles=75, shots_per_address=1, seed=202611152)
    assert layout.batch_size == 6 and layout.brot == 8
    assert np.array_equal(recovered,words)
    loader_cost = sum(row["ccx"] for row in rows)
    assert t == 2*loader_cost
    params["tree_edges"] = edges[order]
    params["angle_words"] = words
    np.savez_compressed(args.out/"submission.npz",**params)
    data = dict(permutation=order, disjoint_adjacent_swaps=swaps,
                max_signed_vector_error=float(np.max(difference)),
                max_loader_qubits=max(row["qubits"] for row in rows),
                loader_toffoli_per_pass=loader_cost, native_toffoli=t,
                forward_reverse="PASS on all 1220 legal addresses, 1 shot per address",
                score11_npz_sha256=NPZ_SHA,
                candidate_npz_sha256=hashlib.sha256((args.out/"submission.npz").read_bytes()).hexdigest(),
                improves=loader_cost<=3894, rows=rows)
    (args.out/"result.json").write_text(json.dumps(data,indent=2)+"\n")
    print(json.dumps({k:v for k,v in data.items() if k!="rows"}),flush=True)


if __name__=="__main__":
    main()
