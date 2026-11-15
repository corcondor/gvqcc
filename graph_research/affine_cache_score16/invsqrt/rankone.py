"""Rank-one synthesis of two paid operations between observable cuts."""
import argparse, json, re, sys
from pathlib import Path
import numpy as np
from window_rank import *
from measure_linear import solve

def select(rows):
    result=[]
    b={}
    for value in rows:
        v=value
        while v and v.bit_length()-1 in b: v^=b[v.bit_length()-1][0]
        if v:
            b[v.bit_length()-1]=(v,0); result.append(value)
    return result

def intersection(a,b):
    pre=affine_basis(b)
    pivots=sorted(pre,reverse=True)
    basis={}
    answer=[]
    for p in a:
        t=p
        for pivot in pivots:
            if (t>>pivot)&1:t^=pre[pivot][0]
        while t and t.bit_length()-1 in basis:
            s,v=basis[t.bit_length()-1]; t^=s;p^=v
        if t:basis[t.bit_length()-1]=(t,p)
        else:answer.append(p)
    return answer

def trace(lines,xs,rows):
    mask=(1<<len(xs))-1;w=columns(xs); p=re.compile(r'\bq(\d+)\b')
    states={}
    for i,l in enumerate(lines):
        if (i,0) in rows:states[i,0]=[mask,*w]
        op=l.split()[0]
        if op in OPS|{'HMR','R'}:
            advance('HMR' if op=='R' else op,tuple(map(int,p.findall(l))),w,mask)
        if (i,1) in rows:states[i,1]=[mask,*w]
    return states

def screen(old,new):
    a,b=select(old),select(new); a_b,b_b=affine_basis(a),affine_basis(b)
    extra=next((x for x in b if solve(a_b,x) is None),None)
    if extra is None:return None
    common=intersection(a,b); n=len(common)
    if n+1!=len(b) or len(a)>len(b) or n<2:return None
    t=next((x for x in a if solve(b_b,x) is None),0)
    if t==0 and len(a)==len(old):return None
    c=select([old[0],*common]); base=affine_basis(c)
    forms={v for v in c[1:]}
    forms.update(v for v in [*old[1:],*new[1:]] if v and v!=old[0] and solve(base,v) is not None)
    forms.update(x^y for i,x in enumerate(c[1:]) for y in c[1:i+1])
    for v in forms:
        vec=[*c,*[v&w for w in c]]
        out=solve(affine_basis(vec),extra^t)
        if out is None:continue
        w=0
        for j,w0 in enumerate(c):
            if out>>(j+n)&1:w^=w0
        if not w or v==w:continue
        layout=select([old[0],v,w,t,*a])[1:]
        if layout[:2]!=[v,w]:continue
        if not t:layout.insert(2,0)
        layout += [0]*(len(old)-1-len(layout))
        actual=layout.copy();actual[2]^=v&w
        after=[old[0],*actual]
        basis=affine_basis(after)
        if len(basis)!=len(b) or any(solve(basis,v) is None for v in b):continue
        code=encode_common([old[0],*layout],old,None)+['CCX q0 q1 q2']+encode_common(new,after,None)
        verify=old[1:].copy()
        for l in code:advance(l.split()[0],tuple(map(int,re.findall(r'\bq(\d+)\b',l))),verify,old[0])
        assert [old[0],*verify]==new
        return code
    return None

def main():
    a=argparse.ArgumentParser()
    for x in ('source','windows','out'):a.add_argument('--'+x,type=Path,required=True)
    args=a.parse_args()
    import kickmix as km
    lines=str(km.Circuit.from_file(args.source,format='kmb')).splitlines()
    rows=[r for r in json.loads(args.windows.read_text())['hits'] if r['rank']==1]
    x=np.random.default_rng(23017)
    samples=np.unique(np.r_[np.arange(1,600),x.integers(1,MAX_X+1,1900),MAX_X]).astype(np.uint32)
    code=[]
    for s in [samples,np.arange(1,MAX_X+1,dtype=np.uint32)]:
        if not rows:break
        w=trace(lines,s,{(r['start'],0) for r in rows}|{(r['end'],1) for r in rows})
        good=[]
        for r in rows:
            p=screen(w[r['start'],0],w[r['end'],1])
            if p is not None:
                print('hit',len(s),r,len(p),flush=True);good.append((r,p))
        rows=[r for r,p in good];code=good
    args.out.write_text(json.dumps(dict(rows=code),indent=2)+'\n')
    if code:
        r,p=max(code,key=lambda d:(d[0]['paid']-1)*(0.5 if d[0]['depth'] else 1))
        km.Circuit('\n'.join(lines[:r['start']]+p+lines[r['end']+1:])+'\n').to_file(args.out.with_suffix('.kmb'),format='kmb')

if __name__=='__main__':main()
