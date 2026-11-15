"""Native KMB fixture for the narrowed slope product (only this component)."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

import kickmix as km
import numpy as np

from truncated_product import truncated_product


def emit(width_a: int, width_b: int, cut: int, add):
    builder = km.CircuitBuilder()
    a=builder.create_quantum_register(width_a,"a")
    b=builder.create_quantum_register(width_b,"b")
    output=builder.create_quantum_register(width_a+width_b-cut,"product")
    for j,y in enumerate(b):
        lo=max(0,cut-j)
        # This row overlaps output bits [j+lo, j+width_a]. All higher bits are
        # still zero since the input output register is initially clean.
        row=builder.alloc_qubits(width_a-lo)
        for i,t in zip(range(lo,width_a),row):
            builder.init_and(a[i],y,t)
        add(builder, list(row), list(output[j+lo-cut:j+width_a+1-cut]))
        for i,t in zip(range(lo,width_a),row):
            builder.del_and(a[i],y,t)
        builder.free(row)
    return builder.finish_circuit()


def bits(v, size):
    return (v[None,:] >> np.arange(size,dtype=np.int64)[:,None]) & 1 == 1


def int_bits(v):
    return np.sum(v.astype(np.int64) << np.arange(len(v),dtype=np.int64)[:,None],axis=0)


def check(circuit, record, cut, max_x, batch_size=65536, seed=42571):
    cfg=record["design"]
    logp=cfg["prefix_bits"]
    lowbits=21-logp
    regs=circuit.register_data
    aa,bb,oo=(km.array(list(regs[n])) for n in ("a","b","product"))
    ready=set(list(aa)+list(bb)+list(oo))
    scratch=km.array([km.q(i) for i in range(circuit.num_qubits) if km.q(i) not in ready])
    tables=[np.asarray(row["slope"],dtype=np.int64) for row in record["tables"]]
    stats=circuit.operation_statistics()
    counts=dict(tested=0,wrong_output=0,wrong_inputs=0,dirty_workspace=0,bad_phase=0,
                measurement_seed=seed,toffoli_like=stats.num_toffoli_like,
                operations=len(circuit),qubits=circuit.num_qubits,
                product_output_bits=len(oo),truncation=cut)
    for exp in range(22):
        stop=min(1 <<(exp+1),max_x+1)
        for start in range(1<<exp,stop,batch_size):
            end=min(stop,start+batch_size)
            xs=np.arange(start, end,dtype=np.int64)
            m=xs << (21-exp)
            a=tables[exp%2][(m >> lowbits) & ((1<<logp)-1)]
            b=m & ((1<<lowbits)-1)
            expected=truncated_product(a,b,cut)>>cut
            sim=km.Simulator(batch_size=len(xs),seed=seed,counting_operations=True)
            sim.write_across_shots(aa,bits(a,len(aa)))
            sim.write_across_shots(bb,bits(b,len(bb)))
            sim.do(circuit)
            counts["tested"]+=len(xs)
            counts["wrong_output"]+=int((int_bits(sim.read_across_shots(oo))!=expected).sum())
            counts["wrong_inputs"]+=int(((int_bits(sim.read_across_shots(aa))!=a)|
                          (int_bits(sim.read_across_shots(bb))!=b)).sum())
            counts["dirty_workspace"]+=int(sim.read_across_shots(scratch).any(axis=0).sum())
            counts["bad_phase"]+=sum(sim.read_shot_phase(i)!=0 for i in range(len(xs)))
    return counts


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--screen",type=Path,required=True)
    ap.add_argument("--out",type=Path,required=True)
    ap.add_argument("--source",type=Path,required=True,help="Path containing public engine/fusion/arithmetic.py")
    ap.add_argument("--max-x",type=int,default=3_133_452)
    args=ap.parse_args()
    sys.path.insert(0,str(args.source))
    from engine.fusion.arithmetic import add
    args.out.mkdir(exist_ok=True)
    record=next(r for r in json.loads(args.screen.read_text())["summaries"]
                if r["design"]["prefix_bits"]==8)
    wa=max(max(table["slope"]).bit_length() for table in record["tables"])
    wb=21-record["design"]["prefix_bits"]
    checks=[]
    for cut in (0,record["truncate_low_product_diagonals"]):
        circuit=emit(wa,wb,cut,add)
        path=args.out/f"slope_product_cut{cut}.kmb"
        circuit.to_file(path,format="kmb")
        native=km.Circuit.from_file(path,format="kmb")
        result=check(native,record,cut,args.max_x)
        checks.append(result)
        print(json.dumps(result),flush=True)
    (args.out/"verification.json").write_text(json.dumps(checks,indent=2)+"\n")


if __name__=="__main__":
    main()
