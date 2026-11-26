# Solve high vectors z and the relations of the unreachable columns (with the quadratic h-conditions).
import numpy as np, subprocess, sys, pickle, random, time, os
from frame import *
from gf2 import *
from planner import chip_vecs
HERE=os.path.dirname(os.path.abspath(__file__))
NO=30

def solve_z(F, cov, seed=7):
    rng=random.Random(seed)
    NX=F.NX; n=len(cov)
    vecs=[v for s,U in cov for v in chip_vecs(s,U,NX)]   # 2n columns: index 2i -> multiplies alpha_i (partner of u=U[0]) 
    # product (alpha+q)(beta+r) contributes alpha*r + beta*q ; with q=U[0], r=U[1]: coefficient of alpha is U[1], of beta is U[0]
    coef=[]
    for s,U in cov:
        a=chip_vecs(s,(U[1],),NX)[0]; b=chip_vecs(s,(U[0],),NX)[0]
        coef.append(a); coef.append(b)    # index 2i: alpha_i, 2i+1: beta_i
    z=[0]*F.ny
    known=[False]*F.ny
    full=F.full
    five=[y for y in range(F.ny) if len(F.carex[y])==5]
    four=[y for y in range(F.ny) if len(F.carex[y])==4]
    other=[y for y in range(F.ny) if y not in full and y not in five and y not in four]
    assert not other
    # full columns
    piv=CombEch()
    for j,v in enumerate(coef):
        dep=piv.add(v,1<<j)
        assert dep is None, 'chip vectors dependent'
    for y in full:
        c=piv.solve(F.col_int(y)); assert c is not None
        z[y]=c; known[y]=True
    # five columns: restricted solve, random
    for y in five:
        mask=F.care_mask(y)
        rows=[v & mask for v in coef]
        # solve sum_j z_j rows[j] = N_R
        target=F.col_int(y)&mask
        bitsR=[i for i in range(NO*NX) if mask>>i&1]
        eqs=[]; rhs=[]
        for i in bitsR:
            r=0
            for j,v in enumerate(rows):
                if v>>i&1: r|=1<<j
            eqs.append(r); rhs.append((target>>i)&1)
        part,null=solve_linear(eqs,rhs,2*n)
        for v in null:
            if rng.random()<0.5: part^=v
        z[y]=part; known[y]=True
    return coef,z,full,five,four

def e_vec(zy, s):
    # sum_i s_i alpha_i beta_i
    e=0
    for i,si in enumerate(s):
        if (zy>>(2*i))&1 and (zy>>(2*i+1))&1: e^=si
    return e

def h_vec(F, y, zy, s):
    d0=0
    for o in range(NO):
        if F.Dg[o,0,y]: d0|=1<<o
    return d0 ^ e_vec(zy,s)

