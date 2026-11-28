#!/usr/bin/env python3
"""Replay saved V110 legal regression inputs using pinned official helpers.

This is a targeted native replay, not a return from the full official verifier.
The regression corpus contains an intentionally included known failing input.
"""
import argparse, hashlib, importlib.util, json, resource, sys, time
from pathlib import Path
import kickmix as km
import numpy as np

def digest(path):
    with Path(path).open('rb') as f: return hashlib.file_digest(f,'sha256').hexdigest()

def main():
    p=argparse.ArgumentParser();p.add_argument('native');p.add_argument('fixture');p.add_argument('official');p.add_argument('out');p.add_argument('--seeds',type=int,default=3);a=p.parse_args()
    start=time.monotonic()
    assert digest(a.official)=='f14274bc0943fb9769ddb01131be6063191a15009fe1caf1d4bdd9fd25194e65'
    ms=importlib.util.spec_from_file_location('official_dqi',a.official);v=importlib.util.module_from_spec(ms);sys.modules[ms.name]=v;ms.loader.exec_module(v)
    data=np.load(a.fixture,allow_pickle=False);syndromes=data['syndromes'];masks=data['mbuc'];expected=data['phase'];shots=len(expected)
    circuit=km.Circuit.from_file(a.native,format='kmb');spec=v.ProblemSpecDQI.benchmark_instance(num_shots=shots)
    sregs,eregs,anc=v.validate_registers(circuit,spec);sarr=km.array(sregs);earr=km.array(eregs);qarr=km.array([km.q(i) for i in range(circuit.num_qubits)])
    inputs=v.to_bits(syndromes,12);classical=v.to_bits(masks,12)
    print(json.dumps({'event':'loaded','ops':len(circuit),'qubits':circuit.num_qubits,'seconds':time.monotonic()-start}),flush=True)
    runs=[]
    for n in range(a.seeds):
        seed=11120261127+n
        sim=km.Simulator(batch_size=shots,counting_operations=True,debug_print=False,seed=seed);sim.use_same_registers_as(circuit)
        sim.write_across_shots(sarr,inputs);sim.write_across_shots(earr,classical);sim.do(circuit)
        values=sim.read_across_shots(sarr);junk=sim.read_across_shots(anc);phase=sim.read_phase_flipped_across_shots();diff=values^inputs
        ve=diff.any(axis=0)|junk.any(axis=0);pe=(phase^expected)&~ve;rows=[]
        for j in np.flatnonzero(ve|pe):
            rows.append({'shot':int(j),'weight':int(data['weights'][j]),'syndrome_difference_count':int(diff[:,j].sum()),'dirty_ancilla_count':int(junk[:,j].sum()),'raw_phase_mismatch':bool(phase[j]^expected[j]),'value_error':bool(ve[j]),'counted_phase_error':bool(pe[j])})
        row={'seed':seed,'value_errors':int(ve.sum()),'counted_phase_errors':int(pe.sum()),'paid_total':int(sim.operation_statistics().num_toffoli_like),'failures':rows,'all_quantum_output_sha256':hashlib.sha256(sim.read_across_shots(qarr).tobytes()).hexdigest()}
        runs.append(row);print(json.dumps(row),flush=True)
    report={'status':'TARGETED_NATIVE_REGRESSION_REPLAY_COMPLETE','official_full_verifier_return':False,'population_failure_rate_estimate':False,'fixture_contains_known_failure':True,'shots':shots,'native_sha256':digest(a.native),'fixture_sha256':digest(a.fixture),'verifier_sha256':digest(a.official),'kickmix_sha256':digest(km.__file__),'ops':len(circuit),'qubits':circuit.num_qubits,'runs':runs,'seconds':time.monotonic()-start,'peak_rss_kib':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss}
    Path(a.out).write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({'status':report['status'],'seconds':report['seconds'],'peak_rss_kib':report['peak_rss_kib']}))
if __name__=='__main__':main()