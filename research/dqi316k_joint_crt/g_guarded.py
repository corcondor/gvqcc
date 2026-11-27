"""G-based #234 all-pole locator codec, using #235 CRT and joint HMR.
Both maps defined on arbitrary 840-bit data. No host-selected branch.
Tag XOR indicates the exact all-pole stratum on legal DQI syndromes.
Not a complete DQI phase oracle.
"""
import crt882 as C,joint_crt as J,narrow_crt as N
import kickmix as km,numpy as np,random,json,hashlib
from pathlib import Path
Q=881
def sw(t,a,b):
 for i,j in zip(a,b):t.cx(i,j);t.cx(j,i);t.cx(i,j)
class GCodec(N.Narrow):
 def ztest(self,x,f,work):
  for q in x:self.x(q)
  chain=[(x[0],x[1],work[0])]+[(work[i-1],x[i+1],work[i]) for i in range(1,len(x)-2)]
  for a,b,c in chain:self.ccx(a,b,c)
  self.ccx(work[len(x)-3],x[-1],f)
  for a,b,c in reversed(chain):self.ccx(a,b,c)
  for q in x:self.x(q)
 def pivot(self):
  a,b=C.word(68),C.word(69);work=list(range(841,Q))
  h=work[:12];f=work[12];tmp=work[13:25];sub=work[12:27]
  self.inv12(a,h,sub)
  self.ztest(a,f,work[13:23]);self.cx(f,a[0]);self.cx(f,h[0])
  sq=tuple(C.m(1<<i,1<<i) for i in range(12))
  self.frame(a,sq);self.frame(h,sq)
  self.prod(b,h,tmp,12,C.MOD);sw(self,b,tmp)
  self.ops.append(('prod',tuple(b),tuple(a),tuple(tmp)))
  self.frame(h,sq,True);self.frame(a,sq,True)
  self.cx(f,h[0]);self.cx(f,a[0]);self.ztest(a,f,work[13:23])
  sw(self,a,h);self.inv12(a,h,sub)
 def crt(self):
  nodes=[k for k in C.ORDER if k!=C.K]
  cols=[]
  for j in range(34):
   for b in range(12):
    v=0
    for i,k in enumerate(nodes):
     r=C.div([0]*(33-j)+[1<<b],[k,1,1])[1]
     v|=sum(x<<(12*h) for h,x in enumerate(r))<<(24*i)
    cols.append(v)
  cols=tuple(cols);reg=list(range(408));cand=[C.lin_ops(cols)]+[C.block_lin(cols,k) for k in range(3,10)];L=min(cand,key=len)
  for a,b in L:self.cx(reg[a],reg[b])
  for i,k in enumerate(nodes):self.inplace_inv24(reg[24*i:24*i+24],list(range(841,Q)),k)
  for a,b in reversed(L):self.cx(reg[a],reg[b])
 def convolution(self):
  for j in range(69,-1,-1):
   for h in range(1,min(j,34)+1):
    if C.G[34-h]:self.constmul(C.word(j-h),C.word(j),C.G[34-h],12,C.MOD)
 def orient(self):
  sw(self,C.word(68),C.word(34));sw(self,C.word(69),C.word(35))
  for j in range(34,0,-1):sw(self,C.word(j),C.word(j-1))
  for j in range(35,1,-1):sw(self,C.word(j),C.word(j-1))
 def lift(self):
  for j in range(34):
   self.constmul(C.word(0),C.word(35-j),(C.G[j-1] if j else 0)^C.m(C.G[j],C.G[33]),12,C.MOD)
   self.constmul(C.word(1),C.word(35-j),C.G[j],12,C.MOD)
def sections():
 def make(name):
  t=GCodec();getattr(t,name)();return t.ops
 return {n:make(n) for n in ('convolution','crt','pivot','orient','lift')}
def andtoggle(b,c,t,w):
 if len(c)==1:b.cx(c[0],t);return
 if len(c)==2:b.ccx(*c,t);return
 a=w[:len(c)-2];chain=[(c[0],c[1],a[0])]+[(a[i-1],c[i+1],a[i]) for i in range(1,len(a))]
 for x,y,z in chain:b.ccx(x,y,z)
 b.ccx(a[-1],c[-1],t)
 for x,y,z in reversed(chain):b.del_and(x,y,z)
def guard(b,reg):
 # After orientation first 36 words encode the projective locator,
 # W[36:68] and moved W[34:36] at positions 68:70 are the 34 zero tests.
 # Tag is an XOR oracle, so arbitrary incoming tag is preserved modulo predicate.
 work=reg[841:Q];flags=work[:18];scratch=work[18:]
 def one(group,f):
  for q in group:b.x(q)
  andtoggle(b,group,f,scratch)
  for q in group:b.x(q)
 for j in range(17):one(reg[432+24*j:432+24*j+24],flags[j])
 one(reg[:12],flags[17]);b.x(flags[17])
 andtoggle(b,flags,reg[840],scratch)
 b.x(flags[17]);one(reg[:12],flags[17])
 for j in reversed(range(17)):one(reg[432+24*j:432+24*j+24],flags[j])