def solve_relations(F, cov, seed=7, verbose=True):
    coef,z,full,five,four=solve_z(F,cov,seed)
    s=[c[0] for c in cov]
    NX=F.NX; n=len(cov)
    B=full+five
    nb=len(B)
    h=[None]*F.ny
    for y in B: h[y]=h_vec(F,y,z[y],s)
    # linear functions of y that must satisfy the relations
    lin=[np.ones(F.ny,np.uint8)] + [F.ybits[t] for t in range(len(F.Y))] + F.tagf
    blocks=[]
    for yst in four:
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
        def comb_z(c):
            v=0
            for t,y in enumerate(B):
                if c>>t&1: v^=z[y]
            return v
        def comb_h(c):
            v=0
            for t,y in enumerate(B):
                if c>>t&1: v^=h[y]
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
        pa,pb=split(comb_z(part))
        rec=[(comb_h(part), pa,pb)]
        for v in null:
            a,b=split(comb_z(v)); rec.append((comb_h(v),a,b))
        blocks.append((yst,part,null,d0,rec,comb_z,comb_h))
    M=(1<<64)-1
    lines=[f'{n} '+' '.join(map(str,s))]
    for yst,part,null,d0,rec,_,_ in blocks:
        lines.append(f'{len(null)} {d0}')
        for r,a,b in rec:
            lines.append(f'{r} {a&M} {a>>64} {b&M} {b>>64}')
    t=time.time()
    out=subprocess.run([os.path.join(HERE,'hsolve.exe')],input='\n'.join(lines),capture_output=True,text=True,check=True)
    if verbose: print(f'  h-solver: {time.time()-t:.0f}s for {len(blocks)} relations',flush=True)
    sols=out.stdout.split()
    assert len(sols)==len(blocks)
    rel={}
    for (yst,part,null,d0,rec,comb_z,comb_h),sv in zip(blocks,sols):
        assert sv!='NONE', f'no solution for column {yst}'
        lam=int(sv); c=part
        for k,v in enumerate(null):
            if lam>>k&1: c^=v
        rel[yst]=[y for t,y in enumerate(B) if c>>t&1]
        z[yst]=comb_z(c)
        h[yst]=h_vec(F,yst,z[yst],s)
        assert h[yst]==comb_h(c), 'h relation failed'
    return dict(coef=coef,z=z,h=h,rel=rel,full=full,five=five,four=four,s=s,lin=lin)

def needed_rows(F, sol):
    # all high functions needed: z rows (2n), h rows (30), const, y bits, tags -> ny-bit ints
    ny=F.ny
    rows=[]
    n=len(sol['s'])
    for j in range(2*n):
        v=0
        for y in range(ny):
            if sol['z'][y]>>j&1: v|=1<<y
        rows.append(v)
    hrows=[]
    for o in range(NO):
        v=0
        for y in range(ny):
            if sol['h'][y]>>o&1: v|=1<<y
        hrows.append(v)
    lin=[]
    for f in sol['lin']:
        v=0
        for y in range(ny):
            if f[y]: v|=1<<y
        lin.append(v)
    return rows,hrows,lin

def check_function(F, cov, sol):
    # exact check of D(o,x,y) on every care cell
    NX=F.NX
    z=sol['z']; h=sol['h']; s=sol['s']
    bad=0
    # l_o(x) = D(o,x,0)+D(o,0,0)+sum s q r (x)
    def pt(u,x):  # value of low function u (point basis over x=1..7) at x
        return 0 if x==0 else (u>>(x-1))&1
    lx=[0]*F.nx
    for x in range(F.nx):
        v=0
        for o in range(NO):
            if F.Dg[o,x,0]^F.Dg[o,0,0]: v|=1<<o
        for i,(si,U) in enumerate(cov):
            if pt(U[0],x) and pt(U[1],x): v^=si
        lx[x]=v
    for y in range(F.ny):
        for x in F.carex[y]:
            v=h[y]^lx[x]
            for i,(si,U) in enumerate(cov):
                a=(z[y]>>(2*i))&1; b=(z[y]>>(2*i+1))&1
                if (a^pt(U[0],x)) & (b^pt(U[1],x)): v^=si
            want=0
            for o in range(NO):
                if F.Dg[o,x,y]: want|=1<<o
            if v!=want: bad+=1
    return bad,lx

if __name__=='__main__':
    k=int(sys.argv[1]); cov=pickle.load(open(sys.argv[2],'rb'))
    F=Frame(k)
    sol=solve_relations(F,cov)
    bad,lx=check_function(F,cov,sol)
    rows,hrows,lin=needed_rows(F,sol)
    e=Ech(rows+hrows+lin)
    ez=Ech(rows)
    print('function mismatches:',bad,' rank of all needed high functions:',e.n,' of ny',F.ny,' (z rows only',ez.n,')')
    print(' => cache products needed for high part:', e.n - (1+len(F.Y)) - len(F.tags_hi), '+ low 4, total cache', e.n-(1+len(F.Y))-len(F.tags_hi)+4, '+ chips', len(cov))
    pickle.dump(sol, open(sys.argv[2].replace('cover','sol'),'wb'))
