#!/usr/bin/env python3
"""Constructive subspace contraction of the 13-AND inverse-phase joint map.

Enumerate all 10,795 decomposable alternating forms on eight inputs. First
test every codimension-one subspace of the current product span containing
the eight required output forms. Then enlarge that span by one decomposable
form and test every codimension-two subspace containing the outputs. This is
a finite new synthesis neighborhood, not a general multiplicative bound.
"""
from collections import defaultdict
from itertools import combinations
from pathlib import Path
import argparse,hashlib,json,time

PAIRS=list(combinations(range(8),2))
def quadratic(u,v):
    return sum((((u>>i&1)&(v>>j&1))^((u>>j&1)&(v>>i&1)))<<k for k,(i,j) in enumerate(PAIRS))

class Basis:
    def __init__(self,rows=()):
        self.rows=[];self.pivots={}
        for v in rows:self.add(v)
    def reduce(self,v):
        coord=0
        for p,(b,m) in sorted(self.pivots.items(),reverse=True):
            if v>>p&1:v^=b;coord^=m
        return v,coord
    def add(self,v):
        rem,coord=self.reduce(v)
        if rem:self.pivots[rem.bit_length()-1]=(rem,coord^(1<<len(self.rows)));self.rows.append(v);return True
        return False

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--out',type=Path,required=True);args=ap.parse_args();start=time.monotonic()
    root=Path(__file__).parent;source=json.loads((root/'score4_dqi_joint_input.json').read_text());terms=source['terms']
    original=[quadratic(a,b) for a,b,w in terms];outputs=[0]*8
    for q,(_,_,w) in zip(original,terms):
        for i in range(8):
            if w>>i&1:outputs[i]^=q
    base=Basis(outputs+original);assert len(base.rows)==13 and len(Basis(outputs).rows)==8
    forms={}
    for a in range(1,256):
        for b in range(a+1,256):forms.setdefault(quadratic(a,b),(a,b))
    assert len(forms)==10795
    groups=defaultdict(list)
    for q in forms:groups[base.reduce(q)[0]].append(q)
    inside=groups.pop(0)
    tested=0;large_enough=0;found=None
    def attempt(vectors,dimension):
        nonlocal tested,large_enough,found
        span=Basis(outputs+vectors);assert len(span.rows)==dimension
        free=dimension-8;coords=[span.reduce(q)[1]>>8 for q in vectors]
        masks=[]
        for h in range(1,1<<free):masks.append(sum(((h&c).bit_count()%2==0)<<i for i,c in enumerate(coords)))
        if dimension==13:allowed=masks
        else:
            assert dimension==14
            allowed=(masks[h-1]&masks[g-1] for h in range(1,64) for g in range(h+1,64) if g<(h^g))
        for selected in allowed:
            tested+=1
            if selected.bit_count()<12:continue
            large_enough+=1;qs=[q for i,q in enumerate(vectors) if selected>>i&1];b=Basis(qs)
            if len(b.rows)>12 or any(b.reduce(q)[0] for q in outputs):continue
            weights=[0]*len(b.rows)
            for out,q in enumerate(outputs):
                rem,co=b.reduce(q);assert rem==0
                for j in range(len(weights)):
                    if co>>j&1:weights[j]|=1<<out
            new_terms=[(*forms[q],w) for q,w in zip(b.rows,weights) if w]
            if len(new_terms)>=13:continue
            found=dict(terms=new_terms,ambient_dimension=dimension,selected_span_dimension=len(b.rows))
            return True
        return False
    attempt(inside,13)
    visited=0
    if found is None:
        for rem,extra in sorted(groups.items(),key=lambda x:(-len(x[1]),x[0])):
            visited+=1
            if attempt(inside+extra,14):break
    result=dict(status='FOUND_EXACT_QUADRATIC_CONTRACTION' if found else 'BOUNDED_NEIGHBORHOOD_COMPLETE_NO_CONTRACTION',
                output_dimension=8,initial_product_span_dimension=13,rank_one_forms=10795,
                rank_one_forms_in_original_span=len(inside),extension_groups=len(groups),
                extension_groups_checked=visited,subspaces_checked=tested,subspaces_with_at_least_12_forms=large_enough,
                candidate=found,seconds=time.monotonic()-start,script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
    if found:
        # Recover all linear terms in the Boolean ring, then check every input.
        oldlin=source['linear_forms'];newlin=oldlin[:]
        for a,b,w in terms+found['terms']:
            for i in range(8):
                if w>>i&1:newlin[i]^=a&b
        def evaluate(x,ts,lin):
            y=sum(((x&f).bit_count()%2)<<i for i,f in enumerate(lin))
            for a,b,w in ts:
                if (x&a).bit_count()%2 and (x&b).bit_count()%2:y^=w
            return y
        assert all(evaluate(x,terms,oldlin)==evaluate(x,found['terms'],newlin) for x in range(256))
        found['linear_forms']=newlin;found['all_256_values_equal']=True
    args.out.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result),flush=True)

if __name__=='__main__':main()
