from tensor_audit import *
from random import Random

def basis(xs):
 bas={}
 for x in xs:
  while x:
   k=x.bit_length()
   if k in bas:x^=bas[k]
   else:bas[k]=x;break
 return list(bas.values())

def coord(bs):
 b={}
 for j,x in enumerate(bs):
  z=1<<j
  while x.bit_length() in b:
   y,i=b[x.bit_length()];x^=y;z^=i
  assert x
  b[x.bit_length()]=(x,z)
 def c(x):
  z=0
  while x:
   y,i=b[x.bit_length()];x^=y;z^=i
  return z
 return c

def extract(g):
 a=[1<<i for i in range(Q)];d=[0]*Q;p=[]
 for op,s,t,u in g:
  if op==16:a[s]^=CC
  if op==33:a[t]^=a[s];d[t]^=d[s]
  if op==49:
   assert not (d[s]|d[t]);d[u]^=1<<len(p);p.append((a[s],a[t]))
 dirs=[0]*len(p)
 for q,dd in enumerate(d):
  for i in ids(dd):dirs[i]|=1<<q
 return [(*pair,z) for pair,z in zip(p,dirs)]

def trial(terms,rng):
 n=rank(t[0] for t in terms)
 assert all(rank(t[j] for t in terms)==n for j in (1,2))
 c=[coord(basis(t[j] for t in terms)) for j in range(3)]
 t=[tuple(f(x) for f,x in zip(c,p)) for p in terms]
 def prod(x,y):
  r=0
  for a,b,w in t:
   if (a&x).bit_count()%2 and (b&y).bit_count()%2:r^=w
  return r
 e=[1<<i for i in range(n)]
 best=[0,0];inv=[None,None]
 for j in range(2):
  for k in range(2048):
   x=rng.randrange(1,1<<n)
   ar=[prod(x,y) if j==0 else prod(y,x) for y in e]
   r=rank(ar)
   if r>best[j]:best[j]=r
   if r==n:inv[j]=coord(ar);break
 if None in inv:return {'max_slice':best}
 left,right=inv[1],inv[0]
 def mul(u,v):return prod(left(u),right(v))
 xs=[left(x) for x in e];ys=[right(y) for y in e]
 tbl=[[prod(x,y) for y in ys] for x in xs]
 comm=all(tbl[i][j]==tbl[j][i] for i in range(n) for j in range(i))
 squ=[tbl[i][i] for i in range(n)]
 assoc=True
 if comm:
  for i in range(n):
   if any(mul(tbl[i][j],e[k])!=mul(e[i],tbl[j][k]) for j in range(n) for k in range(n)):
    assoc=False;break
 else:assoc=None
 rr={}
 kernel=[]
 for i,(u,v) in enumerate(zip(squ,e)):
  a,b=u^v,1<<i
  while a and a.bit_length() in rr:
   aa,bb=rr[a.bit_length()];a^=aa;b^=bb
  if a:rr[a.bit_length()]=(a,b)
  else:kernel.append(b)
 idem=[0]
 for b in kernel:idem += [x^b for x in idem]
 atoms=[x for x in idem[1:] if not any(mul(x,y)==y for y in idem[1:] if x!=y)] if comm and assoc else []
 return dict(max_slice=best,comm=comm,assoc=assoc,square_rank=rank(squ),idempotent_dim=len(kernel),
             crt_dims=sorted(rank(mul(x,y) for y in e) for x in atoms))

if __name__=='__main__':
 rng=Random(778)
 for i,(m,g) in enumerate(parse('blocks.txt')):
  if i>2:break
  t=extract(g)
  print(m,trial(t,rng),[trial(t[k:k+33],rng) for k in (0,33,66)],flush=True)
