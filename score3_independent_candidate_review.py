#!/usr/bin/env python3
"""Focused independent audit of the product cache and classical mode selector.

This does not invoke either candidate's search, build, native test suite, or
official verifier. It checks the literal cache patch, its branchwise local
identity, binary/text binding, and the final selector's recorded artifacts.
The selector's complete source was also reviewed manually; this receipt does
not turn its finite native panel into an exhaustive decoder qualification.
"""
from __future__ import annotations

import argparse
import ast
from collections import Counter
import hashlib
from itertools import product
import json
from pathlib import Path
import re


def digest(path):
    with Path(path).open('rb') as handle:
        return hashlib.file_digest(handle, 'sha256').hexdigest()


def artifact(path):
    path = Path(path)
    return dict(path=str(path), bytes=path.stat().st_size, sha256=digest(path))


def qrefs(line):
    return [int(x) for x in re.findall(r'\bq(\d+)\b', line)]


def phase_compensation_ast(path):
    tree = ast.parse(Path(path).read_text())
    func = next(n for n in tree.body if isinstance(n, ast.FunctionDef)
                and n.name == 'build_and_splice')
    loop = next(n for n in func.body if isinstance(n, ast.For)
                and isinstance(n.target, ast.Tuple)
                and [x.id for x in n.target.elts] == ['scalar', 'syndrome'])
    return ast.dump(loop, include_attributes=False)