def build(parts,reverse):
 b=km.CircuitBuilder();b.set_max_qubits(Q)
 reg=list(b.create_quantum_register(840,'data'))+list(b.create_quantum_register(1,'allpole'))+list(b.alloc_qubits(Q-841))
 def run(ops):
  for g,*a in ops:
   if isinstance(g,str):N.clear(b,(g,*a),reg)
   else:getattr(b,('x','cx','ccx')[g])(*(reg[j] for j in a))
 if not reverse:
  for n in ('convolution','crt','pivot','orient','lift'):run(parts[n])
  guard(b,reg)
 else:
  guard(b,reg);run(list(reversed(parts['lift'])));run(list(reversed(parts['orient'])));run(parts['pivot']);run(parts['crt']);run(list(reversed(parts['convolution'])))
 b.free(km.array(reg[841:]));return b.finish_circuit()
def ref(s):
 W=[C.xor_word(C.m(C.G[34-h],s[j-h]) for h in range(min(j,34)+1)) for j in range(70)]
 H=C.trim(W[:34][::-1]);T=[]
 for k in C.ORDER:
  if k==C.K:continue
  g=[k,1,1];r=C.div(H,g)[1];ri=C.inversemod(r,g) if r else []
  q,rem=C.div(C.G,g);assert not rem
  T=C.add(T,C.mul(q,C.div(C.mul(ri,C.inversemod(C.div(q,g)[1],g)),g)[1]))
 T=C.div(T,C.G)[1];a,b=W[68:70]
 q=C.inv(a) if a else 0; t=C.m(b,C.m(q,q)) if a else b
 F=C.add(T,C.mul(C.G,[t^C.m(q,C.G[33]),q]))
 return list(reversed(F+[0]*(36-len(F))))+W[36:68]+W[34:36],bool(q and not any(W[34:68]))
def main():
 rng=random.Random(235234);rows=[];known=[]
 for _ in range(128):
  xs=rng.sample(range(1,4096),35);D=[1]
  for x in xs:D=C.mul(D,[x,1])
  dp=[D[i] if i%2 else 0 for i in range(1,36)]
  a=rng.randrange(1,4096);es=[C.m(a,C.inv(C.m(C.m(x,C.evalp(C.G,x)),C.evalp(dp,x)))) for x in xs]
  rows.append(C.moment(xs,es));known.append((D,a))
 for w in range(36):
  for _ in range(2):
   xs=rng.sample(range(1,4096),w);rows.append(C.moment(xs,[rng.randrange(1,4096) for x in xs]))
 # Compare with #235's different all-pole stratum and arbitrary coordinates.
 other,_=C.cases();rows+=other
 for _ in range(64):rows.append([rng.randrange(4096) for _ in range(70)])
 out,flag=zip(*(ref(s) for s in rows))
 for (y,f),(d,a) in zip(zip(out,flag),known):
  assert f and y[:36]==list(reversed([C.m(x,C.inv(a)) for x in d])) and not any(y[36:])
 print('REFERENCE',len(rows),'allpole',sum(flag),flush=True)
 parts=sections();rs=[]
 for rev in (False,True):
  c=build(parts,rev);p=Path('g_guarded_'+('rev' if rev else 'fwd')+'.kmb');c.to_file(str(p),format='kmb');c=km.Circuit.from_file(str(p))
  src,dst=(out,rows) if rev else (rows,out)
  q=km.array([km.q(i) for i in range(840)]);a=km.array([km.q(i) for i in range(841,c.num_qubits)]);tag=km.array([km.q(840)])
  err=[0]*4;shots=0
  def bits(z):return ((np.array(z,dtype=np.uint16)[:,:,None]>>np.arange(12))&1).reshape(len(z),840).T.astype(bool)
  for seed in (230,431):
   for st in range(0,len(rows),64):
    A=bits(src[st:st+64]);B=bits(dst[st:st+64]);F=np.array(flag[st:st+64],bool)
    r=np.random.default_rng(seed+st).integers(0,2,len(F)).astype(bool)
    sim=km.Simulator(batch_size=len(F),seed=seed+st,debug_print=False);sim.use_same_registers_as(c);sim.write_across_shots(q,A);sim.write_across_shots(tag,r[None,:]);sim.do(c)
    E=[(sim.read_across_shots(q)!=B).any(0),sim.read_across_shots(tag)[0]!=(r^F),sim.read_across_shots(a).any(0),sim.read_phase_flipped_across_shots()];err=[u+int(v.sum()) for u,v in zip(err,E)];shots+=len(F)
  res=dict(reverse=rev,Q=c.num_qubits,ops=len(c),paid=int(c.operation_statistics().num_toffoli_like),shots=shots,errors=err,sha256=hashlib.file_digest(p.open('rb'),'sha256').hexdigest());print(json.dumps(res),flush=True);assert not any(err);rs.append(res)
 Path('g_guarded_receipt.json').write_text(json.dumps(dict(scope='G-based #234 all-pole locator with exact guard, NOT phase oracle',inputs=len(rows),allpole=sum(flag),known_locators=len(known),results=rs),indent=2)+'\n')
if __name__=='__main__':main()
