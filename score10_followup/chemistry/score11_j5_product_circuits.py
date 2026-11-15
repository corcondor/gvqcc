#!/usr/bin/env python3
"""Search exact shared-product rewrites using small output-direction dependencies."""
import argparse
from collections import Counter, defaultdict
from itertools import combinations
import hashlib
import json
from pathlib import Path
import sys
import time

import kickmix as km
import numpy as np


def highlow_matrix(value, rows):
    low = value & 65535
    if value & 1:
        low ^= 65535
    matrix = []
    for h in range(rows):
        row = ((value >> (16*h)) & 65535) ^ low
        if row & 1:
            row ^= 65535
        matrix.append(row >> 1)
    return tuple(matrix)


def xor_matrix(a, b):
    return tuple(x ^ y for x, y in zip(a, b))


def rank(vectors):
    pivots = {}
    for value in vectors:
        while value:
            pivot = value.bit_length() - 1
            if pivot not in pivots:
                pivots[pivot] = value
                break
            value ^= pivots[pivot]
    return len(pivots)


def dependency_search(forms):
    """With XOR dependency on output directions, pivot one complete product."""
    # Combine sparse pair collisions to enumerate all dependencies of size 3/4.
    out = defaultdict(list)
    for i, (_, _, w) in enumerate(forms):
        out[w].append(i)
    pairs = defaultdict(list)
    for i, j in combinations(range(len(forms)), 2):
        pairs[forms[i][2] ^ forms[j][2]].append((i, j))
    deps = set()
    for direction, candidates in pairs.items():
        for i, j in candidates:
            for k in out.get(direction, ()):
                if j < k:
                    deps.add((i, j, k))
        for left, right in combinations(candidates, 2):
            if not set(left).intersection(right):
                deps.add(tuple(sorted((*left, *right))))
    return sorted(deps)


def evaluate_subset(terms, products, rows):
    matrices = [highlow_matrix(p, rows) for p in products]
    deps = dependency_search(terms)
    result = dict(products=len(terms), dependencies=dict(Counter(map(len, deps))),
                  minimum_replacement_by_size={}, positive_candidates=[])
    cache = {}
    for dep in deps:
        original_count = len(dep)
        costs = []
        for pivot in dep:
            new_count = 0
            for i in dep:
                if i == pivot:
                    continue
                indices = tuple(sorted((i, pivot)))
                if indices not in cache:
                    r = rank(xor_matrix(matrices[i], matrices[pivot]))
                    cache[indices] = (r + 1) // 2
                new_count += cache[indices]
            costs.append(new_count)
            if new_count < original_count:
                result["positive_candidates"].append(dict(pivot=pivot, dependency=dep,
                                                          replacement_count=new_count))
        minimum = min(costs)
        key = str(original_count)
        result["minimum_replacement_by_size"][key] = min(
            result["minimum_replacement_by_size"].get(key, minimum), minimum)
    result['unique_pair_ranks'] = len(cache)
    return result


def star_search(terms, products, rows):
    """Test every pivot with all other products that can share a one-AND sum."""
    matrices = [highlow_matrix(p, rows) for p in products]
    neighbors = [[] for _ in terms]
    pair_histogram = Counter()
    for i, j in combinations(range(len(terms)), 2):
        # A mixed product of two separable high/low forms has cross rank <= 2.
        # Consequently rank > 2 rules out one such product even if the
        # high-only and low-only correction spaces are completely available.
        basis = {}
        for a, b in zip(matrices[i], matrices[j]):
            value = a ^ b
            while value:
                pivot = value.bit_length() - 1
                if pivot not in basis:
                    basis[pivot] = value
                    break
                value ^= basis[pivot]
            if len(basis) > 2:
                break
        pair_histogram[len(basis)] += 1
        if len(basis) <= 2:
            neighbors[i].append(j)
            neighbors[j].append(i)
    hits = []
    for i, indices in enumerate(neighbors):
        # Rank-zero sums are separate opportunities which need linear
        # corrections rather than one AND. Record them even without a star.
        basis = {}
        for j in indices:
            value = terms[j][2]
            support = 1 << j
            while value:
                pivot = value.bit_length() - 1
                if pivot not in basis:
                    basis[pivot] = (value, support)
                    break
                v, expression = basis[pivot]
                value ^= v
                support ^= expression
        value = terms[i][2]
        support = 0
        while value:
            pivot = value.bit_length() - 1
            if pivot not in basis:
                break
            v, expression = basis[pivot]
            value ^= v
            support ^= expression
        if value == 0:
            indices = [j for j in indices if support >> j & 1]
            assert len(indices) and i not in indices
            hits.append(dict(pivot=i, partners=indices))
    return dict(pair_cross_ranks_0_through_2_and_greater=pair_histogram,
                maximum_neighbors=max(map(len, neighbors)),
                positive_candidates=hits)

