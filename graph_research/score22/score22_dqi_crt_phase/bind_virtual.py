#!/usr/bin/env python3
"""Bind production virtual-products work banks and the last coefficient lender."""
from argparse import ArgumentParser
from bisect import bisect_left
from collections import Counter
import json
from pathlib import Path
import sys


def main(args):
    sys.path[:0] = [str(args.central), str(args.repo)]
    import census
    import dqi_ccx_peephole as binary
    import kmb_profile as kp
    from outcome_dqi_chart_match import match

    circuit = census.open_columns(args.circuit, binary.BinaryCircuit, kp)
    width = census.read_width(args.lifetimes, len(circuit.opcodes))
    hot = census.union([(a,b) for a,b,w in width if w==889])
    data = json.loads((args.fixtures/"result.json").read_text())
    records = []
    for fixture in data:
        m = fixture["m"]
        old = fixture["records"][0]
        ref = census.open_columns(args.fixtures/old["gates"], binary.BinaryCircuit, kp)
        pattern = ref.opcodes
        template_ops = tuple(ref.operations(0,len(ref.opcodes)))
        q_boundary = ref.profile["header"]["num_qubits"]-24
        ref.close()
        i = 0
        positions = 0
        rows = []
        while (start := circuit.opcodes.find(pattern, i)) >= 0:
            i = start + 1
            end = start+len(pattern)
            positions += 1
            matched = match(template_ops,circuit.operations(start,end))
            if matched is None:
                continue
            qmap, bmap = matched["qubits"], matched["bits"]
            guard = qmap[24*m+24]
            leading = [qmap[q] for q in range(12*(m-1),12*m)]
            covered = census.size(census.intersection(hot, [(start, end)]))
            rows.append(dict(start=start,end=end,hot=covered,flag=guard,
                             coefficient_lead=leading,
                             scratch=sorted(v for q,v in qmap.items() if q>=q_boundary),
                             qubit_roles=qmap, classical_roles=bmap))
        print(m, "opcode", positions, "exact", len(rows), "Q889 sites", sum(row["hot"]>0 for row in rows),
              "hot cuts", sum(row["hot"] for row in rows), flush=True)
        records.append(dict(points=m,opcode_sites=positions,matches=rows))
    circuit.close()
    result = dict(tape_sha256=census.digest(args.circuit), family="gauge_park_virtual.products",
                  matches=sum(len(r["matches"]) for r in records),
                  hot_matches=sum(row["hot"]>0 for r in records for row in r["matches"]),
                  hot_positions=sum(row["hot"] for r in records for row in r["matches"]),
                  families=records)
    args.out.write_text(json.dumps(result,indent=2)+"\n")
    print({k:v for k,v in result.items() if k!="families"})


if __name__ == "__main__":
    p=ArgumentParser(description=__doc__)
    for key in ("central","repo","circuit","lifetimes","fixtures","out"):
        p.add_argument("--"+key,type=Path,required=True)
    main(p.parse_args())
