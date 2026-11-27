"""Joint four-product root-gated GF8 inverse for #237.
Only a chart-specific scan, not the full DQI decoder."""
import argparse,hashlib,json
from pathlib import Path
import kickmix as km
import crt882 as C, joint_rank15 as R, joint_phase as J, g_guarded as G

# Linear forms over [1,a,b,c,r,g1,g2,g3,g4].
# Explicit forms: (1+c)(1+b), (1+r)(1+a+g1),
# (c+r)(a+b+g1+g2), (b+r)(1+a+c+r+g1+g2).
DAG=((1|8,1|4),(1|16,1|2|32),(8|16,2|4|32|64),(4|16,1|2|8|16|32|64))
OUT=(1|2|32|64,2|4|8|16|64|256,2|4|16|64|128)

def parity(b,mask,wire,dst):
 if mask&1:b.x(dst)
 for i in range(1,9):
  if mask>>i&1:b.cx(wire[i-1],dst)

def guard4(b,nn,r,work):
 g=list(work[:4]); scratch=list(work[4:6])
 w=list(nn)+[r]+g
 for (a,c),z in zip(DAG,g):
  parity(b,a,w,scratch[0]);parity(b,c,w,scratch[1])
  b.ccx(scratch[0],scratch[1],z)
  parity(b,c,w,scratch[1]);parity(b,a,w,scratch[0])
 # Reversible affine output frame, keeping g2 as fourth coordinate.
 for t,mask in [(g[0],1|2|64),(g[3],2|4|8|16|64),(g[2],2|4|16|64)]:
  parity(b,mask,w,t)
 return [g[0],g[3],g[2]]

def unguard4(b,nn,r,work):
 g=list(work[:4]);scratch=list(work[4:6]);w=list(nn)+[r]+g
 for t,mask in [(g[2],2|4|16|64),(g[3],2|4|8|16|64),(g[0],1|2|64)]:
  parity(b,mask,w,t)
 for (a,c),z in reversed(list(zip(DAG,g))):
  parity(b,a,w,scratch[0]);parity(b,c,w,scratch[1])
  b.del_and(scratch[0],scratch[1],z)
  parity(b,c,w,scratch[1]);parity(b,a,w,scratch[0])

def check_truth():
 for x in range(8):
  for r in range(2):
   vals=[1]+[(x>>i)&1 for i in range(3)]+[r]
   def v(m):return sum(z for i,z in enumerate(vals) if m>>i&1)%2
   for a,b in DAG:vals.append(v(a)&v(b))
   y=sum(v(m)<<i for i,m in enumerate(OUT))
   assert y==(C.gf_pow(x,6,3,C.F3MOD) if r else 0),(x,r,y)

def kernel(b,f,d,tag,work,mask,x):
 chain=work[:12];n=work[12:18];nn=work[18:21];gw=work[21:27];y=work[27:33]
 cs=J.root_compute(b,f,tag,chain);r=chain[-1]
 J.frame(b,d,C.BASIS12,True);a,c=d[:6],d[6:]
 J.norm_compute(b,a,c,n,6,C.K6,C.F6MOD)
 J.frame(b,n,C.BASIS6,True);u,v=n[:3],n[3:]
 J.norm_compute(b,u,v,nn,3,C.K3,C.F3MOD)
 hg=guard4(b,nn,r,gw)
 J.xor(b,v,u);J.arith(b,'prod',u,hg,y[:3],3,C.F3MOD);J.xor(b,v,u)
 J.arith(b,'prod',v,hg,y[3:],3,C.F3MOD)
 J.frame(b,y,C.BASIS6)
 dual=list(b.alloc_bits(12))
 for i,col in enumerate(J.mask_cols(x)):
  b.bit_store(dual[i],False)
  for j in C.bits(col):b.cx(mask[j],dual[i])
 J.xor(b,c,a);J.prodphase(b,a,y,dual[:6],6,C.F6MOD);J.xor(b,c,a)
 J.prodphase(b,c,y,dual[6:],6,C.F6MOD);J.cclear(b,dual)
 J.frame(b,y,C.BASIS6,True)
 J.xor(b,v,u);J.product_clear(b,u,hg,y[:3],3,C.F3MOD);J.xor(b,v,u)
 J.product_clear(b,v,hg,y[3:],3,C.F3MOD)
 unguard4(b,nn,r,gw)
 J.norm_clear(b,u,v,nn,3,C.K3,C.F3MOD)
 J.frame(b,n,C.BASIS6)
 J.norm_clear(b,a,c,n,6,C.K6,C.F6MOD)
 J.frame(b,d,C.BASIS12);J.root_clear(b,cs,chain)

def main():
 p=argparse.ArgumentParser();p.add_argument('--count',type=int,default=4095);p.add_argument('--cases',type=int,default=96);a=p.parse_args();check_truth()
 G.GCodec=R.Rank15;C.Compact=R.Rank15;G.Q=880;J.Q=880;G.guard=R.guard39;J.kernel=kernel
 c=J.build(a.count);f=Path(f'guard4_{a.count}.kmb');c.to_file(str(f),format='kmb');del c;c=km.Circuit.from_file(str(f))
 result=dict(scope='allpole chart oracle, identity complement; not complete DQI',Q=c.num_qubits,ops=len(c),static_paid=int(c.operation_statistics().num_toffoli_like),hash=hashlib.file_digest(f.open('rb'),'sha256').hexdigest(),truth_table=16)
 assert c.num_qubits==880
 print(json.dumps(result),flush=True);result.update(J.test(c,a.count,a.cases));assert not any(result['errors']);print(json.dumps(result),flush=True);f.with_suffix('.json').write_text(json.dumps(result,indent=2))
if __name__=='__main__':main()
