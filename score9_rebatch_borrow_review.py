#!/usr/bin/env python3
"""Independent rank-identity audit and a data-pair extension of rebatch borrowing.

Uses low-address indicator functions (not monomials), low-pivot elimination,
and a paired-image rank identity (not the original nullspace enumeration).
No circuit is emitted, changed or run; no full verifier or submission occurs.
"""
from __future__ import annotations

import hashlib
import itertools
import json
from pathlib import Path
import time

import numpy as np


ROOT = Path(__file__).resolve().parent
WORDS = ROOT / 'score8_chem_v27_recovered_words.npy'


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def pack(vector):
    # Independent string conversion, checked against the least/most index.
    vector = np.asarray(vector, dtype=np.uint8)
    return int(''.join('1' if item else '0' for item in vector[::-1]), 2)


class LowPivotBasis:
    def __init__(self, other=None):
        self.rows = {} if other is None else dict(other.rows)

    def add(self, value, expression=0):
        while value:
            pivot = (value & -value).bit_length() - 1
            known = self.rows.get(pivot)
            if known is None:
                self.rows[pivot] = value, expression
                return True, expression
            row, rep = known
            value ^= row
            expression ^= rep
        return False, expression

    def reduce(self, value, expression=0):
        while value:
            pivot = (value & -value).bit_length() - 1
            if pivot not in self.rows:
                return value, expression
            row, rep = self.rows[pivot]
            value ^= row
            expression ^= rep
        return 0, expression

    def __len__(self):
        return len(self.rows)


def xor_selected(values, expression):
    result = 0
    while expression:
        bit = expression & -expression
        expression ^= bit
        result ^= values[bit.bit_length()-1]
    return result


