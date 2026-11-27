"""Guarded G all-pole phase oracle. #237 CRT + direct nested-norm phase.
Only the all-pole stratum is decoded; identity on the complement.
No input-selected host branch, no lookup of the input error support.
"""
import crt882 as C, narrow_crt as N, g_guarded as G
import kickmix as km,numpy as np,random,json,hashlib,argparse
from pathlib import Path
from functools import lru_cache
Q=881

def emit(b,t,reg):
 for g,*a in t.ops:
  if isinstance(g,str):N.clear(b,(g,*a),reg)
  else:getattr(b,('x','cx','ccx')[g])(*(reg[i] for i in a))

def arith(b,method,*args):
 # Directly emit the existing exact Compact generator on local abstract indices.
 groups=[a for a in args if isinstance(a,list)]
 flat=sum(groups,[])
 assert len(set(flat))==len(flat)
 idx={v:i for i,v in enumerate(flat)}
 t=C.Compact()
 getattr(t,method)(*[[idx[v] for v in a] if isinstance(a,list) else a for a in args])
 emit(b,t,flat)

def xor(b,a,z):
 for x,y in zip(a,z):b.cx(x,y)
def frame(b,a,cols,rev=False):
 L=C.lin_ops(tuple(cols))
 for i,j in (reversed(L) if rev else L):b.cx(a[i],a[j])
def cclear(b,bits):
 for v in bits:b.bit_store(v,False)
 b.free(bits)
def measure(b,z):
 m=list(b.alloc_bits(len(z)));b.hmr(z,m);return m

def prodphase(b,a,c,m,n,mod):
 """m is a classical bit mask; pooled high-degree coefficients."""
 mask=list(m)+list(b.alloc_bits(n-1))
 for d in range(n,2*n-1):
  b.bit_store(mask[d],False)
  for j in C.bits(mod^(1<<n)):b.cx(mask[d-n+j],mask[d])
 for i,x in enumerate(a):
  for j,y in enumerate(c):b.ccz(x,y,mask[i+j])
 cclear(b,mask[n:])
def linearphase(b,a,m,cols):
 for i,x in enumerate(a):
  for j in C.bits(cols[i]):b.cz(x,m[j])
def norm_compute(b,a,c,z,n,k,mod):
 arith(b,'square',a,z,1,n,mod)
 arith(b,'square',c,z,k,n,mod)
 arith(b,'prod',a,c,z,n,mod)
def norm_clear(b,a,c,z,n,k,mod):
 m=measure(b,z)
 linearphase(b,a,m,[C.gf_mul(1<<i,1<<i,n,mod) for i in range(n)])
 linearphase(b,c,m,[C.gf_mul(k,C.gf_mul(1<<i,1<<i,n,mod),n,mod) for i in range(n)])
 prodphase(b,a,c,m,n,mod);cclear(b,m)
def product_clear(b,a,c,z,n,mod):
 m=measure(b,z);prodphase(b,a,c,m,n,mod);cclear(b,m)
def inv3_clear(b,a,z):
 m=measure(b,z)
 anf=[C.gf_pow(x,6,3,C.F3MOD) for x in range(8)]
 for k in range(3):
  for j in range(8):
   if j>>k&1:anf[j]^=anf[j^(1<<k)]
 for j,v in enumerate(anf):
  if not v:continue
  xs=[a[k] for k in C.bits(j)]
  assert len(xs) in (1,2)
  for k in C.bits(v):
   if len(xs)==1:b.cz(xs[0],m[k])
   else:b.ccz(xs[0],xs[1],m[k])
 cclear(b,m)
def root_compute(b,f,tag,chain):
 # Store all intermediate conjunctions until phase has been applied.
 for x in f:b.x(x)
 cs=list(f)+[tag]
 b.ccx(cs[0],cs[1],chain[0])
 for i in range(1,len(chain)):b.ccx(chain[i-1],cs[i+1],chain[i])
 return cs
def root_clear(b,cs,chain):
 for i in range(len(chain)-1,0,-1):b.del_and(chain[i-1],cs[i+1],chain[i])
 b.del_and(cs[0],cs[1],chain[0])
 for x in cs[:-1]:b.x(x)
@lru_cache(None)
def mask_cols(x):
 g=C.evalp(C.G,x);assert g
 return tuple(C.m(C.inv(g),a) for a in C.BASIS12)
