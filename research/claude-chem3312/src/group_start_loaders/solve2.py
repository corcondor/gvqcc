# solve high vectors z with `nrel` relation columns (the other partial columns stay free)
import numpy as np, subprocess, sys, pickle, random, os, time
from frame import *
from gf2 import *
from planner import chip_vecs
from solve import e_vec, h_vec, needed_rows, check_function
HERE=os.path.dirname(os.path.abspath(__file__))
NO=30

def coef_vectors(cov, NX):
    coef=[]
    for s,U in cov:
        coef.append(chip_vecs(s,(U[1],),NX)[0]); coef.append(chip_vecs(s,(U[0],),NX)[0])
    return coef

def restricted_solve(F, coef, y, fixed, rng):
    """solve M_R z = N_R(y) for the coordinates not in `fixed` (dict j->bit). Returns z (int) or None."""
    NX=F.NX
    mask=F.care_mask(y)
    target=F.col_int(y)&mask
    base=0
    for j,b in fixed.items():
        if b: base^=coef[j]&mask
    target^=base
    freej=[j for j in range(len(coef)) if j not in fixed]
    eqs=[]; rhs=[]
    for i in range(NO*NX):
        if not mask>>i&1: continue
        r=0
        for t,j in enumerate(freej):
            if coef[j]>>i&1: r|=1<<t
        eqs.append(r); rhs.append((target>>i)&1)
    sol=solve_linear(eqs,rhs,len(freej))
    if sol is None: return None
    part,null=sol
    for v in null:
        if rng.random()<0.5: part^=v
    z=0
    for j,b in fixed.items():
        if b: z|=1<<j
    for t,j in enumerate(freej):
        if part>>t&1: z|=1<<j
    return z

def solve_all(F, cov, nrel, seed=7, need_tags=(), verbose=True):
    rng=random.Random(seed)
    NX=F.NX; n=len(cov)
    s=[c[0] for c in cov]
    coef=coef_vectors(cov,NX)
    full=F.full
    five=[y for y in range(F.ny) if len(F.carex[y])==5]
    four=[y for y in range(F.ny) if len(F.carex[y])==4]
    rel_cols=four[:]; rng.shuffle(rel_cols); rel_cols=sorted(rel_cols[:nrel])
    free_cols=sorted(set(five+four)-set(rel_cols))
    z=[0]*F.ny
    piv=CombEch()
    for j,v in enumerate(coef):
        assert piv.add(v,1<<j) is None, 'chip vectors dependent'
    for y in full:
        c=piv.solve(F.col_int(y)); assert c is not None
        z[y]=c
    h=[None]*F.ny
    for y in full: h[y]=h_vec(F,y,z[y],s)
    lin=[np.ones(F.ny,np.uint8)] + [F.ybits[t] for t in range(len(F.Y))] + list(F.tagf) + list(need_tags)
    B=full; nb=len(B)
    blocks=[]
    for yst in rel_cols:
        R=[x for x in F.carex[yst] if x]
        eqs=[]; rhs=[]
        for o in range(NO):
            for x in R:
                r=0
                for t,y in enumerate(B):
                    if F.N[o,x-1,y]: r|=1<<t
                eqs.append(r); rhs.append(int(F.N[o,x-1,yst]))
        for f in lin:
            r=0
            for t,y in enumerate(B):
                if f[y]: r|=1<<t
            eqs.append(r); rhs.append(int(f[yst]))
        sol=solve_linear(eqs,rhs,nb)
        assert sol is not None, 'linear relation unsolvable'
        part,null=sol
        def comb(c, arr):
            v=0
            for t,y in enumerate(B):
                if c>>t&1: v^=arr[y]
            return v
        def split(v):
            a=0;b=0
            for i in range(n):
                if v>>(2*i)&1: a|=1<<i
                if v>>(2*i+1)&1: b|=1<<i
            return a,b
        d0=0
        for o in range(NO):
            if F.Dg[o,0,yst]: d0|=1<<o
        pa,pb=split(comb(part,z))
        rec=[(comb(part,h),pa,pb)]
        for v in null:
            a,b=split(comb(v,z)); rec.append((comb(v,h),a,b))
        blocks.append((yst,part,null,d0,rec))
    M=(1<<64)-1
    lines=[f'{n} '+' '.join(map(str,s))]
    for yst,part,null,d0,rec in blocks:
        lines.append(f'{len(null)} {d0}')
        for r,a,b in rec:
            lines.append(f'{r} {a&M} {a>>64} {b&M} {b>>64}')
    t=time.time()
    out=subprocess.run([os.path.join(HERE,'hsolve.exe')],input='\n'.join(lines),capture_output=True,text=True,check=True)
    if verbose: print(f'  h-solver: {time.time()-t:.0f}s for {len(blocks)} relations',flush=True)
    sols=out.stdout.split()
    rel={}
    for (yst,part,null,d0,rec),sv in zip(blocks,sols):
        assert sv!='NONE', f'no solution for column {yst}'
        lam=int(sv); c=part
        for k,v in enumerate(null):
            if lam>>k&1: c^=v
        rel[yst]=[y for t,y in enumerate(B) if c>>t&1]
        zv=0; hv=0
        for y in rel[yst]: zv^=z[y]; hv^=h[y]
        z[yst]=zv; h[yst]=h_vec(F,yst,zv,s)
        assert h[yst]==hv, 'h relation failed'
        # care equations on the relation column
        mask=F.care_mask(yst); lhs=0
        for j in range(2*n):
            if zv>>j&1: lhs^=coef[j]&mask
        assert lhs==(F.col_int(yst)&mask), 'care mismatch on relation column'
    for y in free_cols:
        z[y]=restricted_solve(F,coef,y,{},rng); assert z[y] is not None
        h[y]=h_vec(F,y,z[y],s)
    return dict(coef=coef,z=z,h=h,rel=rel,full=full,free=free_cols,relcols=rel_cols,s=s,lin=lin,nrel=nrel)

def relation_functionals(sol):
    out=[]
    for yst,ys in sol['rel'].items():
        v=1<<yst
        for y in ys: v^=1<<y
        out.append(v)
    return out
