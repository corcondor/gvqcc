#!/usr/bin/env python3
"""GF(2) constraints preserving existing 15-bank signed6 bit6^bit5 delta equality
under all 74 Givens sign-frame variables. Algebraic screening, no KMB claim.
"""
import numpy as np,json,sys
from pathlib import Path
from givens_gauge_global import tree_info

def vectors(edges):
    info,slots=tree_info(edges)
    slot_to_i={key:i for i,key in enumerate(slots)}
    last={0:None}
    expr=[]
    for k,(p,q,pf,qf) in enumerate(info):
        inbit=(1<<slot_to_i[last[p]]) if last[p] in slot_to_i else 0
        pbit=(1<<slot_to_i[(k,p)]) if pf else 0
        qbit=(1<<slot_to_i[(k,q)]) if qf else 0
        expr.append((pbit^inbit,qbit^inbit))
        last[p]=(k,p);last[q]=(k,q)
    return expr,slots

def nullspace(rows,n=74):
    m=[int(row) for row in rows if row]
    pivots=[];i=0
    for bit in range(n-1,-1,-1):
        pivot=next((j for j in range(i,len(m)) if (m[j]>>bit)&1),None)
        if pivot is None:continue
        m[i],m[pivot]=m[pivot],m[i]
        for j in range(len(m)):
            if j!=i and (m[j]>>bit)&1:m[j]^=m[i]
        pivots.append(bit);i+=1
        if i>=len(m):break
    free=[q for q in range(n) if q not in pivots]
    base=[]
    for f in free:
        z=1<<f
        for row,pivot in zip(m[:i],pivots):
            if row>>f&1:z|=1<<pivot
        base.append(z)
    assert all(all((row & b).bit_count()%2==0 for row in rows) for b in base)
    return base,len(pivots)

def main():
 with np.load('/mnt/data/gvqcc_joint_new/V8_C46_ORIGINAL.npz') as z:w=z['angle_words'].astype(np.uint8);E=z['tree_edges']
 ex,slots=vectors(E)
 for rowidx in [0,1,10,50,75,76,77,100,200,500,900,1218]:
  masks=[ex[k][int(w[rowidx,k] in (32,96))] for k in range(75)]
  constraints=[masks[k]^masks[k-5] for k in range(5,75)]
  ns,rank=nullspace(constraints,len(slots))
  ns2,rank2=nullspace(masks,len(slots))
  print(rowidx,'zero_angles',sum(int(x in (32,96)) for x in w[rowidx]),'rank',rank,'nullity',len(ns),'keep_base_residue_nullity',len(ns2),'free_basis_sizes',[int(b).bit_count() for b in ns])
if __name__=='__main__':main()