"""Joint inner GF8 dual-number rank17 on #261 direct donor splice."""
import crt882 as C, joint_phase as J, general_scan as G
TERMS=((2,2,42),(6,6,23),(7,7,33),(40,40,14),(41,41,11),(42,42,3),(43,43,46),(44,44,61),(47,47,21),(49,49,24),(51,51,8),(52,52,40),(53,53,56),(58,58,56),(59,59,48),(61,61,40),(63,63,32))
def truth_tensor():
 for a in range(64):
  for b in range(64):
   x,y=a&7,a>>3;z,t=b&7,b>>3
   m=lambda i,j:C.gf_mul(i,j,3,C.F3MOD)
   goal=m(x,z)|((m(x,t)^m(y,z))<<3);v=0
   for l,r,w in TERMS:
    if (l&a).bit_count()%2 and (r&b).bit_count()%2:v^=w
   assert v==goal,(a,b,v,goal)
truth_tensor()
DAG=((1|8,1|4),(1|16,1|2|32),(8|16,2|4|32|64),(4|16,1|2|8|16|32|64))
OUT=(1|2|32|64,2|4|8|16|64|256,2|4|16|64|128)
def truth():
 for x in range(8):
  for r in range(2):
   vals=[1]+[(x>>i)&1 for i in range(3)]+[r]
   def v(m):return sum(z for i,z in enumerate(vals) if m>>i&1)%2
   for a,b in DAG:vals.append(v(a)&v(b))
   assert sum(v(m)<<i for i,m in enumerate(OUT))==(C.gf_pow(x,6,3,C.F3MOD) if r else 0)
def parity(b,mask,w,z):
 if mask&1:b.x(z)
 for i in range(1,9):
  if mask>>i&1:b.cx(w[i-1],z)
def guard(b,nn,r,work,reverse=False):
 g=list(work[:4]);t=list(work[4:6]);w=list(nn)+[r]+g
 frame=((g[0],1|2|64),(g[3],2|4|8|16|64),(g[2],2|4|16|64))
 if reverse:
  for z,m in reversed(frame):parity(b,m,w,z)
 for (a,c),z in (reversed(list(zip(DAG,g))) if reverse else zip(DAG,g)):
  parity(b,a,w,t[0]);parity(b,c,w,t[1])
  if reverse:b.del_and(t[0],t[1],z)
  else:b.ccx(t[0],t[1],z)
  parity(b,c,w,t[1]);parity(b,a,w,t[0])
 if not reverse:
  for z,m in frame:parity(b,m,w,z)
 return [g[0],g[3],g[2]]
def trace3(a):
 z=0
 for _ in range(3):z^=a;a=C.gf_mul(a,a,3,C.F3MOD)
 assert z in (0,1)
 return z
TR=[[trace3(C.gf_mul(1<<i,1<<j,3,C.F3MOD)) for j in range(3)] for i in range(3)]
def compute(b,left,right,out):
 for l,r,z in TERMS:
  a=G.parity_pivot(b,left,l);c=G.parity_pivot(b,right,r)
  t=[out[i] for i in C.bits(z)]
  for x in t[1:]:b.cx(t[0],x)
  b.ccx(a[0],c[0],t[0])
  for x in reversed(t[1:]):b.cx(t[0],x)
  G.unpivot(b,c);G.unpivot(b,a)
def repay(b,left,right,mb):
 tmp=b.alloc_bits(1)[0]
 for l,r,z in TERMS:
  a=G.parity_pivot(b,left,l);c=G.parity_pivot(b,right,r)
  b.bit_store(tmp,False)
  for i in C.bits(z):b.cx(mb[i],tmp)
  b.ccz(a[0],c[0],tmp)
  G.unpivot(b,c);G.unpivot(b,a)
 b.bit_store(tmp,False);b.free(tmp)
def kernel(b,f,d,p,work,mask):
 assert len(work)==35
 chain=work[:11];n=work[11:17];c=work[17:23];up=work[23:35]
 G.root(b,f,chain);r=chain[-1]
 G.masked(b,p,mask,up)
 J.frame(b,d,C.BASIS12,True);a,bb=d[:6],d[6:];left=a+up[:6];right=bb+up[6:]
 G.compute_tensor(b,left,right,n+c)
 sa=[G.gf(1<<i,1<<i) for i in range(6)];sb=[G.gf(C.K6,x) for x in sa]
 J.arith(b,'square',a,n,1,6,0x43);J.arith(b,'square',bb,n,C.K6,6,0x43)
 G.masked(b,p,mask,up)
 J.frame(b,n,C.BASIS6,True);J.frame(b,c,C.BASIS6,True)
 u,v=n[:3],n[3:];s,t=c[:3],c[3:];nn,cc,gw=up[:3],up[3:6],up[6:12]
 compute(b,u+s,v+t,nn+cc)
 J.arith(b,'square',u,nn,1,3,C.F3MOD);J.arith(b,'square',v,nn,C.K3,3,C.F3MOD)
 h=guard(b,nn,r,gw)
 for i in range(3):
  for j in range(3):
   if TR[i][j]:b.cz(cc[i],h[j])
 guard(b,nn,r,gw,True)
 mb=J.measure(b,nn+cc);repay(b,u+s,v+t,mb)
 sc=[C.gf_mul(1<<i,1<<i,3,C.F3MOD) for i in range(3)]
 J.linearphase(b,u,mb[:3],sc);J.linearphase(b,v,mb[:3],[C.gf_mul(C.K3,x,3,C.F3MOD) for x in sc]);J.cclear(b,mb)
 J.frame(b,c,C.BASIS6);J.frame(b,n,C.BASIS6)
 G.masked(b,p,mask,up)
 mb=J.measure(b,n+c);G.repay_tensor(b,left,right,mb);J.linearphase(b,a,mb[:6],sa);J.linearphase(b,bb,mb[:6],sb);J.cclear(b,mb)
 J.frame(b,d,C.BASIS12);G.masked(b,p,mask,up);G.unroot(b,f,chain)
truth()

