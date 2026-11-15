"""Certified dependency order bottlenecks in the actual invsqrt circuit."""

from argparse import ArgumentParser
from collections import Counter
from dataclasses import dataclass
from hashlib import sha256
import heapq
import json
from pathlib import Path
import random
import re

import kickmix as km
import numpy as np

PIN = "684106f101730ca193627229920a0501bef9ea10ccfb34aa453fcf63edadb50a"
DOMAIN = 3133452
INPUTS = 22
QUBITS = 46
QUANTUM = re.compile(r"\bq(\d+)\b")
CLASSICAL = re.compile(r"\bb(\d+)\b")


@dataclass(frozen=True)
class Gate:
    op: str
    wires: tuple
    bits: tuple

    @classmethod
    def parse(cls, line):
        return cls(line.split()[0], tuple(map(int, QUANTUM.findall(line))),
                   tuple(QUBITS + int(x) for x in CLASSICAL.findall(line)))

    def dependencies(self):
        read = set(self.wires)
        written = set()
        if self.op in {"X", "CX", "CCX", "R", "HMR"}:
            target = self.wires[-1]
            read.remove(target)
            written.add(target)
        if self.op in {"SWAP", "CSWAP"}:
            written.update(self.wires[-2:])
        if self.op in {"HMR", "BIT_INVERT", "BIT_STORE0"}:
            destination, *guard = self.bits
            written.add(destination)
            read.update(guard)
        else:
            read.update(self.bits)
        return read, written


@dataclass(frozen=True)
class Scope:
    op: str
    read: frozenset
    written: frozenset

    def dependencies(self):
        return set(self.read), set(self.written)


def collapse_scopes(gates, life):
    """Keep scope bodies intact and let independent external gates cross them."""
    atoms, source_groups = [], []
    origin = []
    i = 0
    while i < len(gates):
        start = i
        origin.append(start)
        gate = gates[i]
        if gate.op != "PUSH_CONDITION":
            atoms.append(gate)
            source_groups.append(len(atoms)-1)
            i += 1
            continue
        depth = 0
        reads, writes = set(), set()
        while True:
            gate = gates[i]
            depth += int(gate.op == "PUSH_CONDITION") - int(gate.op == "POP_CONDITION")
            read, written = gate.dependencies()
            reads.update(read)
            writes.update(written)
            i += 1
            if not depth:
                break
        # Complete POP joins were checked independently on all legal values.
        # A whole scope changes only phases and classical records externally.
        reads.update(q for q in writes if q < QUBITS)
        atoms.append(Scope("SCOPE", frozenset(reads), frozenset(q for q in writes if q >= QUBITS)))
        source_groups.extend([len(atoms)-1]*(i-start))

    per_wire = {}
    for q,birth,death in life:
        a,b = source_groups[birth],source_groups[death]
        if a != b:
            per_wire.setdefault(q,[]).append((a,b))
    fused=[]
    for q, spans in per_wire.items():
        for a,b in sorted(spans):
            if fused and fused[-1][0] == q and fused[-1][2] == a:
                _,first,_ = fused[-1]
                fused[-1] = q,first,b
            else:
                fused.append((q,a,b))
    return atoms, fused, origin


def dependency_dag(gates):
    """Order writers and dependent readers. Gate reads can share a predecessor."""
    writers, readers = {}, {}
    pred, successors = [], [[] for _ in gates]
    fence = None
    untouched = []
    for index, gate in enumerate(gates):
        read, write = gate.dependencies()
        parents = set() if fence is None else {fence}
        parents.update(writers[q] for q in read | write if q in writers)
        for q in write:
            parents.update(readers.get(q, ()))
        if gate.op in {"PUSH_CONDITION", "POP_CONDITION"}:
            parents.update(writers.values())
            for uses in readers.values():
                parents.update(uses)
            parents.update(untouched)
            writers.clear()
            readers.clear()
            untouched.clear()
            fence = index
        elif not read and not write:
            untouched.append(index)
        for q in write:
            writers[q] = index
            readers.pop(q, None)
        for q in read - write:
            readers.setdefault(q, []).append(index)
        pred.append(sorted(parents))
        for source in parents:
            successors[source].append(index)
    return pred, successors


