#!/usr/bin/env python3
"""Native phase/value check for the hybrid tail state machine.

Pairs satisfy the exact admitted seam invariant: zero(raw numerator)=f_j,
zero(raw denominator)=f_(j-1), with no adjacent true flags. Normalization
by a unit preserves zero(v); a reversible placeholder occupies 24 helpers
at each arithmetic seam. This checks the controller and phase accounting,
not the full field arithmetic integration or the whole decoder's Q/T.
"""
from pathlib import Path
import hashlib
import json
import sys
import kickmix as km
import numpy as np
import score_ancilla_hybrid_tail as New

sys.path.insert(0,str(New.SOURCE/'after_c5/converter_width/tail_phase_defer'))
import rolling_tail_deferred as Old

N=17

def build(provider):
    b=km.CircuitBuilder()
    pairs=[(b.create_quantum_register(24,f'n{i}'),b.create_quantum_register(24,f'd{i}')) for i in range(N)]
    seed_n=b.create_quantum_register(12,'seed_n');seed_d=b.create_quantum_register(12,'seed_d')
    probes=[b.create_classical_register(24,f'probe{i}') for i in range(N)]
    data_count=b.num_allocated_qubits
    tail=provider.RollingTail(b,18,35)
    widths=[]
    def arithmetic_probe(index,direction):
        before=b.num_allocated_qubits
        temporary=b.alloc_qubits(24)
        b.cx(pairs[index][0],temporary);b.cx(pairs[index][0],temporary)
        widths.append(dict(index=index+18,direction=direction,live_controller_qubits=before-data_count,
                           allocated_peak_at_probe=b.num_allocated_qubits))
        b.free(temporary)
    for index,(num,den) in enumerate(pairs):
        token=tail.begin_slot(num,den,index+18)
        arithmetic_probe(index,'forward')
        tail.finish_slot(den,token)
        b.cz(probes[index],den)
    tail.release_spare()
    tail.seed_prefix(seed_n,seed_d)
    tail.seed_return(seed_n,seed_d)
    tail.resume_return()
    for index in reversed(range(N)):
        num,den=pairs[index]
        token=tail.begin_return(den,index+18)
        arithmetic_probe(index,'reverse')
        tail.finish_return(num,den,token)
    tail.close()
    assert b.num_allocated_qubits==data_count
    circuit=b.finish_circuit()
    return circuit,dict(Q=circuit.num_qubits,T=circuit.operation_statistics().num_toffoli_like,
                        operations=len(circuit),data_qubits=data_count,widths=widths)


def check(circuit,seed):
    # Every permitted flag string of length17 is included. Numerator and
    # denominator unit representatives are independently varied by seed.
    flags=np.array([v for v in range(1<<N) if not(v&(v<<1))],dtype=np.uint32)
    cases=len(flags);rng=np.random.default_rng(seed);arrays={};expected=np.zeros(cases,dtype=bool)
    def bits(values,width):return ((values[None,:]>>np.arange(width,dtype=np.uint32)[:,None])&1).astype(bool)
    for i in range(N):
        current=(flags>>i)&1;previous=(flags>>(i-1))&1 if i else np.zeros(cases,dtype=np.uint32)
        n=rng.integers(1,1<<24,cases,dtype=np.uint32);d=rng.integers(1,1<<24,cases,dtype=np.uint32)
        n[current.astype(bool)]=0;d[previous.astype(bool)]=0
        p=rng.integers(0,1<<24,cases,dtype=np.uint32)
        arrays[f'n{i}']=bits(n,24);arrays[f'd{i}']=bits(d,24);arrays[f'probe{i}']=bits(p,24)
        v=np.where(current.astype(bool),n,d) # selected v is raw n when current=1, raw d otherwise.
        expected^=np.logical_xor.reduce(bits(v&p,24),axis=0)
    arrays['seed_n']=bits(np.ones(cases,dtype=np.uint32),12)
    arrays['seed_d']=bits(np.zeros(cases,dtype=np.uint32),12)
    sim=km.Simulator(batch_size=cases,seed=seed,counting_operations=True)
    sim.use_same_registers_as(circuit)
    for name,value in arrays.items():sim.write_across_shots(circuit.register_data[name],value)
    sim.do(circuit)
    errors={name:int(np.count_nonzero(np.any(sim.read_across_shots(circuit.register_data[name])!=value,axis=0))) for name,value in arrays.items()}
    errors={k:v for k,v in errors.items() if v}
    phase_errors=int(np.count_nonzero(sim.read_phase_flipped_across_shots()!=expected))
    scratch_errors=bool(sim.read_across_shots([km.q(i) for i in range(840,circuit.num_qubits)]).any())
    assert not errors and not phase_errors and not scratch_errors,(errors,phase_errors,scratch_errors)
    return dict(seed=seed,cases=cases,data_errors=errors,phase_errors=phase_errors,scratch_errors=scratch_errors,
                observed_mean_T=sim.operation_statistics().num_toffoli_like/cases)


def main():
    files=[Path(__file__),Path(New.__file__),Path(Old.__file__),
           Path(New.Early.__file__),Path(__file__).with_name('score_ancilla_prefix_phase.py')]
    before={str(p.resolve()):hashlib.sha256(p.read_bytes()).hexdigest() for p in files}
    report=dict(status='RUNNING',scope=__doc__,source_sha256=before,rows=[])
    for label,provider in [('original',Old),('hybrid',New)]:
        circuit,metrics=build(provider)
        runs=[check(circuit,seed) for seed in (17011,17021,17027)]
        report['rows'].append(dict(name=label,metrics=metrics,runs=runs))
    assert report['rows'][0]['metrics']['T']==report['rows'][1]['metrics']['T']
    assert [r['live_controller_qubits'] for r in report['rows'][1]['metrics']['widths'][:N]]==[0]*(N-1)+[1]
    assert before=={str(p.resolve()):hashlib.sha256(p.read_bytes()).hexdigest() for p in files}
    report.update(status='PASS_ISOLATED_HYBRID_CONTROLLER',static_T_delta=0,
                  forward_arithmetic_stages_freed_of_flag=N-1,
                  whole_decoder_candidate=False,global_Q_reduction_established=False)
    path=Path(__file__).with_name('score_ancilla_hybrid_tail_result.json')
    path.write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({k:v for k,v in report.items() if k!='rows'},indent=2))
    for row in report['rows']:print(json.dumps(dict(name=row['name'],metrics={k:v for k,v in row['metrics'].items() if k!='widths'},runs=row['runs']),indent=2))

if __name__=='__main__':main()
