"""Rank-15 GF64 multiplication, 39 scratch guard and full scan integration."""
import crt882 as C, g_guarded as G, narrow_crt as N, joint_phase as J
import kickmix as km
import argparse,json,hashlib
from pathlib import Path
m=lambda a,b:C.gf_mul(a,b,6,C.F6MOD)
p=lambda a,e:C.gf_pow(a,e,6,C.F6MOD)
w=next(x for x in range(2,64) if m(x,x)^x^1==0)
alpha=next(x for x in range(2,64) if x not in (0,1,w,w^1))
base=[1,w,alpha,m(alpha,w),m(alpha,alpha),m(m(alpha,alpha),w)]
coords={C.xor_word(base[j] for j in range(6) if v>>j&1):v for v in range(64)}
assert len(coords)==64
points=[0,1,w,w^1]
sub={0:0,1:1,w:2,w^1:3}
def ev(x,t):
 v=coords[x];cs=[C.xor_word((1,w)[i] for i in range(2) if v>>(2*j+i)&1) for j in range(3)]
 return cs[2] if t is None else cs[0]^m(cs[1],t)^m(cs[2],m(t,t))
def weight(t):
 x=1
 for z in points:
  if z!=t:x=m(x,m(alpha^z,p(t^z,62)))
 return x
weights=[weight(t) for t in points]
weights.append(p(alpha,4)^C.xor_word(m(p(t,4),u) for t,u in zip(points,weights)))
terms=[]
for t,u in zip(points+[None],weights):
 a,b=[sum(((sub[ev(1<<j,t)]>>i)&1)<<j for j in range(6)) for i in range(2)]
 terms.extend([(a,a,m(u,1^w)),(b,b,u),(a^b,a^b,m(u,w))])
assert len(terms)==15
for i in range(6):
 for j in range(6):
  v=C.xor_word(z for a,b,z in terms if a>>i&1 and b>>j&1)
  assert v==m(1<<i,1<<j),(i,j,v)
class Rank15(G.GCodec):
 def prod(self,a,b,z,n,mod):
  if n!=6:return super().prod(a,b,z,n,mod)
  assert mod==C.F6MOD and len(set(a+b+z))==18
  for p,q,v in terms:
   aa=list(C.bits(p));bb=list(C.bits(q));zz=list(C.bits(v))
   A=a[aa[0]];B=b[bb[0]];Z=z[zz[0]]
   for j in aa[1:]:self.cx(a[j],A)
   for j in bb[1:]:self.cx(b[j],B)
   for j in zz[1:]:self.cx(Z,z[j])
   self.ccx(A,B,Z)
   for j in reversed(zz[1:]):self.cx(Z,z[j])
   for j in reversed(bb[1:]):self.cx(b[j],B)
   for j in reversed(aa[1:]):self.cx(a[j],A)
def guard39(b,reg):
 work=reg[841:];flags=work[:17];scratch=work[17:]
 assert len(scratch)==22
 def one(group,f,s):
  for q in group:b.x(q)
  G.andtoggle(b,group,f,s)
  for q in group:b.x(q)
 for j in range(17):one(reg[432+24*j:432+24*j+24],flags[j],scratch)
 lead=scratch[0];one(reg[:12],lead,scratch[1:]);b.x(lead)
 G.andtoggle(b,flags+[lead],reg[840],scratch[1:])
 b.x(lead);one(reg[:12],lead,scratch[1:])
 for j in reversed(range(17)):one(reg[432+24*j:432+24*j+24],flags[j],scratch)
def main():
 pa=argparse.ArgumentParser();pa.add_argument('--count',type=int,default=32);pa.add_argument('--cases',type=int,default=32);args=pa.parse_args()
 # Keep original arith compiler class for non-rank15 stages, substitute rank15 globally.
 G.GCodec=Rank15;C.Compact=Rank15;G.Q=880;J.Q=880;G.guard=guard39
 print('TENSOR',json.dumps(dict(terms=terms,basis_checks=36)),flush=True)
 c=J.build(args.count);path=Path(f'joint_rank15_{args.count}.kmb');c.to_file(str(path),format='kmb');del c
 c=km.Circuit.from_file(str(path));r=dict(scope='guarded G allpole oracle, identity complement, not full DQI',scan_points=args.count,Q=c.num_qubits,ops=len(c),static_paid=int(c.operation_statistics().num_toffoli_like),sha256=hashlib.file_digest(path.open('rb'),'sha256').hexdigest(),gf64_rank=15,tensor_basis_checks=36)
 assert set(c.register_data)=={f'S{i}' for i in range(70)}|{f'E{i}' for i in range(args.count)}
 assert all(len(v)==12 for v in c.register_data.values())
 r['public_abi_registers']=len(c.register_data)
 print(json.dumps(r),flush=True);r.update(J.test(c,args.count,args.cases));print(json.dumps(r),flush=True);path.with_suffix('.json').write_text(json.dumps(r,indent=2)+'\n');assert not any(r['errors'])
if __name__=='__main__':main()
