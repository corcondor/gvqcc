"""Exactly test Boolean algebraic degrees, not just product-token dependency."""
from pathlib import Path
import sys,itertools,json,hashlib
import numpy as np
from relation_rank_search import rank
from dqi_kernel_motif_audit import arrays_from_kmb,canonical_ccx

def get_windows(path):
    h,v=arrays_from_kmb(path);op,q30,q31,q32,q20,q21,*_=v
    p3=np.flatnonzero((op&48)==48);m=op[p3]==49;pc=p3[m];a,b,t=q30[m],q31[m],q32[m]
    cand=np.arange(len(pc)-41,dtype=np.int32);cand=cand[(t[cand]==t[cand+1])&(a[cand]==a[cand+3])&(b[cand]==b[cand+3])&(a[cand]==a[cand+4])&(b[cand]==b[cand+4])]
    ref=canonical_ccx(0,a,b,t)
    hits=np.array([i for i in cand if canonical_ccx(int(i),a,b,t)==ref],dtype=np.int32)
    assert len(hits)>0
    p2=np.flatnonzero((op&48)==32)
    for k in np.flatnonzero(np.diff(hits)==42):
        start, end=map(int,(pc[hits[k]],pc[hits[k+1]]))
        if int(pc[hits[k]+41])-start!=1292 or int(pc[hits[k+1]+41])-end!=1292: continue
        if np.any((op[start:end+1293]!=33)&(op[start:end+1293]!=49)):continue
        i2,i3=int(np.searchsorted(p2,start)),int(np.searchsorted(p3,start))
        dep=[0]*h['qubits']; triples=[]; nonlinear=0;cc=0
        for i in range(start,end+1293):
            if op[i]==33:
                x,y=int(q20[i2]),int(q21[i2]);i2+=1;dep[y]^=dep[x];triples.append((x,y))
            else:
                x,y,z=int(q30[i3]),int(q31[i3]),int(q32[i3]);i3+=1
                if dep[x] or dep[y]: nonlinear+=1
                dep[z]^=1<<cc;cc+=1;triples.append((x,y,z))
        if nonlinear:yield start,end,triples,nonlinear

def mul(x,y):
    res=set()
    for a,b in itertools.product(x,y):
        m=a|b
        if m in res:res.remove(m)
        else:res.add(m)
    return res

def anf(gates):
    wires=sorted(set(itertools.chain.from_iterable(gates)))
    forms={w:{1<<i} for i,w in enumerate(wires)}
    ctr=[]; first=[[],[]]; second_pure=[]; second_dirty_linear=[]
    for g in gates:
        x,y=g[:2]
        if len(g)==2: forms[y]^=forms[x]
        else:
            a,b=forms[x],forms[y]
            ctr.append([max(f.bit_count() for f in u) if u else -1 for u in [a,b]])
            for ix, f in enumerate((a,b)):
                linear=sum(m for m in f if m.bit_count()==1)
                if len(ctr)<=42: first[ix].append(linear)
                elif ctr[-1][ix]==1: second_pure.append(linear)
                else: second_dirty_linear.append(linear)
            forms[g[-1]]^=mul(a,b)
    stats={}
    for w,u in forms.items():
        for m in u:
            n=m.bit_count()
            stats[n]=stats.get(n,0)+1
    ranks=[rank(v) for v in [*first,second_pure,second_dirty_linear]]
    ints=[ranks[i]+ranks[2]-rank(v+second_pure) for i,v in enumerate(first)]
    three=rank(first[0]+first[1])+ranks[2]-rank(first[0]+first[1]+second_pure)
    return len(wires),stats,ctr[42:],dict(operand_ranks=ranks,linear_second_with_first_intersection=ints, linear_second_with_first_combined_intersection=three)

def main():
    p=Path(sys.argv[1]);rows=[]
    for x,y,g,d in get_windows(p):
        w,s,c,span=anf(g)
        rows.append(dict(first_start=x,second_start=y,active_wires=w,dependent_ccx=d,exit_anf_monomial_histogram=s,
             second_kernel_control_degrees=sorted(set(tuple(pair) for pair in c)),control_span=span))
    with p.open('rb') as f:h=hashlib.file_digest(f,'sha256').hexdigest()
    print(json.dumps(dict(sha256=h,scope='All input wires independent, exact commutative Boolean ANF',cases=rows),indent=2))
if __name__=='__main__':
    assert mul({1,2},{1,2})=={1,2}
    assert mul({1,3},{1})=={1,3}
    main()
