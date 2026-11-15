#!/usr/bin/env python3
"""Read-only independent audit of chemistry rebatching and its score thresholds.

This calls official scalar cost helpers and reads accepted circuits/arrays. It
does not run the full verifier, emit a circuit, mutate a submission, or submit.
The only outputs are score9_rebatch_contract.json and .md beside this script.
"""
from __future__ import annotations

from collections import Counter
import hashlib
import inspect
import json
import math
from pathlib import Path
import sys

REPO = Path(__file__).resolve().parent
VERIFIERS = Path('/workspace/scratch/7f542e06b7cf/official_sources/Inzainos/verifiers')
LOADERS = Path('/workspace/scratch/3815fb5fae06/score8_v27_chemistry')
FACTOR = Path('/workspace/scratch/3815fb5fae06/score8_chem_v27_schur_full/submission.npz')
WORDS = REPO / 'score8_chem_v27_recovered_words.npy'
TAG_PAIRS = [(0, 1), (0, 2), (1, 2), (0, 3), (1, 3)]


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def pin(path):
    path = Path(path)
    return dict(path=str(path), bytes=path.stat().st_size, sha256=sha(path))


def source_ref(function):
    lines, first = inspect.getsourcelines(function)
    return dict(path=inspect.getsourcefile(function), first_line=first,
                last_line=first + len(lines) - 1)


def parse(line):
    parts = line.split()
    if not parts:
        return '', [], None
    return (parts[0], [int(s[1:]) for s in parts[1:] if s.startswith('q')],
            int(parts[-1][1:]) if 'if' in parts else None)


def pack(values):
    return sum(int(v) << i for i, v in enumerate(values))


def linear_basis(values):
    result = {}
    for value in values:
        while value:
            pivot = value.bit_length() - 1
            if pivot in result:
                value ^= result[pivot]
            else:
                result[pivot] = value
                break
    return result


def belongs(value, basis):
    while value:
        pivot = value.bit_length() - 1
        if pivot not in basis:
            return False
        value ^= basis[pivot]
    return True


def low_function_space(vectors, count=1220):
    """Exact intersection of a wire span with functions of low four address bits."""
    quotient, pure = {}, []
    for full in vectors:
        low = full & 0xffff
        repeated = sum(((low >> (a & 15)) & 1) << a for a in range(count))
        residual = full ^ repeated
        while residual:
            pivot = residual.bit_length() - 1
            if pivot in quotient:
                r, f = quotient[pivot]
                residual ^= r
                full ^= f
            else:
                quotient[pivot] = residual, full
                break
        if not residual:
            pure.append(full & 0xffff)
    return linear_basis(pure)


def audit_loaders(km):
    rows, common_high = [], None
    data = set(range(11, 51)) - {18, 26, 34, 42, 50}
    for k in range(15):
        path = LOADERS / f'angle_k_{k}.kmb'
        circuit = km.Circuit.from_file(path)
        lines = str(circuit).splitlines()
        parsed = [parse(line) for line in lines]
        ccx = [i for i, (g, qs, _) in enumerate(parsed) if g == 'CCX' and qs[-1] in data]
        first, last = ccx[0], ccx[-1] + 1
        invalid = [i for i in range(first, last)
                   if parsed[i][0] == 'CCX' and parsed[i][1][-1] not in data]
        row = dict(batch=k, source=pin(path), num_qubits=int(circuit.num_qubits),
                   num_bits=int(circuit.num_bits), instructions=len(circuit),
                   toffolis=int(circuit.operation_statistics().num_toffoli_like),
                   output_accumulation_window_valid=not invalid)
        if invalid:
            row['special_case_reason'] = 'Initialization updates a nonlinear control inside the naive output-product window.'
            row['interleaved_nonlinear_control_positions'] = invalid
        else:
            parts = [parsed[:first], parsed[first:last], parsed[last:]]
            row['parts'] = {
                name: dict(Counter(g for g, _, _ in part))
                for name, part in zip(('prefix', 'output_accumulation', 'cleanup'), parts)
            }
            start = next(i for i, x in enumerate(lines) if x == 'R q51')
            end = next(i for i, x in enumerate(lines) if x == 'R q119')
            high = lines[start:end]
            if common_high is None:
                common_high = high
            row['high_prefix_exactly_matches_batch1'] = high == common_high
            row['high_prefix_ccx'] = sum(parse(line)[0] == 'CCX' for line in high)
            row['remaining_prefix_ccx'] = row['parts']['prefix'].get('CCX', 0) - row['high_prefix_ccx']
            row['prefix_ccx_targets'] = [qs[-1] for g, qs, _ in parsed[:first] if g == 'CCX']
        rows.append(row)
    assert sum(r['toffolis'] for r in rows) == 4030
    assert all(r['num_qubits'] <= 128 for r in rows)
    assert all(r['high_prefix_exactly_matches_batch1'] for r in rows[1:])
    return rows


