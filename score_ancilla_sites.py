#!/usr/bin/env python3
"""Map audited GF24 templates to actual consuming arithmetic sites.

Uses the existing full exact-template match certificate. No simulator or
reset-interval inference is needed to identify rolling-flag source sites.
Classification is checked against the exact direct-carry loops and ABI
word addresses: head_i=q[24*i:24*(i+1)], carry=q[840:864]. The public source
cutoff in the actual candidate is18. All untouched data and source hashes
are recorded for reproducibility.
"""
from collections import Counter
import hashlib
import json
from pathlib import Path

HERE=Path(__file__).resolve().parent
SOURCE=HERE.parent/'official_sources/Syed_v12/source/dqi_source/src/controller_work'
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()

def main():
    manifest=json.loads((HERE/'theory_bilinear_full_build.json').read_text())
    certificate=json.loads((HERE/'inverse_v2_actual_eea_product_certificate.json').read_text())
    rows=[]
    for block in manifest['blocks']:
        if block['template']!='gf24_multiplication':continue
        m=block['wire_mapping']
        output=[m[str(q)] for q in certificate['output_qubits_in_field_order']]
        if min(output)<864:continue
        left=[m[str(q)] for q in certificate['input_left']]
        right=[m[str(q)] for q in certificate['input_right']]
        row=dict(start=block['start'],end=block['end'],left=left,right=right,output=output,
                 inherited_condition_stack_depth=block['inherited_condition_stack_depth'])
        # Three disjoint regions are checked by exact addresses and expected
        # complete slot sets below. Boundaries are tape coordinates in e986.
        if block['start']<25000000:
            row['group']='direct_prefix'
            row['operation']='adjoint_consume' if right==list(range(840,864)) else 'input_scale'
            word=left if row['operation']=='adjoint_consume' else right
            assert word==list(range(word[0],word[0]+24)) and word[0]%24==0
            assert (right if row['operation']=='adjoint_consume' else left)==list(range(840,864))
            row['slot']=word[0]//24
            row['rolling_flag_live']=(row['slot']>=18 if row['operation']=='adjoint_consume' else row['slot']>=19)
            row['hybrid_rolling_flag_live']=row['operation']=='adjoint_consume' and row['slot']==34
        elif block['start']>47300000:
            row['group']='direct_return'
            assert left==list(range(left[0],left[0]+24)) and left[0]%24==0
            row['slot']=left[0]//24
            row['operation']='head_restore' if right==list(range(840,864)) else 'next_adjoint_consume'
            if row['operation']=='next_adjoint_consume':assert right==list(range(left[0]+24,left[0]+48))
            row['rolling_flag_live']=row['hybrid_rolling_flag_live']=row['slot']>=18
        else:
            row.update(group='middle_other',operation='other_consuming',slot=None,
                       rolling_flag_live=False,hybrid_rolling_flag_live=False)
        rows.append(row)
    for group,operation,expected in [
        ('direct_prefix','adjoint_consume',list(range(3,35))),
        ('direct_prefix','input_scale',list(range(4,35))),
        ('direct_return','head_restore',list(range(3,35))),
        ('direct_return','next_adjoint_consume',list(range(3,34)))]:
        assert sorted(r['slot'] for r in rows if r['group']==group and r['operation']==operation)==expected
    assert len(rows)==192
    total_original=sum(r['rolling_flag_live'] for r in rows)
    total_hybrid=sum(r['hybrid_rolling_flag_live'] for r in rows)
    assert total_original==66 and total_hybrid==34
    t=382115.5671582031;q=889;budget=t*((q/(q-1))**2-1)
    source_files=['after_c5/extractor_width/direct_carry_extractor.py',
       'after_c5/extractor_width/direct_carry_arithmetic.py',
       'after_c5/extractor_width/rolling_tail_early.py',
       'after_c5/converter_width/tail_phase_defer/rolling_tail_deferred.py',
       'after_v3/k24/last_return_retained_norm.py']
    result=dict(status='EXACT_TAPE_MATCH_AND_SOURCE_SCHEDULE_COUNTS',input_sha256=manifest['input_sha256'],
      template_manifest_sha256=digest(HERE/'theory_bilinear_full_build.json'),
      source_sha256={p:digest(SOURCE/p) for p in source_files},
      all_rank99_templates=1376,consuming_output_entirely_in_q864_to_q888=len(rows),
      source_groups=dict(Counter(r['group'] for r in rows)),
      rolling_flag_consuming_original=total_original,rolling_flag_consuming_hybrid=total_hybrid,
      original_forward=33,original_reverse=33,hybrid_forward=1,hybrid_reverse=33,
      budget_for_Q888=budget,max_added_T_per_site_original=budget/total_original,
      max_added_T_per_site_hybrid=budget/total_hybrid,
      hybrid_24_extra_T_each=dict(extra_T=34*24,residual_budget=budget-34*24,
                                 optimistic_cost_ratio=(888/889)**2*(t+34*24)/t),
      additional_24_helper_kernels_remaining_in_hybrid_tail={
        'inverse_norm_with_12_live_norm_plus_12_nested_helpers':18,
        'consume_halves_with_12_live_reciprocal_norm_plus_12_temporary':17,
        'GF12_consuming_products_inside_those_half_calls':34},
      limitations=[
        'The 66 middle consuming-output blocks concern other gauge/finish/synthesis operations; they are not covered by this rolling-tail change.',
        '18 norm inversions and 17 half-consume calls still reach24 helpers with a live rolling flag. Narrowing GF24 multipliers alone does not reduce global Q.',
        'Early chart and seed/converter peaks also require separate allocation proof.',
        'No 23-helper consuming multiplier has been synthesized or verified here.',
        'The listed per-site overhead is a global optimistic budget, not an achieved score.'],rows=rows)
    (HERE/'score_ancilla_consuming_sites.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k not in ('rows','source_sha256')},indent=2))

if __name__=='__main__':main()
