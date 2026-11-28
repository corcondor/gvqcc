"""Joint #235 CRT codec + #226 HMR phase transport + #190 exact 42-CCX tensor.
Native KMB; special all-pole locator codec, not a full DQI oracle.
"""
import crt882 as C
import numpy as np, kickmix as km
from pathlib import Path
import hashlib,json,collections
from importlib.metadata import version
Old=C.Compact
def classify():
 for g,*a in C.GATES:
  if g==1:
   assert (a[0]<24)==(a[1]<24)
  else:assert g==2 and a[0]<24 and a[1]<24 and a[2]>=24
class Joint(Old):
 def inplace_inv24(self,x,work,k):
  a,b=x[:12],x[12:];n,h,tmp=work[:12],work[12:24],work[24:36];sub=work[24:42]
  self.square(a,n,1,12,C.MOD);self.square(b,n,k,12,C.MOD);self.prod(a,b,n,12,C.MOD)
  self.inv12(n,h,sub)
  for i,j in zip(b,a):self.cx(i,j)
  for r in (a,b):
   self.prod(r,h,tmp,12,C.MOD)
   for i,j in zip(r,tmp):self.cx(i,j);self.cx(j,i);self.cx(i,j)
   # tmp = r*n exactly, incl zero, so reset and repay phase.
   self.ops.append(('prod',tuple(r),tuple(n),tuple(tmp)))
  self.inv12(h,n,sub)
  # h = norm(new a,b), incl zero.
  self.ops.append(('norm',tuple(a),tuple(b),tuple(h),k))
def clear(b,op,reg):
 mode,x,y,z,*k=op;x,y,z=[[reg[i] for i in w] for w in (x,y,z)]
 mb=list(b.alloc_bits(12));b.hmr(z,mb)
 if mode=='norm':
  for w,c in ((x,1),(y,k[0])):
   for i,q in enumerate(w):
    v=C.m(c,C.m(1<<i,1<<i))
    for j in C.bits(v):b.cz(q,mb[j])
 # Pull the measured mask backward through the target frame.
 # Input frames are replayed and uncomputed, never measuring x,y.
 data=x+y
 for g,*a in C.GATES:
  if g==1 and a[0]<24:b.cx(data[a[0]],data[a[1]])
 for g,*a in reversed(C.GATES):
  if g==1:
   if a[0]<24:b.cx(data[a[0]],data[a[1]])
   else:b.cx(mb[a[1]-24],mb[a[0]-24])
  else:b.ccz(data[a[0]],data[a[1]],mb[a[2]-24])
 for bit in mb:b.bit_store(bit,False)
 b.free(mb)
def emit_kmb(ops,name):
 b=km.CircuitBuilder();b.set_max_qubits(882)
 reg=list(b.create_quantum_register(840,'data'))+list(b.alloc_qubits(42))
 for g,*a in ops:
  if isinstance(g,str):clear(b,(g,*a),reg)
  else:getattr(b,('x','cx','ccx')[g])(*(reg[i] for i in a))
 b.free(km.array(reg[840:]));c=b.finish_circuit()
 p=Path(name+'.kmb');c.to_file(str(p),format='kmb')
 return km.Circuit.from_file(str(p)),p
def test(c,rows,out,seeds=(229,431)):
 q=km.array([km.q(i) for i in range(840)])
 a=km.array([km.q(i) for i in range(840,c.num_qubits)])
 errs=[0]*3;shots=0
 def bits(x):return ((x[:,:,None]>>np.arange(12))&1).reshape(len(x),840).T.astype(bool)
 for seed in seeds:
  for st in range(0,len(rows),64):
   x=bits(np.asarray(rows[st:st+64],np.uint16));y=bits(np.asarray(out[st:st+64],np.uint16))
   s=km.Simulator(batch_size=x.shape[1],seed=seed+st,debug_print=False)
   s.use_same_registers_as(c);s.write_across_shots(q,x);s.do(c)
   errors=[(s.read_across_shots(q)!=y).any(0),s.read_across_shots(a).any(0),s.read_phase_flipped_across_shots()]
   errs=[u+int(np.asarray(v).sum()) for u,v in zip(errs,errors)];shots+=x.shape[1]
 assert not any(errs),errs
 return dict(shots=shots,errors=errs)
def main():
 classify();rows,loc=C.cases();out=[C.ref(s) for s in rows]
 for y,(D,co) in zip(out,loc):
  assert y[:36]==list(reversed([C.m(x,C.inv(co)) for x in D])) and not any(y[36:])
 # Independent forward reference and inverse roundtrip, including zero CRT components.
 old=C.emit();C.Compact=Joint;new=C.emit();C.Compact=Old
 pre=Old()
 for j in range(69,-1,-1):
  for h in range(1,min(j,36)+1):
   if C.M[36-h]:pre.constmul(C.word(j-h),C.word(j),C.M[36-h],12,C.MOD)
 assert new.ops[:len(pre.ops)]==pre.ops
 reverse=new.ops[len(pre.ops):]+list(reversed(pre.ops))
 result=[]
 for name,ops,src,dst,seeds in [('baseline',old.ops,rows,out,(229,)),('joint_forward',new.ops,rows,out,(229,431)),('joint_reverse',reverse,out,rows,(229,431))]:
  c,p=emit_kmb(ops,name)
  r=dict(name=name,Q=c.num_qubits,ops=len(c),paid=int(c.operation_statistics().num_toffoli_like),sha256=hashlib.file_digest(p.open('rb'),'sha256').hexdigest())
  r.update(test(c,src,dst,seeds));result.append(r);print(json.dumps(r),flush=True)
 receipt=dict(scope='all-pole locator codec only, arbitrary-data reversible map; no full DQI oracle or score',kickmix=version('kickmix'),allpole_locators=len(loc),inputs=len(rows),results=result,hmr_product_clears=sum(o[0]=='prod' for o in new.ops),hmr_norm_clears=sum(o[0]=='norm' for o in new.ops))
 Path('joint_crt_receipt.json').write_text(json.dumps(receipt,indent=2)+'\n')
 print(json.dumps(receipt),flush=True)
if __name__=='__main__':main()