def review_cache(repo, run, source_kmb):
    import kickmix as km
    baseline_path = repo/'invsqrt_structural_e46.kmx'
    candidate_path = run/'candidate.kmx'
    baseline = baseline_path.read_text().splitlines()
    candidate = candidate_path.read_text().splitlines()
    first, last, cache = 3321, 3423, 21
    assert baseline[first] == baseline[last] == 'CCX q10 q11 q13'
    max_old_b = max(int(x) for x in re.findall(r'\bb(\d+)\b', '\n'.join(baseline)))
    fresh = max_old_b + 1
    assert fresh == 387
    expected = (baseline[:first] + ['CX q13 q21', baseline[first], 'CX q13 q21']
                + baseline[first+1:last]
                + ['CX q21 q13', f'HMR q21 b{fresh}', f'CZ q10 q11 if b{fresh}']
                + baseline[last+1:])
    assert candidate == expected, 'The candidate contains an unreviewed change'
    previous = max(i for i in range(first) if cache in qrefs(baseline[i]))
    assert baseline[previous] == 'HMR q21 b61'
    assert not any(cache in qrefs(s) for s in baseline[previous+1:last+1])
    depth = 0
    for i, line in enumerate(baseline):
        if i in (previous, first, last):
            assert depth == 0
        if line.startswith('PUSH_CONDITION '):
            depth += 1
        elif line == 'POP_CONDITION':
            depth -= 1
        assert depth >= 0
    assert depth == 0

    # Affine forms in (constant, a, b) certify arbitrary endpoint controls.
    forms = {10: 2, 11: 4}
    mutations = []
    for i in range(first+1, last):
        line = baseline[i]
        op, qs = line.split()[0], qrefs(line)
        assert op in ('X', 'CX', 'CCX', 'HMR'), line
        assert ' if ' not in line
        target = qs[-1]
        if target not in forms:
            continue
        if op == 'X':
            forms[target] ^= 1
        elif op == 'CX':
            assert qs[0] in forms
            forms[target] ^= forms[qs[0]]
        else:
            raise AssertionError(f'Non-affine control mutation: {line}')
        mutations.append(dict(source_line=i+1, instruction=line,
                              affine_forms=dict(forms)))
    assert forms == {10: 2, 11: 4}

    # Independent local Boolean/phase check. t and u may be arbitrary dirty
    # target values at the first and second uses; m is the fresh HMR branch.
    checked = 0
    for a, b, t, u, m in product((0, 1), repeat=5):
        c = t
        new_t = t ^ (a & b)
        c ^= new_t
        assert c == (a & b)
        assert (u ^ c) == (u ^ (a & b))
        assert ((m & c) ^ (m & a & b)) == 0
        checked += 1
    assert sum(bool(re.search(r'\bb387\b', line)) for line in candidate) == 2
    assert [s for s in baseline if s.startswith('Z_POW ')] == [
        s for s in candidate if s.startswith('Z_POW ')]

    old = km.Circuit.from_file(str(source_kmb))
    new = km.Circuit.from_file(str(run/'candidate.kmb'))
    assert str(old).strip() == '\n'.join(baseline).strip()
    assert str(new).strip() == '\n'.join(candidate).strip()
    assert old.num_qubits == new.num_qubits == 46
    assert old.num_bits == 387 and new.num_bits == 388
    assert old.operation_statistics().num_toffoli_like == 1551
    assert new.operation_statistics().num_toffoli_like == 1550
    old_counts = Counter(s.split()[0] for s in baseline)
    new_counts = Counter(s.split()[0] for s in candidate)
    changes = {k: new_counts[k]-old_counts[k] for k in old_counts.keys() | new_counts.keys()
               if new_counts[k] != old_counts[k]}
    assert changes == {'CCX': -1, 'CX': 3, 'HMR': 1, 'CZ': 1}
    report = json.loads((run/'report.json').read_text())
    native = json.loads((run/'native.json').read_text())
    assert report['source_sha256'] == digest(baseline_path)
    assert native['source_sha256'] == digest(source_kmb)
    assert report['candidate_sha256'] == native['candidate_sha256'] == digest(run/'candidate.kmb')
    assert report['script_sha256'] == digest(repo/'score3_invsqrt_product_cache.py')
    assert native['status'] == 'NATIVE_COMPARISON_PASS'
    for row in native['rows']:
        assert row['restored_input_failures'] == row['dirty_scratch_failures'] == row['phase_mismatches_against_baseline'] == 0
    return dict(status='PASS', source=artifact(baseline_path), source_binary=artifact(source_kmb),
                candidate_text=artifact(candidate_path), candidate_binary=artifact(run/'candidate.kmb'),
                generator=artifact(repo/'score3_invsqrt_product_cache.py'),
                producer_report=artifact(run/'report.json'), native_receipt=artifact(run/'native.json'),
                exact_literal_patch=True, all_other_original_instructions_unchanged=True,
                zero_cache_established_by=dict(source_line=previous+1, instruction=baseline[previous]),
                cache_absent_from_original_interval=True, boundary_condition_stack_depth=0,
                control_mutations=mutations, controls_return_as_formal_independent_variables=True,
                fresh_classical_bit=fresh, local_boolean_phase_assignments=checked,
                instrument_identity=(
                    'Copying dirty target before and after the retained CCX gives cache=a*b. '
                    'All original operations ignore the cache, and a,b return formally. '
                    'The replacement CX therefore equals the removed CCX. For each fresh '
                    'HMR outcome m, its phase (-1)^(m*a*b) is canceled by the conditioned '
                    'CZ. The added branch has norm 1/sqrt(2), independent of data. '
                    'Thus each old instrument branch is preserved, including entangled '
                    'inputs; tracing the fresh classical output gives the same channel.'),
                qubits=46, static_toffoli_like_before=1551, static_toffoli_like_after=1550,
                instruction_delta=changes, phase_rotations_byte_identical=True,
                exact_expected_toffoli_reduction=1,
                scope='Independent local all-branch identity and binary binding; no official full-input verification rerun.')


