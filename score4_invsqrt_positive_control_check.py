#!/usr/bin/env python3
"""Native check of the synthetic delayed-cleanup identity, not a benchmark gain."""
from pathlib import Path
import argparse,hashlib,importlib.util,json,sys
import numpy as np
import kickmix as km

def main():
    p=argparse.ArgumentParser();p.add_argument('--candidate',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
    base=Path(__file__).parent;source=base/'score4_invsqrt_positive_control.kmx'
    verifier=Path('/workspace/scratch/7f542e06b7cf/official_sources/Inzainos/verifiers/invsqrt/verify_submission_invsqrt.py')
    spec=importlib.util.spec_from_file_location('score4_control_verifier',verifier);module=importlib.util.module_from_spec(spec);sys.modules[spec.name]=module;spec.loader.exec_module(module)
    xs=np.arange(1,257,dtype=np.uint64)
    truth=(xs&1)&((xs>>1)&1)&((xs>>2)&1)
    expected=truth*np.uint64(module.half_turns_to_units(1));rows=[]
    for path in (source,a.candidate):
        circuit=km.Circuit.from_file(path);xr,scratch=module.validate_registers(circuit,module.ProblemSpecInvSqrt.for_n_p(10))
        for seed in (2026111504,2026111505):
            sim=km.Simulator(batch_size=len(xs),counting_operations=True,seed=seed)
            sim.use_same_registers_as(circuit);sim.write_across_shots(xr,module.to_bits(xs,22));sim.do(circuit)
            phase=np.array([module.half_turns_to_units(sim.read_shot_phase(i)) for i in range(len(xs))],dtype=np.uint64)
            row=dict(path=str(path),seed=seed,inputs=len(xs),input_restore_failures=int(np.count_nonzero(module.from_bits(sim.read_across_shots(xr))!=xs)),
                     dirty_scratch_failures=int(np.any(sim.read_across_shots(scratch),axis=0).sum()),phase_failures_against_exact_triple_product=int(np.count_nonzero(phase!=expected)),
                     static_toffoli=int(circuit.operation_statistics().num_toffoli_like),measured_mean_toffoli=sim.operation_statistics().num_toffoli_like/len(xs))
            assert row['input_restore_failures']==row['dirty_scratch_failures']==row['phase_failures_against_exact_triple_product']==0
            rows.append(row)
    report=dict(status='PASS',synthetic_control_only=True,invsqrt_benchmark_improvement=False,all_eight_relevant_input_patterns_covered=True,
                exact_phase='(-1)^(x0*x1*x2)',rows=rows,source_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),
                candidate_sha256=hashlib.sha256(a.candidate.read_bytes()).hexdigest(),script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
    a.out.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))

if __name__=='__main__':main()