def packed_lifetimes(gates, observe=None):
    """Use all legal x to track where each ancillary Boolean value is nonzero."""
    xs = np.arange(1, DOMAIN + 1, dtype=np.uint32)
    state = [int.from_bytes(np.packbits((xs >> q) & 1, bitorder="little"), "little")
             for q in range(INPUTS)] + [0] * (QUBITS - INPUTS)
    domain = (1 << DOMAIN) - 1
    opened = {}
    life = []
    frames = []
    maximum = 0
    count_peak = 0
    for index, gate in enumerate(gates):
        if observe is not None:
            observe(index,state,domain)
        q = gate.wires
        op = gate.op
        read, write = gate.dependencies()
        targets = [w for w in write if INPUTS <= w < QUBITS]
        before = {w: bool(state[w]) for w in targets}
        if op == "PUSH_CONDITION":
            frames.append(state[:])
        elif op == "POP_CONDITION":
            assert frames.pop() == state
        elif op == "X":
            assert not gate.bits
            state[q[0]] ^= domain
        elif op == "CX":
            assert not gate.bits
            state[q[1]] ^= state[q[0]]
        elif op == "CCX":
            assert not gate.bits
            state[q[2]] ^= state[q[0]] & state[q[1]]
        elif op == "SWAP":
            assert not gate.bits
            a,b = q
            state[a],state[b] = state[b],state[a]
        elif op == "CSWAP":
            assert not gate.bits
            c,a,b = q
            difference = state[c] & (state[a] ^ state[b])
            state[a] ^= difference
            state[b] ^= difference
        elif op == "HMR":
            assert len(gate.bits) == 1
            state[q[0]] = 0
        elif op == "R":
            assert not state[q[0]]
        else:
            assert op in {"Z", "CZ", "CCZ", "NEG", "Z_POW", "BIT_INVERT", "BIT_STORE0"}
        for w in targets:
            if not before[w] and state[w]:
                assert w not in opened
                opened[w] = index
            elif before[w] and not state[w]:
                life.append((w, opened.pop(w), index))
        width = INPUTS + len(opened)
        maximum = max(maximum,width)
        count_peak += width == QUBITS
    assert not frames and not opened
    return life, maximum, count_peak


def closures(edges, initial, reverse=False):
    n = len(edges)
    labels = [0]*n
    visit = range(n-1,-1,-1) if reverse else range(n)
    for index in visit:
        mask = initial[index]
        for adjacent in edges[index]:
            mask |= labels[adjacent]
        labels[index] = mask
    return labels


def forced_cuts(life, predecessors, successors):
    starts = [0]*len(predecessors)
    ends = [0]*len(predecessors)
    for i, (_, birth, death) in enumerate(life):
        starts[birth] |= 1 << i
        ends[death] |= 1 << i
    ancestors = closures(predecessors, starts)
    descendants = closures(successors, ends, reverse=True)
    best = -1
    best_anchor = None
    best_intervals = []
    n = len(ancestors)
    must_have_all = 0
    covered = Counter()
    for anchor in range(n):
        # Only a single interval of any logical scratch bit can cover a cut.
        # Use the cut after the anchor. Intervals ending at that gate are gone.
        both = ancestors[anchor] & (descendants[anchor] ^ ends[anchor])
        width = INPUTS + both.bit_count()
        if width > best:
            best = width
            best_anchor = anchor
            best_intervals = [interval for i,interval in enumerate(life)
                              if both >> i & 1]
            assert len({q for q,_,_ in best_intervals}) == both.bit_count()
        covered[width]+=1
        must_have_all += width == QUBITS
    return dict(max_forced=best, first_gate_index=best_anchor, full_width_anchors=must_have_all,
                must_be_live=best_intervals, histogram=dict(covered))


