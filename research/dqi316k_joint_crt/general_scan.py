"""Generic all-weight canonical rational phase scan. NOT syndrome decoder.
Reuses 2026-11-19 exact dual-number tensor and phase16 template, and #237 rolling/HMR.
Input: 35 coefficients of monic D degree 35, then 35 coefficients of P.
At weight w<35, multiply D and P by X^(35-w); nonzero roots/magnitudes unchanged.
"""
import argparse,hashlib,json,random,base64,zlib
from pathlib import Path
import numpy as np,kickmix as km
import crt882 as C, joint_phase as J
from importlib.metadata import version
Q=891
TERMS=json.loads(zlib.decompress(base64.b64decode("eNotksGRxTAIQxviYMAGXEvm99/GSvIeeJNgHIHI9/mJNqFq/eyL02NCrmwmprYJvk4hsVddEyKbFdmTJux1k1fuMkbu5GuejXOiTuDd/YYJufyywL1MgIQ0d7o9ZB8kzmpj7NWb5z5QICDBrs9cY8Qkz/uUMXx42e/FozCLekjzCD0O1Rxt28OVB56JWiLjDBNr4QaRnc4GusoetixgLS+56iOT7gBZo4aWG8P9eXobngo99DRvuAlRI8+iYY+Q2zUEqh9CU7GY4de1t2hICm9NcXeYUKEpPSkPgcWOcuPkoV2JCsxARCyNBPsFrGpU0Jj/H0wMHGbgq29oOIrwfbWjTo4H3HIteXPJgJcEowLNEn6OfgM4ZoLvoAne/OuIub/fH9wTlJs=")))
TAPE=zlib.decompress(base64.b64decode("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")).decode().splitlines()
def gf(a,b):return C.gf_mul(a,b,6,0x43)
def tr(a,n,mod):
 r=0
 for _ in range(n):r^=a;a=C.gf_mul(a,a,n,mod)
 assert r in (0,1);return r
# Recover the exact 12-bit trace dual mask basis independently.
dual=[next(x for x in range(4096) if all(tr(C.m(x,1<<i),12,C.MOD)==int(i==j) for i in range(12))) for j in range(12)]
# The CRT tower and historical tensor use the same GF64 polynomial basis.
tow={C.xor_word(v for i,v in enumerate(C.BASIS12) if a>>i&1):a for a in range(4096)}
mask_terms=[(i,j,tuple(C.bits(tow[C.m(1<<i,dual[j])]))) for i in range(12) for j in range(12)]
def exact_tensor():
 assert len(TERMS)==42
 for i in range(12):
  for j in range(12):
   a,u=(1<<i,0) if i<6 else (0,1<<(i-6))
   b,v=(1<<j,0) if j<6 else (0,1<<(j-6))
   out=gf(a,b)|((gf(a,v)^gf(u,b))<<6)
   assert C.xor_word(z for l,r,z in TERMS if l>>i&1 and r>>j&1)==out,(i,j)
def parity_pivot(b,reg,mask):
 qs=[reg[i] for i in C.bits(mask)];assert qs
 for x in qs[1:]:b.cx(x,qs[0])
 return qs
def unpivot(b,qs):
 for x in reversed(qs[1:]):b.cx(x,qs[0])
def compute_tensor(b,left,right,out):
 for l,r,z in TERMS:
  a=parity_pivot(b,left,l);c=parity_pivot(b,right,r)
  t=[out[i] for i in C.bits(z)]
  for x in t[1:]:b.cx(t[0],x)
  b.ccx(a[0],c[0],t[0])
  for x in reversed(t[1:]):b.cx(t[0],x)
  unpivot(b,c);unpivot(b,a)
def repay_tensor(b,left,right,mb):
 tmp=b.alloc_bits(1)[0]
 for l,r,z in TERMS:
  a=parity_pivot(b,left,l);c=parity_pivot(b,right,r)
  b.bit_store(tmp,False)
  for i in C.bits(z):b.cx(mb[i],tmp)
  b.ccz(a[0],c[0],tmp)
  unpivot(b,c);unpivot(b,a)
 b.bit_store(tmp,False);b.free(tmp)
