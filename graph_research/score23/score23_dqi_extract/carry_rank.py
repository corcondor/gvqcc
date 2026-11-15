"""Test affine recovery of the physical gauge bank on valid decoder trajectories."""

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


def points(membership, ranges):
    families = ("outer.emit_prefix", "seam.outer_closing_with_inverse")
    peaks = defaultdict(list)
    with membership.open() as stream:
        for row in DictReader(stream, delimiter="\t"):
            peaks[row["caller"]].append((int(row["start"]), int(row["stop_exclusive"])))
    for line in ranges.read_text().splitlines():
        lo,hi,label = line.split()
        if label not in families:
            continue
        selected = peaks[label]
        a,b = selected[len(selected)//2]
        for cut,where in ((int(lo),"entry"),(selected[0][0],"first_peak"),
                          ((a+b)//2,"middle_peak"),(selected[-1][1]-1,"last_peak"),
                          (int(hi),"exit")):
            yield cut,label,where


def main():
    cli = ArgumentParser(description=__doc__)
    for name in ("circuit","membership","ranges","repo","verifier","chart","peak","out"):
        cli.add_argument("--"+name,type=Path,required=True)
    cli.add_argument("--shots",type=int,default=1024)
    a = cli.parse_args()
    sys.path[:0] = [str(a.repo), str(a.chart), str(a.verifier), str(a.peak)]
    import kmb_splice as splice
    import verify_submission_dqi as verifier
    from chart_binding import write_slice
    from sample_idle_data import affine_rank

    source=splice.open_circuit(a.circuit)
    seed=202611152305
    spec=verifier.ProblemSpecDQI.benchmark_instance()
    tables=verifier.FieldTables(km.GF2Field(12))
    syndromes,masks,expected=verifier.sample_shots(spec,tables,np.random.default_rng(seed),a.shots)
    data=verifier.to_bits(syndromes,12)
    sim=km.Simulator(batch_size=a.shots,seed=seed)
    syndrome_ports=km.array([km.q(i) for i in range(840)])
    sim.write_across_shots(syndrome_ports,data)
    sim.write_across_shots(km.array([km.b(i) for i in range(49140)]),verifier.to_bits(masks,12))
    whole=km.array([km.q(q) for q in range(889)])
    obs=sorted([*points(a.membership,a.ranges),(len(source.opcodes),None,None)])
    records=[]
    start=0
    with TemporaryDirectory() as tmp:
        path=Path(tmp)/"slice.kmb"
        for end,caller,kind in obs:
            if start<end:
                write_slice(source,path,start,end)
                sim.do(km.Circuit.from_file(path,format="kmb"))
                path.unlink()
                start=end
            if caller is None:
                continue
            bits=sim.read_across_shots(whole)
            other=np.concatenate((bits[:852],bits[864:]))
            bank=bits[852:864]
            before=affine_rank(other)
            after=affine_rank(bits)
            records.append(dict(pos=end,caller=caller,site=kind,rank_other=before,
                                rank_full=after,rank_gauge_bank=affine_rank(bank),
                                rank_increment=after-before,
                                bank_nonzero_cases=int(bank.any(axis=0).sum())))
    assert np.array_equal(sim.read_across_shots(syndrome_ports),data)
    assert not sim.read_across_shots([km.q(i) for i in range(840,889)]).any()
    assert np.array_equal(sim.read_phase_flipped_across_shots(),expected)
    result=dict(source_sha256=source.profile["raw_kmb_sha256"], verified_shots=a.shots,
                case_digest=sha256(syndromes.tobytes()+masks.tobytes()).hexdigest(),
                seed=seed, rows=records)
    a.out.write_text(json.dumps(result,indent=2)+"\n")
    print(json.dumps(records))
    source.close()


if __name__=="__main__":
    main()
