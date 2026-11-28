"""Full matched #247 repair regression, standard failure kept separate.
No sample-based external circuit selection. Parent and repair execute all rows."""
import json,hashlib,glob,sys
from pathlib import Path
import numpy as np,kickmix as km
field=km.GF2Field(12)
ant=np.array([field.pow(field.primitive_element,i) for i in range(4095)],dtype=np.int64)
log=np.zeros(4096,dtype=np.int64);log[ant]=np.arange(4095)
k=np.arange(36,dtype=float);off=np.sqrt(k[1:]*(4095-k[1:]+1))
d=(4096-4032)/np.sqrt(2016*(4096-2016));_,ev=np.linalg.eigh(np.diag(k*d)+np.diag(off,1)+np.diag(off,-1));p=ev[:,-1]**2;p/=p.sum()
rows=np.arange(1,71)[:,None]
def generate():
 B=256;seed=202611280745
 seeds=np.random.SeedSequence(seed,pool_size=8).generate_state(8*4,dtype=np.uint64).reshape(-1,2,4)
 panels=[]
 for s in seeds:
  rs,ss=(int.from_bytes(s[0],'little'),int.from_bytes(s[1],'little'))
  r=np.random.default_rng(rs);w=r.choice(36,size=B,p=p);M=r.integers(0,4095,size=(B,4095),endpoint=True,dtype=np.int64);w=(np.arange(B)+rs%36)%36
  S=np.zeros((B,70),dtype=np.int64);phase=np.zeros(B,dtype=bool)
  for j in np.flatnonzero(w):
   z=int(w[j]);pos=r.choice(4095,size=z,replace=False);v=r.integers(1,4095,size=z,endpoint=True,dtype=np.int64)
   S[j]=np.bitwise_xor.reduce(ant[(log[v][None,:]+rows*pos[None,:])%4095],axis=1)
   phase[j]=sum(int(x).bit_count() for x in v&M[j,pos])&1==1
  panels.append(('forced',ss,S,M,w,phase))
 # Previously failed standard input, original mask and zero mask, two histories.
 for file in glob.glob('/tmp/fail_*_0.npz'):
  z=np.load(file);S=z['S'];M=z['M'];w=z['weights'];ph=z['expected']
  for seed in (371,372):
   panels.append(('standard_failure_original_mask',seed,S,M,w,ph))
   panels.append(('standard_failure_zero_mask',seed,S,np.zeros_like(M),w,np.zeros(len(w),bool)))
 return panels
def bits(v):return (((v[:,:,None]>>np.arange(12))&1)==1).transpose(1,2,0).reshape(-1,len(v))
def main():
 panels=generate();result={}
 for path in sys.argv[1:]:
  c=km.Circuit.from_file(path);reg=c.register_data
  q=km.array([v for i in range(70) for v in reg[f'S{i}']]);m=km.array([v for j in range(4095) for v in reg[f'E{j}']]);qs=set(q);a=km.array([km.q(i) for i in range(c.num_qubits) if km.q(i) not in qs])
  totals={}
  for name,seed,S,M,W,phase in panels:
   x=bits(S);y=bits(M);sim=km.Simulator(batch_size=len(W),seed=seed,debug_print=False,counting_operations=True);sim.use_same_registers_as(c);sim.write_across_shots(q,x);sim.write_across_shots(m,y);sim.do(c)
   VE=(sim.read_across_shots(q)!=x).any(0);PE=(sim.read_phase_flipped_across_shots()!=phase);AE=sim.read_across_shots(a).any(0);ME=(sim.read_across_shots(m)!=y).any(0);U=VE|PE|AE|ME
   T=totals.setdefault(name,dict(shots=0,value=0,raw_phase=0,ancilla=0,mask=0,union=0,paid=0,by_weight={}))
   T['shots']+=len(W);T['paid']+=int(sim.operation_statistics().num_toffoli_like)
   for k,z in zip(('value','raw_phase','ancilla','mask','union'),(VE,PE,AE,ME,U)):T[k]+=int(z.sum())
   for w in np.unique(W):
    ix=W==w;row=T['by_weight'].setdefault(str(w),[0]*6);row[0]+=int(ix.sum())
    for j,z in enumerate((VE,PE,AE,ME,U),1):row[j]+=int((ix&z).sum())
   print(path,name,seed,len(W),[int(z.sum()) for z in (VE,PE,AE,ME,U)],flush=True)
   if U.any() and name=='forced':np.savez_compressed(f'/tmp/{Path(path).stem}_forced_{seed}.npz',S=S[U],M=M[U],weights=W[U],expected=phase[U],value=VE[U],phase=PE[U])
  for t in totals.values():t['mean_paid']=t.pop('paid')/t['shots']
  result[path]=dict(sha256=hashlib.file_digest(open(path,'rb'),'sha256').hexdigest(),Q=c.num_qubits,static_paid=int(c.operation_statistics().num_toffoli_like),ops=len(c),panels=totals)
  del sim,c
  Path('repaired247_receipt.json').write_text(json.dumps(result,indent=2)+'\n')
 print(json.dumps(result),flush=True)
if __name__=='__main__':main()
