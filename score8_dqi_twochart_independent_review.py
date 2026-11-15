#!/usr/bin/env python3
"""Independent algebra and integration review of the two-chart DQI gauge.

Uses a separate shift-and-reduce GF(2^12) implementation, polynomial builder,
and physical zero-mask counter. This is not an additional native/full-decoder
verification and does not alter the candidate or verifier.
"""
from __future__ import annotations
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import time

import numpy as np

import kmb_profile as K
from dqi_gauge_expand import load_original
from score8_dqi_twochart import geometry

MODULUS=0x1053


def multiply(a,b):
    out=0
    while b:
        if b&1:out^=a
        b>>=1;a<<=1
        if a&4096:a^=MODULUS
    return out


def power(a,n):
    out=1
    while n:
        if n&1:out=multiply(out,a)
        a=multiply(a,a);n>>=1
    return out


def invert(a):
    assert a;return power(a,4094)


def polynomial(roots):
    c=[0,1]
    for r in roots:
        out=[0]*(len(c)+1)
        for j,v in enumerate(c):out[j]^=multiply(v,r);out[j+1]^=v
        c=out
    return c


def evaluate(c,x):
    out=0
    for v in reversed(c):out=multiply(out,x)^v
    return out


def transpose(a,m):
    out=0
    for j in range(12):
        if (multiply(a,1<<j)&m).bit_count()&1:out|=1<<j
    return out


