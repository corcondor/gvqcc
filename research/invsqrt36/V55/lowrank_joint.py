"""Exact GF(2) transvection factorization for conditional affine maps."""
def rankbasis(vs):
 B={}
 for v in vs:
  while v:
   p=v.bit_length()-1
   if p not in B:B[p]=v;break
   v^=B[p]
 return B

def nullspace(rows,n):
 B=rankbasis(rows);out=[]
 for j in range(n):
  if j in B:continue
  v=1<<j
  for p in sorted(B):
   if (v&B[p]).bit_count()&1:v^=1<<p
  out.append(v)
 assert all(not ((v&r).bit_count()&1) for v in out for r in rows)
 return out

def apply(A,v):
 return sum(((a&v).bit_count()&1)<<i for i,a in enumerate(A))

def transvections(rows,n,mode=0):
 I=[1<<i for i in range(n)];A=list(rows);out=[]
 while A!=I:
  D=[a^i for a,i in zip(A,I)];rank=len(rankbasis(D));candidates=[]
  basis=list(rankbasis(D).values());xs=I if mode<2 else I[::-1]
  for x in xs:
   u=apply(D,x)
   if not u:continue
   v0=[v for v in basis if (v&x).bit_count()&1];vs=[]
   for v in v0:
    if not ((v&u).bit_count()&1):vs.append(v)
    else:
     for w in basis:
      if (w&x).bit_count()%2==0 and (w&u).bit_count()%2:vs.append(v^w)
   for v in vs:
    candidates.append((u.bit_count()+v.bit_count(),max(u.bit_count(),v.bit_count()),u,v))
  assert candidates,(n,A)
  _,_,u,v=min(candidates,key=lambda t:(t[mode%2],t[1-mode%2],t[2],t[3]))
  assert u and v and not ((u&v).bit_count()&1)
  va=0
  for j in range(n):
   if v>>j&1:va^=A[j]
  A=[a^(va if u>>i&1 else 0)for i,a in enumerate(A)]
  assert len(rankbasis([a^i for a,i in zip(A,I)]))==rank-1
  out.append((u,v))
 return out[::-1]

if __name__=='__main__':
 import random
 rng=random.Random(55)
 for n in range(2,12):
  for k in range(100):
   A=[1<<i for i in range(n)]
   for _ in range(30):
    i,j=rng.sample(range(n),2);A[i]^=A[j]
   ts=transvections(A,n);B=[1<<i for i in range(n)]
   for u,v in ts:
    w=0
    for j in range(n):
     if v>>j&1:w^=B[j]
    B=[r^(w if u>>i&1 else 0)for i,r in enumerate(B)]
   assert B==A
 print('1000 random invertible matrices PASS')
