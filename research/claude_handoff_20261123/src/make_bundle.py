#!/usr/bin/env python3
"""Build self-contained GVQCC global angle-table research bundle with SHA manifests."""
from __future__ import annotations
import json,hashlib,zipfile,os,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parent
OUTPUT=Path('/mnt/data/GVQCC_20261123_GLOBAL_ANGLE_GAUGE_JOINT_PHYSICS_REAL_KMBS_RESEARCH_UNVERIFIED.zip')
paths={}
def add(target,source):
    p=ROOT/source
    if not p.is_file():raise FileNotFoundError(p)
    assert target not in paths,(target,p)
    paths[target]=p

def filesglob(target,source,pattern):
    d=ROOT/source
    v=sorted(d.glob(pattern))
    assert v,(d,pattern)
    for p in v:
        if p.is_file():add(f'{target}/{p.name}',p.relative_to(ROOT))

add('README_JA.md','README_JA.md');add('REPRODUCE.sh','REPRODUCE.sh')
for s in ['make_bundle.py','affine_sign_zero_t_gauge.py','verify_affine_zero_t.py','givens_gauge_global.py','givens_gauge_tree_dp.py',
    'global_reindex_search.py','joint_toposort_dp.py','highbit_gauge_dp.py','signed6_constraint_rank.py',
    'signed6_coset_gauge.py','joint_gauge_search.py','compile_gauge_partial.py','compile_experiments.py',
    'compile_best_seed.py','verify_exact_ir.py','qhdl_kmb.py','c46_to_c45_sameKMB.py']:
    add(f'src/{s}',s)
for s in ['qhdl_kmb.py','angle_full_truth.py','chemistry_j_scheduler.py','compile_angle_signed_core.py','tensorqrom.py']:
    add('src/axis_old/src/'+s,'axis_old/src/'+s)
add('src/longtrain/physical_verify.py','longtrain/physical_verify.py')
add('src/longtrain/data/chem_gpu_inputs.npz','chem_gpu_inputs.npz')
add('inputs/V8_C46_ORIGINAL.npz','V8_C46_ORIGINAL.npz')
add('inputs/C45_B129_JACOBI_OPTIMIZED.npz','C45_B129_JACOBI_OPTIMIZED.npz')
filesglob('inputs/public3357','public3357','candidate_angle_k_*.kmb')
filesglob('inputs/c45_bestseed','c45_bestseed_public','candidate_angle_k_*.kmb')
for candidate,source in [('I_affine_3357','affine_zeroT_wide'),('J_C45_joint','c45_joint_affine_C_gauge')]:
    for s in ['submission.npz','build_receipt.json']:
        add(f'candidates/{candidate}/{s}',f'{source}/{s}')
    receipt='verify_all_clean.json' if candidate.startswith('I') else 'verify_all.json'
    add(f'candidates/{candidate}/{receipt}',f'{source}/{receipt}')
    filesglob(f'candidates/{candidate}/circuits',f'{source}/circuits','angle_k_*.kmb')
add('candidates/G_global_fold/fold_value.npz','gauges/fold_value.npz')
add('candidates/G_global_fold/verify_full.json','compiled_foldvalue_15/verify_full.json')
filesglob('candidates/G_global_fold/circuits','compiled_foldvalue_15','angle_k_*.kmb')
add('candidates/H_global_dp/bitplane_6.npz','dp_gauges/bitplane_6.npz')
add('candidates/H_global_dp/verify_exact.json','compiled_dp6_0_4/verify_exact.json')
filesglob('candidates/H_global_dp/circuits','compiled_dp6_0_4','angle_k_*.kmb')
add('candidates/S6_coset/signed6_fixed_2.npz','signed6_cosets/signed6_fixed_2.npz')
add('candidates/S6_coset/verify_exact.json','compiled_s6_fixed2_first3/verify_exact.json')
filesglob('candidates/S6_coset/circuits','compiled_s6_fixed2_first3','angle_k_*.kmb')
for target,src in [
 ('experiments/G_global_fold_search_report.json','gauges/landscape_report.json'),
 ('experiments/H_gauge_dp_report.json','dp_gauges/dp_report.json'),
 ('experiments/S6_coset_report.json','signed6_cosets/coset_report.json'),
 ('experiments/R_B_90_global_reindex_report.json','reindexed/reindex_results.json'),
 ('experiments/tree_topological_48_report.json','joint_topo/joint_toposort_results.json'),
 ('experiments/C46_W_H2_orthogonal_report.json','c46_gauge/orthogonal_gauge_result.json'),
 ('experiments/C45_W_H2_orthogonal_report.json','c45_gauge/orthogonal_gauge_result.json'),
 ('experiments/reference_3357_full_validation.json','independent_full_3357_exact.json'),
 ('experiments/reference_3357_dirty_initial_failure.log','baseline_reference_3357/dirty_original_failure.log'),
]:add(target,src)
add('experiments/C45_W_H2_orthogonal_candidate.npz','c45_gauge/C45_B129_JACOBI_OPTIMIZED_C_ORTHOGONAL_GAUGE_6_42.npz')
# Inputs/candidate readback preconditions
assert len([x for x in paths if x.startswith('candidates/I_affine_3357/circuits/')])==15
assert len([x for x in paths if x.startswith('candidates/J_C45_joint/circuits/')])==15
assert len([x for x in paths if x.startswith('candidates/G_global_fold/circuits/')])==15