def digest(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        for block in iter(lambda:f.read(1<<22),b''):h.update(block)
    return h.hexdigest()


def header(path):
    with Path(path).open('rb') as f:values=K.HEADER.unpack(f.read(K.HEADER.size))
    assert values[0]==K.MAGIC
    return dict(zip(K.HEADER_FIELDS,values[1:]))


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--source-root',type=Path,required=True);ap.add_argument('--out',type=Path,required=True);a=ap.parse_args();begin=time.monotonic();root=Path(__file__).resolve().parent
    original=load_original(a.source_root);spec=geometry(original);old=spec['original'];points=list(old['plan'].points)
    assert set(points)==set(range(1,4096))
    assert original.F.modulus==MODULUS
    # Basis products determine every binary multiplication/transpose matrix.
    for scalar in range(4096):
        for j in range(12):assert multiply(scalar,1<<j)==original.F.mul(scalar,1<<j)
    g=polynomial(range(1,70));h=polynomial([*range(1,69),70])
    assert tuple(g[1:])==old['coefficients'] and tuple(h[1:])==spec['h_coefficients']
    gv=[evaluate(g,x) for x in points];hv=[evaluate(h,x) for x in points]
    assert tuple(gv)==old['values'] and tuple(hv)==spec['h_values']
    assert {x for x,v in zip(points,gv) if not v}==set(range(1,70))
    assert {x for x,v in zip(points,hv) if not v}==set([*range(1,69),70])
    indices=list(old['residual_indices']);assert len(indices)==4025
    ratios=[]
    for i in indices:
        x=points[i];r=multiply(x^70,invert(x^69));assert r and multiply(gv[i],r)==hv[i] and r==spec['ratio'][i];ratios.append(r)
    # Build transformations by independent field arithmetic; vectorization
    # changes only application to the fixture arrays, not the field oracle.
    inverses=[invert(r) for r in ratios]
    inv_basis=np.array([[transpose(r,1<<j) for j in range(12)] for r in inverses],dtype=np.uint16)
    basis=np.array([[transpose(r,1<<j) for j in range(12)] for r in ratios],dtype=np.uint16)
    def transform(values,mat):
        ans=np.zeros(len(values),dtype=np.uint16)
        for j in range(12):ans^=np.where((values>>j)&1,mat[:,j],0).astype(np.uint16)
        return ans
    def mode(v):
        c=Counter(map(int,v));c[0]+=1;k=min(c,key=lambda k:(-c[k],k));return k,c[k]
    rng=np.random.default_rng(202611151481)
    fixtures=[('all_zero',np.zeros(4025,dtype=np.uint16)),('old_constant4095',np.full(4025,4095,dtype=np.uint16))]
    for label in (1,2048,4095):fixtures.append((f'new_constant{label}_old_label_zero',transform(np.full(4025,label,dtype=np.uint16),basis)))
    for j in range(64):fixtures.append((f'independent_{j}',rng.integers(0,4096,4025,dtype=np.uint16)))
    rows=[]
    for name,r in fixtures:
        s=transform(r,inv_basis);l0,n0=mode(r);l1,n1=mode(s);promote=n1>n0
        chosen0,chosen1=(0,l1) if promote else (l0,0)
        shifted=r^chosen0^transform(np.full(4025,chosen1,dtype=np.uint16),basis)
        # Physical cells: 68 common fixed-zero points, point69, point70,
        # and all4025 residual points. This also covers old label0 -> new
        # nonzero label, where the added cell has no old pivot cost to cancel.
        old_T=11*(int(l0!=0)+int(np.count_nonzero(r^l0)))
        new_T=11*(int(chosen0!=0)+int(chosen1!=0)+int(np.count_nonzero(shifted)))
        zero_masks=68+int(chosen0==0)+int(chosen1==0)+int(np.count_nonzero(shifted==0))
        assert zero_masks==69+max(n0,n1)
        assert old_T-new_T==11*(max(n0,n1)-n0)>=0
        if name.startswith('new_constant'):assert promote and l0==0 and chosen1!=0
        if name=='all_zero':assert n0==n1==4026 and old_T==new_T==0
        rows.append({'name':name,'old_label':l0,'new_label':l1,'old_mode_count':n0,'new_mode_count':n1,'promote':promote,'physical_scan_T_before':old_T,'physical_scan_T_after':new_T})
    binding=json.loads((root/'score8_dqi_twochart_binding.json').read_text());build=json.loads((root/'score8_dqi_twochart_build.json').read_text());splice=json.loads((root/'score8_dqi_twochart_splice.json').read_text())
    oldpath=Path(binding['baseline_path']);newpath=Path(splice['output_path']);oldheader=header(oldpath);newheader=header(newpath)
    assert oldheader['num_bits']==208169 and min(build['new_pivot'])==208169
    assert min(build['new_pivot'])>=oldheader['num_bits']
    assert newheader['num_qubits']==oldheader['num_qubits']==889
    assert newheader['num_ops_with_3_target_qubits']-oldheader['num_ops_with_3_target_qubits']==11
    assert digest(oldpath)==binding['baseline_sha256'];assert digest(newpath)==splice['output']['sha256']
    U=original.OriginalScan.geometry()['U'];M=original.OriginalScan.Finish.geometry()['M']
    divisor=multiply(69,multiply(evaluate(U,69),evaluate(M,69)))
    factor=multiply(evaluate(h,69),invert(divisor));assert factor==1199==binding['normalized_mask_factor']
    report={
        'status':'PASS_INDEPENDENT_ALGEBRA_AND_STATIC_INTEGRATION_REVIEW',
        'independent_field_modulus':hex(MODULUS),'field_basis_products_checked':4096*12,
        'polynomial_points_checked':4095,'ratio_points_checked':4025,
        'coefficients_match_for_both_degree70_polynomials':True,
        'exact_fixed_zero_sets_checked':True,'point69_independent_scale':factor,
        'mode_and_physical_scan_fixtures':rows,'old_zero_label_new_nonzero_promotion_cases':3,
        'all_physical_scan_differences_match_exact_mode_formula':True,
        'new_pivot_bits_disjoint_from_every_old_body_classical_bit':True,
        'old_num_bits':oldheader['num_bits'],'new_num_bits':newheader['num_bits'],
        'qubits':889,'static_toffoli_like_delta':11,
        'baseline_sha256':binding['baseline_sha256'],'candidate_sha256':splice['output']['sha256'],
        'code_review_findings':[
            'The virtual zero is private row4025; rows4026..4095 carry sentinel4096. Exact12-bit counters accommodate maximum4026.',
            'Strict greater-than preserves old chart on a tie; the unselected label is cleared, so no simultaneous two-gauge shift occurs.',
            'Transpose multiplication has the correct dual-mask direction; normalized residual shift uses h/g, while alternative mode labels use g/h.',
            'Syndrome compensation uses coefficients of x^1..x^70, matching the syndrome power convention.',
            'Whole-body operand-column preservation and bound clean-ladder placement were reviewed from the source and existing exact-match receipts.',
            'Native32-case gauge and8192x2-seed cell receipts were inspected; not rerun by this independent reviewer.',
            'The existing failed decoder input can change its phase. Equivalence and reliability claims must retain the report\'s successful-decoder-domain qualification.'
        ],
        'blocking_defect_found':False,'native_or_full_verifier_rerun':False,
        'scope':'Independent field algebra, physical zero-count model, header/hash checks and static source review; not an exhaustive full-decoder proof or new native verification.',
        'review_script_sha256':digest(__file__),'seconds':time.monotonic()-begin
    }
    a.out.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:v for k,v in report.items() if k not in ('mode_and_physical_scan_fixtures','code_review_findings')},indent=2))


if __name__=='__main__':main()