def evaluate(previous, current, include_data_pairs=False):
    n, J = previous.shape
    address = np.arange(n)
    low = [pack((address & 15) == r) for r in range(16)]
    high = [pack((address >> 4) == h) for h in range((n+15)//16)]
    f_basis = LowPivotBasis()
    for f in low + high:
        f_basis.add(f)
    pure_f = [row for row, _ in f_basis.rows.values()]
    before = [pack((previous[:,j] >> b) & 1) for j in range(J) for b in range(8)]
    after = [pack((current[:,j] >> b) & 1) for j in range(J) for b in range(8)]
    delta = [a ^ b for a, b in zip(before, after)]
    p0, p1, names = [], [], []
    for r, l in enumerate(low):
        for i in range(8*J):
            p0.append(l & before[i]); p1.append(l & after[i])
            names.append(dict(type='low_indicator_times_data', residue=r, data_bit=i))
    if include_data_pairs:
        for i, j in itertools.combinations(range(8*J), 2):
            p0.append(before[i] & before[j]); p1.append(after[i] & after[j])
            names.append(dict(type='data_times_data', data_bits=[i,j]))

    difference_basis = LowPivotBasis()
    paired_basis = LowPivotBasis()
    generators = []
    for f in pure_f:
        generators.append(f | (f << n))
    generators += [a | (b << n) for a, b in zip(p0,p1)]
    for index, value in enumerate(generators):
        paired_basis.add(value, 1 << index)
    for a, b in zip(p0,p1):
        difference_basis.add(a ^ b)
    # The map D:(a,b)->a+b sends the paired image onto the difference image.
    # Its kernel is the diagonal/common image; rank-nullity is exact.
    common_rank = len(paired_basis) - len(difference_basis)
    quotient_new = common_rank - len(f_basis)
    assert quotient_new >= 0
    before_targets = LowPivotBasis(f_basis)
    after_targets = LowPivotBasis(paired_basis)
    witnesses = []
    all_individual = []
    for bit, d in enumerate(delta):
        old_residual, _ = f_basis.reduce(d)
        new_residual, rep = paired_basis.reduce(d | (d << n))
        if old_residual and not new_residual:
            assert xor_selected(generators, rep) == (d | (d << n))
            all_individual.append(bit)
            witnesses.append(dict(output_bit=bit, expression_hex=hex(rep),
                                  product_terms=(rep >> len(pure_f)).bit_count(),
                                  contains_target_in_product=any(
                                      (rep >> (len(pure_f)+i)) & 1 and
                                      (desc.get('data_bit') == bit or bit in desc.get('data_bits', []))
                                      for i,desc in enumerate(names))))
        before_targets.add(d)
        after_targets.add(d | (d << n))
    before_rank = len(before_targets) - len(f_basis)
    after_rank = len(after_targets) - len(paired_basis)
    return dict(
        addresses=n, data_bits=8*J, low_basis='all16 low-address indicator functions',
        low_times_data_generators=16*8*J,
        data_pair_generators=(8*J)*(8*J-1)//2 if include_data_pairs else 0,
        total_generators=len(p0), free_address_rank=len(f_basis),
        paired_image_rank_including_diagonal_address=len(paired_basis),
        branch_difference_rank=len(difference_basis),
        symmetric_image_rank_including_address=common_rank,
        symmetric_kernel_dimension=len(p0)-len(difference_basis),
        additional_symmetric_function_rank_mod_address=quotient_new,
        target_delta_quotient_rank_before=before_rank,
        target_delta_quotient_rank_after=after_rank,
        target_span_dimension_gained=before_rank-after_rank,
        individual_newly_representable_output_bits=all_individual,
        individual_witnesses=witnesses,
    )


def main():
    started = time.monotonic()
    record_path = ROOT/'score9_rebatch_borrow.json'
    source_path = ROOT/'score9_rebatch_borrow.py'
    recorded = json.loads(record_path.read_text())
    assert recorded['source_sha256'] == sha(WORDS)
    assert recorded['script_sha256'] == sha(source_path)
    assert recorded['J'] == 4
    words = np.load(WORDS, allow_pickle=False).astype(np.uint64)
    assert words.shape == (1220,75)
    padded = np.pad(words, ((0,0),(0,1)))
    checks, extended = [], []
    compare_fields = {
        'free_address_rank':'free_address_function_rank',
        'branch_difference_rank':'forward_reverse_difference_rank',
        'symmetric_kernel_dimension':'symmetric_product_kernel_dimension',
        'additional_symmetric_function_rank_mod_address':'new_common_function_rank',
        'target_delta_quotient_rank_before':'target_delta_rank_mod_address_functions',
        'target_delta_quotient_rank_after':'target_delta_rank_after_borrowing',
        'target_span_dimension_gained':'target_span_dimension_gained',
        'individual_newly_representable_output_bits':'individual_newly_representable_output_bits',
    }
    for k in range(19):
        previous = padded[:,4*(k-1):4*k] if k else np.zeros((1220,4),np.uint64)
        current = padded[:,4*k:4*(k+1)]
        audit = evaluate(previous,current)
        for ours, theirs in compare_fields.items():
            assert audit[ours] == recorded['rows'][k][theirs], (k, ours, audit[ours], recorded['rows'][k][theirs])
        checks.append(dict(k=k, matches_original=True, **audit))
        ext = evaluate(previous,current,include_data_pairs=True)
        extended.append(dict(k=k, **ext))
        print(json.dumps(dict(k=k, original_agrees=True,
                              data_pair_new_rank=ext['additional_symmetric_function_rank_mod_address'],
                              data_pair_target_gain=ext['target_span_dimension_gained'],
                              data_pair_new_outputs=ext['individual_newly_representable_output_bits'])),flush=True)

    result = dict(
        status='INDEPENDENT_LOW_DATA_SCREEN_REVIEW_PASS',
        reviewed_source=dict(path=str(source_path),sha256=sha(source_path)),
        reviewed_result=dict(path=str(record_path),sha256=sha(record_path)),
        actual_words=dict(path=str(WORDS),sha256=sha(WORDS)),
        review_source_sha256=sha(__file__),
        independent_method={
            'low_basis':'16 disjoint residue indicators, instead of original Boolean monomials; both span every low4 function.',
            'elimination':'Low-bit pivots, instead of original high-bit pivots.',
            'rank_identity':'Let V be the image spanned by paired (forward,reverse) product values plus diagonal pure-address functions F. D(a,b)=a XOR b. The common diagonal image has dimension rank(V)-rank(D(V)); its additional dimension modulo F is rank(V)-rank(D(V))-rank(F).',
            'target_test':'A diagonal target belongs to the common image iff it lies in V. Adding all diagonal targets gives their residual quotient rank without constructing a nullspace basis.',
            'root_kernel_completeness':'Each dependent generator creates a relation containing its own previously unseen generator coordinate. These relations are independent, and there are m-rank(D) of them, hence they form the full difference kernel.',
        },
        findings={
            'blocking_errors':[],
            'all19_rank_results_reproduced':True,
            'original_added_symmetric_rank_is_zero':all(x['additional_symmetric_function_rank_mod_address']==0 for x in checks),
            'nonblocking_label_issue':'Original symmetric_functions_before_quotient_rank is actually rank(F + common image), since the basis is initialized with F; it is not the rank of common image alone. With zero extra rank it equals92. The reported zero new_common_function_rank and target conclusions remain correct.',
            'no_global_lower_bound':'The result is limited to simultaneous unstaged sums of L(low4)*data on the two specified reachable word states, modulo all pure-low/pure-high functions. It says nothing about high-dependent coefficients, data-data products, staged data updates, changed words, measurement architectures or general reversible circuits.',
            'no_cost_lower_bound':'Pure-low/high functions are quotiented out as a mathematical space, not proved available with zero gates. Zero extra function rank also does not prove that existing functions cannot be synthesized more cheaply by borrowing.',
        },
        original_checks=checks,
        data_pair_extension={
            'scope':'Adds all496 pairwise products d_i*d_j, i<j, of the32 incoming word bits to all512 low-times-data generators. Boolean squares are already included as data terms. This spans arbitrary degree2 polynomials in incoming data with constant coefficients, plus arbitrary low4-times-linear-data terms and pure-low/pure-high functions.',
            'further_limits':'No low-dependent coefficients on data-data pairs, high-dependent data products, cubic data terms, staged updates, or arbitrary-target extension is claimed. Representability alone is not a legal reversible mutation or a gate saving.',
            'rows':extended,
            'any_additional_symmetric_function':any(x['additional_symmetric_function_rank_mod_address'] for x in extended),
            'any_new_target_direction':any(x['target_span_dimension_gained'] for x in extended),
            'any_new_individual_output':any(x['individual_newly_representable_output_bits'] for x in extended),
        },
        circuits_written=False, official_verifier_run=False, submission_performed=False,
        seconds=time.monotonic()-started,
    )
    out = ROOT/'score9_rebatch_borrow_review.json'
    out.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(dict(status=result['status'], original_added_rank_zero=result['findings']['original_added_symmetric_rank_is_zero'],
                          extension_added_rank=result['data_pair_extension']['any_additional_symmetric_function'],
                          extension_target_gain=result['data_pair_extension']['any_new_target_direction'],
                          seconds=result['seconds'])),flush=True)


if __name__ == '__main__':
    main()
