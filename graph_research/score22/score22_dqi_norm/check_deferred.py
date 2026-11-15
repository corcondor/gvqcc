"""Check physical width, exact quotient, and both exposed HMR debts."""
import argparse
import hashlib
import json
from pathlib import Path

import kickmix as km
import numpy as np

import score5_chem_width_classify as public
import outcome_dqi_chart_check_norm as reference
import deferred

FIELD=km.GF2Field(12)


def bits(words,n):
    return ((words[None,:] >> np.arange(n)[:,None]) & 1).astype(bool)


def read(sim,wires):
    return (sim.read_across_shots(wires).T * (1 << np.arange(len(wires)))).sum(axis=1)


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("out",type=Path)
    args=p.parse_args()
    args.out.mkdir(parents=True,exist_ok=True)
    b=km.CircuitBuilder()
    source=b.create_quantum_register(24,"source")
    target=b.create_quantum_register(24,"target")
    old_target=b.create_classical_register(24,"old_target_mask")
    cofactor=b.create_classical_register(12,"cofactor_mask")
    debts=deferred.divide_deferred(b,source,target)
    b.cx(debts.old_target_mask,old_target)
    b.free(debts.old_target_mask)
    b.cx(debts.cofactor_mask,cofactor)
    b.free(debts.cofactor_mask)
    tape=b.finish_circuit()
    assert tape.num_qubits==62
    path=args.out/"deferred.kmb"
    tape.to_file(path,format="kmb")
    rng=np.random.default_rng(202611152307)
    values=np.concatenate((np.arange(4096)|(rng.integers(0,4096,4096)<<12), np.arange(4096)<<12))
    data=rng.integers(0,1 << 24,len(values))
    data[values==0]=0
    expected=np.array([reference.mul(int(v),reference.inv(int(u))) for u,v in zip(values,data)])
    cofactor_value=[]
    for u in values:
        a,b=int(u)&4095,int(u)>>12
        aa=FIELD.mul(a,a)
        norm=aa ^ FIELD.mul(a,b) ^ FIELD.mul(2048,FIELD.mul(b,b))
        cofactor_value.append(FIELD.mul(aa,FIELD.invert(norm)) if norm else 0)
    results=[]
    for seed in (1009,2009):
        sim=km.Simulator(batch_size=len(values),seed=seed,counting_operations=True)
        sim.use_same_registers_as(tape)
        sim.write_across_shots(source,bits(values,24));sim.write_across_shots(target,bits(data,24))
        sim.do(tape)
        assert np.array_equal(read(sim,source),values)
        assert np.array_equal(read(sim,target),expected)
        assert not sim.read_across_shots([km.q(q) for q in range(48,62)]).any()
        m,n=read(sim,old_target),read(sim,cofactor)
        phase=[((int(v)&int(p)).bit_count()^(int(w)&int(q)).bit_count())&1
               for v,p,w,q in zip(data,m,cofactor_value,n)]
        assert np.array_equal(sim.read_phase_flipped_across_shots(),phase)
        results.append(dict(shots=len(values),seed=seed,errors=0,
                            mean_T=sim.operation_statistics().num_toffoli_like/len(values)))
    out=dict(helper_width=14,static_T=tape.operation_statistics().num_toffoli_like,
             sha256=hashlib.sha256(path.read_bytes()).hexdigest(),trials=results)
    (args.out/"deferred.json").write_text(json.dumps(out,indent=2)+"\n")
    print(json.dumps(out))


if __name__=="__main__":
    main()
