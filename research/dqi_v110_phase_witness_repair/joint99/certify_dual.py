"""Recover the exact GF(2^12)[e]/(e²) tensors at the four non-field windows."""
from certify_field import *
from collections import Counter
def kernel(cols):
  r={}
  for i,x in enumerate(cols):
    y=1<<i
    while x and x.bit_length() in r:
      a,b=r[x.bit_length()];x^=a;y^=b
    if x:r[x.bit_length()]=(x,y)
    else:yield y

def identify(terms,rng):
  n=24
  bs=[basis(t[j] for t in terms) for j in range(3)]
  assert [len(b) for b in bs]==[n,n,n]
  assert rank(bs[0]+bs[1])==48
  fs=[coord(b) for b in bs]
  ts=[tuple(f(x) for f,x in zip(fs,t)) for t in terms]
  def prod(x,y):
    r=0
    for a,b,w in ts:
      if (a&x).bit_count()%2 and (b&y).bit_count()%2:r^=w
    return r
  e=[1<<i for i in range(n)]
  for k in range(256):
    a,b=rng.randrange(1,1<<n),rng.randrange(1,1<<n)
    cl,cr=[prod(x,b) for x in e],[prod(a,y) for y in e]
    if rank(cl)==rank(cr)==24:break
  else:raise ValueError('no full slices')
  L,R=coord(cl),coord(cr)
  unit=prod(a,b)
  tbl=[[prod(L(x),R(y)) for y in e] for x in e]
  def mul(x,y):
    z=0; ii=list(ids(y))
    for i in ids(x):
      for j in ii:z^=tbl[i][j]
    return z
  sq=[tbl[i][i] for i in range(n)]
  eta=next(kernel(sq))
  assert rank(sq)==12 and mul(eta,eta)==0
  B=basis(sq)
  for _ in range(32):
    g=0
    for k in ids(rng.randrange(1,1<<12)):g^=B[k]
    powers=[unit]
    for _ in range(11):powers.append(mul(g,powers[-1]))
    if rank(powers)==12:break
  else:raise ValueError('no degree 12 generator')
  C=coord(powers)
  p=(1<<12)|C(mul(g,powers[-1]))
  assert irr(p,12)
  eta_basis=[mul(eta,x) for x in powers]
  D=coord(powers+eta_basis)
  exp=[prem(1<<i,p) for i in range(23)]
  for i,x in enumerate(powers+eta_basis):
    for j,y in enumerate(powers+eta_basis):
      d=(i//12+j//12)
      want=0 if d==2 else exp[i%12+j%12]<<(12*d)
      assert D(mul(x,y))==want
  return p,dict(left=bs[0],right=bs[1],cl=cl,cr=cr,L=D,R=D,output=bs[2],powers=powers+eta_basis)

if __name__=='__main__':
  wanted={x['start'] for x in map(json.loads,open(sys.argv[2])) if x['irreducible'] is None}
  rng=Random(1701)
  for m,g in parse(sys.argv[1]):
    if m[0] in wanted:
      p,_=identify(extract(g),rng)
      print(json.dumps(dict(start=m[0],end=m[1],base_irreducible=hex(p),basis_pairs=576)),flush=True)
