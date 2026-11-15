#!/usr/bin/env python3
"""Replay the fixed paired inputs against the structurally repaired chart candidate."""
import argparse, hashlib, json, sys, time
from pathlib import Path

def digest(path):
    with Path(path).open('rb') as f: return hashlib.file_digest(f,'sha256').hexdigest()

def main():
    p=argparse.ArgumentParser();p.add_argument('--plan',type=Path,required=True);p.add_argument('--variant',choices=['chart_candidate'],required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
    plan=json.loads(a.plan.read_text());src=plan['variants'][a.variant]
    assert digest(src['path'])==src['sha256']
    assert digest(plan['verifier'])==plan['verifier_sha256']
    sys.path.insert(0,str(Path(plan['verifier']).parent))
    import kickmix as km
    import numpy as np
    import verify_submission_dqi as v
    spec=v.ProblemSpecDQI.benchmark_instance();tables=v.FieldTables(km.GF2Field(spec.degree))
    probs=v.optimal_dqi_weights(spec.m,spec.max_errors,spec.degree,spec.r)**2
    begun=time.monotonic(); circuit=km.Circuit.from_file(src['path'],format='kmb')
    S,E,A=v.validate_registers(circuit,spec); S_arr,E_arr=km.array(S),km.array(E)
    result={'variant':a.variant,'circuit_sha256':src['sha256'],'plan_sha256':digest(a.plan),'runner_sha256':digest(__file__),'verifier_sha256':plan['verifier_sha256'],'kickmix_sha256':digest(km.__file__),'batches':[],'failures':[]}
    for group in plan['groups']:
        seed=int(group['seed_sha256'],16)
        seeds=np.random.SeedSequence(seed,pool_size=8).generate_state(8*400,dtype=np.uint64).reshape(-1,2,4)
        for batch in group['batches']:
            rng_seed=int.from_bytes(seeds[batch,0],'little');sim_seed=int.from_bytes(seeds[batch,1],'little')
            syndromes,mbuc,phase=v.sample_shots(spec,tables,np.random.default_rng(rng_seed),256,probs)
            weights=np.random.default_rng(rng_seed).choice(len(probs),size=256,p=probs)
            sim=km.Simulator(batch_size=256,debug_print=False,counting_operations=True,seed=sim_seed)
            sim.use_same_registers_as(circuit); input_s=v.to_bits(syndromes,spec.degree); input_e=v.to_bits(mbuc,spec.degree)
            sim.write_across_shots(S_arr,input_s); sim.write_across_shots(E_arr,input_e);sim.do(circuit)
            output_s=sim.read_across_shots(S_arr); output_a=sim.read_across_shots(A); output_p=sim.read_phase_flipped_across_shots(); output_e=sim.read_across_shots(E_arr)
            delta_s=output_s^input_s;val=delta_s.any(axis=0)|output_a.any(axis=0);phase_err=(output_p^phase)&~val;classical_changed=(output_e^input_e).any(axis=0)
            h=lambda x:hashlib.sha256(x.tobytes()).hexdigest()
            row={'group':group['name'],'batch':batch,'input_syndromes_sha256':h(syndromes),'input_mbuc_sha256':h(mbuc),'expected_phase_sha256':h(phase),'output_syndromes_sha256':h(output_s),'output_ancillas_sha256':h(output_a),'output_phases_sha256':h(output_p),'output_mbuc_sha256':h(output_e),'value_errors':int(val.sum()),'phase_errors':int(phase_err.sum()),'classical_changed_shots':int(classical_changed.sum()),'toffolis':int(sim.operation_statistics().num_toffoli_like)}
            result['batches'].append(row)
            for s in np.flatnonzero(val|phase_err|classical_changed):
                result['failures'].append({'group':group['name'],'batch':batch,'shot_in_batch':int(s),'absolute_shot':batch*256+int(s),'sampled_error_weight':int(weights[s]),'rng_seed':rng_seed,'sim_seed':sim_seed,'value_error':bool(val[s]),'phase_error':bool(phase_err[s]),'classical_changed':bool(classical_changed[s]),'syndrome_difference_indices':np.flatnonzero(delta_s[:,s]).tolist(),'nonzero_ancillas':[str(A[i]) for i in np.flatnonzero(output_a[:,s])],'expected_phase':bool(phase[s]),'actual_phase':bool(output_p[s]),'input_syndromes':syndromes[s].tolist(),'input_mbuc':mbuc[s].tolist()})
            if group['name']!='independent' or batch%16==15:print(json.dumps({'variant':a.variant,'group':group['name'],'batch':batch,'value_errors':row['value_errors'],'phase_errors':row['phase_errors'],'elapsed_seconds':time.monotonic()-begun}),flush=True)
            del sim
    result.update(elapsed_seconds=time.monotonic()-begun,shots=256*len(result['batches']),value_errors=sum(x['value_errors'] for x in result['batches']),phase_errors=sum(x['phase_errors'] for x in result['batches']),classical_changed_shots=sum(x['classical_changed_shots'] for x in result['batches']),scope='Paired output equivalence and known-regression replay. Not a new leaderboard score or official default qualification.')
    a.out.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:result[k] for k in ['variant','shots','value_errors','phase_errors','classical_changed_shots','elapsed_seconds']}),flush=True)
if __name__=='__main__':main()
