"""Use valid inputs to test affine-clean hypotheses for caller-idle data."""

from argparse import ArgumentParser
from collections import defaultdict
from csv import DictReader
from hashlib import sha256
import json
from pathlib import Path
import sys
from tempfile import TemporaryDirectory

import kickmix as km
import numpy as np


def affine_rank(bits):
    rows = np.packbits(bits.T, axis=1, bitorder="little")
    first = int.from_bytes(rows[0], "little")
    pivots = {}
    for row in rows:
        x = int.from_bytes(row, "little") ^ first
        while x:
            pivot = x.bit_length() - 1
            if pivot not in pivots:
                pivots[pivot] = x
                break
            x ^= pivots[pivot]
    return len(pivots)


def main():
    p = ArgumentParser(description=__doc__)
    for name in ("circuit","data-idle","membership","repo","verifier","out"):
        p.add_argument("--"+name, type=Path, required=True)
    p.add_argument("--shots", type=int, default=1024)
    a = p.parse_args()
    sys.path[:0] = [str(a.repo), str(a.verifier)]
    import kmb_splice as splice
    import verify_submission_dqi as ver

    circuit = splice.open_circuit(a.circuit)
    scope = json.loads(a.data_idle.read_text())
    intervals = defaultdict(list)
    with a.membership.open() as stream:
        for row in DictReader(stream, delimiter="\t"):
            intervals[row["caller"]].append((int(row["start"]), int(row["stop_exclusive"])))
    points = []
    for family,row in scope.items():
        wires = row["at_peak"]["idle_data"]
        if wires:
            region = intervals[family]
            points += [(region[0][0], family, wires),(region[-1][1]-1, family, wires)]
    seed = 202611152214
    spec = ver.ProblemSpecDQI.benchmark_instance()
    rng = np.random.default_rng(seed)
    tables = ver.FieldTables(km.GF2Field(spec.degree))
    syndrome, masks, phase = ver.sample_shots(spec,tables,rng,a.shots)
    input_bits = ver.to_bits(syndrome,12)
    sim = km.Simulator(batch_size=a.shots, seed=seed)
    sc = km.array([km.q(q) for q in range(840)])
    sim.write_across_shots(sc, input_bits)
    sim.write_across_shots(km.array([km.b(q) for q in range(49140)]),
                          ver.to_bits(masks,12))
    old = 0
    observations = []
    with TemporaryDirectory() as tmp:
        path = Path(tmp)/"slice.kmb"
        points.append((len(circuit.opcodes), None, None))
        for pos, label, wires in sorted(points):
            if old != pos:
                entries = splice.write_segments(path, circuit, [(circuit,old,pos)])["header"]
                for name, cols, lo in (("num_qubits",range(2,8),840),("num_bits",(8,9),49140)):
                    max_id = lo
                    for column in cols:
                        ids = np.frombuffer(splice.column_bytes(circuit,column,old,pos),dtype="<u4")
                        if ids.size:
                            max_id = max(max_id, int(ids.max()) + 1)
                        del ids
                    entries[name] = max_id
                with path.open("r+b") as stream:
                    stream.write(splice.kp.HEADER.pack(splice.kp.MAGIC, *(
                        entries[field] for field in splice.kp.HEADER_FIELDS)))
                local = km.Circuit.from_file(path,format="kmb")
                sim.do(local)
                del local
                path.unlink()
                old = pos
            if label is not None:
                snapshots = sim.read_across_shots(km.array([km.q(q) for q in wires]))
                observations.append((pos,label,wires,snapshots))
    valid = np.array_equal(sim.read_across_shots(sc), input_bits)
    valid &= not sim.read_across_shots([km.q(q) for q in range(840,889)]).any()
    valid &= np.array_equal(sim.read_phase_flipped_across_shots(),phase)
    if not valid:
        raise AssertionError("The sampled tape changed a value or phase")
    rows = []
    for pos,label,wires,bits in observations:
        rank = affine_rank(bits)
        rows.append(dict(position=pos, caller=label, wires=len(wires), rank=rank,
                         full_rank=rank==len(wires),
                         zero_in_this_test=[q for q,seen in zip(wires,bits.any(axis=1)) if not seen]))
    result = dict(verified_end_to_end_shots=a.shots, source=circuit.profile["raw_kmb_sha256"],
                  input_sha256=sha256(syndrome.tobytes()+masks.tobytes()).hexdigest(),
                  seed=seed, rows=rows)
    a.out.write_text(json.dumps(result, indent=2) + "\n")
    circuit.close()
    print([(r["caller"],r["rank"],r["wires"],len(r["zero_in_this_test"])) for r in rows])


if __name__ == "__main__":
    main()
