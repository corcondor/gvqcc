#!/usr/bin/env python3
"""Normalized quadratic-extension consuming product with one field-word buffer."""
import argparse
import hashlib
import json
from pathlib import Path
import sys

import kickmix as km
import numpy as np


def images(function):
    return [function(1 << j) for j in range(12)]


def dual_mask(mask, columns):
    return sum(((mask & column).bit_count() % 2) << j
               for j, column in enumerate(columns))


def streamed_prefix(builder, source, target, delta):
    """Consume x+yθ into (1+rθ)*(x+yθ), deferring the phase of d=r*y."""
    from field_tensor import accumulate_product
    from tower_inverse import kernel, xor_product
    from quantum_reciprocal import xor_linear

    # The source's low half is the public pivot 1 in this chart.
    r = source[12:]
    x, y = target[:12], target[12:]
    d = builder.alloc_qubits(12)
    xor_product(builder, r, y, d)
    field = km.GF2Field(12)
    delta_cols = images(lambda z: field.mul(delta, z))
    xor_linear(builder, d, x, delta_cols)
    builder.cx(d, y)
    # (x + δd) in this frame is the original x. Select that control parity
    # directly, including the live d coordinate, without saving old x.
    terms = [(a, b | (dual_mask(b, delta_cols) << 12), c) for a,b,c in kernel(12)]
    accumulate_product(builder, r, km.array([*x, *d]), y, terms)
    mask = builder.alloc_bits(12)
    builder.hmr(d, mask)
    builder.free(d)
    return mask


def projected_accumulate(builder, source, target, d, tensor, *, conjugate=False):
    """Substitute the fixed chart into every factor of the rank99 baseline."""
    from field_tensor import parity_pivot, accumulate_product
    from collections import defaultdict

    groups = defaultdict(int)
    for a, b, output in tensor:
        variable = (a >> 12) ^ ((a & 4095) if conjugate else 0)
        groups[variable, a & 1, b] ^= output
    for (r_mask, constant, y_mask), output in groups.items():
        if not output:
            continue
        if not r_mask:
            if constant:
                y = parity_pivot(builder, target, y_mask)
                for i in range(24):
                    if output >> i & 1:
                        builder.cx(y, d[i])
                parity_pivot(builder, target, y_mask)
            continue
        pivot = next(i for i in range(12) if r_mask >> i & 1)
        if constant:
            builder.x(source[12 + pivot])
        accumulate_product(builder, source[12:], target, d, [(r_mask, y_mask, output)])
        if constant:
            builder.x(source[12 + pivot])


def projected_reference_prefix(builder, source, target, tensor):
    d = builder.alloc_qubits(24)
    projected_accumulate(builder,source,target,d,tensor)
    builder.swap(target, d)
    mask = builder.alloc_bits(24)
    builder.hmr(d, mask)
    builder.free(d)
    return mask


def norm_add(builder, r, target, delta, field):
    """Toggle N(r) = 1+r+delta*r² into a disjoint register using Clifford gates."""
    from quantum_reciprocal import xor_linear

    builder.x(target[0])
    xor_linear(builder, r, target, images(lambda z: z ^ field.mul(delta,field.mul(z,z))))


def projected_closing(builder, source, target, record, A):
    """Same closing schedule, with affine norm and projected adjoint."""
    old_init, old_erase, old_product = A.init_norm, A.erase_norm, A.product

    def affine_init(b, left, r, delta):
        n = b.alloc_qubits(12)
        norm_add(b,r,n,delta,A.FIELD)
        return n

    def affine_erase(b, left, r, n, delta):
        norm_add(b,r,n,delta,A.FIELD)

    def specialised_adjoint(b, s, v, out, delta, tensor):
        projected_accumulate(b,s,v,out,tensor,conjugate=True)

    A.init_norm, A.erase_norm, A.product = affine_init, affine_erase, specialised_adjoint
    try:
        A.emit_closing(builder, source, target, record)
    finally:
        A.init_norm, A.erase_norm, A.product = old_init, old_erase, old_product


