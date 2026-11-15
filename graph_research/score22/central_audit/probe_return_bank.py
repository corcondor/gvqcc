"""Probe the exact old closing's helper bank on real decoder calls."""

from argparse import ArgumentParser
import json
from pathlib import Path
import sys
from tempfile import TemporaryDirectory

import numpy as np

from census import PIN, digest, open_columns
from reachable_alias_sample import tighten_header
from splice_plu_crt import locate


def main():
    cli = ArgumentParser(description=__doc__)
    cli.add_argument("candidate", type=Path)
    cli.add_argument("original_e4", type=Path)
    cli.add_argument("native", type=Path)
    cli.add_argument("binding", type=Path)
    cli.add_argument("report", type=Path)
    cli.add_argument("--verifier", type=Path, required=True)
    cli.add_argument("--prior-code", type=Path, required=True)
    cli.add_argument("--shots", type=int, default=1024)
    args = cli.parse_args()
    assert digest(args.original_e4) == PIN
    bound = json.loads(args.binding.read_text())
    assert digest(args.candidate) == bound["output_sha256"]
    sys.path[:0] = [str(args.prior_code), str(args.verifier.parent)]
    import dqi_ccx_peephole as binary
    import kickmix as km
    import kmb_profile
    import kmb_splice
    from outcome_dqi_chart_match import match
    import verify_submission_dqi as verify

    def read(path):
        return open_columns(path, binary.BinaryCircuit, kmb_profile)

    row = next(row for row in json.loads((args.native / "result.json").read_text())["rows"]
               if row["case"] == "original_closed")
    original = read(args.original_e4)
    template = read(args.native / "original_closed.kmb")
    _, _, mapping = locate(original, template, row["marks"]["begin_return"], row["operations"],
                           match)
    original.close()
    template.close()
    qbank = [mapping["qubits"][q] for q in range(852, 876)]
    stop = bound["matches"][1]["new_start"]
    target = read(args.candidate)
    with TemporaryDirectory() as folder:
        sub = Path(folder) / "partial.kmb"
        kmb_splice.write_segments(sub, target, [(target, 0, stop)])
        tighten_header(sub, target, stop, kmb_profile)
        circuit = km.Circuit.from_file(sub)
    target.close()
    spec = verify.ProblemSpecDQI.benchmark_instance(num_shots=args.shots)
    syndromes, mbuc, _ = verify.sample_shots(
        spec, verify.FieldTables(km.GF2Field(12)), np.random.default_rng(182457), args.shots)
    s, b, _ = verify.validate_registers(circuit, spec)
    simulator = km.Simulator(batch_size=args.shots, seed=521398, counting_operations=False)
    simulator.use_same_registers_as(circuit)
    simulator.write_across_shots(km.array(s), verify.to_bits(syndromes, 12))
    simulator.write_across_shots(km.array(b), verify.to_bits(mbuc, 12))
    simulator.do(circuit)
    reads = np.asarray(simulator.read_across_shots(km.array([km.q(q) for q in qbank])))
    report = dict(source_sha256=bound["output_sha256"], cut=stop, shots=args.shots,
                  physical_helper_wires=qbank, ones_by_physical_wire={q: int(y.sum())
                                                                       for q, y in zip(qbank, reads)})
    args.report.write_text(json.dumps(report, indent=2) + "\n")
    print(report, flush=True)


if __name__ == "__main__":
    main()
