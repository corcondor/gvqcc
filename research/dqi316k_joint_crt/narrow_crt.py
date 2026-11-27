"""Joint narrow CRT: HMR mask pooling in polynomial basis, inplace GF8 inverse."""
import joint_crt as J
import crt882 as C
import kickmix as km
import numpy as np
from pathlib import Path
import hashlib,json
class Narrow(J.Joint):
 def inv3_inplace(self,x):
  for v in range(1,8):
   u=C.gf_pow(v,6,3,C.F3MOD)
   if u<=v:continue
   d=u^v;p=(d&-d).bit_length()-1;rest=[j for j in range(3) if j!=p and d>>j&1]
   for j in rest:self.cx(x[p],x[j])
   a=v^(d^(1<<p) if v>>p&1 else 0)
   ctrl=[j for j in range(3) if j!=p];neg=[j for j in ctrl if not a>>j&1]
   for j in neg:self.x(x[j])
   self.ccx(x[ctrl[0]],x[ctrl[1]],x[p])
   for j in neg:self.x(x[j])
   for j in reversed(rest):self.cx(x[p],x[j])
 def inv6(self,x,y,work):
  n=work[:3];a,b=x[:3],x[3:];v,w=y[:3],y[3:]
  self.frame(x,C.BASIS6,True);self.frame(y,C.BASIS6,True)
  st=len(self.ops);self.square(a,n,1,3,C.F3MOD);self.square(b,n,C.K3,3,C.F3MOD);self.prod(a,b,n,3,C.F3MOD);norm=self.ops[st:].copy()
  self.inv3_inplace(n)
  for i,j in zip(b,a):self.cx(i,j)
  self.prod(a,n,v,3,C.F3MOD)
  for i,j in zip(b,a):self.cx(i,j)
  self.prod(b,n,w,3,C.F3MOD)
  self.inv3_inplace(n);self.ops.extend(reversed(norm));self.frame(y,C.BASIS6);self.frame(x,C.BASIS6)
def clear(b,op,reg):
 mode,x,y,z,*k=op;x,y,z=[[reg[i] for i in w] for w in (x,y,z)]
 mb=list(b.alloc_bits(12));b.hmr(z,mb);ext=list(b.alloc_bits(11));mask=mb+ext
 for d in range(12,23):
  b.bit_store(mask[d],False)
  for j in C.bits(C.MOD^(1<<12)):b.cx(mask[d-12+j],mask[d])
 if mode=='norm':
  for i,q in enumerate(x):b.cz(q,mask[2*i])
  for i,q in enumerate(y):
   v=C.m(k[0],C.m(1<<i,1<<i))
   for j in C.bits(v):b.cz(q,mb[j])
 # Exact polynomial-basis field product, dual mask shared by i+j.
 for i,a in enumerate(x):
  for j,d in enumerate(y):b.ccz(a,d,mask[i+j])
 for bit in mask:b.bit_store(bit,False)
 b.free(mask)
def emit(ops,name,Q):
 b=km.CircuitBuilder();b.set_max_qubits(Q)
 reg=list(b.create_quantum_register(840,'data'))+list(b.alloc_qubits(Q-840))
 for g,*a in ops:
  if isinstance(g,str):clear(b,(g,*a),reg)
  else:getattr(b,('x','cx','ccx')[g])(*(reg[i] for i in a))
 b.free(km.array(reg[840:]));c=b.finish_circuit();p=Path(name+'.kmb');c.to_file(str(p),format='kmb')
 return km.Circuit.from_file(str(p)),p
def main():
 rows,loc=C.cases();out=[C.ref(s) for s in rows]
 # Confirm dual recurrence against all field monomial basis products, independent of simulator.
 masks=[1<<i for i in range(12)]
 for d in range(12,23):
  v=0
  for j in C.bits(C.MOD^(1<<12)):v^=masks[d-12+j]
  masks.append(v)
 assert all(masks[i+j]==C.m(1<<i,1<<j) for i in range(12) for j in range(12))
 # Every irreducible chart has norm zero iff (a,b)=(0,0).
 assert all(C.m(v,v)^v^k for k in C.ORDER for v in range(4096))
 pre=J.Old()
 for j in range(69,-1,-1):
  for h in range(1,min(j,36)+1):
   if C.M[36-h]:pre.constmul(C.word(j-h),C.word(j),C.M[36-h],12,C.MOD)
 results=[]
 for cls,Q,label in [(J.Joint,882,'pooled'),(Narrow,879,'narrow')]:
  C.Compact=cls;t=C.emit();C.Compact=J.Old
  assert t.ops[:len(pre.ops)]==pre.ops
  for name,ops,src,dst in [(label+'_fwd',t.ops,rows,out),(label+'_rev',t.ops[len(pre.ops):]+list(reversed(pre.ops)),out,rows)]:
   c,p=emit(ops,name,Q)
   r=dict(name=name,Q=c.num_qubits,ops=len(c),paid=int(c.operation_statistics().num_toffoli_like),sha256=hashlib.file_digest(p.open('rb'),'sha256').hexdigest())
   r.update(J.test(c,src,dst));results.append(r);print(json.dumps(r),flush=True)
 receipt=dict(scope='special all-pole locator codec only; no full DQI',irreducible_norm_checks=len(C.ORDER)*4096,phase_basis_checks=144,results=results)
 Path('narrow_crt_receipt.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps(receipt),flush=True)
if __name__=='__main__':main()
