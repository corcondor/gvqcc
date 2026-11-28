#!/usr/bin/env python3
"""Exact actual-multiplier output-tile audit, not a candidate circuit.

The final masks of each of the 99 CCX terms are recovered by a reverse
linear pass through the certified pure multiplier. A forward pass recovers
the two input parities, and all 576 bilinear basis pairs are checked.
This counts a specific projected tensor decomposition, not optimal rank.
"""
from pathlib import Path
import hashlib
import json
from fractions import Fraction

HERE = Path(__file__).resolve().parent
LEFT = list(range(432, 456))
RIGHT = list(range(840, 864))
ORDER = [868,867,865,866,872,871,869,870,876,875,885,886,
         880,879,881,882,874,887,888,883,884,873,878,877]


def mul12(a,b):
    out=0
    while b:
        if b&1:out^=a
        a<<=1
        if a&4096:a^=0x1053
        b>>=1
    return out


def mul24(a,b):
    a0,a1,b0,b1=a&4095,a>>12,b&4095,b>>12
    aa,bb=mul12(a0,b0),mul12(a1,b1)
    return (aa^mul12(2048,bb))|((mul12(a0^a1,b0^b1)^aa)<<12)


def conjugate(a):
    return a^(a>>12)


def rank(rows):
    basis={}
    for row in rows:
        while row:
            k=row.bit_length()-1
            if k not in basis:basis[k]=row;break
            row^=basis[k]
    return len(basis)


def main():
    source=HERE/'inverse_v2_actual_eea_product.kmx'
    raw=source.read_bytes()
    assert hashlib.sha256(raw).hexdigest()=='f97f2a437fb9b538d85608ce5ae5393c87e5f8b8dcab750ca8af9eae754b5aac'
    ops=[]
    for line in raw.decode().splitlines():
        op,*args=line.split();ops.append((op,[int(s[1:])for s in args]))
    parity={q:1<<i for i,q in enumerate(LEFT+RIGHT)}
    inputs=[]
    for op,q in ops:
        if op=='CX' and q[0] in parity:
            assert q[1] in parity;parity[q[1]]^=parity[q[0]]
        elif op=='CCX':
            a,b=(parity[q[0]],parity[q[1]])
            if a>>24:a,b=b,a
            assert a and a<1<<24 and b and not b&((1<<24)-1)
            inputs.append((a,b>>24))
    assert all(parity[q]==1<<i for i,q in enumerate(LEFT+RIGHT))
    final={q:1<<i for i,q in enumerate(ORDER)};weights=[]
    for op,q in reversed(ops):
        if op=='CX' and q[0] in final:
            assert q[1] in final;final[q[0]]^=final[q[1]]
        elif op=='CCX':weights.append(final[q[2]])
    weights.reverse()
    assert all(final[q]==1<<i for i,q in enumerate(ORDER))
    terms=[(*uv,w)for uv,w in zip(inputs,weights)]
    assert len(terms)==99
    for i in range(24):
        for j in range(24):
            value=0
            for a,b,w in terms:
                if (a>>i)&(b>>j)&1:value^=w
            assert value==mul24(conjugate(1<<i),1<<j)
    single=[]
    for out in range(24):
        rows=[sum(((mul24(conjugate(1<<i),1<<j)>>out)&1)<<j
                  for j in range(24))for i in range(24)]
        single.append(dict(output_bit=out,existing_projected_terms=sum(bool(w&(1<<out))for w in weights),
                           bilinear_matrix_rank=rank(rows)))
    assert all(row['bilinear_matrix_rank']==24 for row in single)
    tiled=[]
    for k in (1,2,3,4,6,8,12,16,20,23):
        mask=(1<<k)-1
        counts=[sum(bool(w&m)for w in weights)for m in (mask,((1<<24)-1)^mask)]
        tiled.append(dict(tile_sizes=[k,24-k],projected_existing_terms=counts,
                          sum_terms=sum(counts),extra_terms_vs_99=sum(counts)-99))
    collisions=[]
    for k in range(1,24):
        # v=1 lies in the discarded first k input bits; w=2^k is invisible
        # to the first k output bits. For F(s,x)=conj(s)*x, s=conj(w).
        s=conjugate(1<<k);a=mul24(conjugate(s),0);b=mul24(conjugate(s),1)
        assert s and a!=b and a&((1<<k)-1)==b&((1<<k)-1)
        collisions.append(dict(first_tile_bits=k,source=s,old_targets=[0,1],
                               full_products=[a,b],first_tile_outputs=[0,0],
                               retained_old_upper_bits=[0,0]))
    T=Fraction('382115.5671582031');Q=889
    budgets=[]
    for saved in (1,2,4,6,8,11,12,24,49):
        extra=T*(Fraction(Q*Q,(Q-saved)**2)-1)
        budgets.append(dict(qubits_saved=saved,new_Q=Q-saved,
                            maximum_extra_mean_T_strict=float(extra)))
    report=dict(status='PASS_EXACT_BLOCK_AND_FIXED_TILE_COUNTEREXAMPLES',
        block_sha256=hashlib.sha256(raw).hexdigest(),bilinear_basis_pairs_checked=576,
        current_CCX=99,current_field_relation='theta^2+theta+2048=0 over GF(2^12), modulus0x1053',
        recovered_tensor_terms=terms,single_output_bits=single,natural_two_tiles=tiled,
        exact_counterexamples_to_consuming_fixed_first_tile=collisions,
        natural_12bit_pivot_zero_nonzero_sources=4095,
        total_nonzero_sources=(1<<24)-1,
        natural_12bit_pivot_zero_fraction='1/4097',
        fresh_tensor_natural_12plus12_cost=168,
        fresh_tensor_natural_12plus12_reason='Each output half is two independent rank42 GF12 products; this computes outputs but does not itself justify input consumption.',
        unchanged_R_cost_budgets=budgets,
        safe_conclusion='Fixed projection plus measurement of consumed input is invalid without reversible pivot handling. No full-circuit improvement or score claimed.')
    (HERE/'theory_ancilla_tiling_result.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({k:report[k]for k in ('status','bilinear_basis_pairs_checked','current_CCX',
                     'natural_12bit_pivot_zero_fraction','fresh_tensor_natural_12plus12_cost')}))


if __name__=='__main__':main()
