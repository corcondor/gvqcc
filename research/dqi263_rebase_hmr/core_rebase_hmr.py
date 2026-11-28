"""Low-rank pad change, followed by the existing half-degree Bezout converter.
Experimental: half-Euclidean gap<=2 is NOT proved for all inputs.
"""
import random, sys, json, hashlib, time
from pathlib import Path
from core_direct_unit import *
from core_direct_unit import Pipeline
import crt882 as C
OLD=[
[2048,2067,2068,2120,2140,2308,2320,2380,2392,3104,3124,3176,3196,3364,3376,3436,3448],
[2054,2066,2069,2126,2138,2306,2326,2378,2398,3110,3122,3182,3194,3362,3382,3434,3454],
[2067,2068,2120,2140,2308,2320,2380,2392,3104,3124,3176,3196,3364,3376,3436,3448],
[2066,2069,2126,2138,2306,2326,2378,2398,3110,3122,3182,3194,3362,3382,3434,3454],
[2067,2120,2140,2308,2320,2380,2392,3104,3124,3176,3196,3364,3376,3436,3448],
[2069,2126,2138,2306,2326,2378,2398,3110,3122,3182,3194,3362,3382,3434,3454]]
MARK=[2048,2054,2068,2066,2120,2126]
def trace(a):
 t=a
 for _ in range(11):a=C.m(a,a);t^=a
 return t
pool=[k for k in range(4096) if trace(k)==1 and all(k not in p for p in OLD)]
random.Random(202611281434).shuffle(pool)
NEW=[]
for p in OLD:
 NEW.append(pool[:len(p)]);del pool[:len(p)]
def pad(w,k):
 p=[0,1] if w%2==0 else [1]
 for a in k:p=C.mul(p,[a,1,1])
 assert len(p)==36-w
 return p
def xor_into(x,y,v):
 if v:
  for i,a in enumerate(x):y[i]^=C.m(a,v)
def basis_ops(w,n):
 if n==0:return []
 old,new=pad(w,OLD[w]),pad(w,NEW[w])
 columns=[];piv={}
 def add(col):
  u=col[:]
  for j,r in sorted(piv.items()):
   if u[j]:xor_into(r,u,u[j])
  j=next((j for j,x in enumerate(u) if x),None)
  if j is None:return False
  piv[j]=[C.m(x,C.inv(u[j])) for x in u];columns.append(col);return True
 for p in (old,new):
  for i in range(n):
   col=[0]*i+p+[0]*(w+(len(pad(w,OLD[w])))-len(p)-i)
   # target dimension D=36 or N=35
   col=col[:len(p)+n-1];assert len(col)==len(p)+n-1
   assert add(col)
 size=len(old)+n-1
 for i in range(size):
  col=[0]*size;col[i]=1;add(col)
 assert len(columns)==size
 a=[list(row) for row in zip(*columns)];ops=[]
 for j in range(size):
  i=next(i for i in range(j,size) if a[i][j])
  if i!=j:a[i],a[j]=a[j],a[i];ops.append(('swap',i,j,0))
  v=C.inv(a[j][j])
  if v!=1:a[j]=[C.m(x,v) for x in a[j]];ops.append(('scale',j,j,v))
  for i in range(size):
   if i!=j and a[i][j]:
    v=a[i][j];xor_into(a[j],a[i],v);ops.append(('add',j,i,v))
 assert a==[[int(i==j) for j in range(size)] for i in range(size)]
 return ops
def change(b,words,ops,rev=False):
 for g,i,j,v in (reversed(ops) if rev else ops):
  if g=='swap':b.swap(km.array(words[i]),km.array(words[j]))
  elif g=='scale':frame(b,words[i],C.inv(v) if rev else v)
  else:lx(b,words[i],words[j],v)
def marker(b,D,k,f):
 # Remainder of D mod XÂ²+X+k is held in D[0:2] temporarily.
 a=[1]
 rem=[]
 for j in range(len(D)):
  rem.append((a+[0,0])[:2])
  a=C.div(C.mul(a,[0,1]),[k,1,1])[1]
 for j in range(2,len(D)):
  for i,v in enumerate(rem[j]):lx(b,D[j],D[i],v)
 wire=D[0]+D[1];anc=list(b.alloc_qubits(22))
 for q in wire:b.x(q)
 b.ccx(wire[0],wire[1],anc[0])
 for i in range(2,23):b.ccx(anc[i-2],wire[i],anc[i-1])
 b.ccx(anc[21],wire[23],f)
 for i in range(22,1,-1):b.del_and(anc[i-2],wire[i],anc[i-1])
 b.del_and(wire[0],wire[1],anc[0])
 for q in wire:b.x(q)
 b.free(km.array(anc))
 for j in range(2,len(D)):
  for i,v in enumerate(rem[j]):lx(b,D[j],D[i],v)
def marker_repay(b,D,k,f):
 # The marker equivalence holds on the admitted old/new pad chart.
 m=b.alloc_bits(1)[0]
 b.hmr(f,m)
 b.push_condition(m)
 a=[1];rem=[]
 for j in range(len(D)):
  rem.append((a+[0,0])[:2])
  a=C.div(C.mul(a,[0,1]),[k,1,1])[1]
 for j in range(2,len(D)):
  for i,v in enumerate(rem[j]):lx(b,D[j],D[i],v)
 wire=D[0]+D[1];anc=list(b.alloc_qubits(22))
 for q in wire:b.x(q)
 b.ccx(wire[0],wire[1],anc[0])
 for i in range(2,23):b.ccx(anc[i-2],wire[i],anc[i-1])
 b.cz(anc[21],wire[23])
 for i in range(22,1,-1):b.del_and(anc[i-2],wire[i],anc[i-1])
 b.del_and(wire[0],wire[1],anc[0])
 for q in wire:b.x(q)
 b.free(km.array(anc))
 for j in range(2,len(D)):
  for i,v in enumerate(rem[j]):lx(b,D[j],D[i],v)
 b.pop_condition()
 b.bit_store(m,False);b.free(m)
