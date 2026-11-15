#!/usr/bin/env python3
"""Scoped public4030 audit and previously excluded batch-0 segment screen.

The already exhausted joint-product searches on batches 1..14 are not rerun.
Only their eligibility counts are read for the new exact public4030 inputs.
Batch 0 is split at nonlinear control updates or measurement boundaries; each
remaining linear-control block is checked for the three elementary sharing
classes. No operation is moved across a boundary and no candidate is emitted.
"""
import collections,hashlib,json,math,time
from pathlib import Path
import kickmix as km
from chemistry_joint_product_resynthesis import DATA_INDEX,extract,keys,classify
from chemistry_affine_span_resynthesis import parse_line

HERE=Path(__file__).resolve().parent
SOURCE=HERE.parent/'inputs/public_v27/dfthcsos'
PINS=json.loads((HERE/'outcome_v27_public_pins.json').read_text())['members']

def eligibility(terms):
    control=collections.Counter(v for a,b,w in terms for v in (a,b))
    output=collections.Counter(w for a,b,w in terms)
    shared=collections.Counter(k for term in terms for k in keys(term))
    degenerate=sum(classify(term)[0]!='quadratic' for term in terms)
    return dict(products=len(terms),distinct_control_forms=len(control),
      distinct_output_directions=len(output),repeated_control_form_groups=sum(v>1 for v in control.values()),
      repeated_output_direction_groups=sum(v>1 for v in output.values()),
      two_shared_factor_groups=sum(v>1 for v in shared.values()),
      degenerate_products=degenerate,
      elementary_search_eligible=bool(degenerate) or any(v>1 for v in control.values()) or any(v>1 for v in output.values()))

def main():
    started=time.monotonic();rows=[];batch0=None
    for k in range(15):
        path=SOURCE/f'angle_k_{k}.kmb';digest=hashlib.sha256(path.read_bytes()).hexdigest()
        assert digest==PINS['dfthcsos/'+path.name]['sha256']
        c=km.Circuit.from_file(path)
        row=dict(k=k,sha256=digest,CCX=int(c.operation_statistics().num_toffoli_like),qubits=c.num_qubits)
        if k:
            e=extract(c);row['core']=eligibility(e['terms']);row['exhaustive_old_search_rerun']=False
        else:batch0=c
        rows.append(row)
    lines=str(batch0).splitlines();parsed=[parse_line(l) for l in lines]
    core=[i for i,(g,q,condition) in enumerate(parsed) if g=='CCX' and q[-1] in DATA_INDEX]
    lo,hi=min(core),max(core)+1;boundaries=[]
    for i in range(lo,hi):
        g,q,condition=parsed[i]
        blocked=(condition is not None or g not in ('X','CX','CCX') or
                 g=='CCX' and q[-1] not in DATA_INDEX or
                 g=='CX' and q[0] in DATA_INDEX and q[1] not in DATA_INDEX)
        if blocked:boundaries.append(i)
    starts=[lo]+[i+1 for i in boundaries];ends=boundaries+[hi];segments=[]
    for a,b in zip(starts,ends):
        if a>=b or not any(a<=i<b for i in core):continue
        sub=km.Circuit('\n'.join(lines[a:b])+'\n');e=extract(sub)
        report=eligibility(e['terms']);report.update(first_operation=a,last_operation_exclusive=b)
        # With no common control or output direction, no first flip exists in
        # the stated algebraic class; running a quadratic pair loop is redundant.
        report['elementary_reduction_found']=False
        segments.append(report)
    assert sum(s['products'] for s in segments)==len(core)
    if any(s['elementary_search_eligible'] for s in segments):
        raise RuntimeError('Eligible block requires an actual search; do not claim a negative result')
    reference_score=27.31512;T=14722
    thresholds=[]
    for increase in (.001,.01,.1,.5):
        delta=math.ceil(T*(1-(reference_score/(reference_score+increase))**3)/2)
        thresholds.append(dict(target_total_score_increment=increase,
          minimum_loader_CCX_perpass_removed_at_fixed_lambda_Q_and_other_tasks=delta))
    result=dict(status='NO_NEW_ELEMENTARY_MERGE_IN_PREVIOUSLY_EXCLUDED_BATCH0_SEGMENTS',
      scope='Exact pinned public4030; k>=1 eligibility audit only; batch0 independent segments between nonlinear/measurement boundaries',
      total_loader_CCX=sum(r['CCX'] for r in rows),rows=rows,
      batch0_newly_screened_output_products=len(core),batch0_segments=segments,
      batch0_boundaries=[dict(operation=i,line=lines[i]) for i in boundaries],
      total_task_T=T,total_task_Q=427,
      one_loader_CCX_removed_gives_task_T_reduction=2,
      one_loader_CCX_removed_chemistry_reduction_percent=100*2/T,
      one_loader_CCX_removed_geomean_score_increment=reference_score*((T/(T-2))**(1/3)-1),
      thresholds_at_fixed_lambda_Q_and_other_tasks=thresholds,
      limits=['Not a global synthesis lower bound','Does not exclude multi-step cost-neutral rewrites, new shared nonlinear products, or coherent encoded-output redesign',
              'Cross-batch scratch reuse is not emitted: each ANGLE call must restore zero scratch, and separate calls include intervening Givens rotations'],
      emitted_candidate=False,new_gate_reduction=0,official_verifier_run=False,
      seconds=time.monotonic()-started)
    out=HERE/'chem_next_public4030_loader_analysis.json';out.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k not in ('rows','batch0_boundaries')},indent=2))

if __name__=='__main__':main()
