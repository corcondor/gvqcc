"""Exact polar-rank audit of measurement-free quadratic KMB windows.
No inference from samples. The formal domain is all physical input wires.
Requires native_kmb.py from the V111 chemistry replay archive.
"""
import argparse,collections,itertools,json,sys
from pathlib import Path

def xor(a,b):return a^b

def multiply(a,b):
    z=set()
    for x in a:
        for y in b:
            z.symmetric_difference_update([x|y])
    return z

def basis(vs):
    p={};ret=[]
    for x in vs:
        y=x
        while y:
            k=y.bit_length()-1
            if k in p:y^=p[k]
            else:p[k]=y;ret.append(x);break
    return ret

def polar_rank(poly,n):
    a=[0]*n
    for m in poly:
        if m.bit_count()!=2:continue
        i=(m&-m).bit_length()-1;j=m.bit_length()-1
        a[i]^=1<<j;a[j]^=1<<i
    return len(basis(a))

def audit(ops,start,end,n):
    q=[{1<<i} for i in range(n)];original=0
    for o in ops[start:end+1]:
        a=o.wires
        if o.raw==17:q[a[0]]^={0}
        elif o.raw==33:q[a[1]]^=q[a[0]]
        elif o.raw==34:q[a[0]],q[a[1]]=q[a[1]],q[a[0]]
        elif o.raw==49:q[a[2]]^=multiply(q[a[0]],q[a[1]]);original+=1
        else:raise ValueError('not a unitary Boolean window')
    degree=max((m.bit_count() for row in q for m in row),default=0)
    if degree>2:return {'start':start,'end':end,'ccx':original,'degree':degree,'certified':False}
    mon=sorted({m for row in q for m in row if m.bit_count()==2});idx={m:j for j,m in enumerate(mon)}
    A=basis([sum(1<<idx[m] for m in row if m in idx) for row in q]);r=len(A)
    if r>14:return {'start':start,'end':end,'ccx':original,'degree':degree,'innovation_rank':r,'certified':False}
    ranks=[];low=[]
    for s in range(1,1<<r):
        x=0
        for j,a in enumerate(A):
            if s>>j&1:x^=a
        pol=[mon[j] for j in range(len(mon)) if x>>j&1]
        pr=polar_rank(pol,n);ranks.append(pr)
        if pr==2:low.append(s)
    return {'start':start,'end':end,'ccx':original,'degree':degree,'innovation_rank':r,'polar_rank_histogram':dict(collections.Counter(ranks)),'rank2_direction_span':len(basis(low)),'two_ccx_impossible_on_full_cube':r>2 or (r==2 and len(basis(low))<2),'certified':True}

def main():
    p=argparse.ArgumentParser();p.add_argument('bank',type=Path);p.add_argument('windows',type=Path);p.add_argument('--out',type=Path,required=True);p.add_argument('--vendor',type=Path,required=True);a=p.parse_args();sys.path.insert(0,str(a.vendor));from native_kmb import NativeKMB
    k=NativeKMB.read(a.bank);w=json.loads(a.windows.read_text())['candidates'];R=[]
    for x in w:
        if x['paid']>5:continue
        r=audit(k.ops,x['start'],x['end'],k.header[1]);R.append(r);print(r,flush=True)
    out={'bank_sha256':k.stats()['sha256'],'scope':'formal all-bit cube; no claim for reachable subset','windows':R};a.out.write_text(json.dumps(out,indent=2)+'\n')
if __name__=='__main__':main()