def replace_pad(b,D,N,rev=False):
 for w in (range(5,-1,-1) if rev else range(6)):
  f=b.alloc_qubits(1)[0]
  marker(b,D,NEW[w][0] if rev else MARK[w],f)
  for words,n in [(D,w+1),(N,w)]:
   if not n:continue
   ops=basis_ops(w,n);change(b,words,ops)
   for i in range(n):
    for a,z in zip(words[i],words[n+i]):b.cx(a,z);b.ccx(f,z,a);b.cx(a,z)
   change(b,words,ops,True)
  marker_repay(b,D,MARK[w] if rev else NEW[w][0],f);b.free(f)
def fft_magnitude(b,D,N,E):
 words=[D,N];L=[0,1];S=[];NB=[[1]]
 for beta in BETA:
  c=C.evalp(L,beta);assert c
  S.append(tuple(C.m(x,C.inv(c)) for x in L));L=C.add(C.mul(L,L),[C.m(c,x) for x in L])
 for j in range(1,36):
  k=(j&-j).bit_length()-1;NB.append(C.mul(NB[j^(1<<k)],list(S[k])))
 def basis(a,rev=False):
  for i in (range(len(a)) if rev else range(len(a)-1,-1,-1)):
   d=NB[i][-1]
   if not rev:frame(b,a[i],C.inv(d))
   for j in range(i):lx(b,a[i],a[j],NB[i][j])
   if rev:frame(b,a[i],d)
 def shear(h,c,deg):
  for a in words:
   for j in range(h,min(len(a),deg+1)):lx(b,a[j],a[j-h],c)
 M=list(Pipeline.P.Finish.geometry()['M'])
 ladder=list(b.alloc_qubits(11));mask=list(b.alloc_bits(12));active=b.alloc_bits(1)[0]
 count=0
 def leaf(x):
  nonlocal count
  if not x:return
  j=C.log[x];factor=C.inv(C.m(x,C.m(C.evalp(U,x),C.evalp(M,x))))
  for k in mask:b.bit_store(k,False)
  for i in range(12):
   for t in C.bits(C.m(factor,1<<i)):b.cx(E[j][t],mask[i])
  b.bit_store(active,False)
  for q in mask:b.bit_store(active,True,control=q)
  b.push_condition(active)
  G.root(b,D[0],ladder);b.ccz(ladder[-1],km.array(N[0]),km.array(mask));G.unroot(b,D[0],ladder)
  b.pop_condition()
  count+=1
  if count%512==0:print('MAGSCAN',count,flush=True)
 def dfs(k,x,deg):
  if not k:leaf(x);return
  h=1<<(k-1)
  if deg<h:dfs(k-1,x,deg);dfs(k-1,x^BETA[k-1],deg);return
  c=C.evalp(S[k-1],x);shear(h,c,deg);dfs(k-1,x,h-1);shear(h,1,deg);dfs(k-1,x^BETA[k-1],h-1);shear(h,c^1,deg)
 for a in words:basis(a)
 dfs(12,0,35);assert count==4095
 for a in words:basis(a,True)
 J.cclear(b,mask+[active]);b.free(km.array(ladder))
def main():
 b=km.CircuitBuilder();b.set_max_qubits(900)
 S=[b.create_quantum_register(12,f'S{i}') for i in range(70)];E=[b.create_classical_register(12,f'E{i}') for i in range(4095)]
 key=Pipeline.emit_key_prefix(b,S,j_min=0,stage=lambda _:None)
 N=[list(x) for x in key['N']];D=[list(x) for x in key['D']]
 print('KEY',b.num_allocated_qubits,flush=True);replace_pad(b,D,N);print('REBASE',b.num_allocated_qubits,flush=True)
 DD=[km.array(x) for x in D];NN=[km.array(x) for x in N]
 outer=Pipeline.NewOuter.emit_prefix(b,DD,NN,gauge_flag=key['gauge'].flag,gauge_other=key['carry'][12:],fused=False,stage=lambda x:print('OUTER',x,b.num_allocated_qubits,flush=True))
 finish=Pipeline.P.Finish.emit_prefix(b,DD,NN)
 fft_magnitude(b,D,N,E)
 rec=Pipeline.P.Finish.emit_closing_keep_inverse(b,DD,NN,finish)
 Pipeline.P.Seam.outer_closing_with_inverse(outer.lender,DD,NN,outer,rec,stage=lambda _:None)
 replace_pad(b,D,N,True);Pipeline.emit_key_closing(b,key,stage=lambda _:None)
 assert b.num_allocated_qubits==840
 c=b.finish_circuit();p=Path(sys.argv[1]);c.to_file(str(p),format='kmb')
 print('CORE',json.dumps(dict(Q=c.num_qubits,ops=len(c),paid=int(c.operation_statistics().num_toffoli_like),sha256=hashlib.file_digest(p.open('rb'),'sha256').hexdigest())),flush=True)
if __name__=='__main__':main()

