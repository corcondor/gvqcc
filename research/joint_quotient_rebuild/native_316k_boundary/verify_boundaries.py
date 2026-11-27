"""Check recovered physical word maps against exact sparse rational function.
High map inferred from 64 w35; mixed64 held out. Not a global proof.
"""
import sys, json, struct
from pathlib import Path
import numpy as np
import direct_codec as D

def read_cuts(file):
 d={}
 with open(file,'rb') as f:
  while i:=f.read(4):
   x=np.frombuffer(f.read(900*8),dtype='<u8');assert len(x)==900
   d[struct.unpack('<I',i)[0]]=x.copy()
 return d

def map_words(cut,base):
 rows=[[]for _ in range(35)]
 for l in Path('highmap.tsv').read_text().splitlines():
  c,w,j,m=map(int,l.split())
  if c==cut and base<=j<base+35:rows[j-base].append((w,m))
 assert all(len(r)==12 for r in rows),[len(r)for r in rows]
 for r in rows:
  assert len({w for w,m in r})==12 and len({m for w,m in r})==12
  assert len({__import__('functools').reduce(int.__xor__,[m for k,(_,m) in enumerate(r) if mask>>k&1],0)for mask in range(4096)})==4096
 return rows

def decode(snapshot,rows):
 out=np.zeros((64,35),dtype=np.int64)
 for j,r in enumerate(rows):
  masks=[m for w,m in r];lut=np.zeros(4096,dtype=np.int64)
  for v in range(4096):lut[sum(((m&v).bit_count()&1)<<k for k,m in enumerate(masks))]=v
  p=np.zeros(64,dtype=np.int64)
  for k,(w,m) in enumerate(r):p|=((snapshot[w]>>np.arange(64,dtype=np.uint64))&1).astype(np.int64)<<k
  out[:,j]=lut[p]
 return out

def check(file):
 d=read_cuts(file);B=decode(d[32727000],map_words(32727000,0));B2=decode(d[38919000],map_words(38919000,0));A=decode(d[47121000],map_words(47121000,140));es=json.load(open('mixed64_errors.json'));out=[]
 for j,e in enumerate(es):
  E={int(x):v for x,v in e.items()};N,T=D.rational(E);p=B[j].tolist()+[1];a=A[j].tolist();cross=D.add(D.pmul(a,T),D.pmul(N,p));rem=cross[:];g=[]
  for k in D.NODES:
   n=0
   while rem:
    q,r=D.divrem(rem,D.g(k))
    if r:break
    rem=q;n+=1
   if n:g.append([k,n])
  out.append(dict(i=j,w=len(E),root_misses=[x for x in E if D.ev(p,x)],B_unchanged=bool(np.array_equal(B[j],B2[j])),ratio_ok=not cross,cross_degree=len(cross)-1,cross_factors=g,remaining_cross_degree=len(rem)-1,consistent_leading_coefficient=len({D.div(D.ev(p[:-1],x),D.EXP[(35*D.LOG[x])%4095]) for x in E})<=1))
 return out
if __name__=='__main__':
 x=check(sys.argv[1]);print(json.dumps(x,indent=2));print('bad',[(r['i'],r['w'])for r in x if not r['ratio_ok']],file=sys.stderr)
