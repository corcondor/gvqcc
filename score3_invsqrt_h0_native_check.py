#!/usr/bin/env python3
"""Native randomized-measurement comparison of the concrete h0 candidate."""
from pathlib import Path
import argparse,hashlib,importlib.util,json,sys,time
import numpy as np
import kickmix as km

ROOT=Path('/workspace/scratch/7f542e06b7cf')


def main():
    p=argparse.ArgumentParser();p.add_argument('--candidate',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
    if a.out.exists():raise FileExistsError(a.out)
    t=time.monotonic()
    spec=importlib.util.spec_from_file_location('score3_official_invsqrt',ROOT/'official_sources/Inzainos/verifiers/invsqrt/verify_submission_invsqrt.py')
    module=importlib.util.module_from_spec(spec);sys.modules[spec.name]=module;spec.loader.exec_module(module)
    xs=np.unique(np.r_[np.arange(1,1025),np.linspace(1,3133452,1024,dtype=np.uint64),[2**i+d for i in range(1,22) for d in (-1,0,1) if 1<=2**i+d<=3133452]]).astype(np.uint64)
    sources=[ROOT/'dqi_inputs/invsqrt_e46d90c36d1b.kmb',a.candidate]
    rows=[];reference=None
    for path in sources:
        circuit=km.Circuit.from_file(path);xr,scratch=module.validate_registers(circuit,module.ProblemSpecInvSqrt.for_n_p(10))
        for seed in (2026111501,2026111502):
            sim=km.Simulator(batch_size=len(xs),debug_print=False,counting_operations=True,seed=seed)
            sim.use_same_registers_as(circuit);sim.write_across_shots(xr,module.to_bits(xs,22));sim.do(circuit)
            phase=np.array([module.half_turns_to_units(sim.read_shot_phase(i)) for i in range(len(xs))],dtype=np.uint64)
            if reference is None:reference=phase
            bad_input=int(np.count_nonzero(module.from_bits(sim.read_across_shots(xr))!=xs))
            bad_scratch=int(np.any(sim.read_across_shots(scratch),axis=0).sum())
            bad_phase=int(np.count_nonzero(reference!=phase))
            row=dict(path=str(path),seed=seed,inputs=len(xs),qubits=circuit.num_qubits,
                     restored_input_failures=bad_input,dirty_scratch_failures=bad_scratch,
                     phase_mismatches_against_baseline=bad_phase,
                     measured_mean_toffoli=sim.operation_statistics().num_toffoli_like/len(xs))
            rows.append(row);print(json.dumps(row),flush=True)
            if bad_input or bad_scratch or bad_phase:raise AssertionError(row)
    record=dict(status='NATIVE_COMPARISON_PASS',rows=rows,candidate_sha256=hashlib.sha256(a.candidate.read_bytes()).hexdigest(),
                source_sha256=hashlib.sha256(sources[0].read_bytes()).hexdigest(),
                exact_full_domain_patch_proof_is_separate=True,full_official_200540928_shots_run=False,
                whole_Q45=False,score_improvement_claimed=False,seconds=time.monotonic()-t,
                script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
    a.out.write_text(json.dumps(record,indent=2)+'\n')


if __name__=='__main__':main()