def kernel(b,f,d,tag,work,mask,x):
 chain=work[:12];n=work[12:18];nn=work[18:21];h=work[21:24];hg=work[24:27];y=work[27:33]
 cs=root_compute(b,f,tag,chain);r=chain[-1]
 frame(b,d,C.BASIS12,True);a,c=d[:6],d[6:]
 norm_compute(b,a,c,n,6,C.K6,C.F6MOD)
 frame(b,n,C.BASIS6,True);u,v=n[:3],n[3:]
 norm_compute(b,u,v,nn,3,C.K3,C.F3MOD)
 arith(b,'inv3',nn,h)
 for i,j in zip(h,hg):b.ccx(r,i,j)
 xor(b,v,u);arith(b,'prod',u,hg,y[:3],3,C.F3MOD);xor(b,v,u)
 arith(b,'prod',v,hg,y[3:],3,C.F3MOD)
 frame(b,y,C.BASIS6)
 # Move constant G(x)^-1 into the classical phase mask, not the quantum data.
 dual=list(b.alloc_bits(12))
 for i,col in enumerate(mask_cols(x)):
  b.bit_store(dual[i],False)
  for j in C.bits(col):b.cx(mask[j],dual[i])
 xor(b,c,a);prodphase(b,a,y,dual[:6],6,C.F6MOD);xor(b,c,a)
 prodphase(b,c,y,dual[6:],6,C.F6MOD);cclear(b,dual)
 frame(b,y,C.BASIS6,True)
 xor(b,v,u);product_clear(b,u,hg,y[:3],3,C.F3MOD);xor(b,v,u)
 product_clear(b,v,hg,y[3:],3,C.F3MOD)
 m=measure(b,hg)
 for q,z in zip(h,m):b.ccz(r,q,z)
 cclear(b,m)
 inv3_clear(b,nn,h)
 norm_clear(b,u,v,nn,3,C.K3,C.F3MOD)
 frame(b,n,C.BASIS6)
 norm_clear(b,a,c,n,6,C.K6,C.F6MOD)
 frame(b,d,C.BASIS12);root_clear(b,cs,chain)

def build(count):
 b=km.CircuitBuilder();b.set_max_qubits(Q)
 reg=[q for i in range(70) for q in b.create_quantum_register(12,f'S{i}')]+list(b.alloc_qubits(Q-840))
 mask=[v for i in range(count) for v in b.create_classical_register(12,f'E{i}')]
 tag=reg[840];work=reg[841:]
 parts=G.sections()
 def run(ops):
  for g,*a in ops:
   if isinstance(g,str):N.clear(b,(g,*a),reg)
   else:getattr(b,('x','cx','ccx')[g])(*(reg[j] for j in a))
 for p in ('convolution','crt','pivot','orient','lift'):run(parts[p])
 G.guard(b,reg)
 # Reversed polynomial coefficients: word j holds coefficient 35-j.
 words=[reg[12*(35-j):12*(36-j)] for j in range(36)]
 rolls=[tuple(C.m(C.exp[j],1<<i) for i in range(12)) for j in range(36)]
 for k in range(count):
  f,d=words[0],words[1]
  for j in range(3,36,2):xor(b,words[j],d)
  xor(b,d,f)
  for j in range(2,36,2):xor(b,words[j],f)
  kernel(b,f,d,tag,work,mask[12*k:12*k+12],C.exp[k])
  for j in range(2,36,2):xor(b,words[j],f)
  xor(b,d,f)
  for j in range(3,36,2):xor(b,words[j],d)
  # Roll all terms by alpha^j to the next evaluation point.
  for j in range(1,36):frame(b,words[j],rolls[j])
  if k%512==0:print('SCAN',k,flush=True)
 # Return polynomial coefficients to the original frame, even for a partial scan.
 if count%4095:
  for j in range(1,36):
   const=C.exp[(-count*j)%4095]
   frame(b,words[j],tuple(C.m(const,1<<i) for i in range(12)))
 G.guard(b,reg)
 for p in ('lift','orient'):run(list(reversed(parts[p])))
 for p in ('pivot','crt'):run(parts[p])
 run(list(reversed(parts['convolution'])))
 b.free(km.array(reg[840:]));return b.finish_circuit()