def review_gauge(repo):
    source = repo/'score3_gauge_sort.py'
    native_path = repo/'score3_gauge_sort_native.json'
    build_path = repo/'score3_gauge_sort_build.json'
    manifest_path = repo/'score3_gauge_sort_manifest.json'
    native = json.loads(native_path.read_text())
    build = json.loads(build_path.read_text())
    manifest = json.loads(manifest_path.read_text())
    expected = '435870acd0698f6b5214622b225cff81085847d6b0571a1b98afe5bcf69a3e2a'
    assert digest(source) == native['script_sha256'] == build['script_sha256'] == expected
    for name, entry in manifest['files'].items():
        assert digest(repo/name) == entry['sha256']
        assert (repo/name).stat().st_size == entry['bytes']
    candidate_path = Path(build['candidate_path'])
    assert digest(candidate_path) == build['candidate']['sha256'] == manifest['candidate']['sha256']
    assert candidate_path.stat().st_size == build['candidate']['bytes']
    assert native['status'] == 'PASS' and native['fixtures'] == 100
    assert native['selected_labels'] == native['expected_labels']
    assert native['input_masks_preserved'] and native['scratch_cleared'] and native['phase_unchanged']
    assert native['quantum_bits'] == native['toffoli_like'] == 0
    assert native['instructions'] == 12336839
    assert native['ledger'] == build['selector_ledger']
    assert native['ledger']['comparators'] == 139263
    assert native['ledger']['sorting_instructions'] == 139263*81
    assert build['phase_compensation_cz'] == 2126
    assert build['all12_label_bits_shifted_and_compensated']
    assert all(value['equal'] for value in build['boundary_checks'].values())
    assert build['decoder_body_preserved_byte_for_byte']
    assert build['candidate']['header']['num_qubits'] == 889
    assert phase_compensation_ast(source) == phase_compensation_ast(repo/'dqi_gauge_dynamic.py')

    # The comparator's induction step: g is any prior lower-bit comparison.
    for a, b, g in product((0, 1), repeat=3):
        d = a ^ b
        updated = g ^ a
        if d:
            updated = 0
        updated ^= a
        assert updated == (a if d else g)
        left = a ^ (g & d)
        right = d ^ left
        assert (left, right) == ((b, a) if g else (a, b))

    return dict(status='PASS_NO_CONCRETE_DEFECT_FOUND', source=artifact(source),
                native_receipt=artifact(native_path), build_receipt=artifact(build_path),
                manifest=artifact(manifest_path), candidate_binary=artifact(candidate_path),
                reviewed_proof=artifact(repo/'score3_gauge_sort_proof.md'),
                selector_is_all_classical=True, selector_additional_qubits=0, selector_toffoli_like=0,
                comparator_induction_step_truth_table_pass=True,
                comparator_width=13, comparator_instructions=81,
                sorting_network='Recursive ascending Batcher odd-even merge; indices and recurrence reviewed.',
                valid_words=4026, sentinel_words=70, sentinel=4096,
                sentinel_scan_excluded=True, maximum_run_count=4026, counter_bits=12,
                mode_invariant=(
                    'Sorted input includes one virtual zero, so initial winner 0/count1 is valid. '
                    'Each prefix increments the exact run count and replaces the winner only '
                    'on strict improvement. Thus the last run is handled and ties keep the '
                    'least numerical label. Twelve bits cover all reachable counts.'),
                existing_full_width_phase_compensation_ast_equal=True,
                integration_review=(
                    'Classical input masks are copied into private storage; all selector '
                    'storage is allocated beyond reserved original bit IDs. The selected '
                    '12-bit label is copied to the original fixed pivot. All 12 bits enter '
                    'both mask shifts and the existing phase compensation. The suffix '
                    'reverses shifts/scaling before closing the original gauge. The splice '
                    'code checks complete old boundaries and copies the original body.'),
                scope=(
                    'Read-only algorithm/integration source audit and actual file-hash binding '
                    'to existing native/build receipts. Native fixtures were not rerun; '
                    'full decoder correctness, runtime Toffoli mean, failure ratio, and '
                    'Public Score require the separate official runner.'),
                concrete_defects=[])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--cache-run', type=Path, required=True)
    parser.add_argument('--source-kmb', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    repo = Path(__file__).resolve().parent
    result = dict(status='FOCUSED_INDEPENDENT_REVIEW_PASS',
                  invsqrt=review_cache(repo, args.cache_run, args.source_kmb),
                  gauge=review_gauge(repo), reviewer_script=artifact(__file__),
                  official_full_runs_performed_by_this_review=False,
                  public_score_claimed=False)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True)+'\n')
    print(json.dumps(dict(status=result['status'], output=str(args.output),
                         sha256=digest(args.output))))


if __name__ == '__main__':
    main()
