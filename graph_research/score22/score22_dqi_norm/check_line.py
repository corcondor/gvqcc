"""Exhaust all target scalars with random unit sources on three GF12 lines."""
import argparse
import hashlib
import json
from pathlib import Path

import kickmix as km
import numpy as np

import score5_chem_width_classify as public_paths
import outcome_dqi_chart_check_norm as reference
import target_line

FIELD=km.GF2Field(12)


def bits(words,n=24):
    return ((words[None,:] >> np.arange(n)[:,None]) & 1).astype(bool)


def decode(sim,wires):
    return (sim.read_across_shots(wires).T*(1<<np.arange(len(wires)))).sum(axis=1)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("out",type=Path)
    args=parser.parse_args()
    rng=np.random.default_rng(202611152312)
    source_data=rng.integers(1,1<<24,4096)
    source_data[0]=0
    result={}
    invnorm=[]
    for value in source_data:
        a,b=int(value)&4095,int(value)>>12
        n=FIELD.mul(a,a)^FIELD.mul(a,b)^FIELD.mul(2048,FIELD.mul(b,b))
        invnorm.append(FIELD.invert(n) if n else 0)
    for line in (1,1<<12,0x50457):
        builder=km.CircuitBuilder()
        source=builder.create_quantum_register(24,"source")
        target=builder.create_quantum_register(24,"target")
        old_masks=[builder.create_classical_register(12,f"mask{i}") for i in range(3)]
        debt=target_line.divide_line(builder,source,target,line=line)
        for out,entry in zip(old_masks,(debt.old_scalar,debt.norm_mask,debt.scaled_input)):
            builder.cx(entry,out)
            builder.free(entry)
        tape=builder.finish_circuit()
        path=args.out/f"line_{line}.kmb"
        tape.to_file(path,format="kmb")
        target_data=np.array([reference.mul(line,x) for x in range(4096)])
        expected=np.array([reference.mul(int(v),reference.inv(int(u)))
                           for u,v in zip(source_data,target_data)])
        assert tape.num_qubits==60
        trials=[]
        for seed in (120,2020):
            sim=km.Simulator(batch_size=len(source_data),seed=seed,counting_operations=True)
            sim.use_same_registers_as(tape)
            sim.write_across_shots(source,bits(source_data))
            sim.write_across_shots(target,bits(target_data))
            sim.do(tape)
            assert np.array_equal(decode(sim,source),source_data)
            assert np.array_equal(decode(sim,target),expected)
            assert not sim.read_across_shots([km.q(i) for i in range(48,60)]).any()
            first,second,third=(decode(sim,w) for w in old_masks)
            expected_phase=[]
            for x,n,m1,m2,m3 in zip(range(4096),invnorm,first,second,third):
                expected_phase.append(((int(m1)&x).bit_count()^
                                       (int(m2)&n).bit_count()^
                                       (int(m3)&FIELD.mul(n,x)).bit_count())&1)
            assert np.array_equal(sim.read_phase_flipped_across_shots(),expected_phase)
            trials.append(dict(shots=len(source_data),seed=seed,errors=0))
        result[str(line)] = dict(helpers=12,T=tape.operation_statistics().num_toffoli_like,
                                 sha256=hashlib.sha256(path.read_bytes()).hexdigest(),trials=trials)
    (args.out/"target_line.json").write_text(json.dumps(result,indent=2)+"\n")
    print(json.dumps(result))


if __name__=="__main__":
    main()
