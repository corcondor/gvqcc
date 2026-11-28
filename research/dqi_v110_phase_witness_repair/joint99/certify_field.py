"""Recover field tensors exactly from the emitted 99-CCX windows."""
from classify import extract,coord,basis
from tensor_audit import parse,rank,ids,CC
from random import Random
import sys,json
def prem(a,b):
 while a.bit_length()>=b.bit_length():a^=b<<(a.bit_length()-b.bit_length())
 return a
def pgcd(a,b):
 while b:a,b=b,prem(a,b)
 return a
def irr(p,n):
 y=2
 for i in range(1,n+1):
  y=prem(sum(1<<(2*k) for k in ids(y)),p)
  if i in (n//2,n//3) and pgcd(y^2,p)!=1:return False
 return y==2

def certify(terms,rng):
 n=24; mask=(1<<n)-1
 assert all(not (a&CC or b&CC) for a,b,_ in terms)
 bs=[basis(t[j] for t in terms) for j in range(3)]
 assert [len(b) for b in bs]==[n,n,n]
 assert rank(bs[0]+bs[1])==2*n
 t=[tuple(f(x) for f,x in zip([coord(b) for b in bs],p)) for p in terms]
 def prod(x,y):
  r=0
  for a,b,w in t:
   if (a&x).bit_count()%2 and (b&y).bit_count()%2:r^=w
  return r
 e=[1<<i for i in range(n)]
 for k in range(64):
  a,b=(1,1) if k==0 else (rng.randrange(1,mask+1),rng.randrange(1,mask+1))
  cols_l,cols_r=[prod(x,b) for x in e],[prod(a,y) for y in e]
  if rank(cols_l)==n and rank(cols_r)==n:break
 else:return None
 L=coord(cols_l)
 R=coord(cols_r)
 unit=prod(a,b)
 tbl=[[prod(L(x),R(y)) for y in e] for x in e]
 def mul(x,y):
  z=0
  js=list(ids(y))
  for i in ids(x):
   for j in js:z^=tbl[i][j]
  return z
 for _ in range(16):
  g=rng.randrange(1,mask+1)
  powers=[unit]
  for _ in range(n-1):powers.append(mul(powers[-1],g))
  if rank(powers)==n:break
 else:raise ValueError('no full degree generator')
 C=coord(powers)
 p=(1<<n)|C(mul(powers[-1],g))
 assert irr(p,n)
 expect=[prem(1<<i,p) for i in range(2*n-1)]
 for i,x in enumerate(powers):
  for j,y in enumerate(powers):
   assert C(mul(x,y))==expect[i+j]
 return p

if __name__=='__main__':
 rng=Random(22019)
 for m,g in parse(sys.argv[1]):
  try:
   p=certify(extract(g),rng)
  except (AssertionError,ValueError) as e:
   p=None
  print(json.dumps(dict(start=m[0],end=m[1],irreducible=hex(p) if p else None,basis_pairs=576 if p else 0)),flush=True)
