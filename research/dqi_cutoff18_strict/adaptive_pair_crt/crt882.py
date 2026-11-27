import random,struct,hashlib,json,collections
from functools import lru_cache
import numpy as np,kickmix as km
MOD=0x1053
def gf_mul(a,b,n,mod):
 t=0
 while b:
  if b&1:t^=a
  b>>=1;a<<=1
  if a&(1<<n):a^=mod
 return t
def gf_pow(a,e,n,mod):
 r=1
 while e:
  if e&1:r=gf_mul(r,a,n,mod)
  a=gf_mul(a,a,n,mod);e>>=1
 return r
exp=[1]
for _ in range(4094):exp.append(gf_mul(exp[-1],2,12,MOD))
assert len(set(exp))==4095
log=[-1]*4096
for i,a in enumerate(exp):log[a]=i
exp*=2
def m(a,b):return exp[log[a]+log[b]] if a and b else 0
def inv(a):assert a;return exp[4095-log[a]]
def trim(a):
 while a and not a[-1]:a.pop()
 return a
def add(a,b):
 c=[0]*max(len(a),len(b))
 for i,v in enumerate(a):c[i]^=v
 for i,v in enumerate(b):c[i]^=v
 return trim(c)
def mul(a,b):
 if not a or not b:return []
 c=[0]*(len(a)+len(b)-1)
 for i,v in enumerate(a):
  for j,w in enumerate(b):c[i+j]^=m(v,w)
 return trim(c)
def div(a,b):
 assert b;a=a[:];q=[0]*max(0,len(a)-len(b)+1);bi=inv(b[-1])
 while len(a)>=len(b):
  d=len(a)-len(b);v=m(a[-1],bi);q[d]=v
  for j,w in enumerate(b):a[d+j]^=m(v,w)
  trim(a)
 return trim(q),a
def evalp(a,x):
 v=0
 for c in a[::-1]:v=m(v,x)^c
 return v
def inversemod(a,b):
 r,s=b[:],a[:];u,v=[],[1]
 while s:
  q,t=div(r,s);r,s=s,t;u,v=v,add(u,mul(q,v))
 assert len(r)==1
 return div([m(c,inv(r[0])) for c in u],b)[1]
ks=[3134,3169,3257,3302,3384,3431,3519,3552,3592,3633,3671,3727,3792,3854,3921,3977,4054]
G=[1]
for k in ks:G=mul(G,[k,1,1])
K=2048
ORDER=[3169,3257,3134,3302,3727,3671,3792,3592]+[k for k in ks if k not in [3169,3257,3134,3302,3727,3671,3792,3592]]+[K]
M=mul(G,[K,1,1]);U70=mul(G,M)
def moment(xs,es):
 S=[0]*70
 for x,e in zip(xs,es):
  v=m(x,e)
  for i in range(70):S[i]^=v;v=m(v,x)
 return S
def bits(a):
 while a:
  l=a&-a;yield l.bit_length()-1;a^=l
F6MOD=0x43
basis6root=next(x for x in range(2,4096) if m(m(m(x,x),m(x,x)),m(x,x))^x^1==0)
basis6=[1]
for _ in range(5):basis6.append(m(basis6[-1],basis6root))
sub6=[0]*64
for a in range(64):
 for i,x in enumerate(basis6):
  if a>>i&1:sub6[a]^=x
rev6={x:i for i,x in enumerate(sub6)}
beta=next(x for x in range(4096) if x and exp[(log[x]*64)%4095]^x==1)
K6=rev6[m(beta,beta)^beta];BASIS12=basis6+[m(beta,x) for x in basis6]
F3MOD=0xb
m6=lambda a,b:gf_mul(a,b,6,F6MOD)
p6=lambda a,e:gf_pow(a,e,6,F6MOD)
b3=next(x for x in range(2,64) if p6(x,3)^x^1==0)
base3=[1,b3,m6(b3,b3)];sub3=[0]*8
for x in range(8):
 for i,v in enumerate(base3):
  if x>>i&1:sub3[x]^=v
