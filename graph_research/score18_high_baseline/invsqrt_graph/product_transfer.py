"""Screen reducing one temporary AND through an affine dataflow region."""
from argparse import ArgumentParser
from hashlib import sha256
import json
from pathlib import Path

import kickmix as km

from width_dag import Gate, PIN, QUBITS, packed_lifetimes


AFFINE = {"CX", "X", "SWAP"}
PHASE = {"Z","CZ","CCZ","NEG"}


def eliminate(rows, rhs, size):
    """Form echelon rows with augmented column and return an optional null direction."""
    rows = list(rows)
    rhs = list(rhs)
    pivots = []
    moves = []
    for col in range(size):
        pick = next((i for i in range(len(pivots),len(rows)) if rows[i] >> col & 1), None)
        if pick is None:
            continue
        k = len(pivots)
        rows[k],rows[pick] = rows[pick],rows[k]
        rhs[k],rhs[pick] = rhs[pick],rhs[k]
        if k != pick:
            moves.append(("SWAP", k, pick))
        for i in range(len(rows)):
            if i != k and rows[i] >> col & 1:
                rows[i] ^= rows[k]
                rhs[i] ^= rhs[k]
                moves.append(("CX",k,i))
        pivots.append(col)
    if len(pivots) == size:
        return size, sum(v<<q for v,q in zip(rhs,pivots)), None,moves
    if len(pivots) == size-1:
        free = ((1<<size)-1) ^ sum(1<<q for q in pivots)
        direction = free ^ sum(1<<q for row,q in zip(rows,pivots) if row & free)
        return size-1, None, direction,moves
    return len(pivots), None, None,moves


def transfer(gates, wire, birth, death):
    start,end = gates[birth],gates[death]
    if (start.op!="CCX" or start.wires[2]!=wire or start.bits
            or end.op!="HMR" or end.wires[0]!=wire):
        return None
    region = gates[birth+1:death]
    if any(g.op not in AFFINE or g.bits for g in region):
        return None
    keep = [q for q in range(QUBITS) if q!=wire]
    size = len(keep)
    product = 1 << size
    constant = product << 1
    state = [0]*QUBITS
    for j,q in enumerate(keep):
        state[q] = 1 << j
    state[wire] = product
    for gate in region:
        if gate.op=="CX":
            a,b=gate.wires
            state[b] ^= state[a]
        elif gate.op=="X":
            state[gate.wires[0]] ^= constant
        else:
            a,b=gate.wires
            state[a],state[b]=state[b],state[a]
    rows = [state[q] & (product-1) for q in keep]
    rhs = [int(bool(state[q] & product)) for q in keep]
    rank, direction, null, moves = eliminate(rows, rhs, size)
    controls = sum(1<<keep.index(q) for q in start.wires[:2])
    ordinary = direction is not None and not (controls & direction)
    erase_early = null is not None and not (controls & null) and not (state[wire]&product)
    replacement = None
    direction_support = [q for j,q in enumerate(keep) if direction is not None and direction >> j & 1]
    if ordinary:
        replacement = []
        if direction_support:
            pivot,*rest=direction_support
            fanout=[("CX",pivot,q) for q in rest]
            replacement.extend(fanout)
            a,b = start.wires[:2]
            replacement.append(("CCX",a,b,pivot))
            replacement.extend(reversed(fanout))
        replacement.extend((op,keep[i],keep[j]) for op,i,j in reversed(moves))
        replacement.extend(("X",q) for q in keep if state[q]&constant)
        candidate = [0]*QUBITS
        for j,q in enumerate(keep):
            candidate[q]=1<<j
        for op,*qs in replacement:
            if op == "X":
                candidate[qs[0]] ^= constant
            elif op == "CX":
                a,b=qs
                candidate[b] ^= candidate[a]
            elif op == "SWAP":
                a,b=qs
                candidate[a],candidate[b]=candidate[b],candidate[a]
            else:
                a,b,t=qs
                assert candidate[a]==1<<keep.index(start.wires[0])
                assert candidate[b]==1<<keep.index(start.wires[1])
                candidate[t] ^= product
        assert all(candidate[q] == state[q] for q in keep)
    return dict(wire=wire,birth=birth,death=death,rank=rank,arity=size,
                reversible_data_contraction=ordinary,early_erasure_screen=erase_early,
                measured_depends_on_product=bool(state[wire]&product),
                control_intersection= None if direction is None else (direction&controls).bit_count(),
                replacement=replacement)


