"""Raw-syndrome, full native KMB regression; no external chart selection."""
import sys, json, hashlib, time
from pathlib import Path
import numpy as np
import kickmix as km
import verify_submission_dqi as V
rng=np.random.default_rng(202611280825)
t=V.FieldTables(km.GF2Field(12))
EXP=np.asarray(t.antilog); LOG=np.asarray(t.log)
def mul(a,b):return int(EXP[(int(LOG[a])+int(LOG[b]))%4095]) if a and b else 0
def inv(a):assert a;return int(EXP[(-int(LOG[a]))%4095])
K=(3134,3169,3257,3302,3384,3431,3519,3552,3592,3633,3671,3727,3792,3854,3921,3977,4054)
def cases():
 # Adversarial algebraic structure, independent of the original regression.
 # All legal supports are distinct and nonzero; no host-side chart selection.
 local=np.random.default_rng(202611281501)
 for w in range(36):
  for trial in range(4):
   # Four coupled affine-subspace supports, with multiplicative rescaling.
   off=int(local.integers(64,4096)) & ~63
   scale=int(local.integers(1,4096))
   X=[mul(scale,off^i) for i in range(w)]
   assert len(set(X))==w and 0 not in X
   pos=np.array([int(LOG[x]) for x in X],np.int64)
   if trial==0:v=np.ones(w,np.int64)
   elif trial==1:v=local.integers(1,4096,w,dtype=np.int64)
   elif trial==2:
    vals=[]
    for x in X:
     d=x
     for y in X:
      if x!=y:d=mul(d,x^y)
     vals.append(inv(d))
    v=np.array(vals,np.int64)
   else:
    vals=[]
    for x in X:
     d=x
     for y in X:
      if x!=y:d=mul(d,x^y)
     vals.append(mul(mul(x,x)^x^3169,inv(d)))
    v=np.array(vals,np.int64)
   assert all(v)
   yield 'affine_subspace_'+str(trial),w,pos,v

rows=[]
for tag,w,p,v in cases():
 a=np.bitwise_xor.reduce(EXP[(LOG[v][None,:]+np.arange(1,71)[:,None]*p[None,:])%4095],axis=1) if w else np.zeros(70,dtype=np.int64)
 for mode in ('zero','random','onehot'):
  M=np.zeros(4095,dtype=np.int64)
  if mode=='random':M=rng.integers(0,4096,4095,dtype=np.int64)
  if mode=='onehot':M[int(p[0]) if w else 0]=1<<int(rng.integers(0,12))
  phase=bool(sum((int(M[j])&int(val)).bit_count() for j,val in zip(p,v))%2)
  rows.append((tag,w,mode,a,M,phase))
# Interleave by weight/mode; first panel samples every weight, with each type of mask.
# Full default 996? rows: (144+70+102+16)*3=996.
if len(sys.argv)>3 and sys.argv[3]=='quick':
 rows=[row for i,row in enumerate(rows[:(144+70)*3]) if i%18<3]
p=Path(sys.argv[1]); out=Path(sys.argv[2]);c=km.Circuit.from_file(str(p))
sp=V.ProblemSpecDQI.benchmark_instance(num_shots=len(rows))
q,b,anc=map(km.array,V.validate_registers(c,sp))
res=dict(Q=c.num_qubits,ops=len(c),static_paid=int(c.operation_statistics().num_toffoli_like),sha256=hashlib.file_digest(p.open('rb'),'sha256').hexdigest(),shots=0,value=0,phase=0,dirty=0,mask=0,paid=0,groups={},failures=[])
for i in range(0,len(rows),64):
 batch=rows[i:i+64];S=V.to_bits(np.array([r[3] for r in batch]),12);M=V.to_bits(np.array([r[4] for r in batch]),12);P=np.array([r[5] for r in batch])
 sim=km.Simulator(batch_size=len(batch),seed=202611280825+i,debug_print=False,counting_operations=True)
 sim.use_same_registers_as(c);sim.write_across_shots(q,S);sim.write_across_shots(b,M);sim.do(c)
 errs=np.array([(sim.read_across_shots(q)!=S).any(0),np.asarray(sim.read_phase_flipped_across_shots())!=P,sim.read_across_shots(anc).any(0),(sim.read_across_shots(b)!=M).any(0)])
 for j,k in enumerate(('value','phase','dirty','mask')):res[k]+=int(errs[j].sum())
 res['paid']+=int(sim.operation_statistics().num_toffoli_like);res['shots']+=len(batch)
 for j,r in enumerate(batch):
  key=f'{r[0]}:{r[1]}:{r[2]}';g=res['groups'].setdefault(key,[0,0,0,0,0]);g[0]+=1
  for k in range(4):g[k+1]+=int(errs[k,j])
  if errs[:,j].any():res['failures'].append(dict(index=i+j,weight=r[1],group=r[0],mask_type=r[2],errors=errs[:,j].astype(int).tolist(),syndrome=r[3].tolist()))
 out.write_text(json.dumps(res,indent=2)+'\n')
 print({k:res[k] for k in ('shots','value','phase','dirty','mask','paid')},flush=True)
res['mean_paid']=res['paid']/res['shots'];res['pass']=not any(res[k] for k in ('value','phase','dirty','mask'));out.write_text(json.dumps(res,indent=2)+'\n')
print('FINAL', {k:v for k,v in res.items() if k not in ('groups','failures')},flush=True)
raise SystemExit(0 if res['pass'] else 1)

