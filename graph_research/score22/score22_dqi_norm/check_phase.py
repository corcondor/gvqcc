"""Independent truth checks of quantum-numerator quotient phase at width 12."""
import argparse
import json
from pathlib import Path
import sys

import kickmix as km
import numpy as np

import score5_chem_width_classify as public_paths
from tower_inverse import quadratic_basis
import quotient_phase


def bits(words):
    return ((words[None,:] >> np.arange(12)[:,None]) & 1).astype(bool)


def scalar_trace(field, value):
    result = 0
    for _ in range(12):
        result ^= value
        value = field.mul(value,value)
    assert result in (0,1)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("out",type=Path)
    args = parser.parse_args()
    field = km.GF2Field(12)
    tower_rows = quadratic_basis(12)["to_tower"]
    rng = np.random.default_rng(202611152305)
    u = np.arange(4096)
    v, mu, eta = rng.integers(0,4096,(3,4096))
    mu[::8] = 0
    result = {}
    for label in ("trace","affine_mask"):
        b=km.CircuitBuilder()
        source=b.create_quantum_register(12,"denominator")
        numer=b.create_quantum_register(12,"numerator")
        if label == "trace":
            quotient_phase.phase_trace_quotient(b,source,numer)
        else:
            mult=b.create_classical_register(12,"mu")
            add=b.create_classical_register(12,"eta")
            quotient_phase.phase_linear_numerator(b,source,numer,mult,add)
        tape=b.finish_circuit()
        assert tape.num_qubits==36
        expected=[]
        for a,z,m,e in zip(u,v,mu,eta):
            inv=field.invert(int(a)) if a else 0
            quo=field.mul(int(z),inv)
            if label=="trace":
                expected.append(scalar_trace(field,quo))
            else:
                tower=sum(((row&inv).bit_count()&1)<<i for i,row in enumerate(tower_rows))
                expected.append(((int(m)&quo).bit_count()^(int(e)&tower).bit_count())&1)
        receipts=[]
        for seed in (91,1091):
            sim=km.Simulator(batch_size=len(u),seed=seed,counting_operations=True)
            sim.use_same_registers_as(tape)
            sim.write_across_shots(source,bits(u));sim.write_across_shots(numer,bits(v))
            if label!="trace":
                sim.write_across_shots(mult,bits(mu));sim.write_across_shots(add,bits(eta))
            sim.do(tape)
            assert np.array_equal(sim.read_across_shots(source),bits(u))
            assert np.array_equal(sim.read_across_shots(numer),bits(v))
            assert not sim.read_across_shots([km.q(i) for i in range(24,36)]).any()
            assert np.array_equal(sim.read_phase_flipped_across_shots(),expected)
            receipts.append(dict(shots=len(u),seed=seed,errors=0,
                                 mean_T=sim.operation_statistics().num_toffoli_like/len(u)))
        result[label]=dict(T=tape.operation_statistics().num_toffoli_like,scratch=12,trials=receipts)
    args.out.write_text(json.dumps(result,indent=2)+"\n")
    print(json.dumps(result))


if __name__=="__main__":
    main()