def phase16(b,n,c,w):
 # Old template is a true phase-only circuit. Clear all private classical bits.
 qs=n+c+w;mb=list(b.alloc_bits(14))
 for line in TAPE:
  g,*args=line.split()
  if g=="PUSH_CONDITION":b.push_condition(mb[int(args[-1][1:])])
  elif g=="POP_CONDITION":b.pop_condition()
  elif g=="HMR":b.hmr(qs[int(args[0][1:])],mb[int(args[1][1:])])
  else:getattr(b,g.lower())(*(qs[int(x[1:])] for x in args))
 J.cclear(b,mb)
def root(b,f,chain):
 for x in f:b.x(x)
 b.ccx(f[0],f[1],chain[0])
 for i in range(1,11):b.ccx(chain[i-1],f[i+1],chain[i])
def unroot(b,f,chain):
 for i in range(10,0,-1):b.del_and(chain[i-1],f[i+1],chain[i])
 b.del_and(f[0],f[1],chain[0])
 for x in f:b.x(x)
def masked(b,p,m,up):
 for i,j,cols in mask_terms:
  for k in cols:b.ccx(p[i],m[j],up[k])
def kernel(b,f,d,p,work,mask):
 chain=work[:11];up=work[11:23];n=work[23:29];c=work[29:35];g=work[35:41];w=work[41:51]
 root(b,f,chain);r=chain[-1]
 masked(b,p,mask,up)
 J.frame(b,d,C.BASIS12,True);a,bb=d[:6],d[6:];u,v=up[:6],up[6:]
 left=a+u;right=bb+v
 compute_tensor(b,left,right,n+c)
 sa=[gf(1<<i,1<<i) for i in range(6)];sb=[gf(C.K6,x) for x in sa]
 J.arith(b,'square',a,n,1,6,0x43);J.arith(b,'square',bb,n,C.K6,6,0x43)
 for x,y in zip(c,g):b.ccx(r,x,y)
 phase16(b,n,g,w)
 for x,y in zip(c,g):b.del_and(r,x,y)
 mb=J.measure(b,n+c);repay_tensor(b,left,right,mb);J.linearphase(b,a,mb[:6],sa);J.linearphase(b,bb,mb[:6],sb);J.cclear(b,mb)
 J.frame(b,d,C.BASIS12);masked(b,p,mask,up);unroot(b,f,chain)
def add_const(b,w,x):
 for i in C.bits(x):b.x(w[i])
def make(count):
 b=km.CircuitBuilder();b.set_max_qubits(Q)
 D=[list(b.create_quantum_register(12,f'D{i}')) for i in range(35)]
 P=[list(b.create_quantum_register(12,f'P{i}')) for i in range(35)]
 M=[list(b.create_classical_register(12,f'E{i}')) for i in range(count)]
 work=list(b.alloc_qubits(51));f,d,p=D[0],D[1],P[0]
 rolls=[tuple(C.m(C.exp[j],1<<i) for i in range(12)) for j in range(35)]
 for k in range(count):
  lead=C.exp[35*k%4095]
  for j in range(3,35,2):J.xor(b,D[j],d)
  add_const(b,d,lead)
  J.xor(b,d,f)
  for j in range(2,35,2):J.xor(b,D[j],f)
  for j in range(1,35):J.xor(b,P[j],p)
  kernel(b,f,d,p,work,M[k])
  for j in range(1,35):J.xor(b,P[j],p)
  for j in range(2,35,2):J.xor(b,D[j],f)
  J.xor(b,d,f);add_const(b,d,lead)
  for j in range(3,35,2):J.xor(b,D[j],d)
  for j in range(1,35):
   J.frame(b,D[j],rolls[j]);J.frame(b,P[j],rolls[j])
  if k%512==0:print("SCAN",k,flush=True)
 if count%4095:
  for j in range(1,35):
   mat=tuple(C.m(C.exp[(-count*j)%4095],1<<i) for i in range(12))
   J.frame(b,D[j],mat);J.frame(b,P[j],mat)
 b.free(km.array(work));return b.finish_circuit()
