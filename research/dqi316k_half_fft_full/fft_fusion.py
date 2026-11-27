import pathlib
import crt882 as C
from functools import lru_cache
from exp.arithmetic import field as ar
@lru_cache(None)
def cols(c):return tuple(C.m(c,1<<i) for i in range(12))
def fft_scan(b,A,B,E,skip_points,node_polynomial):
 data=iter(map(int,pathlib.Path(__file__).with_name('plan.txt').read_text().split()))
 beta=[next(data) for _ in range(12)];assert [next(data) for _ in range(12)]==[1<<i for i in range(12)]
 N=35;M=4095;P=[[next(data) for j in range(i+1)] for i in range(36)];S=[[next(data) for j in range(4096)] for i in range(12)]
 skip=set(skip_points);mask=b.alloc_bits(12);active=b.alloc_bits(1)[0]
 def add(x,y,c):
  if c==1:b.cx(x,y)
  elif c:ar.linear_xor(b,x,y,cols(c))
 def scale(x,c):
  if c!=1:ar.linear_inplace(b,x,cols(c))
 def const(y,c):
  for i in C.bits(c):b.x(y[i])
 def basis(rev):
  for i in (range(36) if rev else range(35,-1,-1)):
   v=C.inv(P[i][i])
   if not rev and i<N:scale(A[i],v);scale(B[i],v)
   for j in (range(i-1,-1,-1) if rev else range(i)):
    if i==N:const(B[j],C.m(v,P[i][j]))
    else:add(A[i],A[j],P[i][j]);add(B[i],B[j],P[i][j])
   if rev and i<N:scale(A[i],P[i][i]);scale(B[i],P[i][i])
 def split(k,c):
  if not c:return
  h=1<<(k-1)
  for i in range(min(h,N-h+1)):
   j=i+h
   if j==N:const(B[i],C.m(c,C.inv(P[N][N])))
   else:add(A[j],A[i],c);add(B[j],B[i],c)
 count=0
 def leaf(x):
  nonlocal count
  if not x:return
  j=C.log[x]
  if j in skip:return
  count+=1;v=C.evalp(node_polynomial,x);c=C.inv(C.m(x,v));assert c
  b.bit_store(mask,False)
  for i in range(12):
   for j2 in C.bits(C.m(c,1<<i)):b.cx(E[j][j2],mask[i])
  b.bit_store(active,False)
  for t in mask:b.bit_store(active,True,control=t)
  b.push_condition(active)
  work=b.alloc_qubits(11);b.init_and(B[0][0],B[0][1],work[0])
  for i in range(2,12):b.init_and(work[i-2],B[0][i],work[i-1])
  b.ccz(work[-1],A[0],mask)
  for i in range(11,1,-1):b.del_and(work[i-2],B[0][i],work[i-1])
  b.del_and(B[0][0],B[0][1],work[0]);b.free(work)
  b.pop_condition()
 def dfs(k,a):
  if k==0:leaf(a);return
  c=S[k-1][a];split(k,c);dfs(k-1,a);split(k,1);dfs(k-1,a^beta[k-1]);split(k,c^1)
 basis(False);b.x(B[0]);dfs(12,0);b.x(B[0]);basis(True)
 assert count==4095-len(skip);b.free(active);b.free(mask)
 print('FFT actual leaves',count,flush=True)