receiptI=json.loads((ROOT/'affine_zeroT_wide/build_receipt.json').read_text())
receiptJ=json.loads((ROOT/'c45_joint_affine_C_gauge/build_receipt.json').read_text())
receiptG=json.loads((ROOT/'compiled_foldvalue_15/verify_full.json').read_text())
receiptH=json.loads((ROOT/'compiled_dp6_0_4/verify_exact.json').read_text())
receiptS=json.loads((ROOT/'compiled_s6_fixed2_first3/verify_exact.json').read_text())
scorecard={
 'date':'2026-11-23','run_class':'RESEARCH_UNVERIFIED','native_KickMix_executed':False,
 'reference_scores':{'user_previous_33p13521306472748':33.13521306472748,'public_33p17023':33.17023},
 'new_official_verified_score':None,
 'new_official_verified_improvements':0,
 'required_independent_official_improvements':3,
 'candidates':{
  'G_global_fold':{'angle_words_changed':52591,'all_banks_generated':True,'total_one_pass_T':receiptG['total_pass_T'],'max_loader_Q':receiptG['maxQ'],'phase_value_workspace_local_pass':bool(receiptG['all_pass']),'physical_feasible_independent_model':True,'official_KickMix':False,'score_gain':None,'status':'higher T than 3357'},
  'H_global_dp':{'angle_words_changed':57590,'tested_banks':receiptH['banks'],'tested_bank_T':receiptH['total_pass_T'],'published_comparison_T_same_banks':1136,'phase_value_workspace_local_pass':bool(receiptH['all_pass']),'official_KickMix':False,'score_gain':None,'status':'noncompetitive / incomplete 15-banks'},
  'S6_coset':{'tested_banks':receiptS['banks'],'tested_bank_T':receiptS['total_pass_T'],'backend_matched_baseline_T':840,'official_KickMix':False,'score_gain':None,'status':'negative in 3-bank synthesis'},
  'I_affine_3357':{'angle_words_changed':receiptI['angle_word_changes'],'total_one_pass_T':receiptI['modified_total_Toffoli'],'max_loader_Q':receiptI['max_qubits'],'added_CX':receiptI['total_new_CX'],'added_X':receiptI['total_new_X'],'physical':receiptI['new_phys'],'all_15_banks_local_clean_phase_value_workspace':True,'arbitrary_dirty_word_contract':False,'official_KickMix':False,'score_gain':None,'status':'nonlocal equivalent reparameterization with no measured T gain'},
  'J_C45_joint':{'angle_words_changed':receiptJ['angle_word_changes'],'total_one_pass_T':receiptJ['modified_total_Toffoli'],'max_loader_Q':receiptJ['max_qubits'],'added_CX':receiptJ['total_new_CX'],'added_X':receiptJ['total_new_X'],'physical':receiptJ['new_phys'],'all_15_banks_local_clean_phase_value_workspace':True,'arbitrary_dirty_word_contract':False,'official_KickMix':False,'score_gain':None,'status':'physical lambda slightly lower; chemistry cost still worse than C46'}
 },
 'limitations':[
  'No native KickMix/official Kaggle verifier installed; cannot promote local tests to official score.',
  'Public V8 backend and conjugated version fail randomized dirty word input for bank1, as documented. Only clean sequential initial-word-zero path was proven for I/J.',
  'Physical errors are reproduced by independent FeMoCo numpy/scipy model, not official validator.',
  'H and S6 are partial-bank negative tests; their full 15-bank cost cannot be imputed.'
 ]
}
scorefile=ROOT/'scorecard_UNVERIFIED.json';scorefile.write_text(json.dumps(scorecard,indent=2,ensure_ascii=False)+'\n');add('scorecard_UNVERIFIED.json','scorecard_UNVERIFIED.json')
manifest={target:{'source_relative_path':str(p.relative_to(ROOT)),'size':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for target,p in sorted(paths.items())}
manifestfile=ROOT/'SHA256_MANIFEST.json';manifestfile.write_text(json.dumps({'sha256_method':'file bytes as stored before zip compression','items':manifest},indent=2,ensure_ascii=False)+'\n')
paths['SHA256_MANIFEST.json']=manifestfile
with zipfile.ZipFile(OUTPUT,'w',zipfile.ZIP_DEFLATED,compresslevel=5,allowZip64=True) as archive:
 for target,p in sorted(paths.items()):archive.write(p,arcname=target)
with zipfile.ZipFile(OUTPUT) as archive:
 assert archive.testzip() is None
 assert len(archive.namelist())==len(paths)
 for target,info in manifest.items():
    data=archive.read(target)
    assert hashlib.sha256(data).hexdigest()==info['sha256']
print(json.dumps({'zip_path':str(OUTPUT),'sha256':hashlib.sha256(OUTPUT.read_bytes()).hexdigest(),'files':len(paths),'bytes':OUTPUT.stat().st_size,'total_one_pass_T':{'I':receiptI['modified_total_Toffoli'],'J':receiptJ['modified_total_Toffoli'],'G':receiptG['total_pass_T'],'H_partial':receiptH['total_pass_T'],'S_partial':receiptS['total_pass_T']},'official_score_verified':False},indent=2))