def cases(count,num):
 rng=random.Random(2432026);rows=[];truth=[];labels=[]
 for w in range(36):
  for rep in range(num):
   inside=rng.sample(range(count),min(w,min(count,1+rep%8))) if w else []
   outside=rng.sample([j for j in range(4095) if j not in set(inside)],w-len(inside))
   loc=inside+outside;xs=[C.exp[j] for j in loc];es=[rng.randrange(1,4096) for _ in xs]
   D=[1];P=[]
   for x,e in zip(xs,es):
    P=C.add(C.mul(P,[x,1]),[C.m(C.m(e,x),a) for a in D]);D=C.mul(D,[x,1])
   D=[0]*(35-w)+D;P=[0]*(35-w)+P if P else []
   rows.append(D[:-1]+P+[0]*(35-len(P)));truth.append(dict(zip(loc,es)));labels.append(w)
 assert all(len(x)==70 for x in rows)
 # For arbitrary coordinates, check the literal canonical contract incl repeated roots / zero derivative.
 for rep in range(16):
  D=[rng.randrange(4096) for _ in range(35)]+[1];P=[rng.randrange(4096) for _ in range(35)]
  x=C.exp[rep%count];D[0]^=C.evalp(D,x)
  if rep%2==0:
   dd=C.xor_word(C.m(D[j],C.exp[(rep%count)*j%4095]) for j in range(1,36,2))
   D[1]^=C.m(dd,C.inv(x));D[0]^=dd
  e={}
  for k in range(count):
   z=C.exp[k]
   if C.evalp(D,z):continue
   dd=C.xor_word(C.m(D[j],C.exp[k*j%4095]) for j in range(1,36,2))
   e[k]=C.m(C.evalp(P,z),C.inv(dd)) if dd else 0
  rows.append(D[:-1]+P);truth.append(e);labels.append(-1)
 return np.asarray(rows,np.uint16),truth,labels
def test(c,count,num):
 rows,truth,labels=cases(count,num);q=km.array([km.q(i) for i in range(840)]);anc=km.array([km.q(i) for i in range(840,Q)]);mask=km.array([km.b(i) for i in range(count*12)])
 errs=[0]*4;shots=0;paid=0;raw=[0,0];rng=np.random.default_rng(2432026)
 def bits(a):return ((a[:,:,None]>>np.arange(12))&1).reshape(len(a),-1).T.astype(bool)
 for seed in (243,971):
  for st in range(0,len(rows),32):
   en=min(st+32,len(rows));n=en-st;M=rng.integers(0,4096,(n,count),dtype=np.uint16)
   for i in range(n):
    if (st+i+seed)%5==0:M[i]=0
    elif (st+i+seed)%5==1:
     M[i]=0
     if truth[st+i]:
      k=next(iter(truth[st+i]))
      if k<count:M[i,k]=1<<((st+i)%12)
   e=np.array([sum((int(M[i,k])&v).bit_count() for k,v in truth[st+i].items() if k<count)%2 for i in range(n)],bool)
   a=bits(rows[st:en]);m=bits(M);s=km.Simulator(batch_size=n,seed=seed+st,counting_operations=True,debug_print=False);s.use_same_registers_as(c);s.write_across_shots(q,a);s.write_across_shots(mask,m);s.do(c)
   E=[(s.read_across_shots(q)!=a).any(0), (s.read_across_shots(mask)!=m).any(0),s.read_across_shots(anc).any(0),s.read_phase_flipped_across_shots()!=e]
   errs=[u+int(v.sum()) for u,v in zip(errs,E)];shots+=n;paid+=int(s.operation_statistics().num_toffoli_like);raw[1]+=int(e.sum());raw[0]+=n-int(e.sum())
   print('TEST',seed,st,errs,flush=True)
 return dict(inputs=len(rows),weights_tested=list(range(36)),shots=shots,errors=errs,mean_paid=paid/shots,expected_phase_counts=raw)
def main():
 p=argparse.ArgumentParser();p.add_argument('--count',type=int,default=4095);p.add_argument('--cases',type=int,default=4);args=p.parse_args();exact_tensor()
 c=make(args.count);f=Path(f'general_{args.count}.kmb');c.to_file(str(f),format='kmb');del c
 c=km.Circuit.from_file(str(f));r=dict(scope='canonical D,P phase scan only, NOT syndrome-to-rational decoder',Q=c.num_qubits,ops=len(c),static_paid=int(c.operation_statistics().num_toffoli_like),sha256=hashlib.file_digest(f.open('rb'),'sha256').hexdigest(),scan_points=args.count,tensor_basis_checks=144,kickmix=version('kickmix'));print(json.dumps(r),flush=True);r.update(test(c,args.count,args.cases));print(json.dumps(r),flush=True);f.with_suffix('.json').write_text(json.dumps(r,indent=2)+'\n');assert not any(r['errors'])
if __name__=='__main__':main()