def borrowed_return(builder, source, target, prefix_mask, delta, A):
    """Compute reciprocal norm in the caller's fixed lower source half."""
    from field_tensor import accumulate_product
    from tower_inverse import kernel, phase_product, xor_product
    from modular_quadratic_direct import repay_twelve_source

    r, norm = source[12:], source[:12]
    x, y = target[:12], target[12:]
    xor_product(builder,r,x,y)
    builder.x(norm[0])  # clear the known a=1 word
    norm_add(builder,r,norm,delta,A.FIELD)
    debts = A.Prior.inverse_twelve_deferred(builder,norm)
    d = builder.alloc_qubits(12)
    # Repay the inversion's entry mask while its input is recoverable from r.
    norm_add(builder,r,d,delta,A.FIELD)
    repay_twelve_source(builder,d,debts)
    norm_add(builder,r,d,delta,A.FIELD)
    xor_product(builder,norm,y,d)
    builder.swap(y,d)
    old_y = builder.alloc_bits(12)
    builder.hmr(d,old_y)
    builder.free(d)
    inverse_mask = builder.alloc_bits(12)
    builder.hmr(norm,inverse_mask)
    norm_add(builder,r,norm,delta,A.FIELD)
    A.Phase12.phase_inverse_twelve_polynomial(builder,norm,inverse_mask)
    builder.free(inverse_mask)
    phase_product(builder,norm,y,old_y,kernel(12))
    builder.free(old_y)
    norm_add(builder,r,norm,delta,A.FIELD)
    builder.x(norm[0])  # restore caller's constant source word
    accumulate_product(builder,r,y,x,[(a,b,A.FIELD.mul(delta,c)) for a,b,c in kernel(12)])
    phase_product(builder,r,y,prefix_mask,kernel(12))
    builder.free(prefix_mask)


def streamed_return(builder, source, target, prefix_mask, delta, A):
    """Restore the old target using the Schur complement in the r register."""
    from field_tensor import accumulate_product, invert_binary_columns
    from tower_inverse import (apply_inplace_linear, kernel, phase_product,
                               quadratic_basis, rows_from_columns, xor_product)
    from modular_quadratic_direct import repay_twelve_source
    from quantum_reciprocal import xor_linear

    field = A.FIELD
    r = source[12:]
    x, y = target[:12], target[12:]
    xor_product(builder, r, x, y)  # y now holds N(r)*y_old
    linear = lambda z: z ^ field.mul(delta,field.mul(z,z))
    line_cols = images(linear)
    image = {linear(v) for v in range(4096)}
    assert len(image) == 2048 and 1 not in image
    ker = next(v for v in range(1,4096) if not linear(v))
    tag_bit = (ker & -ker).bit_length()-1
    # r -> (linear(r), tag(r)). One unused direction, outside image,
    # makes it an invertible map on (r, clean_tag).
    columns = [c | ((j==tag_bit)<<12) for j,c in enumerate(line_cols)] + [1]
    register = km.array([*r, source[1]])  # this pivot bit is known clean in the a=1 chart
    apply_inplace_linear(builder,register,rows_from_columns(columns))
    builder.x(r[0])  # r storage now holds the nonzero N(r)
    norm_debt = A.Prior.inverse_twelve_deferred(builder,r)
    d = builder.alloc_qubits(12)
    xor_product(builder,r,y,d)
    builder.swap(y,d)
    y_debt = builder.alloc_bits(12)
    builder.hmr(d,y_debt)
    builder.free(d)
    inverse_debt = A.Prior.inverse_twelve_deferred(builder,r)
    repay_twelve_source(builder,r,norm_debt)
    phase_product(builder,r,y,y_debt,kernel(12))
    builder.free(y_debt)
    polynomial_mask = builder.alloc_bits(12)
    builder.bit_store(polynomial_mask,False)
    xor_linear(builder,km.array([*inverse_debt[0],*inverse_debt[1]]),
               polynomial_mask,quadratic_basis(12)['to_tower'])
    A.Phase12.phase_inverse_twelve_polynomial(builder,r,polynomial_mask)
    builder.free(polynomial_mask)
    for m in inverse_debt: builder.free(m)
    builder.x(r[0])
    apply_inplace_linear(builder,register,invert_binary_columns(columns))
    accumulate_product(builder,r,y,x,[(a,b,field.mul(delta,c)) for a,b,c in kernel(12)])
    phase_product(builder,r,y,prefix_mask,kernel(12))
    builder.free(prefix_mask)


def build(A, method, close):
    from tower_inverse import kernel, phase_product

    b = km.CircuitBuilder()
    source = b.create_quantum_register(24, 'source')
    target = b.create_quantum_register(24, 'target')
    probe = b.create_classical_register(24, 'probe')
    delta = A.DEFAULT_DELTA
    if method in ('streamed','lifted','borrowed'):
        mask = streamed_prefix(b, source, target, delta)
    elif method in ('projected','projected_full'):
        mask = projected_reference_prefix(b, source, target, A.tensor24(delta))
    else:
        record = A.emit_prefix(b, source, target, delta)
        mask = record.old_target_mask
    if close:
        # A nontrivial phase probe between the two halves proves that the
        # intermediate value is the actual product, not merely a round trip.
        b.cz(probe, target)
        b.cz(target[1], target[17])
        if method == 'borrowed':
            borrowed_return(b,source,target,mask,delta,A)
            assert b.num_allocated_qubits == 48
            return b.finish_circuit()
        if method == 'lifted':
            streamed_return(b,source,target,mask,delta,A)
            return b.finish_circuit()
        if method == 'streamed':
            empty = b.alloc_bits(24)
            b.bit_store(empty, False)
            record = A.make_record(b, empty, delta=delta)
        elif method in ('projected','projected_full'):
            record = A.make_record(b, mask, delta=delta)
        if method == 'projected_full':
            projected_closing(b,source,target,record,A)
            assert b.num_allocated_qubits == 48
            return b.finish_circuit()
        A.emit_closing(b, source, target, record)
        if method == 'streamed':
            phase_product(b, source[12:], target[12:], mask, kernel(12))
            b.free(mask)
    else:
        # Expose the deferred phase so it can be independently verified.
        check = b.create_classical_register(len(mask), 'saved_mask')
        b.cx(mask, check)
        b.free(mask)
    assert b.num_allocated_qubits == 48
    return b.finish_circuit()