def main():
    sys.path.insert(0, str(VERIFIERS))
    # The existing Kickmix venv and primary numerical runtime share Python3.12.
    # Reuse the installed SciPy runtime; do not install or mutate dependencies.
    sys.path.append('/opt/codex/runtimes/codex-primary-runtime/dependencies/python/lib/python3.12/site-packages')
    import kickmix as km
    import numpy as np
    import dfthcsos.verify as official
    from dfthcsos.scoreinfra import circuits, dfthc_math

    score8 = json.loads((REPO / 'score8_scorecard.json').read_text())
    score6 = json.loads((REPO / 'score6_scorecard.json').read_text())
    data = dict(np.load(FACTOR, allow_pickle=False))
    words = np.load(WORDS, allow_pickle=False).astype(np.uint64)
    assert words.shape == (1220, 75)
    assert data['W'].shape == (8, 143, 44)
    assert data['U'].shape[-1] == 76
    heuristic = official.heuristic_costs(76, 8, 143, 44, 8)
    assert (heuristic['toffoli'], heuristic['persistent_qubits'], heuristic['temporary_qubits']) == (6662, 84, 303)
    assert official.QUBIT_CAP == 128

    lam = score8['chemistry_metrics']['lambda_eff']
    base_cost = score8['candidate_costs']['dfthcsos']
    current = math.prod(score8['reference_costs'][t] / cost
                        for t, cost in score8['candidate_costs'].items()) ** (1 / 3)
    factor = (current / 28.0) ** 3
    assert abs(current - 27.32784222155277) < 1e-12
    assert abs(base_cost - lam * 14722 * 427) < 1e-6

    address = np.arange(1220, dtype=np.uint64)
    address_functions = [pack((address >> b) & 1) for b in range(11)]
    low_tags = [sum((int(((a >> b) & 1) & ((a >> c) & 1))) << a
                    for a in range(16)) for b, c in TAG_PAIRS]
    actual_tags = ((words >> 6) ^ (words >> 7)) & 1
    desired_tags = np.stack([((address >> b) & 1) & ((address >> c) & 1)
                             for b, c in TAG_PAIRS], axis=1)
    assert np.array_equal(actual_tags, np.tile(desired_tags, (1, 15)))
    word_functions = [[pack((words[:, j] >> b) & 1) for b in range(8)]
                      for j in range(75)]
    rows = []
    for j in range(1, 9):
        k_count = math.ceil(75 / j)
        max_workspace = 128 - 11 - 8 * j
        q = heuristic['persistent_qubits'] + 8 * j + max(303, max_workspace)
        break_even = (base_cost / (lam * q) - 6662) / 2
        target = (base_cost * factor / (lam * q) - 6662) / 2
        old_threshold = (14728 * 427 / q - 6662) / 2
        old_cost_current_lambda = (score6['candidate_costs']['dfthcsos'] / (lam * q) - 6662) / 2
        batch_spaces = []
        for k in range(k_count):
            cols = list(range(j * k, min(j * (k + 1), 75)))
            vectors = [(1 << 1220) - 1] + address_functions
            vectors += [f for col in cols for f in word_functions[col]]
            low_basis = low_function_space(vectors)
            batch_spaces.append(dict(batch=k, columns=cols, low_function_rank=len(low_basis),
                                     available_tag_indices=[i for i, t in enumerate(low_tags) if belongs(t, low_basis)]))
        rows.append(dict(
            J=j, circuits=k_count, padding_words=k_count*j-75, final_live_words=75-(k_count-1)*j,
            selection_qubits=11, angle_persistent_qubits=8*j,
            maximum_angle_workspace_qubits=max_workspace, total_qubits=q,
            loader_cost_break_even_strict_upper_bound=break_even,
            maximum_integer_loader_cost_to_improve=math.ceil(break_even)-1,
            loader_cost_target28_inclusive_upper_bound=target,
            maximum_integer_loader_cost_to_reach28=math.floor(target),
            score_if_loader_cost_stays_4030=current*(base_cost/(lam*q*14722))**(1/3),
            score6_same_lambda_loader_break_even_strict_upper_bound=old_threshold,
            score6_cost_with_current_lambda_loader_break_even_strict_upper_bound=old_cost_current_lambda,
            output_batch_low_function_spans=batch_spaces,
        ))

    loader_rows = audit_loaders(km)
    source_files = [VERIFIERS / 'dfthcsos' / name for name in
                    ('verify.py', 'scoreinfra/circuits.py', 'scoreinfra/costs_prepare.py', 'scoreinfra/dfthc_math.py')]
    proof_refs = {name: source_ref(fn) for name, fn in {
        'load_circuits': circuits.load_circuits,
        'read_circuit_family': circuits.read_circuit_family,
        'register_layout': circuits.register_layout,
        'recover_words_from_circuits': circuits.recover_words_from_circuits,
        'check_state': circuits._check_state,
        'angles_costs': official.angles_costs,
        'heuristic_costs': official.heuristic_costs,
        'resource_costs': official.resource_costs,
        'score_from_metrics': official.score_from_metrics,
        'reconstruct_u_vectors': dfthc_math.reconstruct_u_vectors,
        'evaluate_dfthc_angle_words': dfthc_math.evaluate_dfthc_angle_words,
    }.items()}
    result = dict(
        status='READ_ONLY_OFFICIAL_CONTRACT_AND_COST_AUDIT_COMPLETE',
        full_verifier_run=False, circuit_mutations=False, submission_performed=False,
        script=pin(Path(__file__)), official_sources=[pin(p) for p in source_files], source_refs=proof_refs,
        inputs=[pin(REPO/'score8_scorecard.json'), pin(REPO/'score6_scorecard.json'), pin(FACTOR), pin(WORDS)],
        baseline=dict(local_score=current, chemistry_lambda=lam, chemistry_cost=base_cost,
                      J=5, loader_toffoli_per_pass=4030, total_toffoli=14722, total_qubits=427),
        target28=dict(required_single_task_cost_factor=factor,
                      chemistry_cost_at_fixed_other_tasks=base_cost*factor),
        heuristic=heuristic, thresholds=rows,
        contract={
            'num_angles':75, 'num_vectors':1220, 'brot':8,
            'num_circuits':'Exactly ceil(75/J); J is inferred from consecutive word_0..word_(J-1) registers.',
            'public_registers':'Identical quantum IDs and order in every family member; selection exactly 11 qubits; words disjoint and equal width.',
            'output_order':'Batch k is flattened as columns k*J..k*J+J-1. There is no column-index indirection or per-file batch-size metadata.',
            'partial_padding':'All final padding words must be zero for every valid address. The same J registers remain declared and charged; the transition into padding still clears the previous slot word.',
            'file_order':'Directory filenames must be contiguous angle_k_0..angle_k_(K-1), with a consistent format in auto mode. An ordered list of arbitrary paths/objects is also accepted by the Python API, but still has exactly K members and positional batch semantics.',
            'scratch_boundary':'Every circuit ends with zero quantum workspace, preserved selection and no phase. reset_between_circuits clears simulator state and restores only selection and words, so classical and quantum prefix scratch cannot persist between files.',
            'workspace_cost':'Q_total=84+8J+max(303, angle_Q-11-8J). angle_Q<=128, so Q_total=387+8J for J=1..8. The 303 shared-workspace floor is not permission to exceed the 128-qubit circuit cap.',
            'toffoli_cost':'A = half of actual mean Toffoli-like execution over forward and reverse passes. T_total=6662+2A. CCX,CCZ,CSWAP count; classical-conditioned gates count only when executed. Static CCX sums equal A only for unconditional fixed-count families.',
            'other_gate_cost':'X/CX/CZ and classical logic are not charged as Toffoli-like gates; HMR/R are available with exact phase correction and cleanup. Z_POW is explicitly banned. Reaction depth and total instruction count are reported but do not multiply this task cost.',
            'documented_oracle':'Module contract says arbitrary-target XOR oracle. The executable verifier checks forward/reverse reachable batches. A reachable word-tag identity alone is not proof of the arbitrary-target extension.',
            'regrouping':'Noncontiguous old columns require reordering/re-encoding the angle table and tree edges; API file order does not introduce a gather map. Parent-before-child is necessary but not sufficient for preserving vectors. Swapping disjoint Givens rotations is exact; rotations sharing a vertex generally do not commute.',
            'extra_identity_files':'Extra files are forbidden by exact circuit count. An identity circuit in a legitimate slot implies identical successive batches and is valid only if those decoded angles and physics remain correct.',
        },
        identity_controls={
            'scope':'All 1220 valid addresses, all 75 actual recovered angle columns, not the declared NPZ angle_words.',
            'tag_relation':'bit6 XOR bit7 = address_bit[a] AND address_bit[b], with pair selected by column modulo 5.',
            'pairs_by_column_mod5':TAG_PAIRS, 'exact_tag_mismatches':0,
            'globally_constant_word_columns':[i for i in range(75) if np.all(words[:,i] == words[0,i])],
            'declared_vs_actual_word_mismatches':int(np.count_nonzero(words != data['angle_words'])),
            'free_use':'One CX exposes each existing word tag without Toffoli on the reachable input batch. J=4 rotates which four tags are present every batch; k=0 starts at zero and has no incoming tags.',
            'synthesis_caution':'Tag transitions and cleanup must be handled in both directions. The 7-product low-basis completion estimate for J4 is only construction of missing low-address functions, not a complete new oracle cost.',
        },
        accepted_loader_structure=loader_rows,
        architecture_findings=[
            'For k=1..14 the exact shared high-address prelude has 68 CCX. Six additional prefix CCX complete the low-address feature set; total prefix 74. Cleanup uses HMR with conditioned CZ and zero additional CCX.',
            'The output-product blocks have output linear mixing, so keeping only gates whose physical targets belong to chosen words does not preserve the projected outputs. Propagate output directions before pruning/projecting.',
            'k=0 has initialization intertwined with nonlinear control updates; the existing simple output-window extractor cannot be used unmodified.',
            'A prefix may be shared between subcomputations inside one file with cleanup at the end. It must be regenerated at the next file boundary. Different J also changes the required old-batch XOR new-batch transition functions.',
            'The smaller J4 word bank releases eight physical qubits under the 128 cap. It increases family size from 15 to 19, so more prefix executions must be offset by product resynthesis and the lower persistent Q cost.',
        ],
    )
    (REPO/'score9_rebatch_contract.json').write_text(json.dumps(result,indent=2)+'\n')

    table = '\n'.join(
        f"| {r['J']} | {r['circuits']} | {r['padding_words']} | {r['total_qubits']} | {r['maximum_angle_workspace_qubits']} | {r['loader_cost_break_even_strict_upper_bound']:.6f} | {r['maximum_integer_loader_cost_to_improve']} | {r['loader_cost_target28_inclusive_upper_bound']:.6f} | {r['maximum_integer_loader_cost_to_reach28']} |"
        for r in rows)
    j4 = rows[3]
    text = fr'''# Chemistry rebatching: independent contract and cost audit

## Decision thresholds

For the accepted score8 coefficients and exact actual angle table, **J=4 requires 19 circuits**, and lowers the scored qubit count from **427 to 419**. It improves the current portfolio if the aggregate loader cost per pass **A < {j4['loader_cost_break_even_strict_upper_bound']:.12f}**. For an unconditional integer-cost family the maximum is **4170**. Reaching portfolio score28 through this task alone requires **A <= {j4['loader_cost_target28_inclusive_upper_bound']:.12f}**, or **3643** for integer cost.

The older threshold4173 used score6's 14728 total Toffoli. Its precise same-lambda threshold is {j4['score6_same_lambda_loader_break_even_strict_upper_bound']:.12f}. The accepted score8 circuit already uses14722, so that old threshold is no longer the correct improvement gate.

These are conditional resource targets, not emitted circuits or new verified scores. Other tasks, coefficients, brot8 and the actual decoded angle words are fixed. No full verifier, circuit mutation or submission was performed by this audit.

| J | Files | Final padding words | Scored Q | Maximum angle workspace | Improve: A strictly below | Integer maximum | Reach28: A at most | Integer maximum |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|
{table}

The official scalar helper gives state preparation plus Givens cost6662, persistent preparation qubits84 and shared workspace303. Every angle circuit has11 selection qubits and8J word qubits, with a separate hard cap128. Thus

\[
T_{{total}}=6662+2A,\qquad Q_{{total}}=84+8J+\max(303,Q_{{angle}}-11-8J)=387+8J.
\]

The scored chemistry cost is lambda_eff times these two factors. Here lambda_eff={lam:.15f}; current chemistry cost={base_cost:.7f}; current portfolio score={current:.14f}. The target28 chemistry cost is {base_cost*factor:.7f}, a factor {factor:.15f} of current cost. A is half of the simulator's actual forward-plus-reverse mean, not necessarily the static gate count when measurements control Toffoli execution.

## What the family must load

Each circuit uses identical `selection` and `word_0` through `word_(J-1)` quantum registers, with identical physical IDs. Selection is exactly11 qubits. The number of circuits is exactly ceil(75/J). The words observed after circuitk are concatenated in file order as columns kJ through kJ+J-1. There is no independent angle-index map or variable final J.

For J4 the last file has three valid words and one zero padding word. That fourth register remains present and charged. Its final transition must clear the prior batch's fourth word; simply omitting it is incorrect. All final padding must be zero on every valid address.

The directory loader accepts contiguous `angle_k_0.kmb` through `angle_k_18.kmb` (or consistently kmx). The Python API also accepts an ordered list of arbitrary paths or Circuit objects. This only changes the source of the ordered family: exact circuit count, fixed register layout and positional output order still apply. Extra helper/identity files do not provide a free prefix stage.

After **every file**, the verifier checks zero quantum workspace, preserved selection and zero phase. It then clears simulator state and restores **only selection and word values**. Neither quantum scratch nor classical measurement bits can carry a prefix into the next file. Prefix sharing is possible inside one circuit, across its internal subcomputations, followed by correct cleanup.

The303-qubit temporary cost floor does not override the128-qubit angle-circuit cap. J4 has at most85 angle workspace qubits, versus77 at J5. Unused or named extra qubits still count through `Circuit.num_qubits`; the11-qubit selection width cannot be enlarged to hide them.

## Existing v27 structure and reusable controls

All15 accepted loaders were read without modification; their static Toffoli counts sum to4030. For k1 through k14 the exact common high-address prefix has **68 CCX**, and six further CCX complete the low-address features. The prefix total is74. Its HMR and conditioned-CZ cleanup has no extra CCX. The first circuit has initialization interleaved with nonlinear control updates and needs separate treatment; the old simple output-window extractor does not apply to it unchanged.

The actual recovered1220×75 angle table satisfies, for every address and every column,

\[
\mathrm{{bit}}_6(w_c)\oplus\mathrm{{bit}}_7(w_c)=a_p a_q,
\]

where the pairs repeat with column modulo5 as (0,1), (0,2), (1,2), (0,3), (1,3). A CX exposes this known tag at no Toffoli cost **on the appropriate reachable input batch**. At J5 the same slot has the same tag in each batch. At J4 the four present tags rotate; incoming and outgoing tag layouts differ, and the last padded slot is zero. At k0 all incoming words are zero, so no such preloaded tags exist.

The JSON also computes the exact intersection of each batch's word/address linear span with functions of the low four address bits. This records which of the five tags really are available without a nonlinear gate. It does not assume that a changing tag remains available across a circuit boundary.

Completing the full low-four-bit monomial basis from four distinct preloaded tags naturally takes seven missing products, rather than the six used with five tags. This is a basis-construction estimate, **not a complete J4 loader cost**: changing tags, word-output synthesis, cleanup and the reverse path still need a correct construction. The smaller word bank does free eight physical qubits under the cap, which can help that construction.

The output accumulation blocks mix many target bits by CX gates. Deleting all gates aimed at unwanted physical output qubits is not a valid way to project onto a smaller word subset. Each CCX's complete output direction must be propagated through the suffix. In addition, the new transition function is old-new-batch XOR new-new-batch; it is not generally a projection of one old J5 transition.

The accepted NPZ declaration differs from the actual decoded table in473 entries. Rebatch synthesis must use the hash-pinned recovered words, not silently replace them with the declared `angle_words` array, if it intends to retain the accepted chemistry metrics.

## Reordering and the exact oracle claim

Noncontiguous old angles can only be grouped by changing their order in the decoded table and correspondingly changing/re-encoding `tree_edges`. The verifier requires a rooted tree in parent-before-child order, but that condition alone does not preserve the old vector. Ordered Givens rotations sharing a vertex generally do not commute. Swapping disjoint rotations preserves the vector exactly; any more general permutation needs a separate equivalence or physics check.

The written circuit contract specifies an arbitrary-target XOR oracle. The executable verifier checks its forward and reverse reachable batches. A proof that word6 XOR word7 equals an address product on those batches is not a proof for arbitrary targetz. Candidate reviews must state whether they establish the reachable isometry, the arbitrary-target XOR extension, or both. This distinction already applies to the inherited tag-based public loaders and should not be hidden by rebatching.

X/CX/CZ and classical logic are not charged as Toffoli-like operations; HMR/R are available with correct phase and cleanup. CCX/CCZ/CSWAP contribute actual executed counts. Z_POW is explicitly rejected. Reaction depth and instruction count are reported but do not multiply this task's scalar score.

## Evidence and reproduction

`score9_rebatch_contract.json` pins the official source files, accepted scorecards, NPZ, recovered actual words and all15 circuit files, and records function source locations. `score9_rebatch_contract.py` calls only the official scalar heuristic helper and reads circuits/arrays; it does not run `verify` or mutate a submission. Re-run it with the existing Kickmix Python environment to reproduce both the JSON and this report.
'''
    (REPO/'score9_rebatch_contract.md').write_text(text)
    print(json.dumps(dict(status=result['status'], J4=rows[3], files=['score9_rebatch_contract.json','score9_rebatch_contract.md']),indent=2))


if __name__ == '__main__':
    main()