def delayed_phase_reads(gates, depth, death):
    """Recognize an isolated measurement bit used only by diagonal corrections."""
    bit,=gates[death].bits
    guards=set()
    phase=set()
    for i in range(death+1,len(gates)):
        gate=gates[i]
        read,written=gate.dependencies()
        if bit in written:
            if gate.op in {"HMR","BIT_STORE0"} and len(gate.bits)==1 and not depth[i]:
                break
            return None
        if bit not in read:
            continue
        if gate.bits!=(bit,) or depth[i]:
            return None
        if gate.op in PHASE:
            phase.add(i)
        elif gate.op=="PUSH_CONDITION":
            end=i+1
            while gates[end].op!="POP_CONDITION":
                if gates[end].op not in PHASE or gates[end].bits:
                    return None
                phase.add(end)
                end+=1
            guards.update((i,end))
        else:
            return None
    return phase,guards


def main():
    parser=ArgumentParser(description=__doc__)
    parser.add_argument("source",type=Path)
    parser.add_argument("output",type=Path)
    parser.add_argument("--candidate",type=Path)
    opt=parser.parse_args()
    assert sha256(opt.source.read_bytes()).hexdigest()==PIN
    raw = str(km.Circuit.from_file(opt.source)).splitlines()
    register_ops = {"APPEND_TO_REGISTER","REGISTER"}
    lines = [s for s in raw if s.split()[0] not in register_ops]
    prefix = [s for s in raw if s.split()[0] in register_ops]
    gates=[Gate.parse(s) for s in lines]
    intervals,_,_=packed_lifetimes(gates)
    rows=[row for interval in intervals if (row:=transfer(gates,*interval)) is not None]
    early=[r for r in rows if r["early_erasure_screen"]]
    full=[r for r in rows if r["reversible_data_contraction"]]
    proof_points=set()
    phase_repairs=[]
    depth=0
    inside=[]
    for gate in gates:
        inside.append(depth)
        depth += int(gate.op=="PUSH_CONDITION") - int(gate.op=="POP_CONDITION")
    for r in full:
        if inside[r["birth"]] or inside[r["death"]]:
            continue
        scope=delayed_phase_reads(gates,inside,r["death"])
        if scope is None:
            continue
        phase,guards=scope
        proof_points.add(r["death"])
        proof_points.update(phase)
        phase_repairs.append((r,phase,guards))
    value_at={}
    def observe(index,state,domain):
        if index in proof_points:
            f=domain
            for q in gates[index].wires:
                f &= state[q]
            value_at[index]=f
    packed_lifetimes(gates, observe)
    replaced=set()
    operations={}
    eliminated_ccx=0
    eliminated_ccz=0
    certified=[]
    for r,phase,guards in sorted(phase_repairs,key=lambda t:t[0]["birth"]):
        measured=value_at[r["death"]]
        for pos in phase:
            measured ^= value_at[pos]
        if measured:
            continue
        deleted=set(range(r["birth"],r["death"]+1))|phase|guards
        if deleted&replaced:
            continue
        replaced.update(deleted)
        operations[r["birth"]]=[" ".join([op,*[f"q{q}" for q in qs]]) for op,*qs in r["replacement"]]
        eliminated_ccx+=1-sum(op=="CCX" for op,*_ in r["replacement"])
        eliminated_ccz+=sum(gates[i].op=="CCZ" for i in phase)
        certified.append(dict(wire=r["wire"],birth=r["birth"],death=r["death"],
                              correction_gate_indices=sorted(phase)))
    data=dict(intervals=len(intervals),checked=len(rows),
              ordinary_contraction_candidates=len(full),early_erasure_candidates=len(early),
              first_full_width_birth=next(r for r in rows if r["birth"]==2364),
              all_rows=rows,certified_data_and_phase=certified,
              eliminated_ccx=eliminated_ccx,eliminated_ccz=eliminated_ccz)
    if operations and opt.candidate:
        output=[]
        for index, line in enumerate(lines):
            if index in operations:
                output.extend(operations[index])
            if index not in replaced:
                output.append(line)
        c=km.Circuit("\n".join(prefix+output)+"\n")
        c.to_file(opt.candidate,format="kmb")
        data.update(candidate_qubits=c.num_qubits,candidate_sha256=sha256(opt.candidate.read_bytes()).hexdigest())
    opt.output.write_text(json.dumps(data,indent=2)+"\n")
    print({k:v for k,v in data.items() if k not in {"all_rows","first_full_width_birth"}})


if __name__=="__main__":
    main()
