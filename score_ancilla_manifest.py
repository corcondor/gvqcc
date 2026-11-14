#!/usr/bin/env python3
"""Inventory for the isolated ancilla study; no full decoder build or simulation."""
import hashlib
import importlib.metadata
import json
from pathlib import Path
import sys

HERE=Path(__file__).resolve().parent
SOURCE=HERE.parent/'official_sources/Syed_v12/source/dqi_source/src/controller_work'

def digest(path):
    h=hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda:stream.read(4<<20),b''):h.update(chunk)
    return h.hexdigest()

def record(path):return dict(path=str(path.resolve()),bytes=path.stat().st_size,sha256=digest(path))

def main():
    # Build only the small isolated controller to observe its actual imports.
    # This is not an additional native test or a full decoder build.
    import score_ancilla_hybrid_tail_check as Check
    Check.build(Check.Old);Check.build(Check.New)
    imports={}
    for name,module in list(sys.modules.items()):
        filename=getattr(module,'__file__',None)
        if not filename:continue
        path=Path(filename).resolve()
        if path.suffix=='.py' and path.is_relative_to(SOURCE):
            item=imports.setdefault(str(path),dict(**record(path),modules=[]))
            item['modules'].append(name)
    files=[p for p in sorted(HERE.glob('score_ancilla_*')) if p.is_file() and p.name!='score_ancilla_manifest.json']
    dependencies=[HERE/p for p in ['kmb_profile.py','test_scratch_audit.py',
        'dqi_ccx_input_factor.py','dqi_ccx_peephole.py','theory_bilinear_full_build.json',
        'inverse_v2_actual_eea_product_certificate.json']]
    baseline=HERE.parent/'dqi_inputs/821_ccx480_gauge128.kmb'
    compact=Path('/workspace/scratch/3815fb5fae06/bilinear_runs/dqi_cpr_compact.kmb')
    baseline_record=record(baseline);compact_record=record(compact)
    assert baseline_record['sha256']=='e986d41663fa78ea2ed4ab0a47ebc4d99441ad1660b80e02872e7508cbce92a7'
    assert compact_record['sha256']=='3dfa80eb777a55659dcc143466d22427ccf278e198b720f24009cc921747bbcc'
    report=dict(status='COMPLETE_ISOLATED_ANCILLA_STUDY_NO_WHOLE_SCORE_CLAIM',
       measured_or_proven=dict(whole_tape_symbolic_instructions=49477357,new_CCX_merges=0,
         new_Toffoli_simplifications=0,symbolic_scratch_peak_bound=49,
         hybrid_controller_static_T_delta=0,forward_arithmetic_flag_lifetimes_removed=16,
         rolling_flag_consuming_sites_before=66,rolling_flag_consuming_sites_after_hybrid=34,
         prefix_phase_bilinear_coefficients_checked=289,
         hybrid_flag_sequences_per_seed=4181,hybrid_native_seeds=3),
       not_established=['Global Q reduction','Whole-decoder T reduction','Whole-decoder equivalence of an emitted new tape',
                        'Competition score improvement','General active Nzero/Dzero chart repair',
                        'A 23-helper consuming multiplier'],
       inputs=[baseline_record,compact_record],files=[record(p) for p in files],
       direct_existing_dependencies=[record(p) for p in dependencies],
       native_source_import_inventory=list(imports.values()),
       runtime=dict(python=sys.version,kickmix=importlib.metadata.version('kickmix'),
                    numpy=importlib.metadata.version('numpy'),cpp='C++17; g++ -O3 -std=c++17'),
       scratch_only_artifacts=[dict(path='/workspace/scratch/3815fb5fae06/score_ancilla_semantic',role='Rebuildable C++ executable'),
          dict(path='/workspace/scratch/3815fb5fae06/score_ancilla_postcpr_ccx.kmb',role='Unchanged byte-identical copy after zero-merge scan',sha256=compact_record['sha256'])],
       external_branch_reports_read_not_modified=['dqi_rare_chart_v2_report.md',
          'results/2026-11-15/kaggle_v2_submission_complete.json'],
       main_report='score_ancilla_report.md',
       reproduction=['g++ -O3 -std=c++17 score_ancilla_semantic.cpp -o /workspace/scratch/3815fb5fae06/score_ancilla_semantic',
          'python3 score_ancilla_semantic_check.py',
          'kickmix_venv/bin/python score_ancilla_prefix_phase.py',
          'kickmix_venv/bin/python score_ancilla_hybrid_tail_check.py',
          'python3 score_ancilla_sites.py'])
    (HERE/'score_ancilla_manifest.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(dict(status=report['status'],files=len(files),source_imports=len(imports),
                         input_hashes=[r['sha256'] for r in report['inputs']]),indent=2))

if __name__=='__main__':main()
