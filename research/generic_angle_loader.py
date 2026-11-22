#!/usr/bin/env python3
"""Generic 7-bit ANGLE XOR loader -> concrete KMX (high-cost correctness baseline).

For a 1219/1246-row table and J=5, use 11 address qubits, 40 target
qubits (five 7-bit words plus their untouched tag wires), and 31 scratch
qubits. Precompute 16 low-address equality flags, stream a 7-bit high
equality predicate, and XOR the selected delta word into dirty targets.
All CCX are uncomputed. The gate set X/CX/CCX has no relative phases.

This is a genuine constructive reversible gate sequence, NOT an optimized
multi-output XAG or HMR compiler, and not a native KickMix PASS.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import math
from pathlib import Path
import numpy as np

ADDRESS = list(range(11))
TAGS = (18, 26, 34, 42, 50)
TARGETS = [[11 + 8*j + b for b in range(7)] for j in range(5)]
PAIR_A = list(range(51,55))
PAIR_B = list(range(55,59))
LOW_FLAGS = list(range(59,75))
HIGH_CHAIN = list(range(75,81))
ACTIVE = 81
NQ = 82


def delta_table(words: np.ndarray, slot: int) -> np.ndarray:
    if words.ndim != 2 or words.shape[1] != 75:
        raise ValueError("expected a 75-column angle table")
    if not 0 <= slot < 15 or not 1 <= len(words) <= 2048:
        raise ValueError("unsupported slot or address count")
    if np.any(words < 0) or np.any(words >= 128):
        raise ValueError("requires 7-bit angle words")
    out = np.array(words[:, 5*slot:5*slot+5], np.int64, copy=True)
    if slot:
        out ^= words[:, 5*slot-5:5*slot]
    return out


def compile_slot(words: np.ndarray, slot: int):
    delta = delta_table(words, slot)
    nrows = len(delta)
    lines = []
    stats = dict(X=0, CX=0, CCX=0, R=0)
    for q in ADDRESS:
        lines.append(f"APPEND_TO_REGISTER q{q} r0")
    lines.append('REGISTER r0 "selection"')
    for q in range(11,51):
        lines.append(f"APPEND_TO_REGISTER q{q} r1")
    lines.append('REGISTER r1 "target"')
    for q in range(51,NQ):
        lines.append(f"R q{q}")
        stats["R"] += 1
    def gate(op, *qubits):
        lines.append(op + " " + " ".join(f"q{q}" for q in qubits))
        stats[op] += 1

    def make_pair_flags(bits, targets, reverse=False):
        for pair in (reversed(range(4)) if reverse else range(4)):
            x0,x1 = bits
            if not (pair & 1):
                gate("X", x0)
            if not (pair & 2):
                gate("X", x1)
            gate("CCX", x0, x1, targets[pair])
            if not (pair & 2):
                gate("X", x1)
            if not (pair & 1):
                gate("X", x0)

    make_pair_flags((0,1), PAIR_A)
    make_pair_flags((2,3), PAIR_B)
    for low in range(16):
        gate("CCX", PAIR_A[low % 4], PAIR_B[low // 4], LOW_FLAGS[low])

    blocks = math.ceil(nrows / 16)
    nonzero = 0
    for high in range(blocks):
        inv = [4+i for i in range(7) if not (high>>i&1)]
        for q in inv:
            gate("X",q)
        gate("CCX",4,5,HIGH_CHAIN[0])
        for i in range(2,7):
            gate("CCX",HIGH_CHAIN[i-2],4+i,HIGH_CHAIN[i-1])
        for low in range(16):
            address=high*16+low
            if address >= nrows:
                break
            d = delta[address]
            outputs = [TARGETS[j][b] for j in range(5)
                       for b in range(7) if int(d[j])>>b&1]
            if not outputs:
                continue
            nonzero += 1
            gate("CCX",HIGH_CHAIN[5],LOW_FLAGS[low],ACTIVE)
            for target in outputs:
                gate("CX",ACTIVE,target)
            gate("CCX",HIGH_CHAIN[5],LOW_FLAGS[low],ACTIVE)
        for i in reversed(range(2,7)):
            gate("CCX",HIGH_CHAIN[i-2],4+i,HIGH_CHAIN[i-1])
        gate("CCX",4,5,HIGH_CHAIN[0])
        for q in reversed(inv):
            gate("X",q)
    for low in reversed(range(16)):
        gate("CCX",PAIR_A[low%4],PAIR_B[low//4],LOW_FLAGS[low])
    make_pair_flags((2,3), PAIR_B, reverse=True)
    make_pair_flags((0,1), PAIR_A, reverse=True)
    stats.update(active_rows=nonzero, high_blocks=blocks, num_qubits=NQ,
                 slot=slot, addresses=nrows, phase_ops=0)
    return lines, stats


def bitparallel_proof(lines: list[str], delta: np.ndarray, seed: int = 0):
    """Exact all-address classical XOR proof with random dirty target bits.

    Every target is absent from all control operands, hence the XOR
    identity extends to arbitrary target bit patterns. No phases occur in
    X/CX/CCX. This is NOT the official native quantum verifier.
    """
    n = len(delta)
    all_bits = (1<<n)-1
    initial = [0]*NQ
    for q in ADDRESS:
        initial[q] = sum(((a>>q)&1)<<a for a in range(n))
    rng = np.random.default_rng(seed)
    for q in range(11,51):
        initial[q] = int.from_bytes(rng.bytes((n+7)//8),"little") & all_bits
    state = initial.copy()
    gates = []
    for line in lines:
        terms = line.split()
        if terms[0] in ("APPEND_TO_REGISTER","REGISTER"):
            continue
        op=terms[0]
        qs=[int(t[1:]) for t in terms[1:]]
        if op=="R":
            if state[qs[0]]:raise AssertionError(("nonzero scratch on reset",qs))
            continue
        if op in ("CX","CCX") and any(11<=q<=50 for q in qs[:-1]):
            raise AssertionError(("dirty target used as control",line))
        gates.append((op,qs))
    for op,qs in gates:
        if op=="X":state[qs[0]] ^= all_bits
        elif op=="CX":state[qs[1]] ^= state[qs[0]]
        elif op=="CCX":state[qs[2]] ^= state[qs[0]] & state[qs[1]]
        else:raise ValueError(op)
    for q in ADDRESS:
        if state[q]!=initial[q]:raise AssertionError(("changed address",q))
    for q in TAGS:
        if state[q]!=initial[q]:raise AssertionError(("changed tag",q))
    for j,qubits in enumerate(TARGETS):
        for bit,q in enumerate(qubits):
            expected=sum(((int(delta[a,j])>>bit)&1)<<a for a in range(n))
            if state[q]!=(initial[q]^expected):
                raise AssertionError(("wrong XOR",j,bit,q))
    for q in range(51,NQ):
        if state[q]:raise AssertionError(("dirty scratch",q))
    return dict(exact_all_addresses=True, scratch_clean=True,
                tags_unchanged=True, arbitrary_dirty_XOR=True,
                relative_phase_zero_by_gate_set=True, addresses=n)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("npz",type=Path)
    parser.add_argument("--out",required=True,type=Path)
    parser.add_argument("--slots",default="all")
    args=parser.parse_args()
    args.out.mkdir(parents=True,exist_ok=True)
    with np.load(args.npz,allow_pickle=False) as z:
        words=np.array(z["angle_words"],np.int64)
    slots=list(range(15)) if args.slots=="all" else [int(x) for x in args.slots.split(",")]
    stats=[]
    for slot in slots:
        lines,counts=compile_slot(words,slot)
        counts.update(bitparallel_proof(lines,delta_table(words,slot)))
        path=args.out/f"angle_k_{slot}.kmx"
        path.write_text("\n".join(lines)+"\n",encoding="utf-8")
        counts["kmx_sha256"]=hashlib.sha256(path.read_bytes()).hexdigest()
        stats.append(counts)
        print(json.dumps(counts),flush=True)
    receipt=dict(
        npz_sha256=hashlib.sha256(args.npz.read_bytes()).hexdigest(),
        scope="CONSTRUCTIVE_KMX_EXACT_BITPARALLEL_NOT_KICKMIX_NATIVE",
        total_ccx_per_pass=sum(s["CCX"] for s in stats),
        max_qubits=NQ, slots=stats)
    (args.out/"receipt.json").write_text(json.dumps(receipt,indent=2)+"\n")
    print("TOTAL_CCX_PER_PASS",receipt["total_ccx_per_pass"],flush=True)


if __name__=="__main__":
    main()