def read_words(sim, register, n):
    bits = np.asarray(sim.read_across_shots(register), dtype=np.uint32)
    return (bits * (1 << np.arange(n, dtype=np.uint32))[:,None]).sum(axis=0).astype(np.uint32)


def check(A, circuit, method, close, r, target, probes, oracle, seed):
    from quantum_reciprocal import bit_matrix

    shots = len(r)
    src = 1 + (r << 12)
    sim = km.Simulator(batch_size=shots, seed=seed, counting_operations=True)
    sim.use_same_registers_as(circuit)
    reg = circuit.register_data
    sim.write_across_shots(reg['source'], bit_matrix(src, 24))
    sim.write_across_shots(reg['target'], bit_matrix(target, 24))
    sim.write_across_shots(reg['probe'], bit_matrix(probes, 24))
    sim.do(circuit)
    assert np.array_equal(read_words(sim, reg['source'], 24), src)
    assert np.array_equal(read_words(sim, reg['target'], 24), target if close else oracle)
    assert np.array_equal(read_words(sim, reg['probe'], 24), probes)
    if circuit.num_qubits > 48:
        assert not np.asarray(sim.read_across_shots(km.array(
            [km.q(i) for i in range(48, circuit.num_qubits)]))).any()
    if close:
        expected = [((int(p)&int(z)).bit_count() + ((int(z)>>1)&(int(z)>>17)&1)) % 2
                    for p,z in zip(probes,oracle)]
    else:
        n = 12 if method in ('streamed','lifted','borrowed') else 24
        masks = read_words(sim, reg['saved_mask'], n)
        data = ([A.FIELD.mul(int(a), int(b)>>12) for a,b in zip(r,target)]
                if method in ('streamed','lifted','borrowed') else target)
        expected = [(int(m)&int(v)).bit_count()%2 for m,v in zip(masks,data)]
    assert np.array_equal(sim.read_phase_flipped_across_shots(), expected), (method,close,seed)
    return sim.operation_statistics().num_toffoli_like/shots


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--work', type=Path, required=True)
    p.add_argument('--out', type=Path, required=True)
    a = p.parse_args()
    for rel in ('after_c5/arithmetic_t','after_v3/k24','night_c27/arithmetic'):
        sys.path.insert(0,str(a.work/rel))
    import gf24_nested_norm as A

    a.out.mkdir(parents=True,exist_ok=True)
    rng = np.random.default_rng(202611151902)
    r = np.tile(np.arange(4096, dtype=np.uint32),2)
    target = rng.integers(0,1<<24,size=len(r),dtype=np.uint32)
    probes = rng.integers(0,1<<24,size=len(r),dtype=np.uint32)
    oracle = np.asarray([A.mul24(1+(int(u)<<12),int(v)) for u,v in zip(r,target)],dtype=np.uint32)
    rows = []
    for method in ('reference','projected','projected_full','streamed','lifted','borrowed'):
        for close in (False,True):
            if method in ('lifted','borrowed','projected_full') and not close: continue
            circuit = build(A,method,close)
            path = a.out/f"{method}_{'pair' if close else 'prefix'}.kmb"
            circuit.to_file(path,format='kmb')
            circuit = km.Circuit.from_file(path)
            means = [check(A,circuit,method,close,r,target,probes,oracle,seed)
                     for seed in (2026111518,2026111519)]
            row = dict(method=method,closed_pair=close,shot_count=2*len(r),
                       helpers=circuit.num_qubits-48,static_toffoli=circuit.operation_statistics().num_toffoli_like,
                       total_operations=len(circuit),mean_toffoli=means,
                       all_source_and_target_value_scratch_and_phase_checks_pass=True,
                       sha256=hashlib.sha256(path.read_bytes()).hexdigest())
            print(json.dumps(row),flush=True)
            rows.append(row)
    (a.out/'result.json').write_text(json.dumps(dict(chart='source = 1 + r*theta, all GF4096 r',
        production_splice=False,rows=rows),indent=2)+'\n')


if __name__=='__main__':
    main()