def rank2_sum(left, right):
    basis = {}
    for a, b in zip(left, right):
        value = a ^ b
        while value:
            pivot = value.bit_length() - 1
            if pivot not in basis:
                basis[pivot] = value
                break
            value ^= basis[pivot]
        if len(basis) > 2:
            return None
    return tuple(a ^ b for a, b in zip(left, right))


def multistep_closure(terms, products, rows, cap):
    """Close the original bilinear components under every rank<=2 pair XOR."""
    matrices = [highlow_matrix(p, rows) for p in products]
    # If exact cofactor matrices are independent, each new matrix has a
    # unique XOR expression of the original products on this care subset.
    flattened = [sum(row << (15*i) for i, row in enumerate(m)) for m in matrices]
    cofactor_rank = rank(flattened)
    assert cofactor_rank == len(matrices)
    index = {m: i for i, m in enumerate(matrices)}
    support = [1 << i for i in range(len(matrices))]
    parents = list(range(len(matrices)))

    def root(i):
        while parents[i] != i:
            parents[i] = parents[parents[i]]
            i = parents[i]
        return i

    def union(mask):
        first_bit = mask & -mask
        a = root(first_bit.bit_length()-1)
        mask ^= first_bit
        while mask:
            bit = mask & -mask
            b = root(bit.bit_length()-1)
            parents[b] = a
            mask ^= bit

    complete = True
    pair_checks = 0
    for i, left in enumerate(matrices):
        for j in range(i):
            pair_checks += 1
            right = matrices[j]
            total = rank2_sum(left, right)
            if total is None:
                continue
            combined = support[i] ^ support[j]
            union(support[i] | support[j])
            if total in index:
                assert support[index[total]] == combined
                continue
            index[total] = len(matrices)
            matrices.append(total)
            support.append(combined)
            if len(matrices) >= cap:
                complete = False
                break
        if not complete:
            break
    components = defaultdict(list)
    for i in range(len(terms)):
        components[root(i)].append(i)
    dependent = [indices for indices in components.values()
                 if rank([terms[i][2] for i in indices]) < len(indices)]
    return dict(closure_complete=complete, closure_size=len(matrices), pair_checks=pair_checks,
                original_cofactor_rank=cofactor_rank,
                components_histogram=dict(Counter(map(len, components.values()))),
                dependent_output_components=dependent)