def cases(count,n=32):
 rng=random.Random(671237);rows=[];mags=[];flags=[]
 # Include allpole with some roots in the scan window; for a short scan, guarantee hits.
 for i in range(n):
  inside=rng.sample(range(count),min(count,1+i%min(8,count)))
  outside=rng.sample([j for j in range(4095) if j not in set(inside)],35-len(inside))
  loc=inside+outside;xs=[C.exp[j] for j in loc];D=[1]
  for x in xs:D=C.mul(D,[x,1])
  dp=[D[i] if i%2 else 0 for i in range(1,36)]
  a=rng.randrange(1,4096);es=[C.m(a,C.inv(C.m(C.m(x,C.evalp(C.G,x)),C.evalp(dp,x)))) for x in xs]
  rows.append(C.moment(xs,es));mags.append(dict(zip(loc,es)));flags.append(True)
 for w in (0,1,2,6,17,18,31,35):
  for _ in range(max(2,n//8)):
   xs=rng.sample(range(1,4096),w);es=[rng.randrange(1,4096) for x in xs]
   s=C.moment(xs,es);assert not G.ref(s)[1]
   rows.append(s);mags.append({});flags.append(False)
 for _ in range(max(4,n//4)):
  s=[rng.randrange(4096) for _ in range(70)];assert not G.ref(s)[1]
  rows.append(s);mags.append({});flags.append(False)
 return rows,mags,flags

def test(c,count,n):
 rows,mags,flags=cases(count,n)
 q=km.array([km.q(i) for i in range(840)])
 anc=km.array([km.q(i) for i in range(840,c.num_qubits)])
 # Registered public mask starts at classical bit 0.
 mask=km.array([km.b(i) for i in range(12*count)])
 errs=[0]*4;shots=0;paid=0;phase_counts=[0,0];rng=np.random.default_rng(697237)
 A=((np.asarray(rows,np.uint16)[:,:,None]>>np.arange(12))&1).reshape(len(rows),840).T.astype(bool)
 for seed in (681,937):
  for st in range(0,len(rows),32):
   en=min(st+32,len(rows));N0=en-st
   M=rng.integers(0,4096,(N0,count),dtype=np.uint16)
   # Deterministic zero and one-hot masks supplement dense masks.
   if seed==681:
    for i in range(N0):
     if (st+i)%4==0:M[i]=0
     elif (st+i)%4==1:
      M[i]=0
      pos=next((p for p in mags[st+i] if p<count),0)
      M[i,pos]=1<<((st+i)%12)
   exp=np.array([sum((int(M[i,p])&v).bit_count() for p,v in mags[st+i].items() if p<count)%2 for i in range(N0)],bool)
   mb=((M[:,:,None]>>np.arange(12))&1).reshape(N0,-1).T.astype(bool)
   s=km.Simulator(batch_size=N0,seed=seed+st,debug_print=False,counting_operations=True)
   s.use_same_registers_as(c);s.write_across_shots(q,A[:,st:en]);s.write_across_shots(mask,mb);s.do(c)
   E=[(s.read_across_shots(q)!=A[:,st:en]).any(0),(s.read_across_shots(mask)!=mb).any(0),s.read_across_shots(anc).any(0),s.read_phase_flipped_across_shots()!=exp]
   errs=[u+int(v.sum()) for u,v in zip(errs,E)];shots+=N0;paid+=int(s.operation_statistics().num_toffoli_like)
   phase_counts[1]+=int(exp.sum());phase_counts[0]+=N0-int(exp.sum())
   print('TEST',seed,st,errs,flush=True)
 return dict(inputs=len(rows),allpole_inputs=sum(flags),shots=shots,errors=errs,expected_phase_counts=phase_counts,mean_paid=paid/shots)

def main():
 p=argparse.ArgumentParser();p.add_argument('--count',type=int,default=32);p.add_argument('--cases',type=int,default=32);a=p.parse_args();assert 1<=a.count<=4095
 c=build(a.count);path=Path(f'guarded_phase_{a.count}.kmb');c.to_file(str(path),format='kmb');del c
 c=km.Circuit.from_file(str(path));r=dict(scope='guarded G allpole phase oracle, identity outside chart, not full DQI',scan_points=a.count,Q=c.num_qubits,ops=len(c),static_paid=int(c.operation_statistics().num_toffoli_like),sha256=hashlib.file_digest(path.open('rb'),'sha256').hexdigest())
 print(json.dumps(r),flush=True);r.update(test(c,a.count,a.cases));print(json.dumps(r),flush=True);path.with_suffix('.json').write_text(json.dumps(r,indent=2)+'\n');assert not any(r['errors'])
if __name__=='__main__':main()
