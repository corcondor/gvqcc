#!/usr/bin/env python3
"""Recompute the locally qualified portfolio score from hash-bound receipts.

This performs no simulation and no submission. Sensitivity rows hold measured
mean Toffoli and component costs fixed while varying the DQI error count.
"""
from pathlib import Path
import argparse
import hashlib
import json
import math

REFERENCE = {
    'invsqrt': 2076774.233715,
    'dqi': 24439463583672.93,
    'dfthcsos': 3355599588.3155375,
}


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def combined(costs):
    return math.prod(REFERENCE[k] / costs[k] for k in REFERENCE) ** (1 / 3)


def upper(k, n, log2_delta):
    """Scalar equivalent of the official one-sided binomial-tail inversion."""
    assert n > 0 and 0 <= k < n and log2_delta < 0
    target = log2_delta * math.log(2.0)
    if k == 0:
        return -math.expm1(target / n)
    log_comb = [0.0]
    for j in range(1, k + 1):
        log_comb.append(log_comb[-1] + math.log(n - j + 1) - math.log(j))

    def log_tail(p):
        terms = [log_comb[j] + j * math.log(p) + (n-j) * math.log1p(-p)
                 for j in range(k+1)]
        maximum = max(terms)
        return maximum + math.log(sum(math.exp(t - maximum) for t in terms))

    lo = k / n if log_tail(k / n) >= target else 0.0
    hi = 1.0
    for _ in range(64):
        mid = (lo + hi) / 2
        if mid in (lo, hi):
            break
        if log_tail(mid) > target:
            lo = mid
        else:
            hi = mid
    return hi


def repetition(eps):
    assert 0 <= eps < 1 / 16
    return math.log(2.0) / -math.log(0.5 + 2 * math.sqrt(eps))


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--dqi', type=Path, default=Path('score5_dqi_final_full_verification.json'))
    p.add_argument('--package', type=Path, default=Path('score5_final_worker_check.json'))
    p.add_argument('--retained', type=Path, default=Path('score3_submission_manifest.json'))
    p.add_argument('--previous', type=Path, default=Path('score4_dqi_full_verification.json'))
    p.add_argument('--out', type=Path, default=Path('score5_final_scorecard.json'))
    a = p.parse_args()
    dqi = json.loads(a.dqi.read_text())
    package = json.loads(a.package.read_text())
    retained = json.loads(a.retained.read_text())
    previous = json.loads(a.previous.read_text())
    assert dqi['status'] == previous['status'] == 'PASS'
    assert package['status'] == 'PACKAGE_INTEGRITY_PASS'
    assert package['all_member_sha256_and_crc_pass']
    assert package['member_count'] == 18
    assert package['candidate_dqi_sha256'] == dqi['circuit_sha256']
    assert package['official_dqi_receipt_sha256'] == sha(a.dqi)
    old_members = {m['name']: m for m in retained['members']}
    assert set(old_members) == set(package['members'])
    for name, info in package['members'].items():
        assert info['sha256_pass'] and info['crc_pass']
        if name != 'dqi.kmb':
            assert info['sha256'] == old_members[name]['sha256'], name
    costs = {'dqi': dqi['score']}
    qualification = {'dqi': {'receipt': str(a.dqi), 'sha256': sha(a.dqi),
                              'shots': dqi['verified_shots']}}
    for key in ['invsqrt', 'dfthcsos']:
        receipt = retained['official_receipts'][key]
        assert receipt['passes_bound_official_check']
        assert receipt['reported_status'] == 'PASS'
        costs[key] = receipt['official_metrics']['score']
        qualification[key] = dict(receipt=receipt['path'], sha256=receipt['sha256'],
                                  shots=receipt['official_metrics']['verified_shots'],
                                  retained_byte_identical=True)
    local = combined(costs)
    before = combined(dict(costs, dqi=previous['score']))
    calc = repetition(upper(dqi['value_errors'] + dqi['phase_errors'],
                            dqi['verified_shots'], dqi['log2_delta']))
    assert math.isclose(calc, dqi['repetition_factor'], rel_tol=1e-14)
    assert math.isclose(calc * dqi['num_qubits'] ** 2 * dqi['toffoli_count'],
                        dqi['score'], rel_tol=1e-14)
    sensitivity = []
    for k in range(3):
        eps = upper(k, dqi['verified_shots'], dqi['log2_delta'])
        rep = repetition(eps)
        cost = rep * dqi['num_qubits'] ** 2 * dqi['toffoli_count']
        sensitivity.append(dict(total_dqi_errors=k, effective_error_rate=eps,
                                repetition_factor=rep, dqi_cost=cost,
                                combined_score=combined(dict(costs, dqi=cost))))
    result = dict(
        status='HASH_BOUND_LOCAL_PORTFOLIO_SCORE',
        reference_costs=REFERENCE,
        reference_source='official_sources/maoxin_4033_cell07.py REFERENCE; independently agrees with atakan_v15_cell_10.py to published precision',
        formula='geometric_mean(reference_cost / candidate_cost); DQI cost = repetition_factor * Q^2 * mean_Toffoli',
        candidate_costs=costs,
        local_combined_score=local,
        previous_score4_local_combined_score=before,
        local_combined_increase=local-before,
        local_combined_increase_percent=100*(local/before-1),
        dqi_cost_reduction_percent=100*(1-dqi['score']/previous['score']),
        candidate=dict(zip_sha256=package['output_sha256'],
                       zip_bytes=package['output_bytes'],
                       dqi_sha256=dqi['circuit_sha256'],
                       invsqrt_sha256=package['members']['invsqrt.kmb']['sha256'],
                       chemistry_npz_sha256=package['members']['dfthcsos/submission.npz']['sha256']),
        qualification=qualification,
        dqi_metrics={k:dqi[k] for k in ['num_qubits','num_bits','toffoli_count',
                        'max_toffoli_count','verified_shots','value_errors','phase_errors',
                        'seed','salt','log2_delta','verifier_sha256']},
        error_count_sensitivity=sensitivity,
        sensitivity_scope='Counterfactual calculation with measured mean Toffoli and other components fixed; not further runs or predictions of server errors.',
        public_score=None,
        new_submission_performed=False,
        exact_ccx_reduction_vs_projective_norm={
            '6a998c4688dc22b33f52e41be46c5e51f7ea927fab40d9141bc5e99ebf6a2e02':24,
            'e4e110436080b8538f50511dc7064185e1708c2bd386ea0e36322d7791311355':26,
        }.get(dqi['circuit_sha256']),
        limits=[
            'Different KMB hashes use different default samples. Exact gate reductions versus the projective-norm predecessor are proved separately; they are not inferred from finite mean differences.',
            'One known node13 numerator-zero input remains incorrect; this finite default PASS is not universal correctness.',
            'This ZIP retains the verified4033-loader chemistry. The newer4030-loader chemistry is not silently credited.',
            'Public scoring may differ because the verifier samples/errors differ.'],
        source_receipts={str(x):sha(x) for x in [a.dqi,a.package,a.retained,a.previous]})
    a.out.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:result[k] for k in ['status','candidate_costs',
                      'local_combined_score','previous_score4_local_combined_score',
                      'local_combined_increase','error_count_sensitivity']},indent=2))


if __name__ == '__main__':
    main()
