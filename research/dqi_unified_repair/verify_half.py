"""Syndrome-only classical preimage + independent native (D,H)->phase->(D,H).
The classical BM and modular division are NOT part of the emitted circuit.
"""
import random, json, hashlib, argparse
from pathlib import Path
import numpy as np
import kickmix as km
import field_scan as F
m=F.mul
K=[3134,3169,3257,3302,3384,3431,3519,3552,3592,3633,3671,3727,3792,3854,3921,3977,4054]
def trim(x):
 x=list(x)
 while x and not x[-1]:x.pop()
 return x
def add(x,y):
 z=[0]*max(len(x),len(y))
 for i,c in enumerate(x):z[i]^=c
 for i,c in enumerate(y):z[i]^=c
 return trim(z)
def prod(x,y):return trim(F.prod(x,y)) if x and y else []
def divrem(x,y):
 x=trim(x);y=trim(y);assert y
 q=[0]*max(0,len(x)-len(y)+1)
 while len(x)>=len(y):
  k=len(x)-len(y);v=m(x[-1],F.inv(y[-1]));q[k]=v
  for j,c in enumerate(y):x[k+j]^=m(c,v)
  x=trim(x)
 return trim(q),x
def invmod(a,b):
 r,s=b[:],divrem(a,b)[1];u,v=[],[1]
 while s:
  q,t=divrem(r,s);r,s=s,t;u,v=v,add(u,prod(q,v))
 assert len(r)==1
 return divrem([m(c,F.inv(r[0])) for c in u],b)[1]
def pad(x,n):
 assert len(x)<=n
 return x+[0]*(n-len(x))
def deriv(x):return trim([c if i%2 else 0 for i,c in enumerate(x)][1:])
def moments(e):
 s=[0]*70
 for j,c in e.items():
  x=F.EXP[j];v=m(c,x)
  for i in range(70):s[i]^=v;v=m(v,x)
 return s
def decode(s):
 c,b=[1],[1];l,j,d=0,1,1
 for i,v in enumerate(s):
  for k in range(1,l+1):
   if k<len(c):v^=m(c[k],s[i-k])
  if not v:j+=1;continue
  old=c[:];c=add(c,[0]*j+[m(m(v,F.inv(d)),x) for x in b])
  if 2*l<=i:l,b,j,d=i+1-l,old,1,v
  else:j+=1
 assert l<=35 and len(c)==l+1 and c[0]==1
 D=c[::-1];N=trim(pad(prod(s,c)[:l],l)[::-1])
 assert not any(prod(s,c)[l:70])
 return D,N,l