r3={v:x for x,v in enumerate(sub3)}
beta3=next(x for x in range(64) if p6(x,8)^x==1)
K3=r3[m6(beta3,beta3)^beta3];BASIS6=base3+[m6(beta3,x) for x in base3]
@lru_cache(None)
def lin_ops(cols):
 n=len(cols);r=[0]*n
 for j,c in enumerate(cols):
  for i in bits(c):r[i]|=1<<j
 ops=[]
 for j in range(n):
  k=next(k for k in range(j,n) if r[k]>>j&1)
  if k!=j:r[k],r[j]=r[j],r[k];ops.extend(((j,k),(k,j),(j,k)))
  for i in range(n):
   if i!=j and r[i]>>j&1:r[i]^=r[j];ops.append((j,i))
 assert r==[1<<i for i in range(n)]
 return tuple(reversed(ops))
@lru_cache(None)
def block_lin(cols,k):
 n=len(cols);r=[0]*n
 for j,c in enumerate(cols):
  for i in bits(c):r[i]|=1<<j
 ops=[]
 def xor(i,j):r[j]^=r[i];ops.append((i,j))
 def swap(i,j):
  if i!=j:xor(i,j);xor(j,i);xor(i,j)
 for s in range(0,n,k):
  e=min(n,s+k);mask=(1<<(e-s))-1;seen={}
  for i in range(s,n):
   v=(r[i]>>s)&mask
   if v:
    if v in seen:xor(seen[v],i)
    else:seen[v]=i
  for j in range(s,e):
   p=next(i for i in range(j,n) if r[i]>>j&1);swap(p,j)
   for i in range(j+1,n):
    if r[i]>>j&1:xor(j,i)
 for e in range(n,0,-k):
  s=max(0,e-k);mask=(1<<(e-s))-1;seen={}
  for i in range(e-1,-1,-1):
   v=(r[i]>>s)&mask
   if v:
    if v in seen:xor(seen[v],i)
    else:seen[v]=i
  for j in range(e-1,s-1,-1):
   p=next(i for i in range(j,-1,-1) if r[i]>>j&1);swap(p,j)
   for i in range(j):
    if r[i]>>j&1:xor(j,i)
 assert r==[1<<i for i in range(n)]
 return tuple(reversed(ops))
def reduce_bin(x,n,mod):
 while x.bit_length()>n:x^=mod<<(x.bit_length()-n-1)
 return x
@lru_cache(None)
def small_terms(n):
 if n==3:return ((1,1,1^2^4),(2,2,2^4^8),(4,4,4^8^16),(3,3,2),(5,5,4),(6,6,8))
 assert n==6
 out=[]
 for a,b,c in small_terms(3):out.extend(((a,b,c^(c<<3)),(a<<3,b<<3,(c<<3)^(c<<6)),(a^(a<<3),b^(b<<3),c<<3)))
 return tuple(out)
