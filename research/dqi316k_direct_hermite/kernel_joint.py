"""Joint nested-norm phase on the #261 direct core.
35 clean workspace: 11 root conjunctions, 12 outer dual norm/cross,
12 reused masked numerator / inner dual norm/cross / Guard4.
No input-dependent host branch. Only measured scratch is HMR-erased.
"""
import crt882 as C, joint_phase as J, general_scan as G
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
 # Tr6(c/n)=Tr3((c0*n1+c1*n0)/Norm(n)), with inverse(0)=0.
 J.frame(b,n,C.BASIS6,True);J.frame(b,c,C.BASIS6,True)
 u,v=n[:3],n[3:];s,t=c[:3],c[3:];nn,cc,gw=up[:3],up[3:6],up[6:12]
 J.norm_compute(b,u,v,nn,3,C.K3,C.F3MOD)
 J.arith(b,'prod',u,t,cc,3,C.F3MOD);J.arith(b,'prod',v,s,cc,3,C.F3MOD)
 h=guard(b,nn,r,gw)
 for i in range(3):
  for j in range(3):
   if TR[i][j]:b.cz(cc[i],h[j])
 guard(b,nn,r,gw,True)
 mb=J.measure(b,cc);J.prodphase(b,u,t,mb,3,C.F3MOD);J.prodphase(b,v,s,mb,3,C.F3MOD);J.cclear(b,mb)
 J.norm_clear(b,u,v,nn,3,C.K3,C.F3MOD)
 J.frame(b,c,C.BASIS6);J.frame(b,n,C.BASIS6)
 G.masked(b,p,mask,up)
 mb=J.measure(b,n+c);G.repay_tensor(b,left,right,mb);J.linearphase(b,a,mb[:6],sa);J.linearphase(b,bb,mb[:6],sb);J.cclear(b,mb)
 J.frame(b,d,C.BASIS12);G.masked(b,p,mask,up);G.unroot(b,f,chain)
truth()
