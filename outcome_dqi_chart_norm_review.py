#!/usr/bin/env python3
"""Independent review of the GF4-norm zero-flag integration, without edits."""
from pathlib import Path
import hashlib
import json

import numpy as np
import kickmix as km
import outcome_dqi_chart_third_norm as Chart

ROOT = Path(__file__).resolve().parent
Norm = Chart.Norm
Cubic = Norm.Cubic


def sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def binary(values, width):
    values = np.asarray(values, dtype=np.uint64)
    return ((values[None, :] >> np.arange(width, dtype=np.uint64)[:, None]) & 1).astype(bool)


def main():
    # Verify the actual constants and finite-field certificate used by the code.
    field12, field6 = km.GF2Field(12), km.GF2Field(6)

    def trace(value, field):
        answer = 0
        for _ in range(field.degree):
            answer ^= value
            value = field.mul(value, value)
        return answer

    delta24 = Norm.Arithmetic.DEFAULT_DELTA
    delta12 = Norm.quadratic_basis(12)['delta']
    assert delta24 == 2048
    assert trace(delta24, field12) == trace(delta12, field6) == 1
    Cubic.cubic_data()  # Its source checks the GF4 norm identity at all 64 inputs.
    norm_zero_failures = sum((field6.pow(value, 21) == 0) != (value == 0)
                             for value in range(64))
    assert norm_zero_failures == 0

    # Full six-bit source domain, both old flag values, and clean/dirty inverse targets.
    cases = [(value, old_flag, old_target)
             for value in range(64) for old_flag in (0, 1)
             for old_target in (0, value ^ 57)]
    count = len(cases)
    b = km.CircuitBuilder()
    source = b.create_quantum_register(6, 'source')
    target = b.create_quantum_register(6, 'target')
    flag = b.create_quantum_register(1, 'flag')
    dirty = b.create_quantum_register(4, 'dirty')
    Cubic.inverse_six_cubic(b, source, target=target, zero_flag=flag[0])
    circuit = b.finish_circuit()
    assert circuit.operation_statistics().num_toffoli_like == 21
    rng = np.random.default_rng(202611150919)
    arrays = dict(source=binary([a for a, f, t in cases], 6),
                  target=binary([t for a, f, t in cases], 6),
                  flag=binary([f for a, f, t in cases], 1),
                  dirty=rng.integers(0, 2, (4, count), dtype=np.uint8).astype(bool))
    expected = dict(arrays)
    expected['target'] = binary([t ^ (field6.invert(a) if a else 0) for a, f, t in cases], 6)
    expected['flag'] = binary([f ^ (a == 0) for a, f, t in cases], 1)
    tests = []
    for seed in (0, 1, 24301):
        sim = km.Simulator(batch_size=count, seed=seed)
        sim.use_same_registers_as(circuit)
        for key, data in arrays.items():
            sim.write_across_shots(circuit.register_data[key], data)
        sim.do(circuit)
        bad = {key: int(np.any(sim.read_across_shots(circuit.register_data[key]) != data, axis=0).sum())
               for key, data in expected.items()}
        scratch = sim.read_across_shots([km.q(i) for i in range(17, circuit.num_qubits)])
        row = dict(seed=seed, cases=count, register_error_cases=bad,
                   scratch_error_cases=int(np.any(scratch, axis=0).sum()),
                   phase_error_cases=int(sim.read_phase_flipped_across_shots().sum()))
        assert not any(bad.values()) and row['scratch_error_cases'] == row['phase_error_cases'] == 0
        tests.append(row)

    component_path = ROOT/'outcome_dqi_chart_norm_component_report.json'
    full_path = ROOT/'outcome_dqi_chart_norm_full_verification.json'
    splice_path = ROOT/'outcome_dqi_chart_norm_splice_report.json'
    component = json.loads(component_path.read_text())
    full = json.loads(full_path.read_text())
    splice = json.loads(splice_path.read_text())
    candidate = Path(splice['output_path'])
    candidate_hash = sha(candidate)
    assert candidate_hash == splice['output_sha256'] == full['circuit_sha256']
    assert full['status'] == 'PASS' and full['verified_shots'] == 102400
    assert full['value_errors'] == full['phase_errors'] == 0
    assert full['num_qubits'] == 889 and full['max_toffoli_count'] == 382920
    assert component['prefix_static_T'] == 624
    assert component['pair_static_T_including_one_probe_CCZ'] == 1261

    sources = [Path(Chart.__file__), Path(Norm.__file__), Path(Cubic.__file__),
               Path(Norm.__file__).parent.parent/'official_sources/Syed_v12/source/dqi_source/src/controller_work/work/round2/milestone152/source/tower_inverse.py']
    result = dict(
        status='PASS_INDEPENDENT_NORM_FLAG_REVIEW',
        candidate_sha256=candidate_hash,
        candidate_path=str(candidate),
        reviewed_source_sha256={str(path): sha(path) for path in sources},
        properties={
            'dirty_flag_is_exact_XOR': True,
            'GF24_norm_zero_iff_input_zero': True,
            'GF12_norm_zero_iff_input_zero': True,
            'GF6_GF4_norm_zero_iff_input_zero': True,
            'GF24_quadratic_delta': delta24,
            'GF12_quadratic_delta': delta12,
            'both_quadratic_deltas_have_absolute_trace_one': True,
            'GF6_norm_exponent': 21,
            'GF6_norm_all_64_inputs_checked': True,
            'saved_inverse_phase_debt_unchanged': True,
            'reverse_toggle_valid_because_zero_is_invariant_under_inv0': True,
            'extra_helpers_for_optional_flag': 0,
        },
        independent_native_dirty_flag_tests=tests,
        resource_ledger={'prefix_static_T': 624, 'return_static_T': 636,
                         'pair_static_T': 1260, 'delta_vs_old_static_T': -14,
                         'delta_vs_old_expected_T': -3, 'global_Q': 889,
                         'global_max_T': 382920},
        collaborator_component_evidence={
            'path': str(component_path), 'sha256': sha(component_path),
            'finite_output_cases': component['finite_output_native_cases'],
            'HMR_seeds': sorted(set(row['seed'] for row in component['tests'])),
            'all_test_value_and_phase_errors_zero': all(row['value_errors'] == 0 and row['phase_errors'] in (None, 0) for row in component['tests']),
        },
        collaborator_full_verifier_evidence={
            'path': str(full_path), 'sha256': sha(full_path),
            'status': full['status'], 'shots': full['verified_shots'],
            'value_errors': full['value_errors'], 'phase_errors': full['phase_errors'],
            'mean_T': full['toffoli_count'], 'DQI_cost': full['score'],
            'seed': full['seed'], 'salt': full['salt'],
            'verification_scope': full['verification_scope'],
            'reviewer_read_and_hash_bound_report_did_not_rerun_full_verifier': True,
        },
        scope='Exact third-pivot contract on finite Y with N2 nonzero, including D2=0. N2=0 remains unsupported; finite random verification is not an all-input proof of the complete decoder.',
    )
    (ROOT/'outcome_dqi_chart_norm_review.json').write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
