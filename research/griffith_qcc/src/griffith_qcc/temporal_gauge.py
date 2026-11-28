"""Exact *linear* projection of the Givens temporal sign gauge onto a tag table.

For 7-bit theta=pi*w/64, define t(w)=bit5(w) XOR bit6(w).
The four sign-equivalent angles are w, -w, 64-w, 64+w (mod 128).
A direct exhaustive Boolean identity gives

  t(w') XOR t(w) = s_input XOR s_parent   for w not in {32,96}
                  s_input XOR s_child    for w in {32,96}.

The selected edge always points to a later rotation or to a final leaf.
Therefore the equations for ALL 75 output tags can be solved by a *single
reverse traversal*, not a combinatorial sign search. The root input sign is
fixed +1; the final global sign is chosen to meet that boundary condition.

For every row, any prescribed 75 output-tag bits have one sign-gauge solution,
which preserves the orbital vector up to a global sign. This gives a rigorous
interface for training the temporal helper-code bits instead of forcing the
MSB to zero. Only tags are prescribed; the other bits are determined by gauge.
"""
from __future__ import annotations


def carrier_tree(edges):
    edges=[tuple(int(x) for x in e) for e in edges]
    n=len(edges)+1
    if set(c for _,c in edges) != set(range(1,n)):
        raise ValueError('need a unique fresh child for every non-root coordinate')
    born={0}
    for p,c in edges:
        if p not in born or c in born:
            raise ValueError('Givens order must split an existing carrier into a fresh child')
        born.add(c)
    live=[-(i+1) for i in range(n)]
    left=[None]*len(edges);right=[None]*len(edges)
    for j in reversed(range(len(edges))):
        p,c=edges[j]
        left[j],right[j]=live[p],live[c]
        live[p]=j;live[c]=None
    if live[0]!=0 or any(x is not None for x in live[1:]):
        raise AssertionError('carrier tree must have one root')
    return left,right


def tag(w):
    return ((int(w)>>5) ^ (int(w)>>6)) & 1


def transformed_word(w, sin, sp, sc):
    """sin,sp,sc are binary sign bits (0 positive, 1 negative)."""
    a=sin^sp;b=sin^sc
    if a==0 and b==0:return int(w)
    if a==0 and b==1:return (-int(w))%128
    if a==1 and b==0:return (64-int(w))%128
    return (64+int(w))%128


def project_row(w, target_tags, left, right):
    m=len(w)
    if len(target_tags)!=m or len(left)!=m or len(right)!=m:
        raise ValueError('mismatched rotation and tag counts')
    s=[0]*m
    for j in reversed(range(m)):
        target=int(target_tags[j])
        if target not in (0,1):raise ValueError('target tag must be binary')
        edge=right[j] if int(w[j]) in (32,96) else left[j]
        child_sign=s[edge] if edge>=0 else 0
        s[j]=child_sign ^ tag(w[j]) ^ target
    g=s[0]
    s=[b^g for b in s]
    assert s[0]==0
    out=[]
    for j,word in enumerate(w):
        sp=s[left[j]] if left[j]>=0 else g
        sc=s[right[j]] if right[j]>=0 else g
        vv=transformed_word(int(word),s[j],sp,sc)
        assert tag(vv) == int(target_tags[j])
        out.append(vv)
    return out,g


def project_table(candidate_words, desired_words, tree_edges):
    """Output a table gauge-equivalent to candidate, with tags from desired.

    `desired_words` determines ONLY its bit5 XOR bit6 tags; not its vectors.
    """
    import numpy as np
    a=np.asarray(candidate_words);b=np.asarray(desired_words)
    if a.shape!=b.shape or a.ndim!=2 or a.shape[1]!=75:raise ValueError('expected matching Nx75 tables')
    l,r=carrier_tree(tree_edges)
    new=np.empty_like(a)
    gs=[]
    for i in range(len(a)):
        target=[tag(v) for v in b[i]]
        row,g=project_row(a[i],target,l,r)
        new[i]=row;gs.append(g)
    return new,np.asarray(gs,dtype=np.uint8)


def main():
    from pathlib import Path
    import argparse,json,hashlib
    import numpy as np
    p=argparse.ArgumentParser()
    p.add_argument('--parent',type=Path,required=True)
    p.add_argument('--candidate',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    p.add_argument('--report',type=Path,required=True)
    a=p.parse_args()
    with np.load(a.parent,allow_pickle=False) as z:ref=z['angle_words']
    with np.load(a.candidate,allow_pickle=False) as z:d={k:z[k].copy() for k in z.files}
    orig=d['angle_words'].copy()
    new,g=project_table(orig,ref,d['tree_edges'])
    d['angle_words']=new
    a.output.parent.mkdir(exist_ok=True,parents=True)
    np.savez_compressed(a.output,**d)
    j={'source':str(a.candidate),'parent_source':str(a.parent),
       'angle_word_edits':int(np.count_nonzero(new!=orig)),
       'rows_changed':int(np.count_nonzero(np.any(new!=orig,axis=1))),
       'global_negative_rows':int(g.sum()),
       'all_tags_equal_desired':bool(np.array_equal(((new>>5)^(new>>6))&1,((ref>>5)^(ref>>6))&1)),
       'output_sha256':hashlib.sha256(a.output.read_bytes()).hexdigest(),
       'official_kickmix_scored':False}
    a.report.write_text(json.dumps(j,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(j,indent=2,ensure_ascii=False))
if __name__=='__main__':main()