def make_squarefree(D,N,w):
 P=[0,1] if (35-w)%2 else [1]
 for k in K[:(35-w)//2]:P=prod(P,[k,1,1])
 return prod(D,P),prod(N,P)
def half(D,N):
 assert len(D)==36 and D[-1]==1
 sqrt=lambda x:F.power(x,2048)
 A=trim([sqrt(c) for c in D[::2]])
 B=trim([sqrt(c) for c in D[1::2]])
 N0=trim([sqrt(c) for c in N[::2]])
 N1=trim([sqrt(c) for c in N[1::2]])
 assert len(B)==18 and B[-1]==1
 C=invmod(A,B)
 U=divrem(prod(N0,C),B)[1];T=divrem(prod(N1,C),B)[1]
 Z,r=divrem(add(N0,prod(A,U)),B);assert not r
 W,r=divrem(add(N1,prod(A,T)),B);assert not r
 V0=add(Z,[0]+T);V1=add(W,U)
 V=[0]*35
 for i,c in enumerate(V0):V[2*i]=m(c,c)
 for i,c in enumerate(V1):V[2*i+1]=m(c,c)
 assert divrem(add(prod(deriv(D),V),N),D)[1]==[]
 q0=N0[17] if len(N0)>17 else 0
 return [q0]+pad(T,17)+pad(U,17),V
def fixtures():
 rng=random.Random(491360);out=[]
 for w in range(36):
  for k in range(4):
   e={j:rng.randrange(1,4096) for j in rng.sample(range(4095),w)}
   out.append(("random",w,e))
  if w:
   js=rng.sample(range(4095),w);D=[1]
   for j in js:D=prod(D,[F.EXP[j],1])
   dp=deriv(D)
   e={j:F.inv(m(F.EXP[j],F.evalpoly(dp,F.EXP[j]))) for j in js}
   out.append(("constant_numerator",w,e))
 G=[1]
 for k in K:G=prod(G,[k,1,1])
 for k in range(24):
  js=rng.sample(range(4095),35);D=[1]
  for j in js:D=prod(D,[F.EXP[j],1])
  dp=deriv(D);a=rng.randrange(1,4096)
  e={j:m(a,F.inv(m(m(F.EXP[j],F.evalpoly(G,F.EXP[j])),F.evalpoly(dp,F.EXP[j])))) for j in js}
  out.append(("allpole",35,e))
 return out
def bits(x):
 a=np.asarray(x,np.uint16)
 return ((a[:,:,None]>>np.arange(12))&1).reshape(len(x),-1).T.astype(bool)
def sha(path):return hashlib.file_digest(open(path,'rb'),'sha256').hexdigest()
def main():
 assert len(set(K))==17
 for k in K:assert all(F.evalpoly([k,1,1],x) for x in range(4096))
 rows=[];target=[];errors=[];groups={}
 for label,w,e in fixtures():
  S=moments(e);D,N,v=decode(S);assert v==w
  for j,c in e.items():
   x=F.EXP[j];assert F.evalpoly(D,x)==0 and F.evalpoly(N,x)==m(m(x,c),F.evalpoly(deriv(D),x))
  D,N=make_squarefree(D,N,w);H,V=half(D,N)
  assert len(D)==36 and len(H)==35 and len(V)==35
  for j,c in e.items():assert F.evalpoly(V,F.EXP[j])==m(F.EXP[j],c)
  rows.append(D[:-1]+H);target.append(D[:-1]+V);errors.append(e);groups[label]=groups.get(label,0)+1
 print('classical exact',len(rows),groups,flush=True)
 q=km.array([km.q(i) for i in range(840)]);anc=km.array([km.q(i) for i in range(840,851)])
 mreg=km.array([km.b(i) for i in range(49140)])
 arr=bits(rows);expected=bits(target)
 rng=np.random.default_rng(7128);receipts=[]
 for name,forward in [('forward.kmb',True),('half.kmb',False)]:
  c=km.Circuit.from_file(name);assert c.num_qubits==(840 if forward else 851)
  assert set(c.register_data)=={f'D{i}' for i in range(35)}|{f'H{i}' for i in range(35)}|{f'E{i}' for i in range(4095)}
  err=np.zeros(4,dtype=int);shots=0;paid=0
  for seed in (611,977):
   for i in range(0,len(rows),32):
    j=min(len(rows),i+32);n=j-i
    M=rng.integers(0,4096,(n,4095),dtype=np.uint16)
    for k in range(n):
     if (i+k)%5==0:M[k]=0
     elif (i+k)%5==1:
      M[k]=0;pos=next(iter(errors[i+k]),0);M[k,pos]=1<<((i+k)%12)
    mb=bits(M);p=np.array([sum((int(M[k,t])&v).bit_count() for t,v in errors[i+k].items())%2 for k in range(n)],bool)
    sim=km.Simulator(batch_size=n,seed=seed+i,debug_print=False,counting_operations=True);sim.use_same_registers_as(c);sim.write_across_shots(q,arr[:,i:j]);sim.write_across_shots(mreg,mb);sim.do(c)
    e=[(sim.read_across_shots(q)!=(expected if forward else arr)[:,i:j]).any(0),(np.zeros(n,bool) if forward else sim.read_across_shots(anc).any(0)),(sim.read_across_shots(mreg)!=mb).any(0),sim.read_phase_flipped_across_shots()!=(False if forward else p)]
    err+=np.array([x.sum() for x in e]);shots+=n;paid+=int(sim.operation_statistics().num_toffoli_like)
    if any(err):print('FAIL',name,i,err.tolist(),flush=True);raise RuntimeError('native mismatch')
  d=dict(file=name,Q=c.num_qubits,ops=len(c),static_paid=int(c.operation_statistics().num_toffoli_like),shots=shots,errors=err.tolist(),mean_paid=paid/shots,sha256=sha(name))
  print(json.dumps(d),flush=True);receipts.append(d)
 result=dict(scope="native half-solved canonical D,H phase; syndrome decoder and two degree-17 modular multiplications not emitted",classical_cases=len(rows),groups=groups,weights=list(range(36)),results=receipts)
 Path('half_receipt.json').write_text(json.dumps(result,indent=2)+'\n')
if __name__=='__main__':main()

