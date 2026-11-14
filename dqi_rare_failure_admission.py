#!/usr/bin/env python3
"""Classify two pre-existing DQI failure fixtures; no circuit or new sample run.

Only replays the saved input-generation state to recover physical errors.
No circuit mutation, seed/hash search, or quantum simulation is performed.
"""
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import time
import numpy as np

root=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(root/'official_sources/Inzainos/verifiers/dqi'))
import kickmix as km
import verify_submission_dqi as V
refpath=root/'official_sources/Syed_v12/source/dqi_source/src/controller_work/night_c27/census/reference.py'
ms=importlib.util.spec_from_file_location('c27_admission_reference',refpath)
C=importlib.util.module_from_spec(ms);ms.loader.exec_module(C)
spec=V.ProblemSpecDQI.benchmark_instance()
tables=V.FieldTables(km.GF2Field(spec.degree))
prob=V.optimal_dqi_weights(spec.m,spec.max_errors,spec.degree,spec.r)**2
start=time.monotonic();records=[]
for name in ['gvqcc_repo/dqi_gauge_dynamic32_failure_localization.json','dqi_inputs/baseline_821_candidate_failure_replay.json']:
 path=root/name;report=json.loads(path.read_text())
 seeds=np.random.SeedSequence(report['base_seed'],pool_size=8).generate_state(8*400,dtype=np.uint64).reshape(-1,2,4)
 for f in report['failures']:
  batch=f['batch_index'];target=f['shot_in_batch']
  rng=np.random.default_rng(int.from_bytes(seeds[batch,0],'little'))
  weights=rng.choice(len(prob),size=256,p=prob)
  masks=rng.integers(0,4095,size=(256,4095),endpoint=True,dtype=np.int64)
  for shot in np.flatnonzero(weights):
   weight=int(weights[shot]);positions=rng.choice(spec.m,size=weight,replace=False)
   values=rng.integers(1,4095,size=weight,endpoint=True,dtype=np.int64)
   if shot==target:break
  assert shot==target and weight==f['sampled_error_weight']
  exps=(tables.log[values][None,:]+np.arange(1,71)[:,None]*positions[None,:])%4095
  syndromes=np.bitwise_xor.reduce(tables.antilog[exps],axis=1)
  assert syndromes.tolist()==f['input_syndromes']
  assert masks[target].tolist()==f['input_mbuc']
  phase=sum(int(x).bit_count() for x in values&masks[target,positions])&1==1
  assert phase==f['expected_phase']
  roots=tables.antilog[positions].astype(int).tolist();values=values.astype(int).tolist()
  # Independently reconstruct all70 syndromes using the classifier field.
  independent=[]
  for degree in range(1,71):
   total=0
   for a,e in zip(roots,values):
    power=1
    for _ in range(degree):power=C.mul(power,a)
    total^=C.mul(e,power)
   independent.append(total)
  assert independent==f['input_syndromes']
  classification=C.classify(roots,values,include_polynomials=True)
  # Capture the exact current polynomials at the first excluded quadratic node.
  n,d=C.physical_pair(roots,values);node_trace=[]
  for node in range(weight):
   nr=C.quadratic_remainder(n,C.KAPPAS[node]);dr=C.quadratic_remainder(d,C.KAPPAS[node])
   row=dict(node=node,numerator_degree=len(n)-1,denominator_degree=len(d)-1,numerator_remainder=list(nr),denominator_remainder=list(dr),kappa=C.KAPPAS[node])
   node_trace.append(row)
   if nr==(0,0) or dr==(0,0):
    row.update(numerator=n,denominator=d);break
   head=C.quadratic_div(dr,nr,C.KAPPAS[node]);child,remainder=C.divrem(C.add(d,C.product(head,n)),C.QUADRATICS[node])
   assert not remainder
   n,d=child,n
  case_sha=hashlib.sha256(json.dumps({'roots':roots,'values':values},sort_keys=True,separators=(',',':')).encode()).hexdigest()
  records.append(dict(case_sha256=case_sha,fixture=name,fixture_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),baseline_circuit=report['circuit_sha256'],batch=batch,shot_in_batch=target,absolute_shot=f['absolute_shot'],input_verified_all70_syndromes_all4095_masks_and_phase=True,independent_field_syndromes_verified=True,positions=positions.astype(int).tolist(),roots=roots,values=values,classification=classification,node_trace=node_trace))
print(json.dumps(dict(status='EXACT_EXISTING_FAILURE_FIXTURES_CLASSIFIED',classifier_path=str(refpath.relative_to(root)),classifier_sha256=hashlib.sha256(refpath.read_bytes()).hexdigest(),verifier_sha256=hashlib.sha256(Path(V.__file__).read_bytes()).hexdigest(),records=records,elapsed_seconds=time.monotonic()-start,scope='Two known regression fixtures only; no population failure-rate estimate, no new quantum simulation, no candidate repair.'),indent=2))
