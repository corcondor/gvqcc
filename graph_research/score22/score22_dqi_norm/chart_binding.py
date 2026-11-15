"""Use independent physical inputs to refute unconditional a=1 at actual GF24 sites."""
import argparse
import hashlib
import json
from pathlib import Path
import sys
import tempfile

import kickmix as km
import numpy as np

import score5_chem_width_classify as public
import kmb_splice as splice
from outcome_dqi_chart_match import match


def witness_rank(words):
    first = int(words[0])
    pivots = {}
    for item in words:
        word = int(item) ^ first
        while word:
            pivot = word.bit_length() - 1
            if pivot not in pivots:
                pivots[pivot] = word
                break
            word ^= pivots[pivot]
    return len(pivots)


def select_divisions(base, template):
    pattern = template.opcodes
    before = list(template.operations(0, len(pattern)))
    cursor = 0
    while (start := base.opcodes.find(pattern, cursor)) >= 0:
        cursor = start + 1
        mapping = match(before, base.operations(start, start+len(pattern)))
        if mapping is None:
            continue
        depth = base.opcodes[:start].count(b"\x81") - base.opcodes[:start].count(b"\x01")
        if depth == 0:
            wire_ids = mapping["qubits"]
            yield start, [wire_ids[i] for i in range(24)], [wire_ids[i] for i in range(24,48)]


def build_template(directory):
    import gf24_nested_norm
    import nested_norm_inverse
    public.Direct.A = gf24_nested_norm
    public.Direct.Prior = nested_norm_inverse
    builder = km.CircuitBuilder()
    source = builder.create_quantum_register(24,"source")
    target = builder.create_quantum_register(24,"target")
    public.Direct.divide_deferred(builder,source,target)
    path = directory / "template.kmb"
    builder.finish_circuit().to_file(path,format="kmb")
    return splice.open_circuit(path)


def decode(simulator, wires):
    return (simulator.read_across_shots(km.array([km.q(i) for i in wires])).T
            * (1<<np.arange(len(wires)))).sum(axis=1)


def write_slice(base, path, first, last):
    flags = splice.write_segments(path, base, [(base, first, last)])["header"]
    for name, columns, declared in (("num_qubits", range(2,8), 840),
                                    ("num_bits", (8,9), 49140)):
        actual = [declared]
        for column in columns:
            view = splice.column_bytes(base, column, first, last)
            data = np.frombuffer(view, dtype="<u4")
            if len(data):
                actual.append(int(data.max())+1)
        flags[name] = max(actual)
    packed = splice.kp.HEADER.pack(splice.kp.MAGIC, *(flags[field] for field in splice.kp.HEADER_FIELDS))
    with path.open("r+b") as stream:
        stream.write(packed)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("tape", type=Path)
    parser.add_argument("verifier", type=Path)
    parser.add_argument("out", type=Path)
    parser.add_argument("--seed", type=int, default=202611152238)
    parser.add_argument("--site", type=int, action="append")
    parser.add_argument("--weight", type=int)
    args = parser.parse_args()
    sys.path.insert(0,str(args.verifier.parent))
    import verify_submission_dqi as verifier
    spec = verifier.ProblemSpecDQI.benchmark_instance()
    rng = np.random.default_rng(args.seed)
    tables = verifier.FieldTables(km.GF2Field(spec.degree))
    weights = None
    if args.weight is not None:
        assert 0 <= args.weight <= spec.max_errors
        weights = np.zeros(spec.max_errors+1)
        weights[args.weight] = 1
    syndromes, classical, expected_phase = verifier.sample_shots(spec,tables,rng,256,weights)
    sample_sha = hashlib.sha256(syndromes.tobytes()+classical.tobytes()).hexdigest()
    base = splice.open_circuit(args.tape)
    summary = dict(tape_sha256=base.profile["raw_kmb_sha256"], seed=args.seed,
                   input_values_sha256=sample_sha, shots=len(syndromes),
                   sample_weight=args.weight,
                   scope="witnesses against a constant coordinate, not proofs that a relation holds")
    with tempfile.TemporaryDirectory() as tmp:
        directory = Path(tmp)
        template = build_template(directory)
        sites = list(select_divisions(base,template))
        template.close()
        if args.site:
            sites = [row for row in sites if row[0] in args.site]
        if not sites:
            raise RuntimeError("no exact division bindings, inspect selected source aliases")
        simulator = km.Simulator(batch_size=len(syndromes),seed=args.seed)
        simulator.write_across_shots(km.array([km.q(i) for i in range(840)]),
                                     verifier.to_bits(syndromes,12))
        simulator.write_across_shots(km.array([km.b(i) for i in range(49140)]),
                                     verifier.to_bits(classical,12))
        from_index = 0
        observations = []
        for start, source, target in sites:
            path = directory / f"region-{start}.kmb"
            write_slice(base,path,from_index,start)
            circuit = km.Circuit.from_file(path,format="kmb")
            simulator.do(circuit)
            from_index = start
            del circuit
            path.unlink()
            observations.append((start, source, decode(simulator,source[:12]),
                                 decode(simulator,source[12:]), decode(simulator,target)))
        path = directory / "final-region.kmb"
        write_slice(base,path,from_index,len(base.opcodes))
        simulator.do(km.Circuit.from_file(path,format="kmb"))
        actual = simulator.read_across_shots(km.array([km.q(i) for i in range(840)]))
        valid = (~(actual ^ verifier.to_bits(syndromes,12)).any(axis=0) &
                 ~simulator.read_across_shots([km.q(i) for i in range(840,889)]).any(axis=0) &
                 ~(simulator.read_phase_flipped_across_shots() ^ expected_phase))
        assert valid.any()
        summary["final_phase_value_valid_shots"] = int(valid.sum())
        samples = []
        for start,source,low,high,target in observations:
            joint = low|(high<<12)
            zero_source = valid & (joint==0)
            selected = valid & (joint!=0)
            hold = low[selected]
            samples.append(dict(start=start,source_wires=source,
                                low_unique=len(set(map(int,hold))),
                                target_affine_rank=witness_rank(target[selected]),
                                target_low_rank=witness_rank(target[selected]&4095),
                                target_high_rank=witness_rank(target[selected]>>12),
                                target_zero_count=int((target[selected]==0).sum()),
                                target_first_words=[int(x) for x in target[selected][:16]],
                                low_affine_rank=witness_rank(hold),
                                high_affine_rank=witness_rank(high[selected]),
                                full_affine_rank=witness_rank(joint[selected]),
                                source_target_affine_rank=witness_rank(joint[selected]|(target[selected]<<24)),
                                first_non_a1=next((int(value) for value in hold if value!=1),None),
                                a1_count=int((hold==1).sum()),
                                zero_source_count=int(zero_source.sum()),
                                zero_source_nonzero_target=int((zero_source & (target!=0)).sum())))
        summary["sites"] = samples
        summary["exact_depth_zero_sites"] = len(samples)
        summary["sites_with_witness_against_fixed_a1"] = sum(row["first_non_a1"] is not None for row in samples)
        summary["sites_with_full_12_bit_low_word_affine_rank"] = sum(row["low_affine_rank"]==12 for row in samples)
    base.close()
    args.out.write_text(json.dumps(summary,indent=2)+"\n")
    print(json.dumps({k:v for k,v in summary.items() if k!="sites"}))


if __name__ == "__main__":
    main()