def run_order(predecessors, successors, life, seed):
    rng = random.Random(seed)
    opened = Counter(birth for _,birth,_ in life)
    closed = Counter(death for _,_,death in life)
    outstanding=[len(x) for x in predecessors]
    n = len(predecessors)
    depth = [0]*n
    for i in range(n-1,-1,-1):
        depth[i] = 1 + max((depth[j] for j in successors[i]), default=0)
    order=[]
    ready=[]
    def push(i):
        priority = (opened[i] - closed[i], -depth[i], rng.random(), i)
        heapq.heappush(ready, priority)
    for i in range(n):
        if not outstanding[i]:
            push(i)
    width = INPUTS
    maximum = INPUTS
    while ready:
        _,_,_,i=heapq.heappop(ready)
        order.append(i)
        width += opened[i] - closed[i]
        maximum = max(maximum,width)
        for j in successors[i]:
            outstanding[j] -= 1
            if outstanding[j] == 0:
                push(j)
    assert len(order) == n and width == INPUTS
    return maximum,order


def positive_control():
    gates = [Gate.parse(s) for s in ("X q22","X q23","X q22","X q23")]
    old_width = INPUTS+2
    pred, successors = dependency_dag(gates)
    life = [(22,0,2),(23,1,3)]
    result, order = run_order(pred,successors,life,seed=0)
    assert result == INPUTS+1
    assert all(order.index(i) < order.index(j) for j, deps in enumerate(pred) for i in deps)
    assert forced_cuts(life,pred,successors)["max_forced"] == INPUTS+1
    return dict(input_width=old_width,reordered_width=result,order=order)


def main():
    cli=ArgumentParser(description=__doc__)
    cli.add_argument("source",type=Path)
    cli.add_argument("report",type=Path)
    cli.add_argument("--expected-sha",default=PIN)
    a=cli.parse_args()
    assert sha256(a.source.read_bytes()).hexdigest()==a.expected_sha
    lines=str(km.Circuit.from_file(a.source)).splitlines()
    lines=[s for s in lines if s.split()[0] not in {"APPEND_TO_REGISTER","REGISTER"}]
    gates=[Gate.parse(s) for s in lines]
    life,peak,points=packed_lifetimes(gates)
    predecessors,successors=dependency_dag(gates)
    forced=forced_cuts(life,predecessors,successors)
    anchor=forced["first_gate_index"]
    forced["first_gate"]=None if anchor is None else lines[anchor]
    print(json.dumps({"life":len(life),"peak":peak, "forced":forced},ensure_ascii=False),flush=True)
    trials=[run_order(predecessors,successors,life,i)[0] for i in range(12)]
    atoms, group_life, origin = collapse_scopes(gates, life)
    atom_pred, atom_successors = dependency_dag(atoms)
    atom_cuts = forced_cuts(group_life, atom_pred, atom_successors)
    atom_anchor = atom_cuts["first_gate_index"]
    atom_cuts["original_gate_index"] = origin[atom_anchor]
    atom_cuts["first_gate"] = lines[origin[atom_anchor]]
    grouped_trials = [run_order(atom_pred,atom_successors,group_life,i)[0] for i in range(12)]
    data=dict(source_sha256=a.expected_sha, legal_inputs=DOMAIN, operations=len(gates),
              intervals=len(life), source_width=peak, original_full_width_cuts=points,
              edges=sum(map(len,predecessors)), forced_cuts=forced, trial_widths=trials,
              collapsed_scope=dict(group_count=len(atoms), edge_count=sum(map(len,atom_pred)),
                                   intervals=len(group_life), forced_cuts=atom_cuts,
                                   boundary_trial_widths=grouped_trials),
              positive_control=positive_control())
    a.report.write_text(json.dumps(data,indent=2)+"\n")


if __name__ == "__main__":
    main()
