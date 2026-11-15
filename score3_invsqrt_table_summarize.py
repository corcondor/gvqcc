#!/usr/bin/env python3
"""Freeze compact evidence from the bounded score3 integer-table experiment.

No circuit simulation or optimization is run here. Large exact predicate
bitsets stay in the work directory and are represented by SHA-256 hashes.
"""
from __future__ import annotations
import argparse,datetime,hashlib,json,platform,subprocess
from pathlib import Path
import numpy as np
import scipy
from score3_invsqrt_table_probe import MAX,PIN,ROOT,coefficient_values,extract_table,packing_violations

def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def write(path,value):path.write_text(json.dumps(value,indent=2)+'\n')

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--work',type=Path,required=True)
    p.add_argument('--prior-drop1',type=Path,default=ROOT.parent/'invsqrt_rearchitecture_phase_work/drop1')
    p.add_argument('--outdir',type=Path,default=ROOT)
    a=p.parse_args();a.outdir.mkdir(parents=True,exist_ok=True)
    out=a.outdir/'score3_invsqrt_table_result.json'
    if out.exists():raise FileExistsError(out)
    src=ROOT/'invsqrt_structural_e46.kmx';assert sha(src)==PIN
    table=extract_table(src.read_text().splitlines())
    write(a.outdir/'score3_invsqrt_integer_table.json',table)
    baseline=json.loads((a.work/'baseline.json').read_text())
    assert baseline['extraction']['base_D_mismatches']==0
    assert abs(baseline['fit']['margin_turns']-(-3.997656491185495e-12))<1e-24
    assert abs(baseline['fit']['max_error_ratio']-1.117288625616)<1e-12
    desc=json.loads((a.work/'basis.json').read_text())['basis']
    prior_desc=json.loads((a.prior_drop1/'basis.json').read_text())['basis']
    ids=[i for i,d in enumerate(prior_desc) if d['kind'] in ('rotation','phase_parity')]
    nw=(MAX+63)//64
    new=np.memmap(a.work/'baseline_drop1.basis.u64',mode='r',dtype='<u8',shape=(len(desc),nw))
    old=np.memmap(a.prior_drop1/'basis.u64',mode='r',dtype='<u8',shape=(len(prior_desc),nw))
    assert len(ids)==len(desc)==39
    for j,k in enumerate(ids):
        diff=new[j]^old[k];diff[-1]&=(1<<(MAX%64))-1
        assert not diff.any(),(j,k)
    trials=[]
    for name in ('probes.json','joint.json'):
        for t in json.loads((a.work/name).read_text())['trials']:
            row=t['row']
            da=t.get('delta_A',t.get('delta',0) if t.get('parameter')=='A' else 0)
            ds=t.get('delta_S',t.get('delta',0) if t.get('parameter')=='S' else 0)
            aa=table['A'].copy();ss=table['S'].copy();aa[row]+=da;ss[row]+=ds
            t.update(delta_A=da,delta_S=ds,
                     existing_shared_wire_chart_bad_rows=packing_violations(aa,ss),
                     candidate_D_truth_sha256=hashlib.sha256(coefficient_values(aa,ss).tobytes()).hexdigest(),
                     predicate_bitsets_sha256=sha(a.work/(t['name']+'.basis.u64')))
            assert t['extract']['inputs']==MAX and t['extract']['base_D_mismatches']==0
            assert t['fit']['gap_turns']<1e-17
            trials.append(t)
    assert len(trials)==16
    best=max(trials,key=lambda x:x['fit']['margin_turns'])
    cost_scope={
        'new_circuit_built':False,'new_official_verification':False,'public_submission':False,
        'achieved_arithmetic_toffoli_reduction':0,'achieved_qubit_reduction':0,
        'baseline_invsqrt_cost':78719.52914734723,'baseline_qubits':46,
        'baseline_raw_mean_toffoli':1479.7500405453395,
        'baseline_generic_rotations':33,'baseline_min_margin_turns':6.3057546380654306e-12,
        'first_loader_CCX_independently_counted':27,
        'second_loader_CCX_from_existing_provenance':29,
        'last_divider_forward_CCX_lines':[7548,7554,7559],
        'last_divider_inverse_CCX_lines':[8582,8589,8594],
        'last_divider_window_note':'Three CCX in each direction are a possible redesign target, NOT six achieved removable gates. Other remainder wires and deferred phase debts must be handled.',
        'same_33_rotation_synthesis_overhead_delta':'4.62 * log2(baseline_margin / candidate_positive_margin) Toffoli equivalents',
        'hypothetical_minimum_margin_if_net_arithmetic_saving_1':5.427240414577187e-12,
        'hypothetical_minimum_margin_if_net_arithmetic_saving_6':2.563238524178867e-12,
        'loader_constraint':'Both loads, high-bit packing identities and all HMR cleanup debts need resynthesis for modified tables. S +/-1 violates the existing packed chart in these rows.',
        'drop_constraint':'Setting q41=0 is a numerical intervention. It is not a reversible reset, a measurement-phase correction, or a coherent reduced divider. q41 and other wires are required again by uncompute.',
    }
    lines=src.read_text().splitlines()
    # Bind the quoted opportunity window to actual operations rather than an
    # estimated gate count detached from the circuit.
    for no in cost_scope['last_divider_forward_CCX_lines']+cost_scope['last_divider_inverse_CCX_lines']:
        assert lines[no-1].startswith('CCX '),(no,lines[no-1])
    result={
        'status':'COMPLETE_BOUNDED_NUMERICAL_SEARCH_NO_ACCEPTED_CANDIDATE',
        'source_kmx_sha256':PIN,'source_kmb_sha256':'e46d90c36d1beb3ce7731a3e0b5c3659b3cda7f5f290b73c6c34513d96c005b6',
        'domain':[1,MAX],
        'table_reconstruction':{'rows':64,'root_cases':4096,'all_signed_row_values_match':True,
                                'complete_input_prefix_D_mismatches':0},
        'positive_control':{'prior_full_circuit_predicates_equal':True,'predicate_functions':39,'inputs':MAX,
                            'prior_full_circuit_basis_sha256':sha(a.prior_drop1/'basis.u64'),
                            'new_prefix_basis_sha256':sha(a.work/'baseline_drop1.basis.u64'),
                            'prior_margin_and_ratio_reproduced':True},
        'baseline_drop1':baseline,
        'tested_rows':[43,45],'tested_neighborhood':'Each row independently: all eight nonzero (delta_A,delta_S) in {-1,0,1}^2. The two rows were not modified jointly.',
        'trial_count':len(trials),'feasible_count':sum(t['fit']['margin_turns']>0 for t in trials),
        'improved_over_unchanged_drop1':sum(t['fit']['margin_turns']>baseline['fit']['margin_turns'] for t in trials),
        'best_changed_table':{k:best[k] for k in ('name','row','delta_A','delta_S','fit')},
        'trials':trials,'cost_and_implementation_scope':cost_scope,
        'numerical_scope':'Exact Boolean predicates, long-double phase/reference sqrt and scaled float64 LP; no official integer-oracle positive acceptance is claimed.',
        'local_phase_angle_bounds_turns':[-1e-5,1e-5],
        'negative_scope':'Only the specified 16 one-row integer neighbors and existing 33 rotation sites; not a no-go for jointly changing many rows, different rounding, or different arithmetic.',
        'versions':{'python':platform.python_version(),'numpy':np.__version__,'scipy':scipy.__version__,
                    'gxx':subprocess.check_output(['g++','--version'],text=True).splitlines()[0]},
        'receipt_created_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
    }
    write(out,result)
    names=['score3_invsqrt_table_probe.py','score3_invsqrt_table_extract.cpp','score3_invsqrt_table_summarize.py',
           'score3_invsqrt_integer_table.json','score3_invsqrt_table_result.json','score3_invsqrt_table_report.md']
    files=[]
    for name in names:
        path=a.outdir/name
        if not path.exists():path=ROOT/name
        files.append({'path':name,'sha256':sha(path),'bytes':path.stat().st_size})
    write(a.outdir/'score3_invsqrt_table_manifest.json',{
        'scope':'Reproducible numeric probes; no accepted circuit and no Public Score update.',
        'source_kmx_sha256':PIN,'files':files,
        'large_intermediates':'Predicate bitsets, compiled extractor and per-trial roots are regenerated in the work directory and intentionally not published.',
        'reproduction_code_note':'Final code adds table-packing metadata checks to the executed numeric algorithm; arithmetic/LP routines and evaluated candidates are unchanged.',
    })
    print(json.dumps({'result':str(out),'trials':len(trials),'feasible':result['feasible_count'],
                      'best_changed_margin':best['fit']['margin_turns'],'new_circuit_built':False}))

if __name__=='__main__':main()
