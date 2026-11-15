#!/usr/bin/env python3
"""Apply only exact virtual-product bindings with certified chart and classical boundaries."""
from argparse import ArgumentParser
from bisect import bisect_left
from collections import Counter
import json
from pathlib import Path
import sys

import numpy as np


def audit(circuit, selected, previous, kp):
    old_writes = {next(iter(row["classical_roles"].values())) for row in selected}
    assert not old_writes & previous.classical_abi(circuit, kp)
    ops = np.frombuffer(circuit.opcodes,dtype=np.uint8)
    top, dominates = previous.condition_scopes(ops)
    reads = previous.bit_accesses(circuit,ops,old_writes)
    known = [dict(row, oldbit=next(iter(row["classical_roles"].values()))) for row in selected]
    # Conservatively require the next occurrence outside every changed wrapper
    # to be an unconditional overwrite. This audit does not use its random value.
    shape = [(row["start"],row["end"]) for row in selected]
    rejected = []
    safe = []
    for row in known:
        assert top(row["start"]) == top(row["end"]) == -1
        oldbit = row["oldbit"]
        later = reads[oldbit]
        at = bisect_left(later, (row["end"],0))
        if at == len(later):
            safe.append(row)
            continue
        p, kind = later[at]
        if (kind==0x40 and ops[p] in (0x40,0x41,0x50) and top(p)==-1
                and not any(a<=p<b for a,b in shape)):
            safe.append(row)
        else:
            rejected.append(dict(start=row["start"], bit=oldbit, first_external=[p,hex(ops[p]),kind,top(p)]))
    return safe,rejected


def main(args):
    sys.path[:0] = [str(args.central),str(args.repo),str(args.phase)]
    import census
    import dqi_ccx_peephole as binary
    import kmb_profile as kp
    from outcome_dqi_chart_splice_norm import encode
    from outcome_dqi_chart_match import match
    import splice_phase_peaks as previous

    binding = json.loads(args.binding.read_text())
    proof = json.loads(args.proof.read_text())
    b_hash = census.digest(args.base)
    assert b_hash == binding["tape_sha256"] == proof["input_sha256"]
    retired = proof.get("lanes",1)
    verified = {x["start"] for x in proof["sites"]
                if x.get("value_counterexample")=="unsat" and x["scratch_clean"]}
    selected = sorted([dict(row, points=family["points"]) for family in binding["families"]
                       for row in family["matches"] if row["start"] in verified],
                       key=lambda x:x["start"])
    fixtures = json.loads((args.fixtures/"result.json").read_text())
    sources = {fixture["m"]:fixture["records"] for fixture in fixtures}
    circuit = census.open_columns(args.base,binary.BinaryCircuit,kp)
    circuit.packets[1]["header_offset"] = circuit.packets[1]["payload_offset"] - kp.PACKET.size
    selected, rejected = audit(circuit,selected,previous,kp)
    assert selected
    assert all(a["end"]<=b["start"] for a,b in zip(selected,selected[1:]))
    new_classical = circuit.profile["header"]["num_bits"]
    columns = {k:[] for k in range(1,11)}
    offsets=[]
    extra_static=0
    delta=0
    Native = {}
    for row in selected:
        start,end,m = row["start"],row["end"],row["points"]
        if m not in Native:
            old,new = sources[m]
            data = []
            shape = []
            for fixture in (old,new):
                path = args.fixtures/fixture["gates"]
                assert census.digest(path)==fixture["sha256"]
                ref = census.open_columns(path,binary.BinaryCircuit,kp)
                assert ref.profile["header"]["num_bits"] == 1
                data.append(tuple(ref.operations(0,len(ref.opcodes))))
                shape.append(ref.profile["header"]["num_qubits"])
                ref.close()
            Native[m] = (*data,*shape, new["static_paid"]-old["static_paid"])
        old,new,old_q,new_q,extra = Native[m]
        matches=match(old,circuit.operations(start,end))
        assert matches is not None
        qmap,bmap = matches["qubits"],matches["bits"]
        assert bmap=={0:row["oldbit"]}
        first_scratch=old_q-24
        assert new_q==old_q-retired
        helpers=sorted(qmap[q] for q in range(first_scratch,old_q))
        assert helpers == row["scratch"]
        new_qmap={q:qmap[q] for q in range(first_scratch)}
        new_qmap.update(zip(range(first_scratch,new_q),helpers[:-retired]))
        after=[binary.Operation(op.opcode,tuple(new_qmap[q] for q in op.qubits),
                new_classical if op.bit is not None else None,
                new_classical if op.condition is not None else None,op.angle) for op in new]
        payload=encode(after)
        for k in columns:
            a,b=circuit.column_range(k,start,end)
            columns[k].append((a,b,payload[k]))
        offsets.append(dict(start=start,end=end,points=m,hot=row["hot"],
                            new_start=start+delta,new_end=start+delta+len(after),
                            retired_physical_helpers=helpers[-retired:],extra_static=extra))
        delta += len(after)-(end-start)
        extra_static+=extra
    counts=Counter()
    for k,patches in columns.items():
        counts[k]=circuit.packets[k]["payload_bytes"]+sum(len(v)-(b-a) for a,b,v in patches)
    header=dict(circuit.profile["header"])
    for key,k,width in previous.HEADER_COUNTS:
        header[key]=counts[k]//width
    header["num_bits"]+=1
    assert header["num_ops_with_3_target_qubits"]-circuit.profile["header"]["num_ops_with_3_target_qubits"]==extra_static
    with args.output.open("xb") as stream:
        stream.write(kp.HEADER.pack(kp.MAGIC,*(header[key] for key in kp.HEADER_FIELDS)))
        first=circuit.packets[1]["payload_offset"]-kp.PACKET.size
        binary.copy_range(circuit.data,stream,kp.HEADER.size,first)
        for k,pkt in circuit.packets.items():
            start=pkt["payload_offset"]
            stream.write(kp.PACKET.pack(k,counts.get(k,pkt["payload_bytes"])))
            cursor=0
            for a,b,payload in columns.get(k,()):
                assert cursor<=a<=b
                binary.copy_range(circuit.data,stream,start+cursor,start+a)
                stream.write(payload)
                cursor=b
            binary.copy_range(circuit.data,stream,start+cursor,start+pkt["payload_bytes"])
    circuit.close()
    report=dict(status="SPLICED_CERTIFIED_LOANS",input_sha256=b_hash,
                output_sha256=census.digest(args.output),variants=len(offsets),retired_helpers_per_site=retired,header=header,
                splice=offsets,extra_static=extra_static,rejected_classical=rejected,
                hot_in_source_spliced=sum(r["hot"] for r in offsets))
    args.receipt.write_text(json.dumps(report,indent=2)+"\n")
    print({k:v for k,v in report.items() if k not in ("splice","rejected_classical")})


if __name__=="__main__":
    p=ArgumentParser(description=__doc__)
    for key in ("central","repo","phase","base","binding","proof","fixtures","output","receipt"):
        p.add_argument("--"+key,type=Path,required=True)
    main(p.parse_args())