CODES=[261,1041,1624,1752,1880,2200,2264,103428,453,1233,1760,1824,1888,1952,2144,2272,136391,707,709,1487,1489,1634,1698,1762,1890,144843,711,1491,1566,1630,1886,2014,2142,2206,128459,261,264,1041,1044,1626,1818,1946,111620,512,518,1292,1298,1563,1947,2075,2267,115976,516,1296,1691,115976,8,9,788,789,1564,1628,2076,2204,119552,7,10,787,790,1825,2081,2273,140032,4,784,1761,140032,4,8,784,788,1697,140032,389,393,1169,1173,1626,2010,2202,2266,111750,259,262,267,1039,1042,1047,1952,136196,263,1043,2206,128004,267,1047,2208,136196,580,584,1360,1364,1570,1826,2274,144713,642,646,1422,1426,1568,1632,1760,2144,136586,449,451,454,1229,1231,1234,1561,1881,2265,107719,513,514,517,1293,1294,1297,2201,107784,456,1236,1630,1694,1758,2014,2270,128199,457,1237,2206,128199,584,1364,1945,107849,259,261,262,263,264,1039,1041,1042,1043,1044,1763,148484,450,452,458,459,1230,1232,1238,1239,1564,1692,120007,391,1171,1564,119942,579,583,584,1295,1299,1301,2272,136457,649,1428,1689,1753,1881,107914,266,1046,2265,107524,265,266,1296,1302,2073,107780,138,1422,2008,2072,2200,103810,323,327,1231,1233,1822,1886,2078,2206,128197,256,259,262,1292,1295,1298,1571,1891,2019,148740,1,2,7,8,9,972,973,981,982,1566,127936,128,982,1763,1955,2019,2147,2211,148418,5,979,982,2264,103360,322,982,1944,103365,512,513,1166,1168,1169,1172,1825,2081,2209,140424,516,1298,1692,1884,1948,2268,120072,67,71,74,75,909,913,915,918,919,2140,119681,68,1294,1298,1691,1883,2011,2075,115969,513,914,2139,115592,2,4,6,10,11,1041,1042,1043,1047,1688,1944,2008,2072,2200,2264,103424,128,256,384,448,129,66,129,1,321,513,577,641,2,258,514,578,3,67,131,259,323,515,579,707,132,324,388,452,516,580,453,327,453,5,261,645,454,391,454,6,134,262,326,518,582,647,458,647,7,135,711,8,9,73,265,457,521,649,713,10,74,266,458,586,714,75,139,651,1036,1164,1228,909,973,1037,1229,1357,1421,1038,1230,1294,1358,1422,1167,978,1167,911,1231,1487,1168,1296,1360,785,1041,1425,1234,1171,1234,914,978,1042,1426,1490,1491,1239,1491,787,915,916,1428,981,1237,1301,918,982,1046,1238,1494,791,983,1303,1367,1561,1624,1561,1562,1563,1566,1568,1627,1632,1634,1635,1692,1818,1692,1688,1689,1694,1698,1699,1753,1754,1758,1760,1824,2076,1824,1818,1827,1880,1881,1882,1884,1888,1891,1944,1947,1948,1953,1955,2008,2009,2010,2017,2018,2083,2272,2083,2073,2074,2075,2076,2078,2137,2138,2142,2144,2147,2211,2274,2211,2200,2202,2203,2204,2206,2208,2209,2265,2266,2268]
GATES=[(1,c%64,(c//64)%64) if c//4096==0 else (2,c%64,(c//64)%64,c//4096-1) for c in CODES]
assert len(GATES)==510 and sum(g[0]==2 for g in GATES)==42
class Compact:
 def __init__(self):self.ops=[]
 def x(self,t):self.ops.append((0,t))
 def cx(self,a,t):assert a!=t;self.ops.append((1,a,t))
 def ccx(self,a,b,t):assert len({a,b,t})==3;self.ops.append((2,a,b,t))
 def frame(self,reg,cols,inverse=False):
  ops=lin_ops(tuple(cols))
  for a,b in (reversed(ops) if inverse else ops):self.cx(reg[a],reg[b])
 def lin_xor(self,a,b,cols):
  assert set(a).isdisjoint(b)
  for i,v in enumerate(cols):
   for j in bits(v):self.cx(a[i],b[j])
 def constmul(self,a,b,k,n,mod):self.lin_xor(a,b,[gf_mul(k,1<<i,n,mod) for i in range(n)])
 def square(self,a,b,k,n,mod):self.lin_xor(a,b,[gf_mul(k,gf_mul(1<<i,1<<i,n,mod),n,mod) for i in range(n)])
 def prod(self,a,b,z,n,modulus):
  if n==12:
   assert modulus==MOD and len(set(a+b+z))==36
   q=a+b+z
   for g,*args in GATES:getattr(self,('x','cx','ccx')[g])(*(q[i] for i in args))
   return
  assert len(set(a+b+z))==3*n
  for p,q,v in small_terms(n):
   v=reduce_bin(v,n,modulus)
   if not v:continue
   aa=list(bits(p));bb=list(bits(q));zz=list(bits(v));A=a[aa[0]];B=b[bb[0]];Z=z[zz[0]]
   for j in aa[1:]:self.cx(a[j],A)
   for j in bb[1:]:self.cx(b[j],B)
   for j in zz[1:]:self.cx(Z,z[j])
   self.ccx(A,B,Z)
   for j in reversed(zz[1:]):self.cx(Z,z[j])
   for j in reversed(bb[1:]):self.cx(b[j],B)
   for j in reversed(aa[1:]):self.cx(a[j],A)
 def inv3(self,a,b):
  vals=[gf_pow(x,6,3,F3MOD) for x in range(8)]
  for k in range(3):
   for j in range(8):
    if j>>k&1:vals[j]^=vals[j^(1<<k)]
  for mask,v in enumerate(vals):
   if not v:continue
   zz=list(bits(v));Z=b[zz[0]]
   for j in zz[1:]:self.cx(Z,b[j])
   c=[a[j] for j in bits(mask)]
   if len(c)==0:self.x(Z)
   elif len(c)==1:self.cx(c[0],Z)
   else:self.ccx(*c,Z)
   for j in reversed(zz[1:]):self.cx(Z,b[j])
 def inv6(self,x,y,work):
  n,h=work[:3],work[3:6];a,b=x[:3],x[3:];v,w=y[:3],y[3:]
  self.frame(x,BASIS6,True);self.frame(y,BASIS6,True)
  start=len(self.ops);self.square(a,n,1,3,F3MOD);self.square(b,n,K3,3,F3MOD);self.prod(a,b,n,3,F3MOD);norm=self.ops[start:].copy()
  start=len(self.ops);self.inv3(n,h);inverse=self.ops[start:].copy()
  for i,j in zip(b,a):self.cx(i,j)
  self.prod(a,h,v,3,F3MOD)
  for i,j in zip(b,a):self.cx(i,j)
  self.prod(b,h,w,3,F3MOD)
  self.ops.extend(reversed(inverse));self.ops.extend(reversed(norm));self.frame(y,BASIS6);self.frame(x,BASIS6)
 def inv12(self,x,y,work):
  n,h=work[:6],work[6:12];a,b=x[:6],x[6:];v,w=y[:6],y[6:]
  self.frame(x,BASIS12,True);self.frame(y,BASIS12,True)
  start=len(self.ops);self.square(a,n,1,6,F6MOD);self.square(b,n,K6,6,F6MOD);self.prod(a,b,n,6,F6MOD);norm=self.ops[start:].copy()
  start=len(self.ops);self.inv6(n,h,work[12:18]);inverse=self.ops[start:].copy()
  for i,j in zip(b,a):self.cx(i,j)
  self.prod(a,h,v,6,F6MOD)
  for i,j in zip(b,a):self.cx(i,j)
  self.prod(b,h,w,6,F6MOD)
  self.ops.extend(reversed(inverse));self.ops.extend(reversed(norm));self.frame(y,BASIS12);self.frame(x,BASIS12)
 def inplace_inv24(self,x,work,k):
  a,b=x[:12],x[12:];n,h,tmp=work[:12],work[12:24],work[24:36];sub=work[24:42]
  def norm(target):
   self.square(a,target,1,12,MOD);self.square(b,target,k,12,MOD);self.prod(a,b,target,12,MOD)
  norm(n);self.inv12(n,h,sub)
  for i,j in zip(b,a):self.cx(i,j)
  for r in (a,b):
   self.prod(r,h,tmp,12,MOD)
   for i,j in zip(r,tmp):self.cx(i,j);self.cx(j,i);self.cx(i,j)
   self.prod(r,n,tmp,12,MOD)
  self.inv12(h,n,sub);norm(h)
def word(j):return list(range(12*j,12*j+12))
def emit():
 t=Compact();work=list(range(840,882));reg=list(range(432))
 for j in range(69,-1,-1):
  for h in range(1,min(j,36)+1):
   if M[36-h]:t.constmul(word(j-h),word(j),M[36-h],12,MOD)
 cols=[]
 for j in range(36):
  for b in range(12):
   c=0
   for i,k in enumerate(ORDER):
    v=div([0]*(35-j)+[1<<b],[k,1,1])[1]
    c|=sum(x<<(12*h) for h,x in enumerate(v))<<(24*i)
   cols.append(c)
 cols=tuple(cols);baseline=lin_ops(cols);cands={k:block_lin(cols,k) for k in range(3,10)}
 best=min(cands,key=lambda k:len(cands[k]));L=cands[best]
 if len(L)>len(baseline):L=baseline
 for a,b in L:t.cx(reg[a],reg[b])
 for i,k in enumerate(ORDER):t.inplace_inv24(reg[24*i:24*i+24],work,k)
 for a,b in reversed(L):t.cx(reg[a],reg[b])
 return t
def xor_word(xs):
 a=0
 for v in xs:a^=v
 return a
def ref(s):
 W=[xor_word(m(M[36-h],s[i-h]) for h in range(min(i,36)+1)) for i in range(70)]
 B=trim(list(reversed(W[:36])));T=[]
 for k in ORDER:
  g=[k,1,1];r=div(B,g)[1];ri=inversemod(r,g) if r else []
  q,rem=div(M,g);assert not rem
  T=add(T,mul(q,div(mul(ri,inversemod(div(q,g)[1],g)),g)[1]))
 T=div(T,M)[1];return list(reversed(T+[0]*(36-len(T))))+W[36:]
def cases():
 rng=random.Random(700229);rows=[];expected=[]
 for _ in range(128):
  c=rng.randrange(1,4096);xs=sorted(rng.sample(range(1,4096),35));D=[1]
  for x in xs:D=mul(D,[x,1])
  dp=[D[i] if i%2 else 0 for i in range(1,36)]
  es=[m(c,inv(m(m(x,evalp(M,x)),evalp(dp,x)))) for x in xs]
  # N=cG for U70, magnitudes given by M.
  rows.append(moment(xs,es));expected.append((D,c))
 for w in range(36):
  for _ in range(2):
   xs=rng.sample(range(1,4096),w);rows.append(moment(xs,[rng.randrange(1,4096) for x in xs]))
 for _ in range(128):rows.append([rng.randrange(4096) for _ in range(70)])
 for k in ORDER:
  B=mul([k,1,1],[rng.randrange(4096) for _ in range(34)])
  W=list(reversed(B+[0]*(36-len(B))))+[rng.randrange(4096) for _ in range(34)];S=[]
  for i,v in enumerate(W):
   for h in range(1,min(i,36)+1):v^=m(M[36-h],S[i-h])
   S.append(v)
  rows.append(S)
 return rows,expected
def run():
 t=emit();sha=hashlib.sha256(b''.join(struct.pack('<4H',*(o+(0,)*(4-len(o)))) for o in t.ops)).hexdigest()
 print('TAPE',len(t.ops),collections.Counter(o[0] for o in t.ops),sha,flush=True)
 assert sha=='e0c8844a3b260d7215f40457137fa978af821e71d0098ab4ccdafa1f9be3d927'
 b=km.CircuitBuilder();b.set_max_qubits(882);reg=list(b.create_quantum_register(840,'data'))+list(b.alloc_qubits(42))
 for g,*a in t.ops:getattr(b,('x','cx','ccx')[g])(*(reg[j] for j in a))
 b.free(km.array(reg[840:]));c=b.finish_circuit();c.to_file('/tmp/crt882.kmb',format='kmb');c=km.Circuit.from_file('/tmp/crt882.kmb')
 rows,loc=cases();out=[ref(s) for s in rows]
 for y,(D,co) in zip(out,loc):assert y[:36]==list(reversed([m(x,inv(co)) for x in D])) and not any(y[36:])
 q=km.array([km.q(i) for i in range(840)]);a=km.array([km.q(i) for i in range(840,882)])
 errors=[0]*3;count=0
 for st in range(0,len(rows),32):
  x=np.asarray(rows[st:st+32],np.uint16);y=np.asarray(out[st:st+32],np.uint16);xb=((x[:,:,None]>>np.arange(12))&1).reshape(len(x),840).T.astype(bool);yb=((y[:,:,None]>>np.arange(12))&1).reshape(len(x),840).T.astype(bool)
  sim=km.Simulator(batch_size=len(x),seed=229+st,debug_print=False);sim.use_same_registers_as(c);sim.write_across_shots(q,xb);sim.do(c)
  e=[(sim.read_across_shots(q)!=yb).any(0),sim.read_across_shots(a).any(0),sim.read_phase_flipped_across_shots()]
  errors=[u+int(np.asarray(v).sum()) for u,v in zip(errors,e)];count+=len(x)
 print(json.dumps(dict(Q=c.num_qubits,ops=len(c),paid=c.operation_statistics().num_toffoli_like,shots=count,errors=errors,raw_tape_sha=sha,kmb_sha=hashlib.file_digest(open('/tmp/crt882.kmb','rb'),'sha256').hexdigest())),flush=True)
 assert not any(errors)
if __name__=='__main__':run()