def positive_control():
    # Three products have common low components and independent high support.
    # Their output directions 1, 2, 3 sum to zero, giving a 3-to-2 rewrite.
    rows = 7
    low_x = sum(1 << l for l in range(16) if l & 1)
    low_y = sum(1 << l for l in range(16) if l & 2)
    products = [(low_x << (16 * (1 + 2*i))) | (low_y << (16 * (2 + 2*i)))
                for i in range(3)]
    terms = [(0, 0, i+1) for i in range(3)]
    direct = evaluate_subset(terms, products, rows)
    star = star_search(terms, products, rows)
    closure = multistep_closure(terms, products, rows, cap=50)
    assert direct['minimum_replacement_by_size'] == {'3': 2}
    assert len(star['positive_candidates']) == 3
    assert closure['closure_complete'] and closure['closure_size'] == 7
    assert closure['dependent_output_components'] == [[0, 1, 2]]
    p, q, r = products
    for a in range(16 * rows):
        before = ((p >> a) & 1) ^ (2 * ((q >> a) & 1)) ^ (3 * ((r >> a) & 1))
        after = (((p ^ r) >> a) & 1) ^ (2 * (((q ^ r) >> a) & 1))
        assert before == after
    return dict(original_products=3, replacement_products=2,
                direct=direct, star=star, closure=closure)

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repo', required=True, type=Path)
    parser.add_argument('--loaders', required=True, type=Path)
    parser.add_argument('--words', required=True, type=Path)
    parser.add_argument('--output', required=True, type=Path)
    parser.add_argument('--closure-cap', type=int, default=4000)
    args = parser.parse_args()
    sys.path.insert(0, str(args.repo))
    from chemistry_affine_span_resynthesis import parse_line
    from chemistry_joint_product_resynthesis import DATA_INDEX, extract
    from chemistry_relation_screen import advance, evaluate_form
    from chemistry_reachable_exact_proof import pack

    words = np.load(args.words, allow_pickle=False).astype(np.uint64)
    assert words.shape in {(1220, 75), (1232, 75)}
    # Use 76 full address rows, a restriction of the care domain. A negative
    # result continues to hold after adding the final four care addresses.
    n = 1216
    addr = np.arange(n, dtype=np.uint64)
    one = (1 << n) - 1
    result = []
    pins = {}
    positive = positive_control()
    started = time.monotonic()
    for k in range(15):
        path = args.loaders / f'angle_k_{k}.kmb'
        pins[path.name] = hashlib.sha256(path.read_bytes()).hexdigest()
        c = km.Circuit.from_file(path)
        lines = str(c).splitlines()
        parsed = [parse_line(line) for line in lines]
        values = [0] * c.num_qubits
        values[:11] = [pack((addr >> q) & 1) for q in range(11)]
        if k:
            for j in range(5):
                for b in range(8):
                    values[11 + 8*j + b] = pack((words[:n, 5*(k-1)+j] >> b) & 1)
        entry = []
        for operation, qubits, condition in parsed:
            entry.append(tuple(values))
            advance(values, operation, qubits, one)
        core = [i for i, (g, q, _) in enumerate(parsed) if g == 'CCX' and q[-1] in DATA_INDEX]
        first, last = min(core), max(core)+1
        cuts = []
        for i in range(first, last):
            g, q, cond = parsed[i]
            if (cond is not None or g not in ('X', 'CX', 'CCX')
                or g == 'CCX' and q[-1] not in DATA_INDEX
                or g == 'CX' and q[0] in DATA_INDEX and q[1] not in DATA_INDEX):
                cuts.append(i)
        for start, stop in zip([first] + [i+1 for i in cuts], cuts + [last]):
            if not any(start <= i < stop for i in core):
                continue
            ex = extract(km.Circuit('\n'.join(lines[start:stop]) + '\n'))
            state = entry[start + ex['first']]
            products = []
            for u, v, _ in ex['terms']:
                factors = [evaluate_form(mask, state, one) for mask in (u, v)]
                assert all(rank(highlow_matrix(f, n//16)) == 0 for f in factors)
                products.append(factors[0] & factors[1])
            report = evaluate_subset(ex['terms'], products, n//16)
            report['star'] = star_search(ex['terms'], products, n//16)
            report['closure'] = multistep_closure(ex['terms'], products, n//16, args.closure_cap)
            result.append(dict(k=k, first=start, last=stop, **report))
            print(json.dumps(result[-1]), flush=True)
    all_improvements = sum(len(row['positive_candidates']) + len(row['star']['positive_candidates']) for row in result)
    args.output.write_text(json.dumps(
        dict(status='SCREEN_COMPLETE', address_count=n, candidates=all_improvements,
             seconds=time.monotonic()-started, segments=result,
             positive_control=positive, source_loader_sha256=pins,
             words_sha256=hashlib.sha256(args.words.read_bytes()).hexdigest()), indent=2) + '\n')


if __name__ == '__main__':
    main()
