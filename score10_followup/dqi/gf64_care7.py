#!/usr/bin/env python3
"""Test seven quadratic products with norm-conditioned GF64 reassembly."""
import argparse
from itertools import combinations
from pathlib import Path
from collections import Counter
import json

from gf64_probe import bases, mix, probe, table, solve
from gf64_quad_spaces import rem_basis, reduce_against, quadratic_anf

def care_scaffolds(source):
    current, targets, _, _ = probe(source)
    import kickmix as km
    field=km.GF2Field(6)
    input_bits=current[1:7]
    quad=[input_bits[i]&input_bits[j] for i,j in combinations(range(6),2)]
    adjugate=[table(lambda x:(field.pow(x,20)>>i)&1) for i in range(6)]
    adj_columns=[quadratic_anf(t) for t in adjugate]
    adj_basis=rem_basis(adj_columns)
    source_forms={}
    for a,b in combinations(range(1,64),2):
        truth=mix(input_bits,a)&mix(input_bits,b)
        source_forms.setdefault(quadratic_anf(truth),(a,b,truth))
    assert len(source_forms)==651
    buckets={}
    for q in source_forms:
        buckets.setdefault(reduce_against(q,adj_basis),[]).append(q)
    kernels=[]
    kernels_quotient=[]
    for label in (1,2,3):
        zone=(current[-2] if label&1 else ((1<<64)-1)^current[-2]) & (
            current[-1] if label&2 else ((1<<64)-1)^current[-1])
        assert zone.bit_count()==21
        # Norm restricted inverse is a linear transform of the adjugate.
        assert len(bases([t&zone for t in current[:7]])[0])==7
        assert len(bases([t&zone for t in (*current[:7],*adjugate)])[0])==13
        assert len(bases([t&zone for t in (*current[:7],*targets)])[0])==13
        assert len(bases([t&zone for t in (*current[:7],*adjugate,*targets)])[0])==13
        _,relations=bases([v&zone for v in current[:7]+quad])
        K=[u>>7 for u in relations]
        assert len(K)==3
        kernels.append({mix(K,i) for i in range(1,8)})
        kernels_quotient.append({reduce_against(u,adj_basis) for u in kernels[-1]})
        assert len(kernels_quotient[-1])==7
    k1,k2,k3=kernels_quotient
    assert not (k1&k2 or k1&k3 or k2&k3)
    # For W dim7, t=dim pi(W), dim(W intersect A)=7-t.
    # A subset W+K in each class implies dim(pi(W) intersect pi(K)) >= t-1.
    # Disjoint pi(K1),pi(K2) implies t<=2.
    # t=1 would contain A. The exact adjugate scaffold check excludes it.
    planes=sorted((u,v) for u in k1 for v in k2 if (u^v) in k3)
    tested=0
    rank_hist=Counter()
    hint_hist=Counter()
    viable=[]
    for u,v in planes:
        forms=sum((buckets.get(x,[]) for x in (0,u,v,u^v)),[])
        hint_hist[len(forms)]+=1
        for normal in range(1,64):
            pivot=normal&-normal
            lift=adj_columns[pivot.bit_length()-1]
            hyperplane={mix(adj_columns,k) for k in range(64)
                        if ((k&normal).bit_count()&1)==0}
            for c,d in [(0,0),(0,lift),(lift,0),(lift,lift)]:
                W=hyperplane | {w^u^c for w in hyperplane} | {
                        w^v^d for w in hyperplane} | {w^u^c^v^d for w in hyperplane}
                tested+=1
                assert len(W)==128
                terms=[q for q in forms if q in W]
                independent=[]
                for q in terms:
                    if solve(q,bases(independent)[0]) is None:
                        independent.append(q)
                rank=len(independent)
                rank_hist[rank]+=1
                if rank!=7:
                    continue
                if not all(set(adj_columns)<=W|space|{w^k for w in W for k in space}
                           for space in kernels):
                    continue
                sig=current[:7]+[source_forms[q][2] for q in independent]+current[-2:]
                cols=sig+[n&q for n in sig[-2:] for q in sig[1:-2]]
                basis,null=bases(cols)
                assert all(solve(t,basis) is not None for t in targets)
                viable.append(dict(plane=[u,v],normal=normal,lifts=[c,d],
                                   quadratics=[source_forms[q][:2] for q in independent],
                                   reassembly_rank=len(basis),reassembly_nullity=len(null)))
    return dict(status='COMPLETE',quotient_planes=planes,
                norm_class_kernels=[sorted(s) for s in kernels],
                quotient_norm_class_kernels=[sorted(s) for s in kernels_quotient],
                count_computed_spaces=tested,
                count_decomposable_forms_by_plane=dict(hint_hist),
                decomposable_span_rank_histogram=dict(rank_hist),viable=viable)

if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--source',required=True)
    p.add_argument('--output',type=Path,required=True)
    args=p.parse_args()
    ans=care_scaffolds(args.source)
    print(ans)
    args.output.write_text(json.dumps(ans,indent=2)+'\n')
