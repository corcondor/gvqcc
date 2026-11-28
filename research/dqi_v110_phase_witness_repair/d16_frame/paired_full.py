import sys,json
import numpy as np
import kickmix as km
from verify_submission_dqi import ProblemSpecDQI, FieldTables, sample_shots, validate_registers, to_bits
spec=ProblemSpecDQI.benchmark_instance()
rng=np.random.default_rng(20261128)
tables=FieldTables(km.GF2Field(spec.degree))
parts=[sample_shots(spec,tables,rng,120)]
for w in range(1,18):
    probs=np.eye(spec.max_errors+1)[w]
    parts.append(sample_shots(spec,tables,rng,8,probs))
synd,mask,expected=map(np.concatenate,zip(*parts))
n=len(synd)
sbits,mbits=to_bits(synd,spec.degree),to_bits(mask,spec.degree)
previous=None
for path in sys.argv[1:]:
    c=km.Circuit.from_file(path,format="kmb")
    q,b,a=validate_registers(c,spec)
    q,b=km.array(q),km.array(b)
    sim=km.Simulator(n,seed=81372471,debug_print=False,counting_operations=True)
    sim.use_same_registers_as(c)
    sim.write_across_shots(q,sbits);sim.write_across_shots(b,mbits)
    sim.do(c)
    data=[sim.read_across_shots(q),sim.read_across_shots(b),sim.read_across_shots(a),sim.read_phase_flipped_across_shots()]
    static=dict(c.operation_statistics()); dynamic=dict(sim.operation_statistics())
    row=dict(path=path,shots=n,Q=c.num_qubits,ops=len(c),static=static,
        dynamic=dynamic,value_errors=[int(x.sum()) for x in np.split((data[0]!=sbits).any(axis=0),[120])],
        raw_phase_errors=[int(x.sum()) for x in np.split(data[3]!=expected,[120])],
        ancilla_errors=int(data[2].any(axis=0).sum()),mask_errors=int((data[1]!=mbits).any(axis=0).sum()))
    if previous is not None:
        assert all(np.array_equal(x,y) for x,y in zip(data,previous)) 
        for op in ('CCX','CCZ','CSWAP'):assert dynamic.get(op,0)==prior_dyn.get(op,0)
        row['matched_fields']=4
    print(json.dumps(row),flush=True)
    previous=data;prior_dyn=dynamic
    del c,sim
