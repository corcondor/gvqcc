#!/usr/bin/env python3
"""Score8-relative resource targets and bounded exact-padding cost screen.

Uses the unmodified official cost model. No candidate or PASS is implied.
Zero padding is only a necessary resource screen: changed address domains
still require matching circuit construction and numerical verification.
"""
import argparse
import hashlib
import importlib.util
import json
import math
from pathlib import Path
import sys


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--model', type=Path, default=Path(__file__).resolve().parents[1] / 'official_sources/Inzainos/verifiers/dfthcsos/scoreinfra/costs_prepare.py')
    args = parser.parse_args()
    repo = Path(__file__).resolve().parent
    scorecard = json.loads((repo / 'score8_scorecard.json').read_text())
    base = scorecard['local_combined_score']
    target_ratio = (base / 28) ** 3
    spec = importlib.util.spec_from_file_location('target28_official_costs', args.model)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)

    def resources(r, b, c):
        m = mod.SpinFreeData_V1(R=r, B=b, C=c, N=76, chi=10, beta=8)
        o, i = m.outer_state_prep_qubit_cost(), m.inner_state_prep_qubit_cost()
        q = o['persistent'] + i['persistent'] + 40 + max(o['temporary'], i['temporary'])
        h = m.outer_state_prep() + m.inner_state_prep() + m.givens_rotations()
        return q, h

    assert resources(8, 143, 44) == (427, 6662)
    base_qt = 427 * 14722
    rows = []
    # Increasing a dimension by zero padding can cross discontinuous QROAM
    # choices. Do not assume monotonicity of the official model.
    configs = {(8, b, 44) for b in range(143, 1025)}
    configs |= {(8, 143, c) for c in range(44, 1025)}
    configs |= {(r, 143, 44) for r in range(8, 65)}
    configs |= {(r, b, c) for r in (8, 9, 16) for b in range(143, 274) for c in range(44, 97)}
    # Exact direct-sum regroupings: merge m rho blocks, concatenate bases,
    # and block-diagonalize ensemble coefficients. Total angle rows unchanged.
    regroupings = [(8 // m, 143 * m, 44 * m) for m in (2, 4, 8)]
    configs.update(regroupings)
    for r, b, c in sorted(configs):
        q, h = resources(r, b, c)
        ratio = q * (h + 8060) / base_qt
        rows.append(dict(R=r, B=b, C=c, Q=q, nonloader_T=h,
                         same_loader_cost_ratio=ratio,
                         improve_loader_A_strict_upper=(base_qt/q-h)/2,
                         reach28_loader_A_strict_upper=(base_qt*target_ratio/q-h)/2,
                         construction='exact_direct_sum' if (r,b,c) in regroupings else 'zero_padding'))
    rows.sort(key=lambda x: x['same_loader_cost_ratio'])
    dqit = 382066.52936523437
    result = dict(status='RESOURCE_SCREEN_ONLY_NO_NEW_CANDIDATE',
        baseline_local_score=base, target_strictly_greater_than=28,
        required_product_ratio_strict_upper=target_ratio,
        model_sha256=hashlib.sha256(args.model.read_bytes()).hexdigest(),
        one_component_targets=dict(
            chemistry_J5_A_max=math.ceil((14722*target_ratio-6662)/2)-1,
            dqi_T_strict_upper_at_fixed_Q_and_R=dqit*target_ratio,
            dqi_Q_max_at_fixed_T_and_R=math.ceil(889*math.sqrt(target_ratio))-1,
            invsqrt_Q_max_at_fixed_effective_T=math.ceil(46*target_ratio)-1),
        screened_configurations=len(rows), best_rows=rows[:25],
        direct_sum_rows=[r for r in rows if r['construction']=='exact_direct_sum'],
        improving_same_loader_rows=[r for r in rows if r['same_loader_cost_ratio']<1],
        limitation='Holding loader A=4030 is conditional, not a constructed circuit. Finite shape ranges only; lambda held fixed. DQI R held fixed, not assumed robust to changed failure rates.',
        full_official_verification=False, new_score_improvement=False)
    args.output.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k not in ('best_rows','direct_sum_rows','improving_same_loader_rows')},indent=2))
    print(json.dumps({'best':rows[0], 'improving':len(result['improving_same_loader_rows']), 'direct_sum':result['direct_sum_rows']},indent=2))


if __name__ == '__main__':
    main()
