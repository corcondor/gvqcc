#!/usr/bin/env python3
"""Verify quotient kernels and search an induced product-support hypergraph."""
from argparse import ArgumentParser
from collections import Counter, defaultdict
import hashlib
import itertools
import json
from pathlib import Path
import random
import struct


def indices(number):
    while number:
        bit = number & -number
        yield bit.bit_length() - 1
        number ^= bit


def remainder(value, basis):
    while value:
        found = basis.get(value.bit_length() - 1)
        if found is None:
            break
        value ^= found
    return value


def insert(value, basis):
    value = remainder(value, basis)
    if value:
        basis[value.bit_length() - 1] = value
    return bool(value)


def output_kernel(directions):
    basis = {}
    relations = []
    for i, direction in enumerate(directions):
        proof = 1 << i
        while direction:
            pivot = direction.bit_length() - 1
            if pivot not in basis:
                basis[pivot] = direction, proof
                break
            row, mask = basis[pivot]
            direction ^= row
            proof ^= mask
        if not direction:
            relations.append(proof)
    return relations


def xor_span(basis):
    out = [0]
    for value in basis:
        out += [member ^ value for member in out]
    return out


def candidates(relations, seed):
    if len(relations) <= 16:
        return xor_span(relations)[1:], True
    rng = random.Random(seed)
    out = set(relations)
    for weight in (2, 3):
        for _ in range(2048):
            member = 0
            for value in rng.sample(relations, weight):
                member ^= value
            out.add(member)
    return sorted(out), False


def components(n, masks):
    groups = [1 << i for i in range(n)]
    for mask in masks:
        combined = 0
        for i in indices(mask):
            combined |= groups[i]
        for i in indices(combined):
            groups[i] = combined
    return sorted(set(groups))


def lower_schedule(directions, masks, seed):
    dependent = 0
    searches = 0
    complete = True
    reduction = None
    for component in components(len(directions), masks):
        local_indices = list(indices(component))
        rels = output_kernel([directions[i] for i in local_indices])
        if not rels:
            continue
        dependent += 1
        output_cols = {}
        for i in local_indices:
            for j in indices(directions[i]):
                output_cols[j] = output_cols.get(j, 0) | (1 << i)
        local_dict = sorted(v for v in masks if v & component == v)
        witness, settled = candidates(rels, seed)
        complete &= settled
        for w in witness:
            searches += 1
            global_w = sum(1 << local_indices[j] for j in indices(w))
            available = {}
            selected = []
            for v in local_dict:
                if not (v & global_w).bit_count() % 2 and insert(v, available):
                    selected.append(v)
            if all(not remainder(v, available) for v in output_cols.values()):
                assert len(selected) < len(local_indices)
                reduction = dict(removed=len(local_indices)-len(selected), witness=hex(global_w),
                                 component=hex(component), keep=[hex(v) for v in selected])
                break
        if reduction:
            break
    return dict(dependent_components=dependent, hyperplanes_tested=searches,
                exhaustive_hyperplanes=complete, witnessed_reduction=reduction,
                component_sizes=dict(Counter(mask.bit_count()
                     for mask in components(len(directions), masks))))


def algebra_fixture():
    # Six edge vectors of a cycle produce exactly a five-term relation
    # after quotienting by the first edge and a shared independent column.
    # Verify the result here independently by brute force.
    dim = 6
    first_edge = 3
    shared = 1 << 9
    projected = [(1 << i) ^ (1 << ((i+1) % dim)) for i in range(dim)]
    admissible = []
    for mask in range(1, 1 << dim):
        left = 0
        for i in indices(mask):
            left ^= projected[i]
        if left in (0, first_edge, shared, first_edge ^ shared):
            admissible.append(mask)
    assert admissible == [1, 62, 63]
    result = lower_schedule([1,2,2,2,2,2], set(admissible) | {1<<i for i in range(dim)}, 1)
    assert result['witnessed_reduction']
    return dict(valid_masks=admissible, result=result)


def flatten(matrix):
    return sum(row << (16*i) for i, row in enumerate(matrix))


def derive(words, masks):
    value = 0
    for i in indices(masks):
        value ^= words[i]
    return value


def verify_contained(matrix, plane):
    a,b = plane
    allowed = {0,a,b,a^b}
    for i in range(76):
        assert (matrix >> (16*i)) & 65535 in allowed


def main():
    cli = ArgumentParser(description=__doc__)
    cli.add_argument('--matrices',type=Path,required=True)
    cli.add_argument('--segments',type=Path,required=True)
    cli.add_argument('--kernels',type=Path,required=True)
    cli.add_argument('--counts',type=Path,required=True)
    cli.add_argument('--known',type=Path,nargs='*',default=[])
    cli.add_argument('--out',type=Path,required=True)
    args = cli.parse_args()
    data = args.matrices.read_bytes()
    segments = json.loads(args.segments.read_text())
    basis_groups = defaultdict(lambda: defaultdict(list))
    base = defaultdict(set)
    for line in args.kernels.read_text().splitlines():
        k,a,b,*words = line.split()
        n = sum(int(v,16) << (64*i) for i,v in enumerate(words))
        basis_groups[int(k)][(int(a),int(b))].append(n)
    for p in args.known:
        for line in p.read_text().splitlines():
            k,*terms=map(int,line.split())
            base[k].add(sum(1<<i for i in terms))
    counts = [tuple(map(int,line.split())) for line in args.counts.read_text().splitlines()]
    assert len(counts) == len(segments)
    report = []
    offset = 0
    for index,meta in enumerate(segments):
        n=struct.unpack_from('<I',data,offset)[0]
        offset+=4
        values=[flatten(cs) for cs in struct.iter_unpack('<76H',data[offset:offset+n*152])]
        offset+=n*152
        rank_check={}
        assert all(insert(v,rank_check) for v in values)
        direct={1<<i for i in range(n)}
        known = direct | base[index]
        extra = set()
        maxdim = 0
        for p,relations in basis_groups[index].items():
            independent={}
            assert all(insert(v,independent) for v in relations)
            for mask in relations:
                verify_contained(derive(values,mask),p)
            maxdim=max(maxdim,len(relations))
            assert len(relations)<=16, 'larger kernel needs an explicit enumeration policy'
            extra.update(xor_span(relations)[1:])
        assert direct <= extra
        s,n2,trials,nrelations,dim,*fallbacks = counts[index]
        assert (s,n2,dim)==(index,n,maxdim)
        assert nrelations == sum(map(len,basis_groups[index].values()))
        novel = extra - known
        result = lower_schedule(meta['directions'], extra|known, index)
        row=dict(segment=index,batch=meta['batch'],original_terms=n,
                 trial_low_planes=trials,kernel_basis_entries=nrelations,
                 maximum_kernel_dimension=maxdim,full_elimination_fallbacks=(fallbacks[0] if fallbacks else None),
                 discovered_masks=len(extra),
                 outside_seed_products=len(novel),
                 support_size_histogram=dict(Counter(v.bit_count() for v in novel)),**result)
        report.append(row)
        print(json.dumps(row))
    assert offset==len(data)
    args.out.write_text(json.dumps(dict(
        matrix_sha256=hashlib.sha256(data).hexdigest(),comparison_address_count=1216,
        positive_fixture=algebra_fixture(),rows=report),indent=2)+'\n')


if __name__=='__main__':
    main()
